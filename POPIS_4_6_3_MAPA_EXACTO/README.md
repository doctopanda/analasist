# POPIS 4.6.3 · Mapa Exacto

**POPIS = Procesador Operativo de Patógenos e Indicadores Sanitarios**

Esta revisión agrega al módulo territorial de POPIS una capa espacial pensada para vigilancia epidemiológica operativa:

- puntos con coordenadas exactas, cuando la base o un archivo institucional las contiene;
- diferenciación entre coordenadas exactas y aproximadas;
- mapa de concentración con opacidad regulable;
- vista `Solo concentración`, `Solo puntos` y `Concentración + puntos`;
- límites municipales y distritales como capas independientes;
- tabla municipal con incidencia por 1,000, 10,000 o 100,000 habitantes;
- porcentaje de casos estatales, porcentaje de población estatal y razón casos/población;
- filtro `Solo exactos`;
- carga de un archivo institucional de coordenadas por `Folio`, sin enviar domicilios a servicios públicos de geocodificación;
- descarga del mapa interactivo en HTML y de la tabla municipal en Excel.

## Privacidad

POPIS 4.6.3 **no geocodifica domicilios automáticamente en Internet**. Para representar un caso en una ubicación exacta se utilizan únicamente:

1. coordenadas ya incluidas en la base; o
2. un archivo institucional de coordenadas enlazado por `Folio`.

Los popups del mapa no muestran calle, número exterior, teléfono, CURP ni nombre del paciente.

## Archivos

- `app_mapa.py`: visor autónomo para probar el módulo espacial.
- `modulos/mapa_espacial.py`: motor cartográfico reutilizable dentro del POPIS principal.
- `requirements_mapa.txt`: dependencias adicionales.

## Archivo de coordenadas institucionales

Se puede cargar CSV/XLSX con al menos:

| Folio | Latitud | Longitud | Fuente_Coordenada |
|---|---:|---:|---|
| DIA26-000001 | 29.0820 | -110.9620 | Exacta institucional |

`Fuente_Coordenada` es opcional, pero ayuda a distinguir una coordenada exacta de un centroide.

## Capas GeoJSON

El visor acepta dos GeoJSON opcionales:

- municipios;
- distritos de salud.

Cuando están cargados, se dibujan sin relleno para mantener visibles las calles y la capa de concentración.

## Integración en POPIS 4.6.x

En el `app.py` principal:

```python
from modulos.mapa_espacial import render_mapa_espacial

# Dentro de la pestaña Territorio
render_mapa_espacial(base_sinave)
```

La función también acepta objetos GeoJSON y una tabla de población ya cargados por el motor principal:

```python
render_mapa_espacial(
    base_sinave,
    geojson_municipios=geo_municipios,
    geojson_distritos=geo_distritos,
    poblacion=poblacion_municipal,
)
```

## Dependencias

```bash
pip install -r requirements_mapa.txt
streamlit run app_mapa.py
```

La versión de Streamlit permanece fijada en `1.59.2`, que es la rama que ya funcionó con el entorno aislado de POPIS en Windows.

## Nota epidemiológica

La incidencia municipal usa como numerador los casos asignados al municipio de residencia y como denominador la población municipal cargada. Los casos sin población válida se conservan en el conteo, pero su tasa queda sin calcular. La razón casos/población es:

`(% de casos estatales) / (% de población estatal)`

Una razón > 1 indica una participación de casos mayor que la participación poblacional del municipio. No implica por sí sola causalidad, brote ni riesgo individual.
