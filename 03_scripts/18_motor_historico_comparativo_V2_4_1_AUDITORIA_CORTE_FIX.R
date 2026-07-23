# ============================================================
# PRISMA-R
# MODULO 18 V2.4.1 - FIX AUDITORIA DE CORTE OPERATIVO
# ============================================================
#
# BUILD_18_V2_4_1_AUDITORIA_CORTE_FIX_20260724_01
#
# Corrige un fallo detectado en ejecucion real de V2.4:
# construir_base_analitica_temporal_18_v24() ya incorpora
# semana_corte_operativa, origen_corte y estado_corte en la
# base longitudinal enriquecida. La funcion original
# auditar_corte_operativo_18_v24() volvia a unir esas mismas
# columnas, generando sufijos .x/.y y haciendo que group_by()
# no encontrara los nombres originales.
#
# Este parche:
# - carga V2.4;
# - reemplaza SOLO auditar_corte_operativo_18_v24();
# - reutiliza columnas de corte si ya existen;
# - completa columnas faltantes sin duplicarlas;
# - agrega una prueba que reproduce la ruta real del motor;
# - NO cambia definiciones epidemiologicas ni bases originales.
# ============================================================

archivo_v24 <- here::here(
  "03_scripts",
  "18_motor_historico_comparativo_V2_4_INTEGRIDAD_TEMPORAL.R"
)

if (!file.exists(archivo_v24)) {
  stop(
    paste0(
      "No se encontro el modulo 18 V2.4 requerido: ",
      archivo_v24
    )
  )
}

source(archivo_v24)


# ============================================================
# 1. AUDITORIA DE CORTE CORREGIDA
# ============================================================

auditar_corte_operativo_18_v24 <- function(
  base_longitudinal,
  cortes_operativos,
  anio_actual
) {

  requeridas_base <- c(
    "sistema",
    "anio_fuente",
    "semana_epi",
    "cruza_anio_fuente",
    "incluido_analisis_semanal"
  )

  faltantes_base <- setdiff(
    requeridas_base,
    names(base_longitudinal)
  )

  if (length(faltantes_base) > 0) {
    stop(
      paste0(
        "auditar_corte_operativo_18_v24: faltan columnas en base_longitudinal: ",
        paste(faltantes_base, collapse = ", ")
      )
    )
  }

  requeridas_corte <- c(
    "sistema",
    "anio_fuente",
    "semana_corte_operativa",
    "origen_corte",
    "estado_corte"
  )

  faltantes_corte <- setdiff(
    requeridas_corte,
    names(cortes_operativos)
  )

  if (length(faltantes_corte) > 0) {
    stop(
      paste0(
        "auditar_corte_operativo_18_v24: faltan columnas en cortes_operativos: ",
        paste(faltantes_corte, collapse = ", ")
      )
    )
  }

  actual <- base_longitudinal |>
    dplyr::filter(
      .data$anio_fuente == .env$anio_actual
    )

  columnas_corte <- c(
    "semana_corte_operativa",
    "origen_corte",
    "estado_corte"
  )

  # La ruta real del motor entrega una base longitudinal ya
  # enriquecida con estas columnas. Si estan completas, se usan
  # directamente. Si falta alguna, se eliminan las parciales y
  # se reconstruyen desde cortes_operativos para evitar .x/.y.
  if (!all(columnas_corte %in% names(actual))) {

    actual <- actual |>
      dplyr::select(
        -dplyr::any_of(columnas_corte)
      ) |>
      dplyr::left_join(
        cortes_operativos |>
          dplyr::filter(
            .data$anio_fuente == .env$anio_actual
          ) |>
          dplyr::select(
            sistema,
            anio_fuente,
            semana_corte_operativa,
            origen_corte,
            estado_corte
          ),
        by = c(
          "sistema",
          "anio_fuente"
        )
      )
  }

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
        if (length(x) == 0) {
          NA_integer_
        } else {
          max(x)
        }
      },

      registros_posteriores_corte = sum(
        !is.na(semana_corte_operativa) &
          !is.na(semana_epi) &
          semana_epi > semana_corte_operativa,
        na.rm = TRUE
      ),

      posteriores_explicados_otro_anio = sum(
        cruza_anio_fuente %in% TRUE &
          !is.na(semana_corte_operativa) &
          !is.na(semana_epi) &
          semana_epi > semana_corte_operativa,
        na.rm = TRUE
      ),

      posteriores_mismo_anio_epi = sum(
        cruza_anio_fuente %in% FALSE &
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
        if (length(x) == 0) {
          NA_integer_
        } else {
          max(x)
        }
      },

      .groups = "drop"
    ) |>
    dplyr::mutate(
      estado_auditoria_corte = dplyr::case_when(
        is.na(semana_corte_operativa) ~
          "CORTE_NO_RESUELTO",

        estado_corte != "OK" ~
          "REVISAR_CORTE",

        registros_posteriores_corte == 0 &
          !is.na(semana_max_observada) &
          semana_max_observada < semana_corte_operativa ~
          "FUENTE_CUBRE_CORTE_SIN_EVENTOS_HASTA_EL_FINAL",

        registros_posteriores_corte == 0 ~
          "OK",

        registros_posteriores_corte ==
          posteriores_explicados_otro_anio ~
          "POSTERIORES_EXPLICADOS_POR_ANIO_EPI",

        posteriores_mismo_anio_epi > 0 ~
          "REVISAR_REGISTROS_POST_CORTE_MISMO_ANIO",

        TRUE ~
          "REVISAR"
      )
    ) |>
    dplyr::arrange(
      sistema
    )
}


# ============================================================
# 2. PRUEBA ESPECIFICA DE REGRESION DEL BUG REAL
# ============================================================

prueba_auditoria_corte_v241 <- function() {

  base_test <- tibble::tibble(
    sistema = rep("DENGUE", 4),
    anio_fuente = rep(2026L, 4),
    semana_epi = c(1L, 2L, 30L, 52L),
    cruza_anio_fuente = c(FALSE, FALSE, FALSE, TRUE),
    incluido_analisis_semanal = c(TRUE, TRUE, TRUE, FALSE)
  )

  cortes_test <- tibble::tibble(
    sistema = "DENGUE",
    anio_fuente = 2026L,
    semana_corte_operativa = 30L,
    origen_corte = "FECHA_CORTE_EN_NOMBRE",
    estado_corte = "OK"
  )

  # Simula exactamente la salida de
  # construir_base_analitica_temporal_18_v24(): la base YA trae
  # las columnas de corte antes de entrar a la auditoria.
  base_enriquecida <- base_test |>
    dplyr::left_join(
      cortes_test,
      by = c("sistema", "anio_fuente")
    )

  salida_enriquecida <- auditar_corte_operativo_18_v24(
    base_longitudinal = base_enriquecida,
    cortes_operativos = cortes_test,
    anio_actual = 2026L
  )

  # Tambien prueba compatibilidad con una base que aun NO trae
  # las columnas de corte.
  salida_no_enriquecida <- auditar_corte_operativo_18_v24(
    base_longitudinal = base_test,
    cortes_operativos = cortes_test,
    anio_actual = 2026L
  )

  tibble::tibble(
    prueba = c(
      "Ruta real con columnas de corte preexistentes no falla",
      "No se crean columnas semana_corte_operativa.x/y",
      "Auditoria conserva semana corte 30",
      "Detecta un registro posterior al corte",
      "Explica posterior por cruce de anio epidemiologico",
      "No reporta posterior del mismo anio epi",
      "Ultima semana analitica queda en 30",
      "Base sin columnas de corte sigue siendo compatible",
      "Ambas rutas producen el mismo resultado esencial"
    ),
    pasa = c(
      is.data.frame(salida_enriquecida) &&
        nrow(salida_enriquecida) == 1L,

      !any(grepl(
        "semana_corte_operativa\\.[xy]",
        names(salida_enriquecida)
      )),

      salida_enriquecida$semana_corte_operativa[1] == 30L,

      salida_enriquecida$registros_posteriores_corte[1] == 1L,

      salida_enriquecida$posteriores_explicados_otro_anio[1] == 1L,

      salida_enriquecida$posteriores_mismo_anio_epi[1] == 0L,

      salida_enriquecida$ultima_semana_analitica[1] == 30L,

      is.data.frame(salida_no_enriquecida) &&
        nrow(salida_no_enriquecida) == 1L,

      identical(
        salida_enriquecida$registros_posteriores_corte,
        salida_no_enriquecida$registros_posteriores_corte
      )
    )
  )
}


validar_hotfix_18_v241 <- function() {

  pruebas <- prueba_auditoria_corte_v241()

  cat(
    "\n====================================================\n"
  )
  cat(
    "PRISMA-R | VALIDACION HOTFIX 18 V2.4.1\n"
  )
  cat(
    "====================================================\n\n"
  )

  print(
    pruebas,
    n = Inf,
    width = Inf
  )

  if (all(pruebas$pasa)) {
    cat(
      "\nOK HOTFIX 18 V2.4.1 VALIDADO FUNCIONALMENTE\n"
    )
  } else {
    cat(
      "\nATENCION: HOTFIX 18 V2.4.1 REQUIERE REVISION\n"
    )
  }

  invisible(pruebas)
}


cat(
  "\n====================================================\n"
)
cat(
  "PRISMA-R | MODULO 18 V2.4.1 CARGADO\n"
)
cat(
  "FIX AUDITORIA DE CORTE OPERATIVO\n"
)
cat(
  "====================================================\n"
)
cat(
  "\nValidacion del hotfix:\n"
)
cat(
  "validacion_18_v241 <- validar_hotfix_18_v241()\n"
)
cat(
  "\nEjecucion real:\n"
)
cat(
  "resultado_18_v24 <- ejecutar_motor_historico_comparativo_18(resultado_17 = resultado_17)\n"
)
