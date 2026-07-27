# POPIS 4.1

**Procesador Operativo de Patógenos e Indicadores Sanitarios**

Aplicación local Python + Streamlit para vigilancia de EDA en Sonora, integrando **SUIVE/SUAVE**, **SINAVE EDA**, CONAPO, indicadores, territorio y control de calidad.

## Cambio principal de 4.1: los datos viven localmente en POPIS

Ya no es necesario cargar todos los archivos cada vez que se abre el tablero.

```text
POPIS_4_0/
├── data/
│   ├── sinave/
│   │   ├── historico/       ← se actualiza una vez al año
│   │   └── actual/          ← se reemplaza una vez por semana
│   ├── suive/
│   │   ├── historico/       ← se actualiza una vez al año
│   │   └── actual/          ← se reemplaza una vez por semana
│   └── poblacion/           ← CONAPO
├── app_v41.py
├── app_bootstrap.py
├── popis_core.py
├── popis_core_patch.py
├── popis_data.py
├── CONFIGURAR_DATOS_INICIALES.bat
├── CERRAR_ANIO.bat
├── INICIAR_POPIS.bat
└── REPARAR_POPIS.bat
```

Las carpetas `data/` y `IMPORTAR/` están excluidas de Git para impedir publicar accidentalmente bases nominales.

## Primera instalación

1. Descomprime POPIS en una ruta sencilla, por ejemplo `C:\POPIS4`.
2. Crea/abre la carpeta `IMPORTAR` ejecutando `CONFIGURAR_DATOS_INICIALES.bat` una primera vez.
3. Coloca allí los archivos iniciales.
4. Ejecuta nuevamente `CONFIGURAR_DATOS_INICIALES.bat`.
5. Ejecuta `INICIAR_POPIS.bat`.

También puedes cargar históricos y actualizaciones desde la barra lateral del tablero. Los archivos se guardan localmente.

## Rutina semanal

Solo hay dos movimientos:

- reemplazar `SINAVE actual` con la exportación nominal más reciente;
- reemplazar `SUIVE actual` con el reporte más reciente.

Desde el tablero: **Actualización semanal → Guardar como SINAVE/SUIVE actual**.

POPIS vuelve a leer los históricos congelados y combina automáticamente el nuevo corte.

## Cierre anual

Ejecuta `CERRAR_ANIO.bat` o agrega el archivo anual desde la sección de mantenimiento. El cierre copia los archivos actuales al histórico y no borra la fuente original.

## Correcciones de calidad incorporadas

### Año epidemiológico separado del año calendario

Las bases reales pueden contener casos de los primeros días de enero con `SemanaInicio=52/53`. POPIS **no cambia la semana capturada**. En su lugar calcula `epi_year`:

- SE52/53 + inicio en enero → año epidemiológico anterior;
- SE1 + inicio en diciembre → año epidemiológico siguiente;
- resto → año del inicio de síntomas.

Esto evita que una SE53 de cierre quede artificialmente colocada al final del nuevo año.

### Municipios

Se homologan variantes frecuentes antes de unir con CONAPO, por ejemplo:

- `BENITO JUAREZ   SON` → `Benito Juárez`;
- `ROSARIO SON` → `Rosario`;
- `COLORADA LA` → `La Colorada`.

Las tasas territoriales usan **municipio de residencia** y excluyen del denominador Sonora a residentes de otras entidades, aunque esos registros siguen disponibles en los conteos generales de vigilancia.

### Muestras rechazadas

Los rechazos se identifican tanto por diagnóstico final como por campos de calidad de laboratorio. La bitácora distingue el evento operativo del resultado negativo.

### Duplicados entre archivos

Si el mismo folio aparece en histórico y actual, POPIS conserva la versión más reciente y lo registra como observación de calidad.

## Bitácora de calidad

La pestaña `🔍 Calidad y auditoría` revisa, entre otros:

- semana inválida;
- cruces de año epidemiológico;
- fechas de captura anteriores al primer contacto;
- diagnóstico anterior al primer contacto;
- fecha de consumo posterior al inicio de síntomas;
- municipios de Sonora no homologados;
- residentes de otras entidades;
- muestras rechazadas;
- resultados pendientes;
- folios repetidos entre fuentes;
- concordancia de clasificación EDA moderada/grave.

POPIS informa el problema y **no modifica silenciosamente la fuente original**.

## Funciones

- SUIVE/SUAVE: magnitud, tendencia, acumulados, comparativo histórico y canal endémico.
- SINAVE: registros nominales, patógenos, mortalidad, letalidad y series semanales.
- Comparador SUIVE ↔ SINAVE: diferencia, razón y correlaciones.
- Canal endémico SUIVE y SINAVE por patógeno y territorio.
- Territorio: municipio, Distrito de Salud y región.
- CONAPO: incidencia y mortalidad por 100,000 habitantes cuando el denominador es compatible.
- Indicadores NuTraVE y laboratorio.
- Auditor normativo de EDA.
- Excel de resultados.
- PNG individual y ZIP de gráficas.
- Mapa municipal INEGI cuando existe conexión a Internet.

## Privacidad

Las bases SINAVE contienen información nominal. POPIS 4.1 está diseñado para mantenerlas **en la computadora local**. No deben subirse a repositorios públicos ni servicios abiertos. El repositorio contiene el motor, nunca las bases nominales.
