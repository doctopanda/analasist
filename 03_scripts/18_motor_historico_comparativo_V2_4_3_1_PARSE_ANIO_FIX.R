# ============================================================
# PRISMA-R
# MODULO 18 V2.4.3.1 - HOTFIX PARSER ANIO EXPLICITO
# ============================================================
# BUILD_18_V2_4_3_1_PARSE_ANIO_FIX_20260724_01
#
# Carga V2.4.3 y endurece el parser de anio explicito para tolerar
# NA, blancos y textos sin provocar indices logicos con NA.
# ============================================================

archivo_v243 <- here::here(
  "03_scripts",
  "18_motor_historico_comparativo_V2_4_3_ANIO_SEMANA_EXPLICITOS.R"
)

if (!file.exists(archivo_v243)) {
  stop(
    paste0(
      "No se encontro el modulo requerido V2.4.3: ",
      archivo_v243
    )
  )
}

source(archivo_v243)

.extraer_anio_epi_explicito_18_v243 <- function(x) {

  z <- trimws(as.character(x))
  z[is.na(z)] <- ""

  out <- suppressWarnings(as.integer(z))

  faltan <- is.na(out)

  if (any(faltan)) {
    zf <- z[faltan]
    tiene_anio <- grepl("(?:19|20)[0-9]{2}", zf, perl = TRUE)
    extra <- rep(NA_character_, length(zf))

    if (any(tiene_anio)) {
      extra[tiene_anio] <- sub(
        ".*?((?:19|20)[0-9]{2}).*",
        "\\1",
        zf[tiene_anio],
        perl = TRUE
      )
    }

    out[faltan] <- suppressWarnings(as.integer(extra))
  }

  fuera_rango <-
    !is.na(out) &
    (out < 1900L | out > 2100L)

  out[fuera_rango] <- NA_integer_
  out
}

prueba_parser_anio_explicito_18_v2431 <- function() {

  entrada <- c(
    "2025",
    2026,
    NA,
    "",
    "ANIO 2024",
    "sin dato",
    "1899",
    "2101"
  )

  observado <- .extraer_anio_epi_explicito_18_v243(entrada)
  esperado <- c(
    2025L,
    2026L,
    NA_integer_,
    NA_integer_,
    2024L,
    NA_integer_,
    NA_integer_,
    NA_integer_
  )

  tibble::tibble(
    prueba = c(
      "Parser acepta anio numerico en texto",
      "Parser acepta anio numerico",
      "Parser tolera NA",
      "Parser tolera blanco",
      "Parser extrae anio desde texto",
      "Parser tolera texto sin anio",
      "Parser invalida anio menor a 1900",
      "Parser invalida anio mayor a 2100",
      "Vector completo coincide con esperado"
    ),
    pasa = c(
      observado[1] == 2025L,
      observado[2] == 2026L,
      is.na(observado[3]),
      is.na(observado[4]),
      observado[5] == 2024L,
      is.na(observado[6]),
      is.na(observado[7]),
      is.na(observado[8]),
      identical(observado, esperado)
    )
  )
}

validar_hotfix_18_v2431 <- function() {

  validacion_v243 <- validar_hotfix_18_v243()
  pruebas_parser <- prueba_parser_anio_explicito_18_v2431()

  cat("\n====================================================\n")
  cat("PRISMA-R | VALIDACION HOTFIX 18 V2.4.3.1\n")
  cat("PARSER ANIO EXPLICITO\n")
  cat("====================================================\n\n")

  print(pruebas_parser, n = Inf, width = Inf)

  if (all(pruebas_parser$pasa)) {
    cat("\nOK HOTFIX 18 V2.4.3.1 VALIDADO FUNCIONALMENTE\n")
  } else {
    cat("\nREVISAR HOTFIX 18 V2.4.3.1\n")
  }

  invisible(
    list(
      v243 = validacion_v243,
      parser = pruebas_parser
    )
  )
}

cat("\n====================================================\n")
cat("PRISMA-R | MODULO 18 V2.4.3.1 CARGADO\n")
cat("HOTFIX PARSER ANIO EXPLICITO\n")
cat("====================================================\n")
cat("\nValidacion recomendada:\n")
cat("validacion_18_v2431 <- validar_hotfix_18_v2431()\n")
cat("\nEjecucion real:\n")
cat("resultado_18_v243 <- ejecutar_motor_historico_comparativo_18(resultado_17 = resultado_17)\n")
