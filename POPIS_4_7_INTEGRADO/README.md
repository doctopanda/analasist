# POPIS 4.7 · Integración automática

**POPIS** = Procesador Operativo de Patógenos e Indicadores Sanitarios.

Esta actualización integra el mapa territorial probado en POPIS 4.6.3 dentro de la instalación principal y elimina la necesidad de volver a cargar manualmente bases, población o cartografía que ya existen en el proyecto.

## Qué agrega

- Página **Centro de Datos**.
- Página **Mapa Territorial**.
- Descubrimiento automático de bases SINAVE históricas y actuales.
- Detección automática del año actual y de la última semana epidemiológica disponible.
- Descubrimiento de SUIVE/SUAVE, población, GeoJSON municipal, GeoJSON distrital y coordenadas institucionales.
- Bandeja vigilada `data/entrada`.
- Clasificación de nuevas fuentes por estructura y nombre.
- Respaldo antes de reemplazar una fuente operativa.
- Mapa de concentración + puntos exactos/aproximados.
- Rescate cartográfico por centroide municipal cuando un caso no tiene coordenada exacta y existe GeoJSON municipal.
- Incidencia municipal únicamente cuando existe un denominador poblacional compatible.
- Exportación de mapa HTML y tabla municipal Excel.

## Instalación sobre POPIS existente

1. Conserva tu carpeta POPIS actual.
2. Descomprime `POPIS_4_7_INTEGRADO.zip` en una carpeta temporal.
3. Ejecuta `ACTUALIZAR_POPIS_4_7.bat`.
4. El actualizador busca la instalación POPIS. Si no puede encontrarla, solicita la ruta.
5. Abre POPIS con tu `INICIAR_POPIS.bat` habitual.

La actualización **no borra** las bases históricas ni la base actual. Antes de reemplazar archivos de código crea una carpeta `backup_POPIS_4_7_YYYYMMDD_HHMMSS`.

## Actualización semanal simplificada

Puedes usar la interfaz **Centro de Datos** o copiar la nueva base a:

```text
data\entrada\
```

Al abrir el Centro de Datos o el Mapa Territorial, POPIS examina esa bandeja. Las fuentes reconocidas se enrutan automáticamente:

```text
SINAVE       → data\actual\
SUIVE/SUAVE  → data\suive\
Población    → data\poblacion\
GeoJSON      → data\geografia\
Coordenadas  → data\coordenadas\
```

Los archivos no reconocidos permanecen sin modificar.

## Cómo elige las bases SINAVE

POPIS busca archivos dentro de la estructura del proyecto y reconoce una base SINAVE por columnas como:

- `Fec_captura`
- `SemanaInicio`
- `Folio`
- columnas de patógenos como `Salmonella`, `Shigella`, `Rotavirus`, etc.

Cuando encuentra varias bases del mismo año prioriza la carpeta `data/actual`, después históricos y finalmente otras ubicaciones. Así evita sumar dos veces el mismo año.

## Georreferenciación

La jerarquía del mapa es:

1. coordenada institucional por Folio, cuando existe;
2. coordenada presente en SINAVE;
3. centroide municipal derivado del GeoJSON;
4. registro sin coordenada.

Los centroides siempre se marcan como **aproximados**. POPIS no envía domicilios a geocodificadores públicos.

## Población e incidencia

POPIS intenta normalizar automáticamente tablas con columnas equivalentes a:

```text
Municipio | Poblacion | Año
```

Cuando la fuente poblacional no puede interpretarse con seguridad, el mapa mantiene el conteo municipal pero **no calcula una incidencia falsa**. El Centro de Datos muestra el estado de la fuente para poder corregirla de forma explícita.

## Dependencias nuevas

La actualización agrega al `requirements.txt` de POPIS, solo si faltan:

```text
folium>=0.17,<1
streamlit-folium>=0.23,<1
```

La versión de Streamlit recomendada sigue siendo `1.59.2`, compatible con el entorno aislado que ya utilizamos en Windows.
