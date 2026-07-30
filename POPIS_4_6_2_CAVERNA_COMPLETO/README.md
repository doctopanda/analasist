# POPIS 4.6.2 · CAVERNA · COMPLETO

**POPIS** = Procesador Operativo de Patógenos e Indicadores Sanitarios.

Esta carpeta contiene una instalación completa e independiente de POPIS 4.6.2 con la identidad visual CAVERNA integrada desde el núcleo. No es un parche y no necesita otra versión de POPIS para funcionar.

## Módulos incluidos

- Panorama / Resumen epidemiológico
- SINAVE nominal EDA
- SUIVE/SUAVE convencional
- Comparativo SINAVE ↔ SUIVE
- Canal endémico SUIVE
- Canal endémico SINAVE y por patógeno
- Mortalidad registrada y territorio
- Incidencia municipal por año
- Mapa municipal por centroides, sin geocodificación de domicilios
- Indicadores normativos del Manual EDA 2022 con numerador, denominador, meta y auditabilidad
- Calidad y auditoría de datos
- Exportación Excel, Word, HTML y PNG
- Bandeja `data/entrada` para actualización automática
- Migrador opcional de datos desde instalaciones POPIS previas
- Instalación Windows con entorno virtual aislado

## Estructura

```text
POPIS_4_6_2_CAVERNA_COMPLETO/
  app.py
  VERSION.txt
  requirements.txt
  INICIAR_POPIS.bat
  INSTALAR_Y_ABRIR_POPIS.bat
  REPARAR_POPIS.bat
  DIAGNOSTICO_POPIS.bat
  MIGRAR_DATOS_EXISTENTES.py
  config/
    indicadores_eda_2022.yaml
    data_sources.yaml
  modulos/
    __init__.py
    tema_caverna.py
    io_utils.py
    sinave.py
    suive.py
    canal_endemico.py
    comparativo.py
    indicadores.py
    territorio.py
    calidad.py
    exportacion.py
    runtime.py
  pages/
    01_Resumen.py
    02_SINAVE.py
    03_SUIVE.py
    04_Comparativo.py
    05_Canal_Endemico.py
    06_Mortalidad_Territorio.py
    07_Indicadores_Normativos.py
    08_Calidad_Auditoria.py
    09_Exportacion.py
  data/
    historicos/
    actual/
    suive/
    poblacion/
    geografia/
    entrada/
    backups/
  salidas/
  cache/
  logs/
```

## Instalación recomendada en Windows

1. Descomprime la carpeta.
2. Ejecuta `INSTALAR_Y_ABRIR_POPIS.bat`.
3. El entorno virtual se crea en `%LOCALAPPDATA%\POPIS462\venv`.
4. El navegador abre POPIS automáticamente.

La instalación no modifica los paquetes globales de Python.

## Bases

### SINAVE nominal
Coloca bases históricas `Diarreas_*.xls` en `data/historicos/` y la base vigente en `data/actual/`. Los `.xls` que en realidad son texto tabulado son detectados automáticamente. El eje temporal principal es `SemanaInicio`.

### SUIVE/SUAVE y libro de canal endémico
Coloca el histórico en `data/suive/`. POPIS reconoce tanto formato largo (`Año`, `Semana`, `Casos`) como el formato semanal ancho utilizado por el libro de canal endémico.

Está soportada explícitamente la familia de archivos:

```text
Canal endemico EDAs_SUIVE_SINAVE*.xlsx
```

POPIS busca la hoja `SUIVE` aunque no sea la hoja activa y la usa como fuente convencional histórica. Si el libro contiene una hoja `SINAVE` vacía o preparada como plantilla, no se transforma en casos nominales: los registros SINAVE por paciente siguen viniendo de las bases `Diarreas_*.xls`.

### Población municipal
Coloca la fuente en `data/poblacion/`. Además de tablas simples, POPIS reconoce explícitamente:

```text
Sonora.ProyeccionesPoblacionMunicipales2015-2030*.xlsx
```

Busca la hoja `Sonora` y admite la estructura longitudinal:

```text
CLAVE | CLAVE_ENT | NOM_ENT | MUN | SEXO | AÑO | EDAD_QUIN | POB
```

Para la incidencia municipal selecciona el año solicitado, conserva Sonora (`CLAVE_ENT = 26`) y suma `POB` por municipio sobre Hombres y Mujeres y los grupos de edad disponibles. No toma otro año silenciosamente cuando el año solicitado no existe.

### Cartografía
POPIS usa centroides municipales. Si no existe GeoJSON en `data/geografia/`, puede descargar el Marco Geoestadístico municipal de Sonora desde el servicio oficial de INEGI y guardarlo localmente. No se envían domicilios ni datos nominales a geocodificadores públicos.

## Actualización semanal

También puedes copiar una nueva fuente a `data/entrada/`. POPIS clasifica los archivos reconocibles, respalda la fuente operativa anterior y los mueve al directorio correspondiente.

Los dos libros anteriores pueden dejarse directamente en `data/entrada/`: el primero se enruta a `data/suive/` y el segundo a `data/poblacion/`.

## Criterios epidemiológicos importantes

- Semana principal SINAVE: `SemanaInicio`.
- Geografía primaria: municipio de residencia.
- SUIVE y SINAVE se comparan, **no se suman**.
- La métrica comparativa se denomina **Razón de registro SINAVE/SUIVE**, no subregistro.
- Los centroides son aproximaciones territoriales, no domicilios.
- `FecDefuncion` se reporta como defunción registrada en la base, no como defunción normativa por EDA sin validación adicional.
- Una semana futura o posterior al último dato observado se mantiene como ausente (`NaN`), no se convierte en cero.

## Visual CAVERNA

El tema está integrado en todas las páginas: sidebar azul marino, acento coral, tarjetas blancas redondeadas, KPIs compactos y gráficos con paleta azul/verde/morado/coral.
