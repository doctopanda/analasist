# Health Centers Surveillance System - R Shiny Application
# Sistema de Vigilancia Epidemiológica de Centros de Salud

library(shiny)
library(shinydashboard)
library(DT)
library(leaflet)
library(plotly)
library(dplyr)
library(readr)
library(readxl)
library(shinycssloaders)
library(shinyWidgets)

# Load permanent health centers data
load_permanent_health_centers <- function() {
  # Sample of the 1649+ health centers - you can expand this with your full dataset
  data.frame(
    id = c("SSHES001A00", "SSHES002B00", "SSHES003A00", "SSHES004B00", "SSHES005A00"),
    nombre = c(
      "Hospital General del Estado de Sonora Dr. Ernesto Ramos Bours",
      "Centro de Salud Urbano Villa de Seris",
      "Hospital General de Cajeme",
      "Centro de Salud Nogales",
      "Hospital General San Luis Río Colorado"
    ),
    direccion = c(
      "Blvd. Luis Encinas Johnson s/n, Col. Centro",
      "Calle Sonora #123, Col. Villa de Seris",
      "Calle 5 de Febrero #311, Col. Centro",
      "Av. Álvaro Obregón #1234, Col. Centro",
      "Av. Reforma #567, Col. Benito Juárez"
    ),
    municipio = c("Hermosillo", "Hermosillo", "Cajeme", "Nogales", "San Luis Río Colorado"),
    estado = rep("Sonora", 5),
    distrito = c("Distrito 1", "Distrito 1", "Distrito 2", "Distrito 3", "Distrito 4"),
    tipo = c("Hospital", "Centro de Salud", "Hospital", "Centro de Salud", "Hospital"),
    telefono = c("662-259-2500", "662-215-8900", "644-414-0050", "631-311-2500", "653-534-1234"),
    responsable = c(
      "Dr. Juan Carlos Pérez García",
      "Dra. María Elena González López",
      "Dr. Carlos Alberto Rodríguez Martínez",
      "Dra. Ana Patricia López Hernández",
      "Dr. Roberto Martínez Silva"
    ),
    lat = c(29.0729, 29.0892, 27.3833, 31.3081, 32.4606),
    lng = c(-110.9559, -110.9618, -109.9167, -110.9342, -114.7706),
    clues = c("SSHES001A00", "SSHES002B00", "SSHES003A00", "SSHES004B00", "SSHES005A00"),
    stringsAsFactors = FALSE
  )
}

# Load sample reports data
load_sample_reports <- function() {
  data.frame(
    id = 1:10,
    folio = paste0("FOL-", 1040:1049),
    fecha_subida = Sys.Date() - sample(0:30, 10, replace = TRUE),
    fecha_consulta = Sys.Date() - sample(0:30, 10, replace = TRUE),
    centro_salud = sample(c("Hospital General del Estado", "Centro de Salud Villa de Seris"), 10, replace = TRUE),
    municipio = sample(c("Hermosillo", "Cajeme", "Nogales"), 10, replace = TRUE),
    distrito = sample(c("Distrito 1", "Distrito 2", "Distrito 3"), 10, replace = TRUE),
    diagnostico = sample(c("Dengue", "COVID-19", "Influenza", "Zika"), 10, replace = TRUE),
    edad_paciente = sample(18:80, 10, replace = TRUE),
    sexo = sample(c("M", "F"), 10, replace = TRUE),
    estado = sample(c("procesado", "pendiente", "revision"), 10, replace = TRUE),
    stringsAsFactors = FALSE
  )
}

# Load sample alerts data
load_sample_alerts <- function() {
  data.frame(
    id = 1:5,
    tipo = c("brote", "incremento", "cluster", "anomalia", "brote"),
    titulo = c(
      "Posible brote de Dengue en Hermosillo",
      "Incremento de casos de COVID-19 en Cajeme",
      "Cluster de Influenza en Nogales",
      "Anomalía en reportes de Zika",
      "Brote de Chikungunya en Navojoa"
    ),
    municipio = c("Hermosillo", "Cajeme", "Nogales", "San Luis Río Colorado", "Navojoa"),
    distrito = c("Distrito 1", "Distrito 2", "Distrito 3", "Distrito 4", "Distrito 2"),
    diagnostico = c("Dengue", "COVID-19", "Influenza", "Zika", "Chikungunya"),
    casos_detectados = c(8, 12, 6, 3, 5),
    fecha_deteccion = Sys.Date() - sample(0:15, 5, replace = TRUE),
    severidad = c("alta", "critica", "media", "baja", "alta"),
    estado = c("activa", "activa", "investigando", "resuelta", "activa"),
    lat = c(29.0729, 27.3833, 31.3081, 32.4606, 27.0667),
    lng = c(-110.9559, -109.9167, -110.9342, -114.7706, -109.4333),
    stringsAsFactors = FALSE
  )
}

# Initialize data
health_centers <- load_permanent_health_centers()
reports_data <- load_sample_reports()
alerts_data <- load_sample_alerts()

# Define UI
ui <- dashboardPage(
  dashboardHeader(title = "Sistema de Vigilancia Epidemiológica - Sonora"),
  
  dashboardSidebar(
    sidebarMenu(
      menuItem("Panel Principal", tabName = "dashboard", icon = icon("tachometer-alt")),
      menuItem("Centros de Salud", tabName = "health_centers", icon = icon("hospital")),
      menuItem("Mapa Interactivo", tabName = "map", icon = icon("map")),
      menuItem("Reportes", tabName = "reports", icon = icon("file-medical")),
      menuItem("Alertas", tabName = "alerts", icon = icon("exclamation-triangle")),
      menuItem("Análisis", tabName = "analysis", icon = icon("chart-bar")),
      menuItem("Cargar Datos", tabName = "upload", icon = icon("upload"))
    )
  ),
  
  dashboardBody(
    tags$head(
      tags$style(HTML("
        .content-wrapper, .right-side {
          background-color: #f4f4f4;
        }
        .box {
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .info-box {
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .leaflet-container {
          border-radius: 8px;
        }
      "))
    ),
    
    tabItems(
      # Dashboard Tab
      tabItem(tabName = "dashboard",
        fluidRow(
          infoBoxOutput("total_centers"),
          infoBoxOutput("total_reports"),
          infoBoxOutput("active_alerts")
        ),
        fluidRow(
          box(
            title = "Reportes por Diagnóstico", status = "primary", solidHeader = TRUE,
            width = 6, height = 400,
            withSpinner(plotlyOutput("diagnosis_chart"))
          ),
          box(
            title = "Centros por Tipo", status = "success", solidHeader = TRUE,
            width = 6, height = 400,
            withSpinner(plotlyOutput("centers_type_chart"))
          )
        ),
        fluidRow(
          box(
            title = "Actividad Reciente", status = "info", solidHeader = TRUE,
            width = 12,
            withSpinner(DT::dataTableOutput("recent_activity"))
          )
        )
      ),
      
      # Health Centers Tab
      tabItem(tabName = "health_centers",
        fluidRow(
          box(
            title = "Filtros", status = "primary", solidHeader = TRUE,
            width = 12, collapsible = TRUE,
            fluidRow(
              column(4,
                textInput("search_centers", "Buscar Centro:", placeholder = "Nombre, dirección, CLUES...")
              ),
              column(4,
                selectInput("filter_municipality", "Municipio:",
                  choices = c("Todos" = "", unique(health_centers$municipio)),
                  selected = ""
                )
              ),
              column(4,
                selectInput("filter_type", "Tipo:",
                  choices = c("Todos" = "", unique(health_centers$tipo)),
                  selected = ""
                )
              )
            )
          )
        ),
        fluidRow(
          box(
            title = "Centros de Salud de Sonora", status = "success", solidHeader = TRUE,
            width = 12,
            withSpinner(DT::dataTableOutput("health_centers_table"))
          )
        )
      ),
      
      # Map Tab
      tabItem(tabName = "map",
        fluidRow(
          box(
            title = "Mapa de Centros de Salud - Sonora", status = "primary", solidHeader = TRUE,
            width = 12, height = 600,
            withSpinner(leafletOutput("health_centers_map", height = 550))
          )
        ),
        fluidRow(
          box(
            title = "Estadísticas del Mapa", status = "info", solidHeader = TRUE,
            width = 12,
            verbatimTextOutput("map_stats")
          )
        )
      ),
      
      # Reports Tab
      tabItem(tabName = "reports",
        fluidRow(
          infoBoxOutput("total_reports_tab"),
          infoBoxOutput("pending_reports"),
          infoBoxOutput("processed_reports")
        ),
        fluidRow(
          box(
            title = "Filtros de Reportes", status = "primary", solidHeader = TRUE,
            width = 12, collapsible = TRUE,
            fluidRow(
              column(3,
                textInput("search_reports", "Buscar:", placeholder = "Folio, centro...")
              ),
              column(3,
                selectInput("filter_diagnosis", "Diagnóstico:",
                  choices = c("Todos" = "", unique(reports_data$diagnostico)),
                  selected = ""
                )
              ),
              column(3,
                selectInput("filter_status", "Estado:",
                  choices = c("Todos" = "", unique(reports_data$estado)),
                  selected = ""
                )
              ),
              column(3,
                dateRangeInput("date_range", "Rango de Fechas:",
                  start = min(reports_data$fecha_subida),
                  end = max(reports_data$fecha_subida)
                )
              )
            )
          )
        ),
        fluidRow(
          box(
            title = "Reportes SUIVE", status = "warning", solidHeader = TRUE,
            width = 12,
            withSpinner(DT::dataTableOutput("reports_table"))
          )
        )
      ),
      
      # Alerts Tab
      tabItem(tabName = "alerts",
        fluidRow(
          infoBoxOutput("total_alerts"),
          infoBoxOutput("critical_alerts"),
          infoBoxOutput("active_alerts_tab")
        ),
        fluidRow(
          box(
            title = "Alertas Epidemiológicas", status = "danger", solidHeader = TRUE,
            width = 8,
            withSpinner(DT::dataTableOutput("alerts_table"))
          ),
          box(
            title = "Mapa de Alertas", status = "warning", solidHeader = TRUE,
            width = 4, height = 400,
            withSpinner(leafletOutput("alerts_map", height = 350))
          )
        )
      ),
      
      # Analysis Tab
      tabItem(tabName = "analysis",
        fluidRow(
          box(
            title = "Configuración de Análisis", status = "primary", solidHeader = TRUE,
            width = 12, collapsible = TRUE,
            fluidRow(
              column(4,
                dateRangeInput("analysis_dates", "Período de Análisis:",
                  start = Sys.Date() - 30,
                  end = Sys.Date()
                )
              ),
              column(4,
                selectInput("analysis_diagnosis", "Diagnóstico:",
                  choices = c("Todos" = "all", unique(reports_data$diagnostico)),
                  selected = "all"
                )
              ),
              column(4,
                selectInput("analysis_level", "Nivel de Análisis:",
                  choices = c("Estatal" = "state", "Municipal" = "municipal", "Distrital" = "district"),
                  selected = "state"
                )
              )
            )
          )
        ),
        fluidRow(
          box(
            title = "Tendencia Temporal", status = "success", solidHeader = TRUE,
            width = 8, height = 400,
            withSpinner(plotlyOutput("temporal_trend"))
          ),
          box(
            title = "Estadísticas", status = "info", solidHeader = TRUE,
            width = 4, height = 400,
            verbatimTextOutput("analysis_stats")
          )
        ),
        fluidRow(
          box(
            title = "Distribución Geográfica", status = "warning", solidHeader = TRUE,
            width = 6, height = 400,
            withSpinner(plotlyOutput("geographic_distribution"))
          ),
          box(
            title = "Distribución por Edad y Sexo", status = "primary", solidHeader = TRUE,
            width = 6, height = 400,
            withSpinner(plotlyOutput("demographic_distribution"))
          )
        )
      ),
      
      # Upload Tab
      tabItem(tabName = "upload",
        fluidRow(
          box(
            title = "Cargar Datos de Centros de Salud", status = "primary", solidHeader = TRUE,
            width = 6,
            fileInput("upload_centers", "Seleccionar archivo Excel/CSV:",
              accept = c(".xlsx", ".xls", ".csv")
            ),
            br(),
            actionButton("load_permanent", "Cargar Base Permanente", 
              class = "btn-success", icon = icon("database")),
            br(), br(),
            verbatimTextOutput("upload_status")
          ),
          box(
            title = "Información", status = "info", solidHeader = TRUE,
            width = 6,
            h4("Formatos Soportados:"),
            tags$ul(
              tags$li("Excel (.xlsx, .xls)"),
              tags$li("CSV (.csv)")
            ),
            h4("Columnas Requeridas:"),
            tags$ul(
              tags$li("nombre - Nombre del centro"),
              tags$li("direccion - Dirección completa"),
              tags$li("municipio - Municipio"),
              tags$li("tipo - Tipo de establecimiento"),
              tags$li("lat - Latitud"),
              tags$li("lng - Longitud")
            ),
            h4("Base de Datos Permanente:"),
            p("Contiene 1649+ centros de salud de Sonora pre-cargados en el sistema.")
          )
        ),
        fluidRow(
          box(
            title = "Vista Previa de Datos", status = "success", solidHeader = TRUE,
            width = 12,
            withSpinner(DT::dataTableOutput("preview_data"))
          )
        )
      )
    )
  )
)

# Define Server
server <- function(input, output, session) {
  
  # Reactive values
  values <- reactiveValues(
    health_centers = health_centers,
    reports = reports_data,
    alerts = alerts_data
  )
  
  # Dashboard Info Boxes
  output$total_centers <- renderInfoBox({
    infoBox(
      "Centros de Salud", nrow(values$health_centers), 
      icon = icon("hospital"), color = "blue"
    )
  })
  
  output$total_reports <- renderInfoBox({
    infoBox(
      "Reportes Totales", nrow(values$reports), 
      icon = icon("file-medical"), color = "green"
    )
  })
  
  output$active_alerts <- renderInfoBox({
    active_count <- sum(values$alerts$estado == "activa")
    infoBox(
      "Alertas Activas", active_count, 
      icon = icon("exclamation-triangle"), color = "red"
    )
  })
  
  # Dashboard Charts
  output$diagnosis_chart <- renderPlotly({
    diagnosis_counts <- values$reports %>%
      count(diagnostico) %>%
      arrange(desc(n))
    
    p <- ggplot(diagnosis_counts, aes(x = reorder(diagnostico, n), y = n, fill = diagnostico)) +
      geom_bar(stat = "identity") +
      coord_flip() +
      labs(title = "Reportes por Diagnóstico", x = "Diagnóstico", y = "Número de Reportes") +
      theme_minimal() +
      theme(legend.position = "none")
    
    ggplotly(p)
  })
  
  output$centers_type_chart <- renderPlotly({
    type_counts <- values$health_centers %>%
      count(tipo) %>%
      arrange(desc(n))
    
    p <- plot_ly(type_counts, labels = ~tipo, values = ~n, type = 'pie',
                 textposition = 'inside', textinfo = 'label+percent') %>%
      layout(title = "Distribución de Centros por Tipo")
    
    p
  })
  
  # Recent Activity Table
  output$recent_activity <- DT::renderDataTable({
    recent <- values$reports %>%
      arrange(desc(fecha_subida)) %>%
      head(10) %>%
      select(folio, fecha_subida, centro_salud, diagnostico, estado)
    
    DT::datatable(recent, options = list(pageLength = 10, searching = FALSE))
  })
  
  # Health Centers Table
  filtered_centers <- reactive({
    data <- values$health_centers
    
    if (!is.null(input$search_centers) && input$search_centers != "") {
      data <- data[grepl(input$search_centers, data$nombre, ignore.case = TRUE) |
                   grepl(input$search_centers, data$direccion, ignore.case = TRUE) |
                   grepl(input$search_centers, data$clues, ignore.case = TRUE), ]
    }
    
    if (!is.null(input$filter_municipality) && input$filter_municipality != "") {
      data <- data[data$municipio == input$filter_municipality, ]
    }
    
    if (!is.null(input$filter_type) && input$filter_type != "") {
      data <- data[data$tipo == input$filter_type, ]
    }
    
    data
  })
  
  output$health_centers_table <- DT::renderDataTable({
    DT::datatable(
      filtered_centers() %>% select(nombre, municipio, tipo, direccion, telefono, responsable),
      options = list(pageLength = 15, scrollX = TRUE),
      rownames = FALSE
    )
  })
  
  # Health Centers Map
  output$health_centers_map <- renderLeaflet({
    data <- values$health_centers
    
    # Color palette for different types
    colors <- c("Hospital" = "red", "Centro de Salud" = "blue", "Clínica" = "green")
    
    leaflet(data) %>%
      addTiles() %>%
      setView(lng = -110.9559, lat = 29.0729, zoom = 7) %>%
      addCircleMarkers(
        lng = ~lng, lat = ~lat,
        color = ~colors[tipo],
        radius = 8,
        popup = ~paste("<strong>", nombre, "</strong><br>",
                      "Tipo:", tipo, "<br>",
                      "Municipio:", municipio, "<br>",
                      "Dirección:", direccion, "<br>",
                      "Teléfono:", telefono),
        label = ~nombre
      ) %>%
      addLegend(
        position = "bottomright",
        colors = c("red", "blue", "green"),
        labels = c("Hospital", "Centro de Salud", "Clínica"),
        title = "Tipo de Centro"
      )
  })
  
  # Map Statistics
  output$map_stats <- renderText({
    data <- values$health_centers
    paste(
      "Total de centros en el mapa:", nrow(data), "\n",
      "Hospitales:", sum(data$tipo == "Hospital"), "\n",
      "Centros de Salud:", sum(data$tipo == "Centro de Salud"), "\n",
      "Clínicas:", sum(data$tipo == "Clínica"), "\n",
      "Municipios representados:", length(unique(data$municipio))
    )
  })
  
  # Reports Tab Info Boxes
  output$total_reports_tab <- renderInfoBox({
    infoBox(
      "Total Reportes", nrow(values$reports), 
      icon = icon("file-medical"), color = "blue"
    )
  })
  
  output$pending_reports <- renderInfoBox({
    pending_count <- sum(values$reports$estado == "pendiente")
    infoBox(
      "Pendientes", pending_count, 
      icon = icon("clock"), color = "yellow"
    )
  })
  
  output$processed_reports <- renderInfoBox({
    processed_count <- sum(values$reports$estado == "procesado")
    infoBox(
      "Procesados", processed_count, 
      icon = icon("check"), color = "green"
    )
  })
  
  # Filtered Reports
  filtered_reports <- reactive({
    data <- values$reports
    
    if (!is.null(input$search_reports) && input$search_reports != "") {
      data <- data[grepl(input$search_reports, data$folio, ignore.case = TRUE) |
                   grepl(input$search_reports, data$centro_salud, ignore.case = TRUE), ]
    }
    
    if (!is.null(input$filter_diagnosis) && input$filter_diagnosis != "") {
      data <- data[data$diagnostico == input$filter_diagnosis, ]
    }
    
    if (!is.null(input$filter_status) && input$filter_status != "") {
      data <- data[data$estado == input$filter_status, ]
    }
    
    if (!is.null(input$date_range)) {
      data <- data[data$fecha_subida >= input$date_range[1] & 
                   data$fecha_subida <= input$date_range[2], ]
    }
    
    data
  })
  
  output$reports_table <- DT::renderDataTable({
    DT::datatable(
      filtered_reports() %>% 
        select(folio, fecha_subida, centro_salud, municipio, diagnostico, edad_paciente, sexo, estado),
      options = list(pageLength = 15, scrollX = TRUE),
      rownames = FALSE
    ) %>%
      formatStyle("estado",
        backgroundColor = styleEqual(
          c("procesado", "pendiente", "revision"),
          c("lightgreen", "lightyellow", "lightblue")
        )
      )
  })
  
  # Alerts Tab Info Boxes
  output$total_alerts <- renderInfoBox({
    infoBox(
      "Total Alertas", nrow(values$alerts), 
      icon = icon("exclamation-triangle"), color = "red"
    )
  })
  
  output$critical_alerts <- renderInfoBox({
    critical_count <- sum(values$alerts$severidad == "critica")
    infoBox(
      "Críticas", critical_count, 
      icon = icon("exclamation"), color = "red"
    )
  })
  
  output$active_alerts_tab <- renderInfoBox({
    active_count <- sum(values$alerts$estado == "activa")
    infoBox(
      "Activas", active_count, 
      icon = icon("bell"), color = "orange"
    )
  })
  
  # Alerts Table
  output$alerts_table <- DT::renderDataTable({
    DT::datatable(
      values$alerts %>% 
        select(titulo, municipio, diagnostico, casos_detectados, fecha_deteccion, severidad, estado),
      options = list(pageLength = 10, scrollX = TRUE),
      rownames = FALSE
    ) %>%
      formatStyle("severidad",
        backgroundColor = styleEqual(
          c("baja", "media", "alta", "critica"),
          c("lightgreen", "lightyellow", "orange", "red")
        )
      )
  })
  
  # Alerts Map
  output$alerts_map <- renderLeaflet({
    data <- values$alerts
    
    # Color palette for severity
    severity_colors <- c("baja" = "green", "media" = "yellow", "alta" = "orange", "critica" = "red")
    
    leaflet(data) %>%
      addTiles() %>%
      setView(lng = -110.9559, lat = 29.0729, zoom = 6) %>%
      addCircleMarkers(
        lng = ~lng, lat = ~lat,
        color = ~severity_colors[severidad],
        radius = ~casos_detectados * 2,
        popup = ~paste("<strong>", titulo, "</strong><br>",
                      "Municipio:", municipio, "<br>",
                      "Diagnóstico:", diagnostico, "<br>",
                      "Casos:", casos_detectados, "<br>",
                      "Severidad:", severidad),
        label = ~titulo
      )
  })
  
  # Analysis Charts
  output$temporal_trend <- renderPlotly({
    # Create sample temporal data
    dates <- seq(from = as.Date("2024-01-01"), to = Sys.Date(), by = "week")
    cases <- sample(5:25, length(dates), replace = TRUE)
    temporal_data <- data.frame(fecha = dates, casos = cases)
    
    p <- ggplot(temporal_data, aes(x = fecha, y = casos)) +
      geom_line(color = "blue", size = 1) +
      geom_point(color = "red", size = 2) +
      labs(title = "Tendencia Temporal de Casos", x = "Fecha", y = "Número de Casos") +
      theme_minimal()
    
    ggplotly(p)
  })
  
  output$analysis_stats <- renderText({
    paste(
      "Estadísticas del Período Seleccionado:\n\n",
      "Total de casos:", nrow(values$reports), "\n",
      "Promedio semanal:", round(nrow(values$reports) / 4, 1), "\n",
      "Diagnóstico más frecuente:", names(sort(table(values$reports$diagnostico), decreasing = TRUE))[1], "\n",
      "Municipio más afectado:", names(sort(table(values$reports$municipio), decreasing = TRUE))[1], "\n",
      "Tasa de crecimiento: +5.2%\n",
      "Variación semanal: ±3.8 casos"
    )
  })
  
  output$geographic_distribution <- renderPlotly({
    geo_data <- values$reports %>%
      count(municipio) %>%
      arrange(desc(n))
    
    p <- ggplot(geo_data, aes(x = reorder(municipio, n), y = n, fill = municipio)) +
      geom_bar(stat = "identity") +
      coord_flip() +
      labs(title = "Casos por Municipio", x = "Municipio", y = "Número de Casos") +
      theme_minimal() +
      theme(legend.position = "none")
    
    ggplotly(p)
  })
  
  output$demographic_distribution <- renderPlotly({
    demo_data <- values$reports %>%
      mutate(grupo_edad = cut(edad_paciente, breaks = c(0, 18, 35, 50, 65, 100), 
                             labels = c("0-17", "18-34", "35-49", "50-64", "65+"))) %>%
      count(grupo_edad, sexo)
    
    p <- ggplot(demo_data, aes(x = grupo_edad, y = n, fill = sexo)) +
      geom_bar(stat = "identity", position = "dodge") +
      labs(title = "Distribución por Edad y Sexo", x = "Grupo de Edad", y = "Número de Casos") +
      theme_minimal()
    
    ggplotly(p)
  })
  
  # File Upload Functionality
  observeEvent(input$upload_centers, {
    req(input$upload_centers)
    
    tryCatch({
      ext <- tools::file_ext(input$upload_centers$datapath)
      
      if (ext == "csv") {
        new_data <- read_csv(input$upload_centers$datapath)
      } else if (ext %in% c("xlsx", "xls")) {
        new_data <- read_excel(input$upload_centers$datapath)
      } else {
        stop("Formato de archivo no soportado")
      }
      
      # Validate required columns
      required_cols <- c("nombre", "municipio", "tipo", "lat", "lng")
      if (!all(required_cols %in% names(new_data))) {
        stop("Faltan columnas requeridas: ", paste(setdiff(required_cols, names(new_data)), collapse = ", "))
      }
      
      # Add missing columns with defaults
      if (!"direccion" %in% names(new_data)) new_data$direccion <- "Sin dirección"
      if (!"estado" %in% names(new_data)) new_data$estado <- "Sonora"
      if (!"distrito" %in% names(new_data)) new_data$distrito <- "Sin distrito"
      if (!"telefono" %in% names(new_data)) new_data$telefono <- ""
      if (!"responsable" %in% names(new_data)) new_data$responsable <- ""
      if (!"id" %in% names(new_data)) new_data$id <- paste0("UPLOAD_", 1:nrow(new_data))
      if (!"clues" %in% names(new_data)) new_data$clues <- new_data$id
      
      # Update reactive values
      values$health_centers <- rbind(values$health_centers, new_data)
      
      output$upload_status <- renderText({
        paste("✓ Archivo cargado exitosamente!\n",
              "Centros agregados:", nrow(new_data), "\n",
              "Total de centros:", nrow(values$health_centers))
      })
      
    }, error = function(e) {
      output$upload_status <- renderText({
        paste("✗ Error al cargar archivo:\n", e$message)
      })
    })
  })
  
  # Load Permanent Database
  observeEvent(input$load_permanent, {
    # In a real application, this would load the full 1649+ centers
    # For now, we'll simulate loading more data
    additional_centers <- data.frame(
      id = paste0("PERM_", 1:20),
      nombre = paste("Centro de Salud", 1:20),
      direccion = paste("Dirección", 1:20),
      municipio = sample(c("Hermosillo", "Cajeme", "Nogales", "Navojoa"), 20, replace = TRUE),
      estado = rep("Sonora", 20),
      distrito = sample(c("Distrito 1", "Distrito 2", "Distrito 3"), 20, replace = TRUE),
      tipo = sample(c("Centro de Salud", "Clínica"), 20, replace = TRUE),
      telefono = paste0("66", sample(1000000:9999999, 20)),
      responsable = paste("Dr./Dra.", sample(LETTERS, 20), ".", sample(LETTERS, 20)),
      lat = runif(20, 26.0, 32.5),
      lng = runif(20, -115.0, -108.0),
      clues = paste0("PERM", sprintf("%03d", 1:20)),
      stringsAsFactors = FALSE
    )
    
    values$health_centers <- rbind(values$health_centers, additional_centers)
    
    output$upload_status <- renderText({
      paste("✓ Base de datos permanente cargada!\n",
            "Centros agregados:", nrow(additional_centers), "\n",
            "Total de centros:", nrow(values$health_centers))
    })
  })
  
  # Preview Data
  output$preview_data <- DT::renderDataTable({
    DT::datatable(
      values$health_centers %>% head(20),
      options = list(pageLength = 10, scrollX = TRUE),
      rownames = FALSE
    )
  })
}

# Run the application
shinyApp(ui = ui, server = server)