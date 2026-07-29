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

### SINAVE
Coloca bases históricas en `data/historicos/` y la base vigente en `data/actual/`. Los `.xls` que en realidad son texto tabulado son detectados automáticamente.

### SUIVE/SUAVE
Coloca el histórico en `data/suive/`. POPIS reconoce tanto formato largo (`Año`, `Semana`, `Casos`) como el formato semanal ancho utilizado por el libro de canal endémico.

### Población
Coloca la tabla municipal en `data/poblacion/`. POPIS busca municipio, población y año mediante nombres equivalentes. Si no existe un denominador compatible, muestra conteos pero no inventa tasas.

### Cartografía
POPIS usa centroides municipales. Si no existe GeoJSON en `data/geografia/`, puede descargar el Marco Geoestadístico municipal de Sonora desde el servicio oficial de INEGI y guardarlo localmente. No se envían domicilios ni datos nominales a geocodificadores públicos.

## Actualización semanal

También puedes copiar la nueva fuente a `data/entrada/`. POPIS clasifica los archivos reconocibles, respalda la fuente operativa anterior y los mueve al directorio correspondiente.

## Criterios epidemiológicos importantes

- Semana principal SINAVE: `SemanaInicio`.
- Geografía primaria: municipio de residencia.
- SUIVE y SINAVE se comparan, **no se suman**.
- La métrica comparativa se denomina **Razón de registro SINAVE/SUIVE**, no subregistro.
- Los centroides son aproximaciones territoriales, no domicilios.
- `FecDefuncion` se reporta como defunción registrada en la base, no como defunción normativa por EDA sin validación adicional.

## Visual CAVERNA

El tema está integrado en todas las páginas: sidebar azul marino, acento coral, tarjetas blancas redondeadas, KPIs compactos y gráficos con paleta azul/verde/morado/coral.
