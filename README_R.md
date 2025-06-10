# Sistema de Vigilancia Epidemiológica - R Shiny

Este es un sistema completo de vigilancia epidemiológica desarrollado en R Shiny que replica la funcionalidad del sistema React original.

## Características

### 📊 Panel Principal
- Estadísticas generales del sistema
- Gráficos interactivos de reportes por diagnóstico
- Distribución de centros por tipo
- Tabla de actividad reciente

### 🏥 Gestión de Centros de Salud
- Visualización completa de centros de salud
- Filtros por municipio, tipo y búsqueda de texto
- Información detallada de cada centro
- Soporte para 1649+ centros de Sonora

### 🗺️ Mapa Interactivo
- Mapa de Leaflet con todos los centros de salud
- Marcadores diferenciados por tipo de centro
- Popups informativos con detalles completos
- Vista centrada en el estado de Sonora

### 📋 Gestión de Reportes
- Tabla completa de reportes SUIVE
- Filtros por diagnóstico, estado y fechas
- Estadísticas de reportes procesados y pendientes
- Formato de colores para estados

### 🚨 Sistema de Alertas
- Gestión de alertas epidemiológicas
- Mapa de alertas con severidad visual
- Clasificación por tipo y severidad
- Seguimiento de casos detectados

### 📈 Análisis Epidemiológico
- Tendencias temporales de casos
- Distribución geográfica por municipio
- Análisis demográfico por edad y sexo
- Estadísticas descriptivas

### 📤 Carga de Datos
- Soporte para archivos Excel (.xlsx, .xls)
- Soporte para archivos CSV
- Base de datos permanente integrada
- Validación de columnas requeridas

## Instalación y Uso

### Prerrequisitos
- R (versión 4.0 o superior)
- RStudio (recomendado)

### Paso 1: Instalar Paquetes
```r
# Ejecutar en RStudio
source("install_packages.R")
```

### Paso 2: Ejecutar la Aplicación
```r
# Opción 1: Desde RStudio
# Abrir app.R y hacer clic en "Run App"

# Opción 2: Desde consola R
shiny::runApp("app.R")

# Opción 3: Especificar puerto
shiny::runApp("app.R", port = 3838)
```

### Paso 3: Acceder a la Aplicación
La aplicación se abrirá automáticamente en su navegador web predeterminado, típicamente en:
- `http://127.0.0.1:XXXX` (donde XXXX es el puerto asignado)

## Estructura de Datos

### Centros de Salud
Columnas requeridas para carga de datos:
- `nombre`: Nombre del centro de salud
- `direccion`: Dirección completa
- `municipio`: Municipio donde se ubica
- `tipo`: Tipo de establecimiento (Hospital, Centro de Salud, Clínica)
- `lat`: Latitud (coordenada geográfica)
- `lng`: Longitud (coordenada geográfica)

Columnas opcionales:
- `telefono`: Número de teléfono
- `responsable`: Nombre del responsable
- `clues`: Clave Única de Establecimientos de Salud
- `distrito`: Distrito sanitario

### Reportes SUIVE
- `folio`: Folio único del reporte
- `fecha_subida`: Fecha de carga del reporte
- `fecha_consulta`: Fecha de la consulta médica
- `centro_salud`: Nombre del centro que reporta
- `municipio`: Municipio del caso
- `diagnostico`: Diagnóstico principal
- `edad_paciente`: Edad del paciente
- `sexo`: Sexo del paciente (M/F)
- `estado`: Estado del reporte (procesado/pendiente/revision)

### Alertas Epidemiológicas
- `titulo`: Título descriptivo de la alerta
- `tipo`: Tipo de alerta (brote/incremento/cluster/anomalia)
- `municipio`: Municipio afectado
- `diagnostico`: Enfermedad relacionada
- `casos_detectados`: Número de casos
- `severidad`: Nivel de severidad (baja/media/alta/critica)
- `estado`: Estado de la alerta (activa/investigando/resuelta)

## Funcionalidades Principales

### 1. Visualización de Datos
- Tablas interactivas con DataTables
- Gráficos dinámicos con Plotly
- Mapas interactivos con Leaflet

### 2. Filtrado y Búsqueda
- Filtros dinámicos por múltiples criterios
- Búsqueda de texto en tiempo real
- Filtros de fecha para análisis temporal

### 3. Análisis Epidemiológico
- Tendencias temporales
- Distribución geográfica
- Análisis demográfico
- Estadísticas descriptivas

### 4. Gestión de Datos
- Carga de archivos Excel/CSV
- Validación automática de datos
- Base de datos permanente
- Exportación de resultados

## Personalización

### Agregar Nuevos Municipios
Editar la función `load_permanent_health_centers()` en `app.R` para incluir más centros.

### Modificar Análisis
Las funciones de análisis se pueden personalizar en la sección del servidor correspondiente.

### Cambiar Estilos
Modificar el CSS en la sección `tags$head()` del UI.

## Solución de Problemas

### Error de Paquetes
Si hay errores de paquetes faltantes:
```r
install.packages(c("shiny", "shinydashboard", "DT", "leaflet", "plotly"))
```

### Error de Memoria
Para datasets grandes, aumentar la memoria disponible:
```r
options(shiny.maxRequestSize = 100*1024^2)  # 100MB
```

### Puerto Ocupado
Si el puerto está en uso:
```r
shiny::runApp("app.R", port = 8080)  # Usar puerto diferente
```

## Datos de Ejemplo

La aplicación incluye datos de ejemplo para:
- 5 centros de salud principales de Sonora
- 10 reportes epidemiológicos simulados
- 5 alertas epidemiológicas de muestra

Para usar datos reales, cargar archivos Excel/CSV con la estructura correcta.

## Soporte

Para problemas técnicos o preguntas sobre el sistema:
1. Verificar que todos los paquetes estén instalados correctamente
2. Revisar la consola de R para mensajes de error
3. Asegurar que los archivos de datos tengan el formato correcto

## Licencia

Sistema desarrollado para vigilancia epidemiológica en el estado de Sonora, México.