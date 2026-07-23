# POPIS 4.0

**Procesador Operativo de Patógenos e Indicadores Sanitarios**

Aplicación local en Python + Streamlit para vigilancia de Enfermedad Diarreica Aguda (EDA), orientada al análisis conjunto de **SUIVE/SUAVE** y **SINAVE EDA**.

## Qué hace

- SUIVE/SUAVE: magnitud, tendencia, acumulados, comparativo histórico y canal endémico.
- SINAVE: registros nominales, patógenos, mortalidad, letalidad y series semanales.
- Comparador SUIVE ↔ SINAVE: diferencias, razón entre sistemas y correlaciones.
- Canal endémico dinámico SUIVE y SINAVE, incluyendo selección de patógeno y años históricos.
- Análisis territorial por municipio de residencia.
- Mapa municipal de Sonora con geometría oficial del servicio web de INEGI.
- Indicadores mensuales NuTraVE y de laboratorio con numerador, denominador, resultado, meta y cumplimiento.
- Auditor de definiciones operacionales EDA moderada/grave.
- Exportación de tablas a Excel.
- Descarga individual de gráficas PNG y descarga masiva en ZIP.
- Mapas Plotly con botón de cámara para descargar PNG desde el navegador.

## Instalación en Windows

1. Descarga/descomprime la carpeta `POPIS_4_0` en una ruta sencilla, por ejemplo `C:\POPIS4`.
2. Ejecuta `INICIAR_POPIS.bat`.
3. La primera ejecución crea un entorno virtual aislado en `%LOCALAPPDATA%\POPIS4\venv`.
4. POPIS abre en `http://127.0.0.1:8501`.

El entorno corto evita el problema de rutas excesivamente largas observado con Python instalado desde Microsoft Store.

## Rutina semanal recomendada

No es necesario modificar los históricos cada semana.

1. Conserva tu histórico SUIVE/SUAVE.
2. Actualiza la información del año en curso en el archivo SUIVE, o carga el nuevo archivo que ya contenga la semana más reciente.
3. Carga las bases históricas SINAVE una sola vez por sesión y la base actualizada del año en curso.
4. Selecciona año y semana epidemiológica.
5. POPIS recalcula todos los módulos.

## Archivos de entrada

### SUIVE/SUAVE

POPIS busca automáticamente la hoja `SUIVE` y detecta filas que contienen un año y al menos 20 valores semanales. El resultado se normaliza a:

- Año
- Semana epidemiológica
- Casos

Si un archivo tiene una estructura distinta, el módulo mostrará un error en lugar de inventar datos.

### SINAVE EDA

Acepta XLS real, XLSX, CSV y también exportaciones tabuladas que llevan extensión `.xls`. El lector detecta automáticamente ese caso.

Las variables se buscan por alias. Entre las principales:

- `SemanaInicio`
- `Fec_captura`
- `Fec_Primer_Contacto`
- `Fec_Dx_Final`
- `Diag_Final`
- `FecDefuncion`
- `Mun_Res`
- `CLUES`
- `NuTraVE`
- campos de muestras y laboratorio
- resultados de Salmonella, Shigella, Rotavirus, Vibrio y E. coli

## Indicadores incluidos

### NuTraVE

- Notificación oportuna de EDA, meta 100%.
- Clasificación oportuna de EDA, meta 80%.
- Cobertura de notificación, meta 80%.
- Muestreo de EDA en menores de 5 años, meta 80%.
- Muestreo de EDA en personas de 5 años o más, meta 80%.

### Laboratorio

- Muestras rechazadas.
- Toma oportuna bacteriana.
- Toma oportuna viral.
- Envío oportuno bacteriano.
- Envío oportuno viral.

Los indicadores se muestran con numerador y denominador para permitir auditoría.

## Importante sobre SUIVE vs SINAVE

POPIS **no suma** SUIVE y SINAVE ni interpreta automáticamente la diferencia como subregistro. Los sistemas tienen objetivos y universos distintos. El módulo comparador estudia la relación temporal entre ambos mediante:

- diferencia absoluta;
- razón SINAVE/SUIVE;
- correlación de Pearson;
- correlación de Spearman.

## Población y tasas

POPIS permite cargar un archivo de población CONAPO. Para el análisis territorial intenta reconocer columnas equivalentes a:

- Municipio
- Año
- Población

Cuando están disponibles, calcula incidencia y mortalidad por 100,000 habitantes.

Fuente demográfica recomendada:

- CONAPO / datos.gob.mx: reconstrucción y proyecciones municipales de población 1990-2040.

## Cartografía

El mapa consulta en tiempo real el servicio web oficial de INEGI para las Áreas Geoestadísticas Municipales de Sonora:

`https://gaia.inegi.org.mx/wscatgeo/v2/geo/mgem/26`

Si no hay conexión a internet, las tablas territoriales continúan funcionando y únicamente el mapa queda temporalmente no disponible.

## Privacidad

Las bases nominales se cargan en la sesión local de Streamlit. **No subas bases nominales con datos personales a repositorios públicos.** Este repositorio contiene únicamente el motor de análisis.

## Estructura

```text
POPIS_4_0/
├── app.py
├── popis_core.py
├── requirements.txt
├── INICIAR_POPIS.bat
├── REPARAR_POPIS.bat
├── DIAGNOSTICO_POPIS.bat
└── README.md
```

## Próximos módulos previstos

- meta normativa del monitoreo del 2% vinculando SUIVE histórico con SINAVE;
- Red Negativa de Cólera;
- distritos y regiones de Sonora;
- tasas específicas por edad y sexo;
- detección de hotspots con estabilización para poblaciones pequeñas;
- informe ejecutivo automático en Word/PDF.
