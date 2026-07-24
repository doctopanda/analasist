# ============================================================
# PRISMA-R
# MODULO 18 V2.4.3 - ANIO + SEMANA EPIDEMIOLOGICOS EXPLICITOS
# ============================================================
# BUILD_18_V2_4_3_ANIO_SEMANA_EXPLICITOS_20260724_01
#
# Hallazgos reales que motivan este parche:
# - DENGUE 2026: 111 registros con ANO=2025, SEM=53 y fechas de
#   inicio de signos/sintomas del 01-03 enero 2026.
# - RICKETTSIA 2026: 8 registros con ANO=2025, SEM=53 y fechas de
#   inicio de signos/sintomas del 01-03 enero 2026.
# - SARAMPION 2026: 23 registros con AÑO=2025, SEMANA=31..53 y
#   fechas de inicio de exantema/notificacion en 2025.
# - EDAS 2024: 8 registros del 29-31 dic 2024 codificados como SE52
#   por la fuente, mientras epiweek los ubica en SE01 del siguiente
#   anio epidemiologico. Se conserva como convencion documentada.
#
# PRINCIPIOS:
# 1) anio_fuente != anio_epi != cobertura de la fuente.
# 2) Si la fuente trae un par epidemiologico explicito AÑO+SEMANA,
#    se usa ese par con prioridad y se audita contra la fecha.
# 3) Un cruce de anio se excluye del numerador del anio fuente,
#    pero NO se agrega automaticamente al archivo historico previo.
# 4) Las bases originales permanecen intactas.
# 5) Los conflictos entre AÑO+SEMANA y fecha no se corrigen en silencio.
# ============================================================

archivo_v242 <- here::here(
  "03_scripts",
  "18_motor_historico_comparativo_V2_4_2_CALENDARIO_EPI_FIX.R"
)

if (!file.exists(archivo_v242)) {
  stop(
    paste0(
      "No se encontro el modulo requerido V2.4.2: ",
      archivo_v242
    )
  )
}

source(archivo_v242)

# Congelar motor maestro V2.4.2 antes de redefinirlo.
.ejecutar_motor_historico_comparativo_18_v242 <-
  ejecutar_motor_historico_comparativo_18


# ============================================================
# 1. DETECCION CONSERVADORA DEL ANIO EPIDEMIOLOGICO EXPLICITO
# ============================================================

.detector_variable_anio_epi_18_v243 <- function(datos, sistema) {

  originales <- names(datos)
  norm <- .normalizar_texto_v24(originales)
  sis <- toupper(as.character(sistema)[1])

  # Nombres inequivocos pueden utilizarse en cualquier sistema.
  especificos <- c(
    "anio_epi",
    "ano_epi",
    "anio_epidemiologico",
    "ano_epidemiologico"
  )

  idx_especifico <- which(norm %in% especificos)

  if (length(idx_especifico) > 0) {
    return(originales[idx_especifico[1]])
  }

  # ANO/AÑO desnudo solo se habilita en sistemas auditados en datos
  # reales donde se observo emparejado con SEM/SEMANA.
  sistemas_auditados <- c(
    "DENGUE",
    "RICKETTSIA",
    "SARAMPION"
  )

  if (!sis %in% sistemas_auditados) {
    return(NA_character_)
  }

  idx <- which(norm %in% c("ano", "anio"))

  if (length(idx) == 0) {
    return(NA_character_)
  }

  # Preferir la columna con mayor proporcion de anios plausibles.
  puntaje <- vapply(
    idx,
    function(i) {
      x <- .extraer_anio_epi_explicito_18_v243(datos[[i]])
      mean(!is.na(x) & x >= 1900L & x <= 2100L)
    },
    numeric(1)
  )

  originales[idx[which.max(puntaje)]]
}


.extraer_anio_epi_explicito_18_v243 <- function(x) {

  z <- trimws(as.character(x))
  z[is.na(z)] <- ""

  out <- suppressWarnings(as.integer(z))

  faltan <- is.na(out)

  if (any(faltan)) {
    m <- regexpr("(?:19|20)[0-9]{2}", z[faltan], perl = TRUE)
    txt <- rep(NA_character_, sum(faltan))
    ok <- m > 0
    txt[ok] <- regmatches(z[faltan], m)[ok]
    out[faltan] <- suppressWarnings(as.integer(txt))
  }

  out[out < 1900L | out > 2100L] <- NA_integer_
  out
}


# ============================================================
# 2. FECHA DE EVENTO CONTEXTUAL PARA LOS SISTEMAS AUDITADOS
# ============================================================

.detectar_fecha_evento_contextual_18_v243 <- function(
  datos,
  sistema,
  variable_detectada = NA_character_
) {

  if (
    length(variable_detectada) == 1L &&
    !is.na(variable_detectada) &&
    variable_detectada %in% names(datos)
  ) {
    return(variable_detectada)
  }

  sis <- toupper(as.character(sistema)[1])

  candidatos <- switch(
    sis,
    DENGUE = c("FEC_INI_SIGNOS_SINT"),
    RICKETTSIA = c("FEC_INI_SIGNOS_SINT"),
    SARAMPION = c("FEC_INI_EXANT"),
    character(0)
  )

  if (length(candidatos) == 0) return(NA_character_)

  nombres <- names(datos)
  norm <- .normalizar_texto_v24(nombres)
  cand_norm <- .normalizar_texto_v24(candidatos)

  idx <- match(cand_norm, norm)
  idx <- idx[!is.na(idx)]

  if (length(idx) == 0) return(NA_character_)
  nombres[idx[1]]
}


# ============================================================
# 3. RESOLVER TEMPORALIDAD V2.4.3
# ============================================================

resolver_integridad_temporal_18_v243 <- function(
  sistema,
  semana_epi,
  fuente_semana,
  fecha_evento,
  anio_fuente,
  variable_fecha_evento = NA_character_,
  anio_epi_explicito = NA_integer_,
  variable_anio_epi = NA_character_
) {

  n <- length(semana_epi)

  sistema <- .rep_seguro_v24(sistema, n)
  fuente_semana <- .rep_seguro_v24(fuente_semana, n)
  anio_fuente <- as.integer(.rep_seguro_v24(anio_fuente, n))
  variable_fecha_evento <- .rep_seguro_v24(variable_fecha_evento, n)
  variable_anio_epi <- .rep_seguro_v24(variable_anio_epi, n)
  anio_epi_explicito <- as.integer(
    .rep_seguro_v24(anio_epi_explicito, n)
  )
  fecha_evento <- as.Date(.rep_seguro_v24(fecha_evento, n))

  epi_fecha <- semana_epidemiologica_domingo_18(fecha_evento)
  anio_epi_fecha <- as.integer(epi_fecha$anio_epi)
  semana_epi_fecha <- as.integer(epi_fecha$semana_epi)

  tiene_semana <- !is.na(semana_epi)
  tiene_fecha <- !is.na(fecha_evento)
  tiene_anio_explicito <-
    !is.na(anio_epi_explicito) &
    anio_epi_explicito >= 1900L &
    anio_epi_explicito <= 2100L

  desde_fecha <- grepl("^FECHA:", fuente_semana)
  desde_variable <- grepl("^VARIABLE:", fuente_semana)

  comparabilidad <- vapply(
    seq_len(n),
    function(i) {
      .clasificar_comparabilidad_semana_fecha_v24(
        sistema = sistema[i],
        fuente_semana = fuente_semana[i],
        variable_fecha_evento = variable_fecha_evento[i]
      )
    },
    character(1)
  )

  comparable <- comparabilidad %in% c(
    "MISMA_FECHA_GENERA_SEMANA",
    "COMPARABLE",
    "COMPARABLE_POTENCIAL"
  )

  coincide_semana_fecha <-
    tiene_semana &
    tiene_fecha &
    semana_epi == semana_epi_fecha

  par_explicito <-
    desde_variable &
    tiene_semana &
    tiene_anio_explicito

  par_fecha_concordante <-
    par_explicito &
    comparable &
    tiene_fecha &
    anio_epi_explicito == anio_epi_fecha &
    semana_epi == semana_epi_fecha

  par_fecha_discrepante <-
    par_explicito &
    comparable &
    tiene_fecha &
    !par_fecha_concordante

  # Convencion EDAS 2024 observada en registros 29-31 dic:
  # la fuente conserva SE52 del anio fuente mientras epiweek ya marca SE01.
  limite_anio_edas <-
    toupper(sistema) == "EDAS" &
    !par_explicito &
    desde_variable &
    comparable &
    tiene_semana &
    tiene_fecha &
    lubridate::month(fecha_evento) == 12L &
    semana_epi %in% c(52L, 53L) &
    semana_epi_fecha == 1L &
    anio_epi_fecha == anio_fuente + 1L

  anio_epi <- anio_fuente
  confianza <- rep("MEDIA_ANIO_FUENTE", n)
  fuente_anio_epi <- rep("ANIO_FUENTE", n)

  # Prioridad 1: par AÑO + SEMANA explicito.
  anio_epi[par_explicito] <- anio_epi_explicito[par_explicito]
  confianza[par_explicito] <- "ALTA"
  fuente_anio_epi[par_explicito] <- paste0(
    "VARIABLE:",
    variable_anio_epi[par_explicito]
  )

  # Conflicto del par explicito con fecha: se conserva la evidencia
  # explicita, pero se obliga a revision.
  confianza[par_fecha_discrepante] <- "BAJA_REVISAR"

  # Prioridad 2: semana derivada directamente de fecha.
  idx_fecha <- desde_fecha & tiene_fecha & !par_explicito
  anio_epi[idx_fecha] <- anio_epi_fecha[idx_fecha]
  confianza[idx_fecha] <- "ALTA"
  fuente_anio_epi[idx_fecha] <- paste0(
    "FECHA:",
    variable_fecha_evento[idx_fecha]
  )

  # Prioridad 3: semana explicita sin anio, validada por fecha concordante.
  idx_explicita_concordante <-
    desde_variable &
    !par_explicito &
    comparable &
    coincide_semana_fecha

  anio_epi[idx_explicita_concordante] <-
    anio_epi_fecha[idx_explicita_concordante]
  confianza[idx_explicita_concordante] <- "ALTA"
  fuente_anio_epi[idx_explicita_concordante] <- paste0(
    "FECHA:",
    variable_fecha_evento[idx_explicita_concordante]
  )

  discrepancia_semana_fecha <-
    desde_variable &
    !par_explicito &
    comparable &
    tiene_semana &
    tiene_fecha &
    !coincide_semana_fecha &
    !limite_anio_edas

  confianza[discrepancia_semana_fecha] <- "BAJA_REVISAR"

  no_comparable <-
    desde_variable &
    !comparable &
    tiene_fecha

  confianza[no_comparable & !par_explicito] <- "MEDIA_NO_COMPARABLE"

  confianza[limite_anio_edas] <- "MEDIA_CONVENCION_FUENTE"
  fuente_anio_epi[limite_anio_edas] <- "ANIO_FUENTE_CONVENCION_DOCUMENTADA"

  evidencia_alta_cruce <-
    (
      par_explicito & !par_fecha_discrepante
    ) |
    idx_fecha |
    idx_explicita_concordante

  cruza_anio_fuente <-
    evidencia_alta_cruce &
    !is.na(anio_epi) &
    anio_epi != anio_fuente

  requiere_revision <-
    par_fecha_discrepante |
    discrepancia_semana_fecha

  concordancia_semana_fecha <- dplyr::case_when(
    limite_anio_edas ~ "SEMANA_FECHA_DISCREPAN_LIMITE_ANIO_DOCUMENTADO",
    !tiene_fecha ~ "SIN_FECHA_EVENTO",
    desde_fecha ~ "SEMANA_DERIVADA_DE_FECHA",
    no_comparable ~ comparabilidad,
    coincide_semana_fecha ~ "SEMANA_FECHA_COINCIDEN",
    par_fecha_discrepante | discrepancia_semana_fecha ~ "SEMANA_FECHA_DISCREPAN",
    TRUE ~ "NO_EVALUABLE"
  )

  concordancia_anio_semana_fecha <- dplyr::case_when(
    !par_explicito ~ "NO_APLICA",
    !tiene_fecha ~ "SIN_FECHA_PARA_VALIDAR_PAR",
    !comparable ~ "FECHA_NO_COMPARABLE_SEMANTICAMENTE",
    par_fecha_concordante ~ "ANIO_SEMANA_FECHA_COINCIDEN",
    par_fecha_discrepante ~ "ANIO_SEMANA_FECHA_DISCREPAN",
    TRUE ~ "NO_EVALUABLE"
  )

  estado_temporal <- dplyr::case_when(
    par_fecha_discrepante ~ "DISCREPANCIA_ANIO_SEMANA_FECHA_REVISAR",
    par_explicito & cruza_anio_fuente ~ "ARRASTRE_ANIO_SEMANA_EXPLICITOS",
    par_explicito ~ "ANIO_SEMANA_EXPLICITOS",
    limite_anio_edas ~ "DISCREPANCIA_LIMITE_ANIO_FUENTE_DOCUMENTADA",
    cruza_anio_fuente ~ "ARRASTRE_OTRO_ANIO_EPIDEMIOLOGICO",
    discrepancia_semana_fecha ~ "DISCREPANCIA_SEMANA_FECHA_REVISAR",
    desde_fecha & tiene_fecha ~ "FECHA_EVENTO_RESUELTA",
    desde_variable & coincide_semana_fecha & comparable ~ "SEMANA_FECHA_CONCORDANTES",
    no_comparable ~ "SEMANA_FECHA_NO_COMPARABLE_SEMANTICAMENTE",
    desde_variable & !tiene_fecha ~ "SEMANA_EXPLICITA_ANIO_FUENTE",
    tiene_semana ~ "SEMANA_DISPONIBLE",
    TRUE ~ "SIN_TEMPORALIDAD_SEMANAL"
  )

  tibble::tibble(
    anio_fuente = anio_fuente,
    fecha_evento = fecha_evento,
    anio_epi_fecha = anio_epi_fecha,
    semana_epi_fecha = semana_epi_fecha,
    anio_epi_explicito = anio_epi_explicito,
    variable_anio_epi = variable_anio_epi,
    fuente_anio_epi = fuente_anio_epi,
    anio_epi = anio_epi,
    comparabilidad_semana_fecha = comparabilidad,
    concordancia_semana_fecha = concordancia_semana_fecha,
    concordancia_anio_semana_fecha = concordancia_anio_semana_fecha,
    confianza_anio_epi = confianza,
    cruza_anio_fuente = cruza_anio_fuente,
    candidato_reasignacion_epi = cruza_anio_fuente,
    requiere_revision_temporal = requiere_revision,
    limite_anio_fuente_documentado = limite_anio_edas,
    estado_temporal = estado_temporal,
    incluido_anio_fuente = !cruza_anio_fuente
  )
}

# Alias retrocompatible: mantiene llamadas de V2.4/V2.4.2.
resolver_integridad_temporal_18_v24 <-
  resolver_integridad_temporal_18_v243


# ============================================================
# 4. PREPARAR UNIDAD CON PAR AÑO+SEMANA
# ============================================================

preparar_unidad_historica_18 <- function(
  unidad,
  overrides_variables = NULL
) {

  base <- .preparar_unidad_historica_18_v23(
    unidad = unidad,
    overrides_variables = overrides_variables
  )

  datos <- leer_unidad_historica_18(
    archivo = unidad$archivo[1],
    hoja = unidad$hoja[1]
  )

  if (nrow(datos) != nrow(base)) {
    stop(
      paste0(
        "V2.4.3: longitud incompatible en ",
        unidad$id_unidad[1],
        ": datos=", nrow(datos),
        " temporal=", nrow(base)
      )
    )
  }

  sistema <- unidad$sistema[1]
  anio_fuente <- as.integer(unidad$anio[1])

  deteccion <- .deteccion_temporal_efectiva_18_v24(
    datos = datos,
    sistema = sistema,
    anio = anio_fuente,
    overrides_variables = overrides_variables
  )

  variable_fecha_evento <- .detectar_fecha_evento_contextual_18_v243(
    datos = datos,
    sistema = sistema,
    variable_detectada = deteccion$variable_fecha_inicio[1]
  )

  variable_fecha_defuncion <- NA_character_

  if (
    !is.na(deteccion$variable_fecha_defuncion[1]) &&
    deteccion$variable_fecha_defuncion[1] %in% names(datos)
  ) {
    variable_fecha_defuncion <- deteccion$variable_fecha_defuncion[1]
  }

  variable_anio_epi <- .detector_variable_anio_epi_18_v243(
    datos = datos,
    sistema = sistema
  )

  fecha_evento <- rep(as.Date(NA), nrow(datos))
  fecha_defuncion <- rep(as.Date(NA), nrow(datos))
  anio_epi_explicito <- rep(NA_integer_, nrow(datos))

  if (!is.na(variable_fecha_evento)) {
    fecha_evento <- parsear_fecha_18(datos[[variable_fecha_evento]])
  }

  if (!is.na(variable_fecha_defuncion)) {
    fecha_defuncion <- parsear_fecha_18(datos[[variable_fecha_defuncion]])
  }

  if (!is.na(variable_anio_epi)) {
    anio_epi_explicito <- .extraer_anio_epi_explicito_18_v243(
      datos[[variable_anio_epi]]
    )
  }

  temporal_evento <- resolver_integridad_temporal_18_v243(
    sistema = sistema,
    semana_epi = base$semana_epi,
    fuente_semana = base$fuente_semana,
    fecha_evento = fecha_evento,
    anio_fuente = anio_fuente,
    variable_fecha_evento = variable_fecha_evento,
    anio_epi_explicito = anio_epi_explicito,
    variable_anio_epi = variable_anio_epi
  )

  temporal_defuncion <- resolver_integridad_temporal_18_v243(
    sistema = sistema,
    semana_epi = base$semana_defuncion,
    fuente_semana = base$fuente_defuncion,
    fecha_evento = fecha_defuncion,
    anio_fuente = anio_fuente,
    variable_fecha_evento = variable_fecha_defuncion,
    anio_epi_explicito = NA_integer_,
    variable_anio_epi = NA_character_
  )

  base |>
    dplyr::mutate(
      anio_fuente = temporal_evento$anio_fuente,
      fecha_evento = temporal_evento$fecha_evento,
      variable_fecha_evento = variable_fecha_evento,
      anio_epi_fecha = temporal_evento$anio_epi_fecha,
      semana_epi_fecha = temporal_evento$semana_epi_fecha,
      anio_epi_explicito = temporal_evento$anio_epi_explicito,
      variable_anio_epi = temporal_evento$variable_anio_epi,
      fuente_anio_epi = temporal_evento$fuente_anio_epi,
      anio_epi = temporal_evento$anio_epi,
      comparabilidad_semana_fecha = temporal_evento$comparabilidad_semana_fecha,
      concordancia_semana_fecha = temporal_evento$concordancia_semana_fecha,
      concordancia_anio_semana_fecha = temporal_evento$concordancia_anio_semana_fecha,
      confianza_anio_epi = temporal_evento$confianza_anio_epi,
      cruza_anio_fuente = temporal_evento$cruza_anio_fuente,
      candidato_reasignacion_epi = temporal_evento$candidato_reasignacion_epi,
      requiere_revision_temporal = temporal_evento$requiere_revision_temporal,
      limite_anio_fuente_documentado = temporal_evento$limite_anio_fuente_documentado,
      estado_temporal = temporal_evento$estado_temporal,
      incluido_anio_fuente = temporal_evento$incluido_anio_fuente,

      fecha_defuncion_v24 = temporal_defuncion$fecha_evento,
      variable_fecha_defuncion_v24 = variable_fecha_defuncion,
      anio_epi_defuncion = temporal_defuncion$anio_epi,
      semana_epi_defuncion_fecha = temporal_defuncion$semana_epi_fecha,
      confianza_anio_epi_defuncion = temporal_defuncion$confianza_anio_epi,
      cruza_anio_defuncion = temporal_defuncion$cruza_anio_fuente
    )
}


# ============================================================
# 5. AUDITORIA DEL PAR AÑO + SEMANA EXPLICITO
# ============================================================

auditar_anio_semana_explicitos_18_v243 <- function(base_longitudinal) {

  requeridas <- c(
    "sistema",
    "anio_fuente",
    "semana_epi",
    "anio_epi_explicito",
    "variable_anio_epi",
    "fuente_anio_epi",
    "anio_epi",
    "cruza_anio_fuente",
    "requiere_revision_temporal",
    "estado_temporal"
  )

  faltan <- setdiff(requeridas, names(base_longitudinal))
  if (length(faltan) > 0) {
    stop(
      paste0(
        "Faltan columnas V2.4.3: ",
        paste(faltan, collapse = ", ")
      )
    )
  }

  base_longitudinal |>
    dplyr::filter(!is.na(anio_epi_explicito)) |>
    dplyr::group_by(
      sistema,
      anio_fuente,
      variable_anio_epi,
      fuente_anio_epi,
      anio_epi_explicito,
      semana_epi,
      anio_epi,
      estado_temporal
    ) |>
    dplyr::summarise(
      registros = dplyr::n(),
      cruces_anio = sum(cruza_anio_fuente, na.rm = TRUE),
      revisar = sum(requiere_revision_temporal, na.rm = TRUE),
      .groups = "drop"
    ) |>
    dplyr::arrange(
      sistema,
      anio_fuente,
      anio_epi_explicito,
      semana_epi
    )
}


# ============================================================
# 6. ENDURECIMIENTO DE CANDIDATOS DE DUPLICIDAD
# ============================================================
# Evita concatenar miles de referencias en una celda Excel y marca
# grupos masivos como valores no discriminantes.

resumir_candidatos_duplicidad_18_v24 <- function(detalle_ids) {

  if (
    is.null(detalle_ids) ||
    !is.data.frame(detalle_ids) ||
    nrow(detalle_ids) == 0
  ) {
    return(tibble::tibble())
  }

  detalle_ids |>
    dplyr::group_by(
      sistema,
      rol_identificador,
      valor_norm
    ) |>
    dplyr::summarise(
      n_anios = dplyr::n_distinct(anio_fuente),
      anios_fuente = paste(
        sort(unique(anio_fuente)),
        collapse = " | "
      ),
      n_registros = dplyr::n(),
      columnas_origen = paste(
        unique(columna_identificador),
        collapse = " | "
      ),
      referencias = paste(
        utils::head(
          unique(paste0(id_unidad, "#", fila_origen)),
          50L
        ),
        collapse = " | "
      ),
      referencias_omitidas = max(
        dplyr::n_distinct(paste0(id_unidad, "#", fila_origen)) - 50L,
        0L
      ),
      .groups = "drop"
    ) |>
    dplyr::filter(n_anios >= 2) |>
    dplyr::mutate(
      grupo_duplicidad = dplyr::row_number(),
      valor_no_discriminante = n_registros > 100L,
      confianza = dplyr::case_when(
        valor_no_discriminante ~ "BAJA_VALOR_NO_DISCRIMINANTE",
        rol_identificador == "CURP" ~ "ALTA_CANDIDATO_EXACTO",
        TRUE ~ "MEDIA_REQUIERE_VERIFICACION"
      ),
      accion = dplyr::case_when(
        valor_no_discriminante ~
          "NO_USAR_COMO_DUPLICIDAD_IDENTIFICADOR_NO_DISCRIMINANTE",
        TRUE ~ "NO_ELIMINAR_REVISAR_DUPLICIDAD"
      )
    ) |>
    dplyr::select(
      sistema,
      grupo_duplicidad,
      rol_identificador,
      confianza,
      valor_no_discriminante,
      n_anios,
      anios_fuente,
      n_registros,
      columnas_origen,
      referencias,
      referencias_omitidas,
      accion
    ) |>
    dplyr::arrange(
      sistema,
      valor_no_discriminante,
      dplyr::desc(n_anios),
      dplyr::desc(n_registros)
    )
}


# ============================================================
# 7. PRUEBAS SINTETICAS V2.4.3
# ============================================================

prueba_anio_semana_explicitos_18_v243 <- function() {

  x_dengue <- resolver_integridad_temporal_18_v243(
    sistema = "DENGUE",
    semana_epi = 53L,
    fuente_semana = "VARIABLE:SEM",
    fecha_evento = as.Date("2026-01-02"),
    anio_fuente = 2026L,
    variable_fecha_evento = "FEC_INI_SIGNOS_SINT",
    anio_epi_explicito = 2025L,
    variable_anio_epi = "ANO"
  )

  x_sar <- resolver_integridad_temporal_18_v243(
    sistema = "SARAMPION",
    semana_epi = 52L,
    fuente_semana = "VARIABLE:SEMANA",
    fecha_evento = as.Date("2025-12-23"),
    anio_fuente = 2026L,
    variable_fecha_evento = "FEC_INI_EXANT",
    anio_epi_explicito = 2025L,
    variable_anio_epi = "AÑO"
  )

  x_conflicto <- resolver_integridad_temporal_18_v243(
    sistema = "DENGUE",
    semana_epi = 10L,
    fuente_semana = "VARIABLE:SEM",
    fecha_evento = as.Date("2026-01-02"),
    anio_fuente = 2026L,
    variable_fecha_evento = "FEC_INI_SIGNOS_SINT",
    anio_epi_explicito = 2026L,
    variable_anio_epi = "ANO"
  )

  x_sin_anio <- resolver_integridad_temporal_18_v243(
    sistema = "DENGUE",
    semana_epi = 10L,
    fuente_semana = "VARIABLE:SEM",
    fecha_evento = as.Date(NA),
    anio_fuente = 2026L,
    variable_fecha_evento = NA_character_,
    anio_epi_explicito = NA_integer_,
    variable_anio_epi = NA_character_
  )

  x_edas <- resolver_integridad_temporal_18_v243(
    sistema = "EDAS",
    semana_epi = 52L,
    fuente_semana = "VARIABLE:SemanaInicio",
    fecha_evento = as.Date("2024-12-29"),
    anio_fuente = 2024L,
    variable_fecha_evento = "Fecha_Inicio",
    anio_epi_explicito = NA_integer_,
    variable_anio_epi = NA_character_
  )

  det <- tibble::tibble(
    sistema = rep("EDAS", 120),
    anio_fuente = rep(c(2024L, 2025L), each = 60),
    id_unidad = rep(c("A", "B"), each = 60),
    fila_origen = rep(seq_len(60), 2),
    rol_identificador = "FOLIO",
    columna_identificador = "Folio_Laboratorio",
    valor_norm = "REPETIDO"
  )

  dup <- resumir_candidatos_duplicidad_18_v24(det)

  tibble::tibble(
    prueba = c(
      "Dengue ANO=2025 SEM53 usa anio epidemiologico explicito",
      "Dengue ANO=2025 SEM53 detecta cruce desde fuente 2026",
      "Dengue cruce queda fuera del numerador del anio fuente",
      "Dengue par anio-semana coincide con fecha",
      "Dengue confianza del par concordante es alta",
      "Sarampion AÑO=2025 se conserva aunque fuente sea 2026",
      "Sarampion se identifica como arrastre explicito",
      "Conflicto anio-semana-fecha queda para revision",
      "Conflicto no se corrige silenciosamente con fecha",
      "Semana sin anio ni fecha conserva anio fuente",
      "Semana sin anio ni fecha no se marca cruce",
      "EDAS 29-dic-2024 se reconoce como limite anual documentado",
      "EDAS limite anual no exige revision critica",
      "EDAS limite anual conserva anio fuente",
      "Duplicidad masiva se marca no discriminante",
      "Duplicidad limita referencias exportadas",
      "Duplicidad informa referencias omitidas"
    ),
    pasa = c(
      x_dengue$anio_epi[1] == 2025L,
      isTRUE(x_dengue$cruza_anio_fuente[1]),
      !isTRUE(x_dengue$incluido_anio_fuente[1]),
      x_dengue$concordancia_anio_semana_fecha[1] ==
        "ANIO_SEMANA_FECHA_COINCIDEN",
      x_dengue$confianza_anio_epi[1] == "ALTA",
      x_sar$anio_epi[1] == 2025L,
      x_sar$estado_temporal[1] == "ARRASTRE_ANIO_SEMANA_EXPLICITOS",
      isTRUE(x_conflicto$requiere_revision_temporal[1]),
      x_conflicto$anio_epi[1] == 2026L,
      x_sin_anio$anio_epi[1] == 2026L,
      !isTRUE(x_sin_anio$cruza_anio_fuente[1]),
      isTRUE(x_edas$limite_anio_fuente_documentado[1]),
      !isTRUE(x_edas$requiere_revision_temporal[1]),
      x_edas$anio_epi[1] == 2024L,
      isTRUE(dup$valor_no_discriminante[1]),
      nchar(dup$referencias[1]) < 32767L,
      dup$referencias_omitidas[1] > 0L
    )
  )
}


validar_hotfix_18_v243 <- function() {

  funciones <- c(
    ".detector_variable_anio_epi_18_v243",
    ".extraer_anio_epi_explicito_18_v243",
    ".detectar_fecha_evento_contextual_18_v243",
    "resolver_integridad_temporal_18_v243",
    "preparar_unidad_historica_18",
    "auditar_anio_semana_explicitos_18_v243",
    "resumir_candidatos_duplicidad_18_v24",
    "prueba_anio_semana_explicitos_18_v243"
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

  pruebas <- prueba_anio_semana_explicitos_18_v243()

  cat("\n====================================================\n")
  cat("PRISMA-R | VALIDACION HOTFIX 18 V2.4.3\n")
  cat("ANIO + SEMANA EPIDEMIOLOGICOS EXPLICITOS\n")
  cat("====================================================\n\n")

  cat("Funciones:\n")
  print(estructura, n = Inf)

  cat("\nPruebas sinteticas:\n")
  print(pruebas, n = Inf, width = Inf)

  if (all(estructura$disponible) && all(pruebas$pasa)) {
    cat("\nOK HOTFIX 18 V2.4.3 VALIDADO FUNCIONALMENTE\n")
  } else {
    cat("\nREVISAR HOTFIX 18 V2.4.3\n")
  }

  invisible(list(estructura = estructura, pruebas = pruebas))
}


# ============================================================
# 8. MOTOR MAESTRO V2.4.3
# ============================================================

ejecutar_motor_historico_comparativo_18 <- function(
  resultado_17 = NULL,
  archivo_inventario = NULL,
  sistemas = NULL,
  overrides_unidades = NULL,
  overrides_variables = NULL,
  denominadores = NULL,
  semanas_objetivo = c(25L, 26L, 27L),
  anio_actual = as.integer(format(Sys.Date(), "%Y")),
  cortes_manual = NULL,
  archivo_salida = here::here(
    "04_resultados",
    paste0(
      "comparativo_historico_epidemiologico_V2_4_3_",
      format(Sys.Date(), "%Y-%m-%d"),
      ".xlsx"
    )
  ),
  generar_graficas = TRUE,
  detectar_duplicados = TRUE,
  guardar_checkpoint = TRUE,
  archivo_checkpoint = here::here(
    "04_resultados",
    "checkpoints",
    "resultado_18_V2_4_3_PRISMA_R.rds"
  ),
  mostrar_progreso = TRUE
) {

  resultado <- .ejecutar_motor_historico_comparativo_18_v242(
    resultado_17 = resultado_17,
    archivo_inventario = archivo_inventario,
    sistemas = sistemas,
    overrides_unidades = overrides_unidades,
    overrides_variables = overrides_variables,
    denominadores = denominadores,
    semanas_objetivo = semanas_objetivo,
    anio_actual = anio_actual,
    cortes_manual = cortes_manual,
    archivo_salida = archivo_salida,
    generar_graficas = generar_graficas,
    detectar_duplicados = detectar_duplicados,
    guardar_checkpoint = FALSE,
    mostrar_progreso = mostrar_progreso
  )

  auditoria_par <- auditar_anio_semana_explicitos_18_v243(
    resultado$base_longitudinal
  )

  resultado$auditoria_anio_semana_explicitos <- auditoria_par
  resultado$build_v243 <-
    "BUILD_18_V2_4_3_ANIO_SEMANA_EXPLICITOS_20260724_01"

  if (!is.null(resultado$resumen_general)) {
    idx_modulo <- resultado$resumen_general$indicador == "Modulo"
    idx_build <- resultado$resumen_general$indicador == "Build"

    resultado$resumen_general$valor[idx_modulo] <-
      "18 V2.4.3 - INTEGRIDAD TEMPORAL + ANIO/SEMANA EXPLICITOS"
    resultado$resumen_general$valor[idx_build] <-
      "BUILD_18_V2_4_3_ANIO_SEMANA_EXPLICITOS_20260724_01"
  }

  if (file.exists(archivo_salida)) {
    wb <- openxlsx::loadWorkbook(archivo_salida)

    .escribir_hoja_v24(
      wb,
      "Resumen_General",
      resultado$resumen_general
    )

    .escribir_hoja_v24(
      wb,
      "Anio_Semana_Explicitos",
      auditoria_par
    )

    openxlsx::saveWorkbook(
      wb,
      archivo_salida,
      overwrite = TRUE
    )
  }

  if (isTRUE(guardar_checkpoint)) {
    dir.create(
      dirname(archivo_checkpoint),
      recursive = TRUE,
      showWarnings = FALSE
    )

    saveRDS(resultado, archivo_checkpoint)
    resultado$checkpoint <- normalizePath(
      archivo_checkpoint,
      winslash = "/",
      mustWork = FALSE
    )
  }

  resultado$archivo_salida <- archivo_salida

  if (isTRUE(mostrar_progreso)) {
    cat("\n====================================================\n")
    cat("PRISMA-R | MODULO 18 V2.4.3 COMPLETADO\n")
    cat("====================================================\n")
    cat("\nAÑO+SEMANA explicitos integrados de forma conservadora.\n")
    cat("Cruces de anio NO se reasignan automaticamente al historico previo.\n")
    cat("Bases originales intactas.\n")
    cat("\nReporte:\n", archivo_salida, "\n", sep = "")
    if (isTRUE(guardar_checkpoint)) {
      cat("\nCheckpoint:\n", resultado$checkpoint, "\n", sep = "")
    }
  }

  resultado
}


cat("\n====================================================\n")
cat("PRISMA-R | MODULO 18 V2.4.3 CARGADO\n")
cat("ANIO + SEMANA EPIDEMIOLOGICOS EXPLICITOS\n")
cat("====================================================\n")
cat("\nReglas nuevas:\n")
cat("- DENGUE/RICKETTSIA/SARAMPION pueden usar ANO/AÑO + SEM/SEMANA.\n")
cat("- El par explicito se audita contra fecha cuando existe.\n")
cat("- EDAS frontera anual 2024 se conserva como convencion documentada.\n")
cat("- Cruces se excluyen del anio fuente sin migracion automatica.\n")
cat("- Referencias de duplicidad se limitan para Excel y grupos masivos se marcan.\n")
cat("\nValidacion:\n")
cat("validacion_18_v243 <- validar_hotfix_18_v243()\n")
cat("\nEjecucion real:\n")
cat("resultado_18_v243 <- ejecutar_motor_historico_comparativo_18(resultado_17 = resultado_17)\n")
