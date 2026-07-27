# POPIS 5.0 · TODO EN UNO

**POPIS = Procesador Operativo de Patógenos e Indicadores Sanitarios**

Versión integral para Windows con instalación automatizada, migración no destructiva de versiones anteriores y mapa territorial basado por defecto en **centroides municipales**.

## Instalación

1. Descomprime el paquete completo.
2. Haz doble clic en `INSTALAR_Y_ABRIR_POPIS.bat`.
3. POPIS crea un entorno aislado en `%LOCALAPPDATA%\POPIS5\venv`.
4. El instalador busca una instalación POPIS anterior y migra de forma no destructiva sus carpetas de datos.
5. Al terminar abre automáticamente el tablero en el navegador.

Para uso diario ejecuta `INICIAR_POPIS.bat` o el acceso `POPIS 5.0.cmd` que el instalador intenta crear en el Escritorio.

## Funciones integradas

- Resumen epidemiológico por año y semana de corte.
- Casos acumulados y de la semana epidemiológica.
- Comparación histórica 2022–actualidad según las bases disponibles.
- Patógenos acumulados y por semana.
- Serie semanal SINAVE.
- Lectura automática SUIVE/SUAVE.
- Comparativo SUIVE ↔ SINAVE con **Razón de registro SINAVE/SUIVE**, sin etiquetarla automáticamente como subregistro.
- Canal endémico SUIVE.
- Canal endémico SINAVE.
- Canal endémico por patógeno.
- Selector de años históricos y exclusión opcional de 2020–2021 para SUIVE.
- Mortalidad registrada a partir de `FecDefuncion`, separada conceptualmente de la defunción normativa por EDA.
- Indicadores operativos del Manual EDA con numerador, denominador, meta y nota metodológica.
- Mapa territorial.
- Incidencia municipal cuando existe denominador poblacional compatible.
- Exportación Excel integral.
- Exportación masiva de gráficas PNG en ZIP.
- Centro de Datos y bandeja automática `data\entrada`.
- Respaldo automático antes de sustituir una fuente vigente.

## Mapa: centroides por defecto

POPIS 5.0 regresa al enfoque operativo de centroides:

1. Si hay GeoJSON municipal, calcula un centroide del polígono y lo usa.
2. Si no existe GeoJSON, usa el catálogo interno de municipios de Sonora.
3. Las coordenadas exactas de la base **NO se usan por defecto**.
4. Existe un interruptor opcional `Usar coordenadas exactas cuando estén disponibles` para análisis internos donde proceda.

Esto evita que el mapa quede vacío cuando las bases nominales no traen latitud/longitud y evita presentar una aproximación como si fuera un domicilio exacto.

## Actualización semanal

Puedes usar el cargador del panel lateral o simplemente copiar el nuevo archivo a:

`data\entrada\`

Al abrir POPIS, el sistema clasifica la fuente. Para una base SINAVE nueva:

- crea respaldo de la vigente;
- mueve la nueva a `data\actual`;
- vuelve a detectar año y semana máxima;
- recalcula tableros, canales, patógenos, mortalidad, territorio e indicadores.

También reconoce automáticamente fuentes SUIVE, población, GeoJSON y archivos institucionales de coordenadas.

## Datos y privacidad

El instalador no necesita publicar las bases nominales. Las bases del proyecto anterior se migran localmente en la computadora del usuario. Los paquetes de código y las pruebas no contienen nombres, domicilios ni folios reales.

## Reparación

Ejecuta `REPARAR_POPIS.bat`. El procedimiento reconstruye únicamente el entorno virtual de POPIS y conserva la carpeta `data`.

## Diagnóstico

Ejecuta `DIAGNOSTICO_POPIS.bat` para revisar Python, dependencias, fuentes detectadas y catálogo de centroides.
