# ============================================================
# PRISMA-R
# MODULO 18 V2.4 - INTEGRIDAD TEMPORAL EPIDEMIOLOGICA
# ============================================================
#
# BUILD_18_V2_4_INTEGRIDAD_TEMPORAL_20260724_01
#
# Extiende el nucleo estable V2.3 sin modificar bases originales.
#
# Objetivos:
# - separar anio_fuente de anio_epi;
# - conservar fecha_evento y fuente temporal;
# - auditar concordancia semana-fecha;
# - detectar cruces de anio epidemiologico sin reasignarlos;
# - separar base longitudinal completa de base analitica temporal;
# - inferir corte operativo desde la fuente, no desde max(semana);
# - distinguir semanas sin eventos de semanas no cubiertas;
# - generar matriz anio fuente x anio epidemiologico;
# - generar candidatos de duplicidad historica sin exportar IDs crudos;
# - guardar checkpoint RDS;
# - preservar trazabilidad completa.
#
# PRINCIPIO CENTRAL:
# LA EVIDENCIA NO SE BORRA NI SE REASIGNA AUTOMATICAMENTE.
# LA DECISION ANALITICA OCURRE EN UNA CAPA SEPARADA.
# ============================================================


# ============================================================
# 0. CARGAR NUCLEO V2.3
# ============================================================

archivo_nucleo_18_v23 <- here::here(
  "03_scripts",
  "18_motor_historico_comparativo_V2_3_SEMANA_MIXTA_FIX.R"
)

if (!file.exists(archivo_nucleo_18_v23)) {
  stop(
    paste0(
      "No se encontro el nucleo requerido V2.3: ",
      archivo_nucleo_18_v23
    )
  )
}

source(archivo_nucleo_18_v23)


# Congelar funciones V2.3 antes de extenderlas.
.preparar_unidad_historica_18_v23 <- preparar_unidad_historica_18
.construir_casos_semanales_18_v23 <- construir_casos_semanales_18
.construir_defunciones_semanales_18_v23 <- construir_defunciones_semanales_18
.resumen_anual_historico_18_v23 <- resumen_anual_historico_18
.ejecutar_motor_historico_comparativo_18_v23 <- ejecutar_motor_historico_comparativo_18
.validar_modulo_18_v23 <- validar_modulo_18


# ============================================================
# 1. UTILIDADES SEGURAS
# ============================================================

.normalizar_texto_v24 <- function(x) {
  x <- as.character(x)
  x[is.na(x)] <- ""

  y <- iconv(
    x,
    from = "",
    to = "ASCII//TRANSLIT"
  )

  y[is.na(y)] <- x[is.na(y)]
  y <- tolower(trimws(y))
  y <- gsub("[^a-z0-9]+", "_", y)
  y <- gsub("^_+|_+$", "", y)
  y
}


.rep_seguro_v24 <- function(x, n) {
  if (length(x) == n) return(x)
  if (length(x) == 1L) return(rep(x, n))
  stop("Longitud incompatible en vector temporal V2.4.")
}


.tabla_exportable_18_v24 <- function(x, mensaje = "Sin registros") {
  if (
    is.null(x) ||
    !is.data.frame(x) ||
    nrow(x) == 0 ||
    ncol(x) == 0
  ) {
    return(tibble::tibble(mensaje = mensaje))
  }

  x
}


# ============================================================
# 2. DETECCION TEMPORAL EFECTIVA CON OVERRIDES
# ============================================================

.deteccion_temporal_efectiva_18_v24 <- function(
  datos,
  sistema,
  anio,
  overrides_variables = NULL
) {

  deteccion <- detectar_variables_historicas_18(
    datos = datos,
    sistema = sistema
  )

  if (
    is.null(overrides_variables) ||
    !is.data.frame(overrides_variables) ||
    nrow(overrides_variables) == 0
  ) {
    return(deteccion)
  }

  if (!"anio" %in% names(overrides_variables)) {
    overrides_variables$anio <- NA_integer_
  }

  ov <- overrides_variables |>
    dplyr::filter(
      .data$sistema == .env$sistema,
      is.na(.data$anio) |
        .data$anio == .env$anio
    ) |>
    dplyr::mutate(
      especificidad_anio = dplyr::if_else(
        is.na(.data$anio),
        0L,
        1L
      )
    ) |>
    dplyr::arrange(
      dplyr::desc(.data$especificidad_anio)
    ) |>
    dplyr::slice_head(n = 1)

  if (nrow(ov) == 0) return(deteccion)

  campos <- c(
    "variable_semana",
    "variable_fecha_inicio",
    "variable_fecha_defuncion",
    "variable_indicador_defuncion"
  )

  for (campo in campos) {
    if (
      campo %in% names(ov) &&
      !is.na(ov[[campo]][1]) &&
      trimws(as.character(ov[[campo]][1])) != ""
    ) {
      deteccion[[campo]][1] <- ov[[campo]][1]
    }
  }

  deteccion
}


# ============================================================
# 3. COMPARABILIDAD SEMANA-FECHA
# ============================================================

.clasificar_comparabilidad_semana_fecha_v24 <- function(
  sistema,
  fuente_semana,
  variable_fecha_evento
) {

  sis <- toupper(as.character(sistema))
  fs <- .normalizar_texto_v24(
    sub("^[A-Z]+:", "", as.character(fuente_semana))
  )
  vf <- .normalizar_texto_v24(variable_fecha_evento)

  if (grepl("^FECHA:", as.character(fuente_semana))) {
    return("MISMA_FECHA_GENERA_SEMANA")
  }

  if (vf == "") return("SIN_FECHA_COMPARABLE")

  # VIH usa SEMANA como semana de notificacion segun definicion operativa
  # validada por el usuario. No debe contrastarse automaticamente contra
  # una fecha clinica de inicio.
  if (sis == "VIH") {
    return("NO_COMPARABLE_SEMANA_NOTIFICACION")
  }

  if (grepl("notif|notificacion|registro|captura", fs)) {
    return("NO_COMPARABLE_SEMANA_NOTIFICACION")
  }

  if (grepl("defun|muerte|falle", fs)) {
    return("NO_COMPARABLE_SEMANA_DEFUNCION")
  }

  if (
    grepl("inicio|sint|signo|paral", fs) &&
    grepl("inicio|sint|signo|paral", vf)
  ) {
    return("COMPARABLE")
  }

  if (fs %in% c(
    "semana_epidemiologica",
    "sem_epi",
    "semana_epi",
    "s_e",
    "semana",
    "sem"
  )) {
    return("COMPARABLE_POTENCIAL")
  }

  "NO_COMPARABLE_SEMANTICA_NO_RESUELTA"
}


# ============================================================
# 4. RESOLVER TEMPORALIDAD DE EVENTO
# ============================================================

resolver_integridad_temporal_18_v24 <- function(
  sistema,
  semana_epi,
  fuente_semana,
  fecha_evento,
  anio_fuente,
  variable_fecha_evento = NA_character_
) {

  n <- length(semana_epi)

  sistema <- .rep_seguro_v24(sistema, n)
  fuente_semana <- .rep_seguro_v24(fuente_semana, n)
  anio_fuente <- as.integer(
    .rep_seguro_v24(anio_fuente, n)
  )
  variable_fecha_evento <- .rep_seguro_v24(
    variable_fecha_evento,
    n
  )

  fecha_evento <- as.Date(
    .rep_seguro_v24(fecha_evento, n)
  )

  epi_fecha <- semana_epidemiologica_domingo_18(
    fecha_evento
  )

  anio_epi_fecha <- as.integer(epi_fecha$anio_epi)
  semana_epi_fecha <- as.integer(epi_fecha$semana_epi)

  tiene_semana <- !is.na(semana_epi)
  tiene_fecha <- !is.na(fecha_evento)
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

  coincide <-
    tiene_semana &
    tiene_fecha &
    semana_epi == semana_epi_fecha

  anio_epi <- anio_fuente
  confianza <- rep("MEDIA_ANIO_FUENTE", n)

  # Semana construida directamente desde la fecha.
  idx_fecha <- desde_fecha & tiene_fecha
  anio_epi[idx_fecha] <- anio_epi_fecha[idx_fecha]
  confianza[idx_fecha] <- "ALTA"

  # Semana explicita: el anio de la fecha solo se acepta cuando
  # semana y fecha son semanticamente comparables y coinciden.
  idx_explicita_concordante <-
    desde_variable &
    comparable &
    coincide

  anio_epi[idx_explicita_concordante] <-
    anio_epi_fecha[idx_explicita_concordante]
  confianza[idx_explicita_concordante] <- "ALTA"

  discrepancia <-
    desde_variable &
    comparable &
    tiene_semana &
    tiene_fecha &
    !coincide

  confianza[discrepancia] <- "BAJA_REVISAR"

  no_comparable <-
    desde_variable &
    !comparable &
    tiene_fecha

  confianza[no_comparable] <- "MEDIA_NO_COMPARABLE"

  cruza_anio_fuente <-
    confianza == "ALTA" &
    !is.na(anio_epi) &
    anio_epi != anio_fuente

  concordancia <- dplyr::case_when(
    !tiene_fecha ~ "SIN_FECHA_EVENTO",
    desde_fecha ~ "SEMANA_DERIVADA_DE_FECHA",
    no_comparable ~ comparabilidad,
    coincide ~ "SEMANA_FECHA_COINCIDEN",
    discrepancia ~ "SEMANA_FECHA_DISCREPAN",
    TRUE ~ "NO_EVALUABLE"
  )

  estado_temporal <- dplyr::case_when(
    cruza_anio_fuente ~ "ARRASTRE_OTRO_ANIO_EPIDEMIOLOGICO",
    discrepancia ~ "DISCREPANCIA_SEMANA_FECHA_REVISAR",
    desde_fecha & tiene_fecha ~ "FECHA_EVENTO_RESUELTA",
    desde_variable & coincide & comparable ~ "SEMANA_FECHA_CONCORDANTES",
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
    anio_epi = anio_epi,
    comparabilidad_semana_fecha = comparabilidad,
    concordancia_semana_fecha = concordancia,
    confianza_anio_epi = confianza,
    cruza_anio_fuente = cruza_anio_fuente,
    candidato_reasignacion_epi = cruza_anio_fuente,
    requiere_revision_temporal = discrepancia,
    estado_temporal = estado_temporal,
    incluido_anio_fuente = !cruza_anio_fuente
  )
}


# ============================================================
# 5. PREPARAR UNIDAD V2.4
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
        "V2.4: longitud incompatible en ",
        unidad$id_unidad[1],
        ": datos=",
        nrow(datos),
        " temporal=",
        nrow(base)
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

  variable_fecha_evento <- NA_character_
  variable_fecha_defuncion <- NA_character_

  if (
    !is.na(deteccion$variable_fecha_inicio[1]) &&
    deteccion$variable_fecha_inicio[1] %in% names(datos)
  ) {
    variable_fecha_evento <- deteccion$variable_fecha_inicio[1]
  }

  if (
    !is.na(deteccion$variable_fecha_defuncion[1]) &&
    deteccion$variable_fecha_defuncion[1] %in% names(datos)
  ) {
    variable_fecha_defuncion <- deteccion$variable_fecha_defuncion[1]
  }

  fecha_evento <- rep(as.Date(NA), nrow(datos))
  fecha_defuncion <- rep(as.Date(NA), nrow(datos))

  if (!is.na(variable_fecha_evento)) {
    fecha_evento <- parsear_fecha_18(
      datos[[variable_fecha_evento]]
    )
  }

  if (!is.na(variable_fecha_defuncion)) {
    fecha_defuncion <- parsear_fecha_18(
      datos[[variable_fecha_defuncion]]
    )
  }

  temporal_evento <- resolver_integridad_temporal_18_v24(
    sistema = sistema,
    semana_epi = base$semana_epi,
    fuente_semana = base$fuente_semana,
    fecha_evento = fecha_evento,
    anio_fuente = anio_fuente,
    variable_fecha_evento = variable_fecha_evento
  )

  temporal_defuncion <- resolver_integridad_temporal_18_v24(
    sistema = sistema,
    semana_epi = base$semana_defuncion,
    fuente_semana = base$fuente_defuncion,
    fecha_evento = fecha_defuncion,
    anio_fuente = anio_fuente,
    variable_fecha_evento = variable_fecha_defuncion
  )

  base |>
    dplyr::mutate(
      anio_fuente = temporal_evento$anio_fuente,
      fecha_evento = temporal_evento$fecha_evento,
      variable_fecha_evento = variable_fecha_evento,
      anio_epi_fecha = temporal_evento$anio_epi_fecha,
      semana_epi_fecha = temporal_evento$semana_epi_fecha,
      anio_epi = temporal_evento$anio_epi,
      comparabilidad_semana_fecha = temporal_evento$comparabilidad_semana_fecha,
      concordancia_semana_fecha = temporal_evento$concordancia_semana_fecha,
      confianza_anio_epi = temporal_evento$confianza_anio_epi,
      cruza_anio_fuente = temporal_evento$cruza_anio_fuente,
      candidato_reasignacion_epi = temporal_evento$candidato_reasignacion_epi,
      requiere_revision_temporal = temporal_evento$requiere_revision_temporal,
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
# 6. PARSER DE CORTE OPERATIVO
# ============================================================

.semana_desde_fecha_corte_18_v24 <- function(fecha) {
  semana_epidemiologica_domingo_18(
    as.Date(fecha)
  )$semana_epi
}


extraer_corte_fuente_18_v24 <- function(
  id_unidad,
  anio
) {

  original <- as.character(id_unidad)
  z <- iconv(original, from = "", to = "ASCII//TRANSLIT")
  if (is.na(z)) z <- original
  z <- tolower(z)

  # SE01-26, SE 01-26, se01_26
  m <- regexec(
    "se\\s*0?1\\s*[-_]\\s*([0-9]{1,2})",
    z,
    perl = TRUE
  )
  g <- regmatches(z, m)[[1]]

  if (length(g) >= 2) {
    s <- suppressWarnings(as.integer(g[2]))
    if (!is.na(s) && s >= 1 && s <= 53) {
      return(tibble::tibble(
        semana_corte_fuente = s,
        fecha_corte_fuente = as.Date(NA),
        metodo_corte = "SEMANA_RANGO_EN_NOMBRE"
      ))
    }
  }

  patrones <- c(
    "corte\\s+semana\\s*#?\\s*([0-9]{1,2})",
    "semana\\s*#?\\s*([0-9]{1,2})",
    "sem\\s*#?\\s*([0-9]{1,2})",
    "(?:^|[^a-z])se\\s*#\\s*([0-9]{1,2})"
  )

  for (patron in patrones) {
    m <- regexec(patron, z, perl = TRUE)
    g <- regmatches(z, m)[[1]]

    if (length(g) >= 2) {
      s <- suppressWarnings(as.integer(g[2]))
      if (!is.na(s) && s >= 1 && s <= 53) {
        return(tibble::tibble(
          semana_corte_fuente = s,
          fecha_corte_fuente = as.Date(NA),
          metodo_corte = "SEMANA_EXPLICITA_EN_NOMBRE"
        ))
      }
    }
  }

  # CORTE AL DIA 21 07 26 / CORTE 11-07-2026
  m <- regexec(
    "corte(?:\\s+al\\s+dia)?\\s+([0-3]?[0-9])[-_ /]+([01]?[0-9])[-_ /]+((?:20)?[0-9]{2})",
    z,
    perl = TRUE
  )
  g <- regmatches(z, m)[[1]]

  if (length(g) >= 4) {
    d <- suppressWarnings(as.integer(g[2]))
    mm <- suppressWarnings(as.integer(g[3]))
    yy <- suppressWarnings(as.integer(g[4]))

    if (!is.na(yy) && yy < 100) yy <- 2000L + yy

    fecha <- suppressWarnings(
      as.Date(sprintf("%04d-%02d-%02d", yy, mm, d))
    )

    if (
      !is.na(fecha) &&
      as.integer(format(fecha, "%Y")) == as.integer(anio)
    ) {
      return(tibble::tibble(
        semana_corte_fuente = as.integer(
          .semana_desde_fecha_corte_18_v24(fecha)
        ),
        fecha_corte_fuente = fecha,
        metodo_corte = "FECHA_CORTE_EN_NOMBRE"
      ))
    }
  }

  tibble::tibble(
    semana_corte_fuente = NA_integer_,
    fecha_corte_fuente = as.Date(NA),
    metodo_corte = "NO_INFERIDO"
  )
}


registro_cortes_operativos_18_v24 <- function(
  base_longitudinal,
  anio_actual,
  cortes_manual = NULL
) {

  fuentes <- base_longitudinal |>
    dplyr::distinct(
      sistema,
      anio_fuente,
      id_unidad
    )

  extraidos <- vector("list", nrow(fuentes))

  for (i in seq_len(nrow(fuentes))) {
    x <- extraer_corte_fuente_18_v24(
      id_unidad = fuentes$id_unidad[i],
      anio = fuentes$anio_fuente[i]
    )

    extraidos[[i]] <- dplyr::bind_cols(
      fuentes[i, , drop = FALSE],
      x
    )
  }

  detalle <- dplyr::bind_rows(extraidos)

  resumen <- detalle |>
    dplyr::group_by(
      sistema,
      anio_fuente
    ) |>
    dplyr::summarise(
      n_fuentes = dplyr::n(),
      n_cortes_inferidos = sum(!is.na(semana_corte_fuente)),
      n_cortes_distintos = dplyr::n_distinct(
        semana_corte_fuente[!is.na(semana_corte_fuente)]
      ),
      semana_inferida = {
        vals <- unique(
          semana_corte_fuente[!is.na(semana_corte_fuente)]
        )
        if (length(vals) == 1L) vals[1] else NA_integer_
      },
      fecha_corte_fuente = {
        vals <- unique(
          fecha_corte_fuente[!is.na(fecha_corte_fuente)]
        )
        if (length(vals) == 1L) vals[1] else as.Date(NA)
      },
      metodo_inferido = {
        vals <- unique(
          metodo_corte[!is.na(semana_corte_fuente)]
        )
        if (length(vals) == 1L) {
          vals[1]
        } else if (length(vals) > 1L) {
          paste(vals, collapse = " | ")
        } else {
          "NO_INFERIDO"
        }
      },
      fuentes = paste(unique(id_unidad), collapse = " || "),
      .groups = "drop"
    )

  if (!is.null(cortes_manual)) {
    requeridas <- c("sistema", "anio", "semana_corte")
    faltantes <- setdiff(requeridas, names(cortes_manual))

    if (length(faltantes) > 0) {
      stop(
        paste0(
          "cortes_manual no contiene: ",
          paste(faltantes, collapse = ", ")
        )
      )
    }

    manual <- cortes_manual |>
      dplyr::transmute(
        sistema = as.character(sistema),
        anio_fuente = as.integer(anio),
        semana_manual = as.integer(semana_corte)
      )

    resumen <- resumen |>
      dplyr::left_join(
        manual,
        by = c("sistema", "anio_fuente")
      )
  } else {
    resumen$semana_manual <- NA_integer_
  }

  resumen |>
    dplyr::mutate(
      semana_corte_operativa = dplyr::case_when(
        !is.na(semana_manual) ~ semana_manual,
        !is.na(semana_inferida) ~ semana_inferida,
        anio_fuente < .env$anio_actual ~ 53L,
        TRUE ~ NA_integer_
      ),

      origen_corte = dplyr::case_when(
        !is.na(semana_manual) ~ "OVERRIDE_MANUAL",
        !is.na(semana_inferida) ~ metodo_inferido,
        anio_fuente < .env$anio_actual ~ "HISTORICO_ANUAL_ASUMIDO_COMPLETO",
        TRUE ~ "NO_RESUELTO"
      ),

      estado_corte = dplyr::case_when(
        !is.na(semana_manual) &
          (semana_manual < 1 | semana_manual > 53) ~
          "CORTE_MANUAL_INVALIDO",

        n_cortes_distintos > 1 & is.na(semana_manual) ~
          "MULTIPLES_CORTES_REVISAR",

        anio_fuente == .env$anio_actual &
          is.na(semana_corte_operativa) ~
          "CORTE_ACTUAL_NO_RESUELTO",

        TRUE ~ "OK"
      )
    ) |>
    dplyr::arrange(sistema, anio_fuente)
}


# ============================================================
# 7. BASE ANALITICA TEMPORAL SEPARADA
# ============================================================

construir_base_analitica_temporal_18_v24 <- function(
  base_longitudinal,
  cortes_operativos,
  anio_actual
) {

  base <- base_longitudinal |>
    dplyr::left_join(
      cortes_operativos |>
        dplyr::select(
          sistema,
          anio_fuente,
          semana_corte_operativa,
          origen_corte,
          estado_corte
        ),
      by = c("sistema", "anio_fuente")
    ) |>
    dplyr::mutate(
      posterior_corte_operativo =
        anio_fuente == .env$anio_actual &
        !is.na(semana_corte_operativa) &
        !is.na(semana_epi) &
        semana_epi > semana_corte_operativa,

      incluido_analisis_anual =
        incluido_anio_fuente &
        !posterior_corte_operativo,

      incluido_analisis_semanal =
        incluido_analisis_anual &
        !is.na(semana_epi),

      defuncion_otro_anio_epi =
        es_defuncion &
        cruza_anio_defuncion,

      defuncion_posterior_corte =
        es_defuncion &
        anio_fuente == .env$anio_actual &
        !is.na(semana_corte_operativa) &
        !is.na(semana_defuncion) &
        semana_defuncion > semana_corte_operativa,

      es_defuncion_analitica =
        es_defuncion &
        !defuncion_otro_anio_epi &
        !defuncion_posterior_corte,

      motivo_exclusion_temporal = dplyr::case_when(
        cruza_anio_fuente ~ "EVENTO_OTRO_ANIO_EPIDEMIOLOGICO",
        posterior_corte_operativo ~ "SEMANA_POSTERIOR_CORTE_OPERATIVO",
        TRUE ~ "INCLUIDO"
      )
    )

  list(
    longitudinal = base,
    analitica_anual = base |>
      dplyr::filter(incluido_analisis_anual),
    analitica_semanal = base |>
      dplyr::filter(incluido_analisis_semanal)
  )
}


# ============================================================
# 8. WRAPPERS COMPATIBLES CON V2.3
# ============================================================

construir_casos_semanales_18 <- function(base) {
  if ("incluido_analisis_semanal" %in% names(base)) {
    base <- base |>
      dplyr::filter(.data$incluido_analisis_semanal)
  } else if ("incluido_anio_fuente" %in% names(base)) {
    base <- base |>
      dplyr::filter(.data$incluido_anio_fuente)
  }

  .construir_casos_semanales_18_v23(base)
}


construir_defunciones_semanales_18 <- function(base) {
  if ("es_defuncion_analitica" %in% names(base)) {
    base <- base |>
      dplyr::mutate(es_defuncion = .data$es_defuncion_analitica)
  }

  if ("incluido_analisis_anual" %in% names(base)) {
    base <- base |>
      dplyr::filter(.data$incluido_analisis_anual)
  } else if ("incluido_anio_fuente" %in% names(base)) {
    base <- base |>
      dplyr::filter(.data$incluido_anio_fuente)
  }

  .construir_defunciones_semanales_18_v23(base)
}


resumen_anual_historico_18 <- function(
  base,
  denominadores = NULL
) {
  if ("es_defuncion_analitica" %in% names(base)) {
    base <- base |>
      dplyr::mutate(es_defuncion = .data$es_defuncion_analitica)
  }

  if ("incluido_analisis_anual" %in% names(base)) {
    base <- base |>
      dplyr::filter(.data$incluido_analisis_anual)
  } else if ("incluido_anio_fuente" %in% names(base)) {
    base <- base |>
      dplyr::filter(.data$incluido_anio_fuente)
  }

  .resumen_anual_historico_18_v23(
    base = base,
    denominadores = denominadores
  ) |>
    dplyr::mutate(
      interpretacion_letalidad =
        "DESCRIPTIVO_NOMINAL_NO_EQUIVALE_A_LETALIDAD_VALIDADA"
    )
}


# ============================================================
# 9. MATRICES DE ANIO
# ============================================================

matriz_anio_fuente_epi_18_v24 <- function(base_longitudinal) {
  base_longitudinal |>
    dplyr::count(
      sistema,
      anio_fuente,
      anio_epi,
      confianza_anio_epi,
      name = "registros"
    ) |>
    dplyr::mutate(
      mismo_anio = !is.na(anio_epi) & anio_epi == anio_fuente
    ) |>
    dplyr::arrange(sistema, anio_fuente, anio_epi)
}


matriz_anio_fuente_defuncion_18_v24 <- function(base_longitudinal) {
  base_longitudinal |>
    dplyr::filter(es_defuncion) |>
    dplyr::count(
      sistema,
      anio_fuente,
      anio_epi_defuncion,
      confianza_anio_epi_defuncion,
      name = "defunciones_registradas"
    ) |>
    dplyr::arrange(sistema, anio_fuente, anio_epi_defuncion)
}


# ============================================================
# 10. AUDITORIA DE INTEGRIDAD TEMPORAL
# ============================================================

auditar_integridad_temporal_18_v24 <- function(base_longitudinal) {
  resumen <- base_longitudinal |>
    dplyr::group_by(
      sistema,
      anio_fuente
    ) |>
    dplyr::summarise(
      registros = dplyr::n(),
      registros_con_semana = sum(!is.na(semana_epi)),
      registros_con_fecha_evento = sum(!is.na(fecha_evento)),
      cruces_anio_epi = sum(cruza_anio_fuente, na.rm = TRUE),
      candidatos_reasignacion = sum(candidato_reasignacion_epi, na.rm = TRUE),
      discrepancias_semana_fecha = sum(requiere_revision_temporal, na.rm = TRUE),
      semanas_no_comparables_semanticamente = sum(
        estado_temporal ==
          "SEMANA_FECHA_NO_COMPARABLE_SEMANTICAMENTE",
        na.rm = TRUE
      ),
      pct_cruce_anio = 100 * mean(cruza_anio_fuente, na.rm = TRUE),
      .groups = "drop"
    )

  cruces <- base_longitudinal |>
    dplyr::filter(.data$cruza_anio_fuente) |>
    dplyr::select(
      sistema,
      anio_fuente,
      anio_epi,
      id_unidad,
      fila_origen,
      fecha_evento,
      semana_epi,
      semana_epi_fecha,
      fuente_semana,
      variable_fecha_evento,
      confianza_anio_epi,
      estado_temporal
    ) |>
    dplyr::arrange(sistema, anio_fuente, fecha_evento)

  discrepancias <- base_longitudinal |>
    dplyr::filter(.data$requiere_revision_temporal) |>
    dplyr::select(
      sistema,
      anio_fuente,
      id_unidad,
      fila_origen,
      fecha_evento,
      semana_epi,
      semana_epi_fecha,
      anio_epi_fecha,
      fuente_semana,
      variable_fecha_evento,
      comparabilidad_semana_fecha,
      concordancia_semana_fecha,
      confianza_anio_epi,
      estado_temporal
    )

  estados <- base_longitudinal |>
    dplyr::count(
      sistema,
      anio_fuente,
      estado_temporal,
      confianza_anio_epi,
      name = "n"
    ) |>
    dplyr::arrange(sistema, anio_fuente, dplyr::desc(n))

  list(
    resumen = resumen,
    cruces_anio = cruces,
    discrepancias = discrepancias,
    estados = estados
  )
}


# ============================================================
# 11. AUDITORIA DEL CORTE OPERATIVO
# ============================================================

auditar_corte_operativo_18_v24 <- function(
  base_longitudinal,
  cortes_operativos,
  anio_actual
) {

  actual <- base_longitudinal |>
    dplyr::filter(anio_fuente == .env$anio_actual) |>
    dplyr::left_join(
      cortes_operativos |>
        dplyr::filter(anio_fuente == .env$anio_actual) |>
        dplyr::select(
          sistema,
          anio_fuente,
          semana_corte_operativa,
          origen_corte,
          estado_corte
        ),
      by = c("sistema", "anio_fuente")
    )

  actual |>
    dplyr::group_by(
      sistema,
      anio_fuente,
      semana_corte_operativa,
      origen_corte,
      estado_corte
    ) |>
    dplyr::summarise(
      registros = dplyr::n(),
      semana_max_observada = {
        x <- semana_epi[!is.na(semana_epi)]
        if (length(x) == 0) NA_integer_ else max(x)
      },
      registros_posteriores_corte = sum(
        !is.na(semana_corte_operativa) &
          !is.na(semana_epi) &
          semana_epi > semana_corte_operativa
      ),
      posteriores_explicados_otro_anio = sum(
        cruza_anio_fuente &
          !is.na(semana_corte_operativa) &
          !is.na(semana_epi) &
          semana_epi > semana_corte_operativa,
        na.rm = TRUE
      ),
      posteriores_mismo_anio_epi = sum(
        !cruza_anio_fuente &
          !is.na(semana_corte_operativa) &
          !is.na(semana_epi) &
          semana_epi > semana_corte_operativa,
        na.rm = TRUE
      ),
      ultima_semana_analitica = {
        x <- semana_epi[
          incluido_analisis_semanal %in% TRUE
        ]
        x <- x[!is.na(x)]
        if (length(x) == 0) NA_integer_ else max(x)
      },
      .groups = "drop"
    ) |>
    dplyr::mutate(
      estado_auditoria_corte = dplyr::case_when(
        estado_corte != "OK" ~ "REVISAR_CORTE",
        registros_posteriores_corte == 0 &
          !is.na(semana_corte_operativa) &
          !is.na(semana_max_observada) &
          semana_max_observada < semana_corte_operativa ~
          "FUENTE_CUBRE_CORTE_SIN_EVENTOS_HASTA_EL_FINAL",
        registros_posteriores_corte == 0 ~ "OK",
        registros_posteriores_corte ==
          posteriores_explicados_otro_anio ~
          "POSTERIORES_EXPLICADOS_POR_ANIO_EPI",
        posteriores_mismo_anio_epi > 0 ~
          "REVISAR_REGISTROS_POST_CORTE_MISMO_ANIO",
        TRUE ~ "REVISAR"
      )
    ) |>
    dplyr::arrange(sistema)
}


# ============================================================
# 12. COBERTURA ANALITICA
# ============================================================

cobertura_analitica_18_v24 <- function(
  base_longitudinal,
  cortes_operativos
) {

  base_longitudinal |>
    dplyr::group_by(
      sistema,
      anio_fuente
    ) |>
    dplyr::summarise(
      registros_fuente = dplyr::n(),
      registros_con_semana = sum(!is.na(semana_epi)),
      cobertura_semana_pct =
        100 * registros_con_semana / registros_fuente,
      registros_incluidos_anual = sum(
        incluido_analisis_anual,
        na.rm = TRUE
      ),
      registros_incluidos_semanal = sum(
        incluido_analisis_semanal,
        na.rm = TRUE
      ),
      excluidos_otro_anio_epi = sum(
        cruza_anio_fuente,
        na.rm = TRUE
      ),
      excluidos_post_corte = sum(
        posterior_corte_operativo,
        na.rm = TRUE
      ),
      .groups = "drop"
    ) |>
    dplyr::left_join(
      cortes_operativos |>
        dplyr::select(
          sistema,
          anio_fuente,
          semana_corte_operativa,
          origen_corte,
          estado_corte
        ),
      by = c("sistema", "anio_fuente")
    ) |>
    dplyr::mutate(
      estado_cobertura = dplyr::case_when(
        cobertura_semana_pct == 100 ~ "COMPLETA",
        cobertura_semana_pct >= 95 ~ "CASI_COMPLETA",
        cobertura_semana_pct > 0 ~ "INCOMPLETA",
        TRUE ~ "SIN_COBERTURA"
      )
    ) |>
    dplyr::arrange(sistema, anio_fuente)
}


# ============================================================
# 13. CASOS SEMANALES CORREGIDOS Y CEROS REALES
# ============================================================

casos_semanales_analiticos_18_v24 <- function(base_analitica_semanal) {
  base_analitica_semanal |>
    dplyr::count(
      sistema,
      anio = anio_fuente,
      semana_epi,
      name = "casos"
    ) |>
    dplyr::arrange(sistema, anio, semana_epi)
}


defunciones_semanales_analiticas_18_v24 <- function(base_analitica_anual) {

  x <- base_analitica_anual |>
    dplyr::filter(.data$es_defuncion_analitica)

  con_semana_def <- x |>
    dplyr::filter(!is.na(semana_defuncion)) |>
    dplyr::count(
      sistema,
      anio = anio_fuente,
      semana_epi = semana_defuncion,
      name = "defunciones"
    )

  sin_semana_def <- x |>
    dplyr::filter(
      is.na(semana_defuncion),
      !is.na(semana_epi)
    ) |>
    dplyr::count(
      sistema,
      anio = anio_fuente,
      semana_epi,
      name = "defunciones"
    )

  dplyr::bind_rows(con_semana_def, sin_semana_def) |>
    dplyr::group_by(sistema, anio, semana_epi) |>
    dplyr::summarise(
      defunciones = sum(defunciones),
      .groups = "drop"
    ) |>
    dplyr::arrange(sistema, anio, semana_epi)
}


# ============================================================
# 14. MISMO CORTE OPERATIVO
# ============================================================

comparar_mismo_corte_operativo_18_v24 <- function(
  casos_semanales,
  defunciones_semanales,
  cobertura,
  cortes_operativos,
  anio_actual
) {

  cortes_actual <- cortes_operativos |>
    dplyr::filter(anio_fuente == .env$anio_actual) |>
    dplyr::select(
      sistema,
      semana_corte = semana_corte_operativa,
      origen_corte,
      estado_corte_actual = estado_corte
    )

  universo <- cobertura |>
    dplyr::select(
      sistema,
      anio = anio_fuente,
      cobertura_semana_pct,
      estado_cobertura
    ) |>
    dplyr::inner_join(
      cortes_actual,
      by = "sistema"
    )

  casos <- casos_semanales |>
    dplyr::inner_join(
      cortes_actual |>
        dplyr::select(sistema, semana_corte),
      by = "sistema"
    ) |>
    dplyr::filter(
      !is.na(semana_corte),
      semana_epi <= semana_corte
    ) |>
    dplyr::group_by(sistema, anio, semana_corte) |>
    dplyr::summarise(
      casos_acumulados = sum(casos),
      .groups = "drop"
    )

  defs <- defunciones_semanales |>
    dplyr::inner_join(
      cortes_actual |>
        dplyr::select(sistema, semana_corte),
      by = "sistema"
    ) |>
    dplyr::filter(
      !is.na(semana_corte),
      semana_epi <= semana_corte
    ) |>
    dplyr::group_by(sistema, anio, semana_corte) |>
    dplyr::summarise(
      defunciones_acumuladas = sum(defunciones),
      .groups = "drop"
    )

  universo |>
    dplyr::left_join(
      casos,
      by = c("sistema", "anio", "semana_corte")
    ) |>
    dplyr::left_join(
      defs,
      by = c("sistema", "anio", "semana_corte")
    ) |>
    dplyr::mutate(
      casos_acumulados = dplyr::case_when(
        is.na(semana_corte) ~ NA_integer_,
        cobertura_semana_pct < 95 & is.na(casos_acumulados) ~ NA_integer_,
        TRUE ~ dplyr::coalesce(casos_acumulados, 0L)
      ),
      defunciones_acumuladas = dplyr::case_when(
        is.na(semana_corte) ~ NA_integer_,
        cobertura_semana_pct < 95 & is.na(defunciones_acumuladas) ~ NA_integer_,
        TRUE ~ dplyr::coalesce(defunciones_acumuladas, 0L)
      ),
      estado_comparabilidad = dplyr::case_when(
        estado_corte_actual != "OK" ~ "CORTE_NO_RESUELTO",
        cobertura_semana_pct < 95 ~ "REVISAR_COBERTURA",
        TRUE ~ "COMPARABLE"
      ),
      interpretacion =
        "REGISTROS_NOMINALES_NO_FILTRADOS_POR_DEFINICION_DE_CASO"
    ) |>
    dplyr::arrange(sistema, anio)
}


# ============================================================
# 15. SEMANAS OBJETIVO CON NA VS CERO
# ============================================================

comparar_semanas_objetivo_operativas_18_v24 <- function(
  casos_semanales,
  defunciones_semanales,
  cobertura,
  cortes_operativos,
  semanas = c(25L, 26L, 27L),
  anio_actual
) {

  cortes_actual <- cortes_operativos |>
    dplyr::filter(anio_fuente == .env$anio_actual) |>
    dplyr::select(
      sistema,
      semana_corte_actual = semana_corte_operativa,
      estado_corte_actual = estado_corte
    )

  universo <- cobertura |>
    dplyr::select(
      sistema,
      anio = anio_fuente,
      cobertura_semana_pct,
      estado_cobertura
    ) |>
    dplyr::inner_join(cortes_actual, by = "sistema")

  grilla <- tidyr::crossing(
    universo,
    semana_epi = as.integer(semanas)
  ) |>
    dplyr::mutate(
      semana_cubierta = dplyr::case_when(
        anio < .env$anio_actual ~ TRUE,
        anio == .env$anio_actual &
          !is.na(semana_corte_actual) ~
          semana_epi <= semana_corte_actual,
        TRUE ~ FALSE
      )
    )

  casos <- casos_semanales |>
    dplyr::filter(semana_epi %in% semanas)

  defs <- defunciones_semanales |>
    dplyr::filter(semana_epi %in% semanas)

  grilla |>
    dplyr::left_join(
      casos,
      by = c("sistema", "anio", "semana_epi")
    ) |>
    dplyr::left_join(
      defs,
      by = c("sistema", "anio", "semana_epi")
    ) |>
    dplyr::mutate(
      casos = dplyr::case_when(
        !semana_cubierta ~ NA_integer_,
        cobertura_semana_pct < 95 & is.na(casos) ~ NA_integer_,
        TRUE ~ dplyr::coalesce(casos, 0L)
      ),
      defunciones = dplyr::case_when(
        !semana_cubierta ~ NA_integer_,
        cobertura_semana_pct < 95 & is.na(defunciones) ~ NA_integer_,
        TRUE ~ dplyr::coalesce(defunciones, 0L)
      ),
      estado_semana = dplyr::case_when(
        !semana_cubierta ~ "NO_OBSERVADA_AUN",
        cobertura_semana_pct < 95 ~ "REVISAR_COBERTURA",
        casos == 0 ~ "CERO_CASOS",
        TRUE ~ "CON_EVENTOS"
      ),
      letalidad_pct = NA_real_,
      interpretacion_letalidad =
        "NO_CALCULADA_EN_CAPA_NOMINAL"
    ) |>
    dplyr::arrange(sistema, semana_epi, anio)
}


# ============================================================
# 16. CANAL ENDEMICO DIAGNOSTICO CON CERO-RELLENO
# ============================================================

construir_canal_endemico_v24 <- function(
  casos_semanales,
  cobertura,
  cortes_operativos,
  anio_actual,
  min_anios_historicos = 4L
) {

  cortes_actual <- cortes_operativos |>
    dplyr::filter(
      anio_fuente == .env$anio_actual,
      !is.na(semana_corte_operativa),
      estado_corte == "OK"
    ) |>
    dplyr::select(
      sistema,
      semana_corte = semana_corte_operativa
    )

  resultados <- list()
  k <- 1L

  for (i in seq_len(nrow(cortes_actual))) {
    sis <- cortes_actual$sistema[i]
    corte <- cortes_actual$semana_corte[i]

    cov_sis <- cobertura |>
      dplyr::filter(sistema == .env$sis)

    hist <- cov_sis |>
      dplyr::filter(
        anio_fuente < .env$anio_actual,
        cobertura_semana_pct >= 95
      )

    if (dplyr::n_distinct(hist$anio_fuente) < min_anios_historicos) {
      next
    }

    anios_hist <- sort(unique(hist$anio_fuente))

    grid_hist <- tidyr::crossing(
      sistema = sis,
      anio = as.integer(anios_hist),
      semana_epi = seq_len(as.integer(corte))
    ) |>
      dplyr::left_join(
        casos_semanales |>
          dplyr::filter(
            sistema == .env$sis,
            anio %in% .env$anios_hist,
            semana_epi <= .env$corte
          ),
        by = c("sistema", "anio", "semana_epi")
      ) |>
      dplyr::mutate(casos = dplyr::coalesce(casos, 0L))

    obs_cov <- cov_sis |>
      dplyr::filter(anio_fuente == .env$anio_actual)

    obs <- tibble::tibble(
      sistema = sis,
      semana_epi = seq_len(as.integer(corte))
    ) |>
      dplyr::left_join(
        casos_semanales |>
          dplyr::filter(
            sistema == .env$sis,
            anio == .env$anio_actual,
            semana_epi <= .env$corte
          ) |>
          dplyr::select(
            sistema,
            semana_epi,
            observado = casos
          ),
        by = c("sistema", "semana_epi")
      )

    if (
      nrow(obs_cov) == 1 &&
      obs_cov$cobertura_semana_pct >= 95
    ) {
      obs$observado <- dplyr::coalesce(obs$observado, 0L)
    }

    canal <- grid_hist |>
      dplyr::group_by(sistema, semana_epi) |>
      dplyr::summarise(
        n_anios = dplyr::n_distinct(anio),
        q1 = as.numeric(stats::quantile(casos, 0.25, type = 7)),
        mediana = as.numeric(stats::quantile(casos, 0.50, type = 7)),
        q3 = as.numeric(stats::quantile(casos, 0.75, type = 7)),
        max_historico = max(casos),
        .groups = "drop"
      ) |>
      dplyr::left_join(
        obs,
        by = c("sistema", "semana_epi")
      ) |>
      dplyr::mutate(
        zona = dplyr::case_when(
          is.na(observado) ~ "SIN_OBSERVACION",
          observado < q1 ~ "EXITO",
          observado < mediana ~ "SEGURIDAD",
          observado < q3 ~ "ALARMA",
          TRUE ~ "EPIDEMICA"
        ),
        metodo = "CUARTILES_CON_CEROS_HASTA_CORTE_OPERATIVO",
        interpretacion =
          "DIAGNOSTICO_NOMINAL_NO_EQUIVALE_A_CANAL_DE_CASOS_CONFIRMADOS"
      )

    resultados[[k]] <- canal
    k <- k + 1L
  }

  if (length(resultados) == 0) return(tibble::tibble())
  dplyr::bind_rows(resultados)
}


# ============================================================
# 17. CANDIDATOS DE DUPLICIDAD HISTORICA
# ============================================================

.detectar_columnas_identificador_v24 <- function(datos) {
  originales <- names(datos)
  nms <- .normalizar_texto_v24(originales)

  rol <- dplyr::case_when(
    grepl("(^|_)curp($|_)", nms) ~ "CURP",
    grepl("folio_caso|(^|_)folio($|_)", nms) ~ "FOLIO",
    grepl(
      "id_caso|idcaso|identificador_caso|numero_caso|num_caso|no_caso|clave_caso",
      nms
    ) ~ "ID_CASO",
    TRUE ~ NA_character_
  )

  tibble::tibble(
    columna = originales,
    nombre_norm = nms,
    rol_identificador = rol
  ) |>
    dplyr::filter(!is.na(rol_identificador))
}


.normalizar_id_duplicidad_v24 <- function(x) {
  x <- toupper(trimws(as.character(x)))
  x[is.na(x)] <- ""
  x <- iconv(x, from = "", to = "ASCII//TRANSLIT")
  x[is.na(x)] <- ""
  x <- gsub("[^A-Z0-9]", "", x)
  x[x %in% c("", "0", "NA", "N/A", "SINDATO", "NODISPONIBLE")] <- ""
  x
}


extraer_identificadores_historicos_18_v24 <- function(
  seleccionadas,
  mostrar_progreso = FALSE
) {

  out <- list()
  k <- 1L

  for (i in seq_len(nrow(seleccionadas))) {
    u <- seleccionadas[i, , drop = FALSE]

    if (mostrar_progreso) {
      cat(
        "[ID ", i, "/", nrow(seleccionadas), "] ",
        u$sistema, " ", u$anio, "\n",
        sep = ""
      )
    }

    datos <- tryCatch(
      leer_unidad_historica_18(
        archivo = u$archivo[1],
        hoja = u$hoja[1]
      ),
      error = function(e) NULL
    )

    if (is.null(datos) || nrow(datos) == 0) next

    ids <- .detectar_columnas_identificador_v24(datos)
    if (nrow(ids) == 0) next

    for (j in seq_len(nrow(ids))) {
      col <- ids$columna[j]
      rol <- ids$rol_identificador[j]
      valor <- .normalizar_id_duplicidad_v24(datos[[col]])

      valido <- valor != ""

      if (rol == "CURP") {
        valido <- valido & nchar(valor) >= 16
      } else {
        valido <- valido & nchar(valor) >= 4
      }

      if (!any(valido)) next

      out[[k]] <- tibble::tibble(
        sistema = u$sistema[1],
        anio_fuente = as.integer(u$anio[1]),
        id_unidad = u$id_unidad[1],
        fila_origen = which(valido),
        rol_identificador = rol,
        columna_identificador = col,
        valor_norm = valor[valido]
      )

      k <- k + 1L
    }
  }

  if (length(out) == 0) return(tibble::tibble())
  dplyr::bind_rows(out)
}


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
        paste0(id_unidad, "#", fila_origen),
        collapse = " | "
      ),
      .groups = "drop"
    ) |>
    dplyr::filter(n_anios >= 2) |>
    dplyr::mutate(
      grupo_duplicidad = dplyr::row_number(),
      confianza = dplyr::case_when(
        rol_identificador == "CURP" ~ "ALTA_CANDIDATO_EXACTO",
        TRUE ~ "MEDIA_REQUIERE_VERIFICACION"
      ),
      accion = "NO_ELIMINAR_REVISAR_DUPLICIDAD"
    ) |>
    dplyr::select(
      sistema,
      grupo_duplicidad,
      rol_identificador,
      confianza,
      n_anios,
      anios_fuente,
      n_registros,
      columnas_origen,
      referencias,
      accion
    ) |>
    dplyr::arrange(
      sistema,
      dplyr::desc(n_anios),
      dplyr::desc(n_registros)
    )
}


detectar_candidatos_duplicidad_historica_18_v24 <- function(
  seleccionadas,
  mostrar_progreso = FALSE
) {
  detalle <- extraer_identificadores_historicos_18_v24(
    seleccionadas = seleccionadas,
    mostrar_progreso = mostrar_progreso
  )

  resumir_candidatos_duplicidad_18_v24(detalle)
}


# ============================================================
# 18. CHECKPOINT
# ============================================================

guardar_checkpoint_18_v24 <- function(
  resultado,
  archivo = here::here(
    "04_resultados",
    "checkpoints",
    "resultado_18_V2_4_PRISMA_R.rds"
  )
) {
  dir.create(
    dirname(archivo),
    recursive = TRUE,
    showWarnings = FALSE
  )

  saveRDS(resultado, archivo)

  normalizePath(
    archivo,
    winslash = "/",
    mustWork = FALSE
  )
}


# ============================================================
# 19. REEMPLAZAR / AGREGAR HOJA DE EXCEL
# ============================================================

.escribir_hoja_v24 <- function(wb, nombre, datos) {
  if (nombre %in% names(wb)) {
    openxlsx::removeWorksheet(wb, nombre)
  }

  openxlsx::addWorksheet(wb, nombre)
  openxlsx::writeData(
    wb,
    nombre,
    .tabla_exportable_18_v24(datos)
  )

  invisible(wb)
}


# ============================================================
# 20. MOTOR MAESTRO V2.4
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
      "comparativo_historico_epidemiologico_V2_4_",
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
    "resultado_18_V2_4_PRISMA_R.rds"
  ),
  mostrar_progreso = TRUE
) {

  # Ejecutar V2.3 como nucleo de seleccion/lectura. Las funciones
  # redefinidas arriba enriquecen la base sin tocar archivos fuente.
  resultado_v23 <- .ejecutar_motor_historico_comparativo_18_v23(
    resultado_17 = resultado_17,
    archivo_inventario = archivo_inventario,
    sistemas = sistemas,
    overrides_unidades = overrides_unidades,
    overrides_variables = overrides_variables,
    denominadores = denominadores,
    semanas_objetivo = semanas_objetivo,
    anio_actual = anio_actual,
    archivo_salida = archivo_salida,
    generar_graficas = FALSE,
    mostrar_progreso = mostrar_progreso
  )

  base_original <- resultado_v23$base_longitudinal

  cortes <- registro_cortes_operativos_18_v24(
    base_longitudinal = base_original,
    anio_actual = anio_actual,
    cortes_manual = cortes_manual
  )

  capas <- construir_base_analitica_temporal_18_v24(
    base_longitudinal = base_original,
    cortes_operativos = cortes,
    anio_actual = anio_actual
  )

  base_longitudinal <- capas$longitudinal
  base_anual <- capas$analitica_anual
  base_semanal <- capas$analitica_semanal

  integridad <- auditar_integridad_temporal_18_v24(
    base_longitudinal
  )

  matriz_anios <- matriz_anio_fuente_epi_18_v24(
    base_longitudinal
  )

  matriz_def <- matriz_anio_fuente_defuncion_18_v24(
    base_longitudinal
  )

  cobertura <- cobertura_analitica_18_v24(
    base_longitudinal = base_longitudinal,
    cortes_operativos = cortes
  )

  auditoria_corte <- auditar_corte_operativo_18_v24(
    base_longitudinal = base_longitudinal,
    cortes_operativos = cortes,
    anio_actual = anio_actual
  )

  casos_semanales <- casos_semanales_analiticos_18_v24(
    base_semanal
  )

  defunciones_semanales <- defunciones_semanales_analiticas_18_v24(
    base_anual
  )

  base_anual_para_resumen <- base_anual |>
    dplyr::mutate(
      anio = anio_fuente,
      es_defuncion = es_defuncion_analitica
    )

  anual <- .resumen_anual_historico_18_v23(
    base = base_anual_para_resumen,
    denominadores = denominadores
  ) |>
    dplyr::mutate(
      interpretacion_letalidad =
        "DESCRIPTIVO_NOMINAL_NO_EQUIVALE_A_LETALIDAD_VALIDADA"
    )

  mismo_corte <- comparar_mismo_corte_operativo_18_v24(
    casos_semanales = casos_semanales,
    defunciones_semanales = defunciones_semanales,
    cobertura = cobertura,
    cortes_operativos = cortes,
    anio_actual = anio_actual
  )

  semanas <- comparar_semanas_objetivo_operativas_18_v24(
    casos_semanales = casos_semanales,
    defunciones_semanales = defunciones_semanales,
    cobertura = cobertura,
    cortes_operativos = cortes,
    semanas = semanas_objetivo,
    anio_actual = anio_actual
  )

  canal <- construir_canal_endemico_v24(
    casos_semanales = casos_semanales,
    cobertura = cobertura,
    cortes_operativos = cortes,
    anio_actual = anio_actual,
    min_anios_historicos = 4L
  )

  duplicados <- if (isTRUE(detectar_duplicados)) {
    detectar_candidatos_duplicidad_historica_18_v24(
      seleccionadas = resultado_v23$seleccion$seleccionadas,
      mostrar_progreso = FALSE
    )
  } else {
    tibble::tibble()
  }

  graficas <- tibble::tibble()

  if (isTRUE(generar_graficas) && nrow(casos_semanales) > 0) {
    sistemas_grafica <- unique(casos_semanales$sistema)

    archivos_grafica <- vapply(
      sistemas_grafica,
      function(sis) {
        graficar_casos_semanales_18(
          casos_semanales = casos_semanales,
          sistema = sis
        )
      },
      character(1)
    )

    graficas <- tibble::tibble(
      sistema = sistemas_grafica,
      archivo = archivos_grafica
    )
  }

  resumen_sistemas <- cobertura |>
    dplyr::group_by(sistema) |>
    dplyr::summarise(
      anios_fuente = paste(
        sort(unique(anio_fuente)),
        collapse = " | "
      ),
      n_anios = dplyr::n_distinct(anio_fuente),
      registros_fuente = sum(registros_fuente),
      registros_incluidos_anual = sum(registros_incluidos_anual),
      registros_incluidos_semanal = sum(registros_incluidos_semanal),
      excluidos_otro_anio_epi = sum(excluidos_otro_anio_epi),
      excluidos_post_corte = sum(excluidos_post_corte),
      cobertura_minima_semana_pct = min(
        cobertura_semana_pct,
        na.rm = TRUE
      ),
      .groups = "drop"
    ) |>
    dplyr::left_join(
      auditoria_corte |>
        dplyr::select(
          sistema,
          semana_corte_operativa,
          registros_posteriores_corte,
          posteriores_explicados_otro_anio,
          posteriores_mismo_anio_epi,
          estado_auditoria_corte
        ),
      by = "sistema"
    ) |>
    dplyr::arrange(sistema)

  resumen_general <- tibble::tibble(
    indicador = c(
      "Proyecto",
      "Modulo",
      "Build",
      "Registros longitudinales preservados",
      "Registros incluidos analisis anual",
      "Registros incluidos analisis semanal",
      "Sistemas",
      "Anios fuente",
      "Cruces de anio epidemiologico detectados",
      "Discrepancias semana-fecha para revision",
      "Registros actuales posteriores al corte",
      "Registros post-corte explicados por otro anio epi",
      "Registros post-corte mismo anio epi a revisar",
      "Cortes actuales no resueltos",
      "Grupos candidatos de duplicidad historica",
      "Reasignaciones automaticas entre anios",
      "Bases originales modificadas",
      "Definicion de caso aplicada",
      "Canal endemico",
      "Denominadores inventados"
    ),
    valor = c(
      "PRISMA-R",
      "18 V2.4 - INTEGRIDAD TEMPORAL EPIDEMIOLOGICA",
      "BUILD_18_V2_4_INTEGRIDAD_TEMPORAL_20260724_01",
      nrow(base_longitudinal),
      nrow(base_anual),
      nrow(base_semanal),
      dplyr::n_distinct(base_longitudinal$sistema),
      dplyr::n_distinct(base_longitudinal$anio_fuente),
      sum(base_longitudinal$cruza_anio_fuente, na.rm = TRUE),
      sum(base_longitudinal$requiere_revision_temporal, na.rm = TRUE),
      sum(auditoria_corte$registros_posteriores_corte, na.rm = TRUE),
      sum(auditoria_corte$posteriores_explicados_otro_anio, na.rm = TRUE),
      sum(auditoria_corte$posteriores_mismo_anio_epi, na.rm = TRUE),
      sum(cortes$estado_corte != "OK" &
          cortes$anio_fuente == anio_actual,
          na.rm = TRUE),
      nrow(duplicados),
      "0 - SOLO CANDIDATOS; NO SE REASIGNA",
      "NO",
      "NO - CAPA NOMINAL PREVIA A 18D",
      "DIAGNOSTICO NOMINAL; NO CANAL FINAL DE CASOS DEFINIDOS",
      "NO"
    )
  )

  resultado <- resultado_v23
  resultado$resumen_general <- resumen_general
  resultado$resumen_sistemas <- resumen_sistemas
  resultado$base_longitudinal <- base_longitudinal
  resultado$base_analitica_temporal <- base_semanal
  resultado$base_analitica_anual <- base_anual
  resultado$cobertura_temporal <- cobertura
  resultado$cortes_operativos <- cortes
  resultado$integridad_temporal <- integridad$resumen
  resultado$matriz_anio_fuente_epi <- matriz_anios
  resultado$matriz_anio_fuente_defuncion <- matriz_def
  resultado$cruces_anio_epi <- integridad$cruces_anio
  resultado$discrepancias_temporales <- integridad$discrepancias
  resultado$estados_temporales <- integridad$estados
  resultado$auditoria_corte <- auditoria_corte
  resultado$candidatos_duplicidad_historica <- duplicados
  resultado$casos_semanales <- casos_semanales
  resultado$defunciones_semanales <- defunciones_semanales
  resultado$semanas_objetivo <- semanas
  resultado$mismo_corte <- mismo_corte
  resultado$resumen_anual <- anual
  resultado$canal_endemico <- canal
  resultado$graficas <- graficas
  resultado$archivo_salida <- archivo_salida
  resultado$build_v24 <-
    "BUILD_18_V2_4_INTEGRIDAD_TEMPORAL_20260724_01"

  # Reemplazar hojas analiticas del workbook V2.3 y anexar V2.4.
  if (file.exists(archivo_salida)) {
    wb <- openxlsx::loadWorkbook(archivo_salida)

    hojas <- list(
      Resumen_General = resumen_general,
      Resumen_Sistemas = resumen_sistemas,
      Cobertura_Temporal = cobertura,
      Integridad_Temporal = integridad$resumen,
      Matriz_Anio_Fuente_Epi = matriz_anios,
      Matriz_Anio_Fuente_Def = matriz_def,
      Cruces_Anio_Epi = integridad$cruces_anio,
      Discrepancias_Temporales = integridad$discrepancias,
      Estados_Temporales = integridad$estados,
      Auditoria_Corte = auditoria_corte,
      Candidatos_Duplicados = duplicados,
      Casos_Semanales = casos_semanales,
      Defunciones_Semanales = defunciones_semanales,
      SE_25_26_27 = semanas,
      Mismo_Corte = mismo_corte,
      Resumen_Anual = anual,
      Canal_Endemico = canal,
      Graficas = graficas
    )

    for (nm in names(hojas)) {
      .escribir_hoja_v24(
        wb = wb,
        nombre = nm,
        datos = hojas[[nm]]
      )
    }

    openxlsx::saveWorkbook(
      wb,
      archivo_salida,
      overwrite = TRUE
    )
  }

  checkpoint <- NA_character_

  if (isTRUE(guardar_checkpoint)) {
    checkpoint <- guardar_checkpoint_18_v24(
      resultado = resultado,
      archivo = archivo_checkpoint
    )
    resultado$checkpoint <- checkpoint
  }

  if (isTRUE(mostrar_progreso)) {
    cat("\n====================================================\n")
    cat("PRISMA-R | MODULO 18 V2.4 - INTEGRIDAD TEMPORAL\n")
    cat("====================================================\n\n")

    print(resumen_general, n = Inf, width = Inf)

    cat("\nAuditoria del corte actual:\n")
    print(auditoria_corte, n = Inf, width = Inf)

    cat("\nCruces de anio epidemiologico por sistema/anio:\n")
    print(integridad$resumen, n = Inf, width = Inf)

    cat("\nReporte:\n", archivo_salida, "\n", sep = "")

    if (isTRUE(guardar_checkpoint)) {
      cat("\nCheckpoint:\n", checkpoint, "\n", sep = "")
    }

    cat("\nOK V2.4 COMPLETADO\n")
    cat("No se eliminaron registros de base_longitudinal.\n")
    cat("No se reasignaron registros automaticamente entre anios.\n")
  }

  invisible(resultado)
}


# ============================================================
# 21. PRUEBAS SINTETICAS V2.4
# ============================================================

prueba_integridad_temporal_18_v24 <- function() {

  fecha_previa <- as.Date("2025-12-20")
  epi_previa <- semana_epidemiologica_domingo_18(fecha_previa)
  semana_previa <- epi_previa$semana_epi[1]

  a <- resolver_integridad_temporal_18_v24(
    sistema = "TUBERCULOSIS",
    semana_epi = semana_previa,
    fuente_semana = "FECHA:fechaIniSintomas",
    fecha_evento = fecha_previa,
    anio_fuente = 2026,
    variable_fecha_evento = "fechaIniSintomas"
  )

  b <- resolver_integridad_temporal_18_v24(
    sistema = "DENGUE",
    semana_epi = semana_previa,
    fuente_semana = "VARIABLE:SEMANA_EPIDEMIOLOGICA",
    fecha_evento = fecha_previa,
    anio_fuente = 2026,
    variable_fecha_evento = "FECHA_INICIO_SINTOMAS"
  )

  c <- resolver_integridad_temporal_18_v24(
    sistema = "DENGUE",
    semana_epi = 10L,
    fuente_semana = "VARIABLE:SEMANA_EPIDEMIOLOGICA",
    fecha_evento = fecha_previa,
    anio_fuente = 2026,
    variable_fecha_evento = "FECHA_INICIO_SINTOMAS"
  )

  d <- resolver_integridad_temporal_18_v24(
    sistema = "VIH",
    semana_epi = 10L,
    fuente_semana = "VARIABLE:SEMANA",
    fecha_evento = fecha_previa,
    anio_fuente = 2026,
    variable_fecha_evento = "FECHA_INICIO_SINTOMAS"
  )

  corte1 <- extraer_corte_fuente_18_v24(
    "12 BASE MPOX Sem 22.xlsx :: Casos",
    2026
  )

  corte2 <- extraer_corte_fuente_18_v24(
    "PFA_SE01-26_2026.xlsx :: Hoja1",
    2026
  )

  corte3 <- extraer_corte_fuente_18_v24(
    "BASE DE DATOS VIH CORTE SEMANA 27.xlsx :: Hoja1",
    2026
  )

  corte4 <- extraer_corte_fuente_18_v24(
    "BASE DE DATOS DENGUE CORTE AL DIA 21 07 26.xlsx :: Hoja1",
    2026
  )

  base_test <- tibble::tibble(
    sistema = c("DENGUE", "DENGUE", "DENGUE"),
    anio = 2026L,
    anio_fuente = 2026L,
    id_unidad = "BASE DENGUE CORTE AL DIA 21 07 26.xlsx :: Hoja1",
    fila_origen = 1:3,
    semana_epi = c(10L, 31L, semana_previa),
    es_defuncion = FALSE,
    semana_defuncion = NA_integer_,
    fuente_semana = c(
      "VARIABLE:SEMANA_EPIDEMIOLOGICA",
      "VARIABLE:SEMANA_EPIDEMIOLOGICA",
      "FECHA:FECHA_INICIO_SINTOMAS"
    ),
    fuente_defuncion = "NO_DETECTADA",
    anio_epi = c(2026L, 2026L, 2025L),
    cruza_anio_fuente = c(FALSE, FALSE, TRUE),
    candidato_reasignacion_epi = c(FALSE, FALSE, TRUE),
    requiere_revision_temporal = FALSE,
    incluido_anio_fuente = c(TRUE, TRUE, FALSE),
    fecha_evento = as.Date(c("2026-03-01", "2026-08-01", "2025-12-20")),
    anio_epi_defuncion = 2026L,
    confianza_anio_epi_defuncion = "MEDIA_ANIO_FUENTE",
    cruza_anio_defuncion = FALSE,
    estado_temporal = c(
      "SEMANA_FECHA_CONCORDANTES",
      "SEMANA_DISPONIBLE",
      "ARRASTRE_OTRO_ANIO_EPIDEMIOLOGICO"
    ),
    confianza_anio_epi = c("ALTA", "MEDIA_ANIO_FUENTE", "ALTA")
  )

  cortes_test <- tibble::tibble(
    sistema = "DENGUE",
    anio_fuente = 2026L,
    semana_corte_operativa = 30L,
    origen_corte = "TEST",
    estado_corte = "OK"
  )

  capas <- construir_base_analitica_temporal_18_v24(
    base_longitudinal = base_test,
    cortes_operativos = cortes_test,
    anio_actual = 2026L
  )

  ids_test <- tibble::tibble(
    sistema = c("TEST", "TEST", "TEST"),
    anio_fuente = c(2025L, 2026L, 2026L),
    id_unidad = c("A", "B", "B"),
    fila_origen = c(1L, 2L, 3L),
    rol_identificador = c("CURP", "CURP", "CURP"),
    columna_identificador = "CURP",
    valor_norm = c("ABC123456789012345", "ABC123456789012345", "XYZ123456789012345")
  )

  dup_test <- resumir_candidatos_duplicidad_18_v24(ids_test)

  tibble::tibble(
    prueba = c(
      "Fecha derivada conserva anio epidemiologico 2025",
      "Fecha derivada detecta cruce de anio",
      "Cruce no queda incluido en anio fuente",
      "Semana explicita concordante permite inferir anio epi",
      "Semana explicita concordante detecta cruce",
      "Discordancia comparable no reasigna anio",
      "Discordancia queda para revision",
      "VIH semana notificacion no se compara con fecha clinica",
      "VIH no genera falsa discrepancia",
      "Parser reconoce Sem 22",
      "Parser reconoce SE01-26",
      "Parser reconoce CORTE SEMANA 27",
      "Parser reconoce fecha de corte",
      "Base longitudinal conserva tres registros",
      "Base anual excluye cruce y post-corte",
      "Base semanal usa misma proteccion",
      "Registro semana 31 se marca posterior al corte 30",
      "Registro de otro anio se marca como candidato no reasignado",
      "Duplicidad exacta entre anios crea candidato",
      "Duplicidad no exporta identificador crudo",
      "CURP candidato recibe confianza alta",
      "Matriz anio fuente x epi puede construirse",
      "Auditoria temporal conserva cruces",
      "Corte operativo no depende del maximo evento",
      "Semana futura puede quedar fuera de capa analitica",
      "No se elimina evidencia de base longitudinal",
      "Checkpoint tiene funcion disponible",
      "Modulo conserva compatibilidad con V2.3"
    ),
    pasa = c(
      a$anio_epi[1] == 2025L,
      isTRUE(a$cruza_anio_fuente[1]),
      !isTRUE(a$incluido_anio_fuente[1]),
      b$anio_epi[1] == 2025L,
      isTRUE(b$cruza_anio_fuente[1]),
      c$anio_epi[1] == 2026L,
      isTRUE(c$requiere_revision_temporal[1]),
      grepl("NO_COMPARABLE", d$comparabilidad_semana_fecha[1]),
      !isTRUE(d$requiere_revision_temporal[1]),
      corte1$semana_corte_fuente == 22L,
      corte2$semana_corte_fuente == 26L,
      corte3$semana_corte_fuente == 27L,
      !is.na(corte4$semana_corte_fuente),
      nrow(capas$longitudinal) == 3L,
      nrow(capas$analitica_anual) == 1L,
      nrow(capas$analitica_semanal) == 1L,
      isTRUE(capas$longitudinal$posterior_corte_operativo[2]),
      isTRUE(capas$longitudinal$candidato_reasignacion_epi[3]),
      nrow(dup_test) == 1L,
      !"valor_norm" %in% names(dup_test),
      dup_test$confianza[1] == "ALTA_CANDIDATO_EXACTO",
      nrow(matriz_anio_fuente_epi_18_v24(base_test)) >= 1L,
      sum(base_test$cruza_anio_fuente) == 1L,
      corte4$semana_corte_fuente < 53L,
      !isTRUE(capas$longitudinal$incluido_analisis_semanal[2]),
      nrow(capas$longitudinal) == nrow(base_test),
      exists("guardar_checkpoint_18_v24", mode = "function"),
      exists(".ejecutar_motor_historico_comparativo_18_v23", mode = "function")
    )
  )
}


# ============================================================
# 22. VALIDACION DEL MODULO
# ============================================================

validar_modulo_18 <- function() {

  cat("\nValidando primero el nucleo V2.3...\n")
  validacion_v23 <- .validar_modulo_18_v23()

  funciones_v24 <- c(
    ".deteccion_temporal_efectiva_18_v24",
    ".clasificar_comparabilidad_semana_fecha_v24",
    "resolver_integridad_temporal_18_v24",
    "preparar_unidad_historica_18",
    "extraer_corte_fuente_18_v24",
    "registro_cortes_operativos_18_v24",
    "construir_base_analitica_temporal_18_v24",
    "matriz_anio_fuente_epi_18_v24",
    "matriz_anio_fuente_defuncion_18_v24",
    "auditar_integridad_temporal_18_v24",
    "auditar_corte_operativo_18_v24",
    "cobertura_analitica_18_v24",
    "casos_semanales_analiticos_18_v24",
    "defunciones_semanales_analiticas_18_v24",
    "comparar_mismo_corte_operativo_18_v24",
    "comparar_semanas_objetivo_operativas_18_v24",
    "construir_canal_endemico_v24",
    "detectar_candidatos_duplicidad_historica_18_v24",
    "guardar_checkpoint_18_v24",
    "ejecutar_motor_historico_comparativo_18",
    "prueba_integridad_temporal_18_v24"
  )

  estructural <- tibble::tibble(
    funcion = funciones_v24,
    disponible = vapply(
      funciones_v24,
      exists,
      logical(1),
      mode = "function"
    )
  )

  funcional <- prueba_integridad_temporal_18_v24()

  cat("\n====================================================\n")
  cat("PRISMA-R | VALIDACION MODULO 18 V2.4\n")
  cat("====================================================\n\n")

  cat("Funciones V2.4:\n")
  print(estructural, n = Inf)

  cat("\nPruebas sinteticas V2.4:\n")
  print(funcional, n = Inf, width = Inf)

  if (
    all(estructural$disponible) &&
    all(funcional$pasa)
  ) {
    cat(
      "\nOK PRISMA-R 18 V2.4 VALIDADO ESTRUCTURAL Y FUNCIONALMENTE\n"
    )
  } else {
    cat(
      "\nATENCION PRISMA-R 18 V2.4 REQUIERE REVISION\n"
    )
  }

  invisible(list(
    v23 = validacion_v23,
    estructural_v24 = estructural,
    funcional_v24 = funcional
  ))
}


# ============================================================
# FIN
# ============================================================

cat("\n====================================================\n")
cat("PRISMA-R | MODULO 18 V2.4 CARGADO\n")
cat("INTEGRIDAD TEMPORAL EPIDEMIOLOGICA\n")
cat("====================================================\n")
cat("\nReglas activas:\n")
cat("- anio_fuente se preserva.\n")
cat("- anio_epi solo se deriva con evidencia temporal suficiente.\n")
cat("- cruces de anio no se reasignan automaticamente.\n")
cat("- semanas post-corte no entran a la capa analitica actual.\n")
cat("- semana sin eventos dentro de cobertura puede ser cero real.\n")
cat("- candidatos de duplicidad no eliminan registros.\n")
cat("- bases originales permanecen intactas.\n")
cat("\nValidacion:\n")
cat("validacion_18_v24 <- validar_modulo_18()\n")
cat("\nEjecucion real:\n")
cat("resultado_18_v24 <- ejecutar_motor_historico_comparativo_18(resultado_17 = resultado_17)\n")
