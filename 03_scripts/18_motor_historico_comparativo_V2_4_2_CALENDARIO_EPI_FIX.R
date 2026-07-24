# ============================================================
# PRISMA-R
# MODULO 18 V2.4.2 - FIX CALENDARIO EPIDEMIOLOGICO
# ============================================================
#
# BUILD_18_V2_4_2_CALENDARIO_EPI_FIX_20260724_01
#
# Hallazgo real que origina este parche:
# - EDAS 2026: SemanaInicio vs Fecha_Inicio
# - 857/857 registros coinciden con lubridate::epiweek()
# - 0/857 coinciden con la funcion previa de PRISMA-R
# - La funcion previa desplazaba fecha + 1 y aplicaba ISO week/year.
#
# Convencion corregida:
# - semana epidemiologica domingo-sabado;
# - lubridate::epiweek() para semana;
# - lubridate::epiyear() para anio epidemiologico.
#
# Este archivo:
# - carga V2.4.1 para conservar el fix de auditoria de corte;
# - reemplaza la funcion central de semana epidemiologica;
# - por transitividad corrige fechas de evento, defuncion y cortes
#   derivados de fecha;
# - agrega pruebas de regresion del cambio de anio 2025/2026;
# - agrega auditoria opcional contra EDAS real;
# - NO modifica bases originales;
# - NO reasigna registros automaticamente.
# ============================================================

archivo_v241 <- here::here(
  "03_scripts",
  "18_motor_historico_comparativo_V2_4_1_AUDITORIA_CORTE_FIX.R"
)

if (!file.exists(archivo_v241)) {
  stop(
    paste0(
      "No se encontro el modulo requerido V2.4.1: ",
      archivo_v241
    )
  )
}

source(archivo_v241)


# ============================================================
# 1. RELOJ EPIDEMIOLOGICO CENTRAL CORREGIDO
# ============================================================

semana_epidemiologica_domingo_18 <- function(fecha) {

  fecha <- as.Date(fecha)

  tibble::tibble(
    anio_epi = as.integer(
      lubridate::epiyear(fecha)
    ),
    semana_epi = as.integer(
      lubridate::epiweek(fecha)
    )
  )
}


# ============================================================
# 2. PARSER DE CORTE BASADO EN EL MISMO RELOJ
# ============================================================
#
# La funcion V2.4 ya llama al reloj central. Se redefine de forma
# explicita para dejar trazabilidad metodologica en este build.

.semana_desde_fecha_corte_18_v24 <- function(fecha) {
  semana_epidemiologica_domingo_18(
    as.Date(fecha)
  )$semana_epi
}


# ============================================================
# 3. PRUEBAS UNITARIAS DEL CALENDARIO 2026
# ============================================================

prueba_calendario_epidemiologico_18_v242 <- function() {

  fechas <- as.Date(
    c(
      "2026-01-01",
      "2026-01-02",
      "2026-01-03",
      "2026-01-04",
      "2026-01-10",
      "2026-01-11",
      "2026-07-13",
      "2026-07-21"
    )
  )

  epi <- semana_epidemiologica_domingo_18(fechas)

  esperado_anio <- c(
    2025L,
    2025L,
    2025L,
    2026L,
    2026L,
    2026L,
    2026L,
    2026L
  )

  esperado_semana <- c(
    53L,
    53L,
    53L,
    1L,
    1L,
    2L,
    28L,
    29L
  )

  corte_13_jul <- extraer_corte_fuente_18_v24(
    id_unidad = "BASE EDAS CORTE AL DIA 13 07 26.xlsx :: Datos",
    anio = 2026L
  )

  corte_21_jul <- extraer_corte_fuente_18_v24(
    id_unidad = "BASE DENGUE CORTE AL DIA 21 07 26.xlsx :: Hoja1",
    anio = 2026L
  )

  tibble::tibble(
    prueba = c(
      "01-ene-2026 pertenece a SE53 de 2025",
      "02-ene-2026 pertenece a SE53 de 2025",
      "03-ene-2026 pertenece a SE53 de 2025",
      "04-ene-2026 inicia SE01 de 2026",
      "10-ene-2026 permanece en SE01",
      "11-ene-2026 inicia SE02",
      "13-jul-2026 pertenece a SE28",
      "21-jul-2026 pertenece a SE29",
      "Vector de anios epidemiologicos coincide con esperado",
      "Vector de semanas epidemiologicas coincide con esperado",
      "Parser de corte 13-jul produce SE28",
      "Parser de corte 21-jul produce SE29",
      "epiweek directo coincide con reloj PRISMA-R",
      "epiyear directo coincide con reloj PRISMA-R",
      "No se usa desplazamiento artificial fecha + 1"
    ),
    pasa = c(
      epi$anio_epi[1] == 2025L && epi$semana_epi[1] == 53L,
      epi$anio_epi[2] == 2025L && epi$semana_epi[2] == 53L,
      epi$anio_epi[3] == 2025L && epi$semana_epi[3] == 53L,
      epi$anio_epi[4] == 2026L && epi$semana_epi[4] == 1L,
      epi$anio_epi[5] == 2026L && epi$semana_epi[5] == 1L,
      epi$anio_epi[6] == 2026L && epi$semana_epi[6] == 2L,
      epi$anio_epi[7] == 2026L && epi$semana_epi[7] == 28L,
      epi$anio_epi[8] == 2026L && epi$semana_epi[8] == 29L,
      identical(as.integer(epi$anio_epi), esperado_anio),
      identical(as.integer(epi$semana_epi), esperado_semana),
      corte_13_jul$semana_corte_fuente[1] == 28L,
      corte_21_jul$semana_corte_fuente[1] == 29L,
      identical(
        as.integer(epi$semana_epi),
        as.integer(lubridate::epiweek(fechas))
      ),
      identical(
        as.integer(epi$anio_epi),
        as.integer(lubridate::epiyear(fechas))
      ),
      !identical(
        as.integer(epi$semana_epi),
        as.integer(lubridate::isoweek(fechas + 1))
      )
    )
  )
}


# ============================================================
# 4. AUDITORIA REAL OPCIONAL DE EDAS
# ============================================================

validar_calendario_edas_real_18_v242 <- function(
  resultado_18,
  anio = 2026L
) {

  if (
    is.null(resultado_18$base_longitudinal) ||
    !is.data.frame(resultado_18$base_longitudinal)
  ) {
    stop("resultado_18 no contiene base_longitudinal valida.")
  }

  x <- resultado_18$base_longitudinal |>
    dplyr::filter(
      .data$sistema == "EDAS",
      .data$anio_fuente == .env$anio,
      !is.na(.data$fecha_evento),
      !is.na(.data$semana_epi)
    )

  if (nrow(x) == 0) {
    return(
      tibble::tibble(
        registros = 0L,
        coinciden_fuente_fecha = NA_integer_,
        pct_concordancia = NA_real_,
        estado = "SIN_REGISTROS_EVALUABLES"
      )
    )
  }

  semana_fecha <- as.integer(
    lubridate::epiweek(x$fecha_evento)
  )

  coincide <- as.integer(x$semana_epi) == semana_fecha

  tibble::tibble(
    registros = nrow(x),
    coinciden_fuente_fecha = sum(coincide, na.rm = TRUE),
    pct_concordancia = 100 * mean(coincide, na.rm = TRUE),
    estado = dplyr::case_when(
      all(coincide, na.rm = TRUE) ~ "CONCORDANCIA_TOTAL",
      mean(coincide, na.rm = TRUE) >= 0.95 ~ "CONCORDANCIA_ALTA",
      TRUE ~ "REVISAR"
    )
  )
}


# ============================================================
# 5. VALIDACION DEL HOTFIX V2.4.2
# ============================================================

validar_hotfix_18_v242 <- function() {

  pruebas_calendario <- prueba_calendario_epidemiologico_18_v242()

  funciones <- c(
    "semana_epidemiologica_domingo_18",
    ".semana_desde_fecha_corte_18_v24",
    "prueba_calendario_epidemiologico_18_v242",
    "validar_calendario_edas_real_18_v242"
  )

  estructura <- tibble::tibble(
    funcion = funciones,
    disponible = vapply(
      funciones,
      exists,
      logical(1),
      mode = "function"
    )
  )

  cat("\n====================================================\n")
  cat("PRISMA-R | VALIDACION HOTFIX 18 V2.4.2\n")
  cat("CALENDARIO EPIDEMIOLOGICO DOMINGO-SABADO\n")
  cat("====================================================\n\n")

  cat("Funciones:\n")
  print(estructura, n = Inf)

  cat("\nPruebas del calendario:\n")
  print(pruebas_calendario, n = Inf, width = Inf)

  if (
    all(estructura$disponible) &&
    all(pruebas_calendario$pasa)
  ) {
    cat("\nOK HOTFIX 18 V2.4.2 VALIDADO FUNCIONALMENTE\n")
  } else {
    cat("\nREVISAR HOTFIX 18 V2.4.2\n")
  }

  invisible(
    list(
      estructura = estructura,
      calendario = pruebas_calendario
    )
  )
}


cat("\n====================================================\n")
cat("PRISMA-R | MODULO 18 V2.4.2 CARGADO\n")
cat("FIX CALENDARIO EPIDEMIOLOGICO\n")
cat("====================================================\n")
cat("\nConvencion activa:\n")
cat("- semana epidemiologica inicia domingo.\n")
cat("- semana: lubridate::epiweek().\n")
cat("- anio epidemiologico: lubridate::epiyear().\n")
cat("- 01-03 enero 2026 = SE53 de 2025.\n")
cat("- 04-10 enero 2026 = SE01 de 2026.\n")
cat("\nValidacion:\n")
cat("validacion_18_v242 <- validar_hotfix_18_v242()\n")
cat("\nEjecucion real:\n")
cat("resultado_18_v242 <- ejecutar_motor_historico_comparativo_18(resultado_17 = resultado_17)\n")
