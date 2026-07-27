from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _date(df: pd.DataFrame, *candidates: str) -> pd.Series:
    col = next((c for c in candidates if c in df.columns), None)
    if col is None:
        return pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")
    return pd.to_datetime(df[col], dayfirst=True, errors="coerce")


def _text(df: pd.DataFrame, *candidates: str) -> pd.Series:
    col = next((c for c in candidates if c in df.columns), None)
    if col is None:
        return pd.Series([""] * len(df), index=df.index, dtype="object")
    return df[col].fillna("").astype(str).str.strip()


def _result(name: str, numerator: int | None, denominator: int | None, target: float | None, note: str = "") -> dict[str, Any]:
    if numerator is None or denominator is None or denominator == 0:
        value = np.nan
        status = "N/A"
    else:
        value = numerator / denominator * 100
        status = "Cumple" if target is not None and value >= target else ("No cumple" if target is not None else "Calculado")
    return {
        "Indicador": name,
        "Numerador": numerator,
        "Denominador": denominator,
        "Resultado %": value,
        "Meta %": target,
        "Estado": status,
        "Nota": note,
    }


def _age_years(df: pd.DataFrame) -> pd.Series:
    for col in ("Edad", "EDAD", "Edad_Anios", "EdadAnios"):
        if col in df.columns:
            return pd.to_numeric(df[col], errors="coerce")
    # Formato frecuente: Edad + Uni_Med_Edad / UnidadEdad.
    age = pd.to_numeric(_text(df, "Edad"), errors="coerce")
    unit = _text(df, "Uni_Med_Edad", "UnidadEdad", "Unidad_Edad").str.casefold()
    out = age.copy()
    out[unit.str.contains("mes", regex=False)] = age[unit.str.contains("mes", regex=False)] / 12
    out[unit.str.contains("dia", regex=False)] = age[unit.str.contains("dia", regex=False)] / 365.25
    return out


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if df is None or df.empty:
        return pd.DataFrame(columns=["Indicador", "Numerador", "Denominador", "Resultado %", "Meta %", "Estado", "Nota"])

    first_contact = _date(df, "Fec_Primer_Contacto", "FEC_PRIM_CONTACT", "FecPrimerContacto")
    capture = _date(df, "Fec_captura", "FEC_CAP", "Fecha_Captura")
    available = first_contact.notna() & capture.notna()
    if available.any():
        delta = (capture - first_contact).dt.days
        num = int((available & delta.between(0, 1)).sum())
        den = int(available.sum())
        rows.append(_result("Notificación oportuna EDA ≤24 h", num, den, 100.0, "Basado en fecha de captura menos primer contacto; cronologías negativas no se consideran oportunas."))
    else:
        rows.append(_result("Notificación oportuna EDA ≤24 h", None, None, 100.0, "Faltan fechas de primer contacto/captura."))

    final_date = _date(df, "Fec_Dx_Final", "FEC_FIN_ESTUDIO", "Fecha_Clasificacion")
    final_diag = _text(df, "Diag_Final", "DES_DIAG_FINAL")
    classifiable = first_contact.notna() & final_date.notna() & final_diag.ne("")
    if classifiable.any():
        delta = (final_date - first_contact).dt.days
        rows.append(_result("Clasificación oportuna EDA ≤9 días", int((classifiable & delta.between(0, 9)).sum()), int(classifiable.sum()), 80.0, "Proxy operativo con casos que tienen fecha y diagnóstico final; el denominador normativo procesado depende de datos de muestra/calidad."))
    else:
        rows.append(_result("Clasificación oportuna EDA ≤9 días", None, None, 80.0, "No hay fechas suficientes para calcular."))

    # Calidad preanalítica: usa cualquier campo de calidad de muestra disponible.
    quality_cols = [c for c in ["Calidad_Hiso_Vibrio", "Calidad_Hiso_Entero", "Calidad_Muest_Virus", "CalidadMuestra"] if c in df.columns]
    if quality_cols:
        vals = pd.concat([_text(df, c) for c in quality_cols], ignore_index=True)
        vals = vals[vals.str.strip().ne("")]
        if len(vals):
            rejected = vals.str.casefold().str.contains("rechaz", regex=False).sum()
            rows.append(_result("Rechazo preanalítico de muestras", int(rejected), int(len(vals)), None, "Meta normativa: rechazo ≤10%. Un valor menor es mejor."))
    else:
        rows.append(_result("Rechazo preanalítico de muestras", None, None, None, "No se detectaron campos de calidad de muestra."))

    age = _age_years(df)
    severity = _text(df, "Tipo_EDA", "TipoEDA", "Severidad").str.casefold()
    modsev = severity.str.contains("moder", regex=False) | severity.str.contains("sever", regex=False)
    bacterial_sample = _text(df, "MuestraVibrio", "MuestraEntero").str.casefold().str.contains("si|sí|1|positivo|tom", regex=True)
    bacterial_received = _date(df, "Fec_Recep_Hiso_Vibrio", "Fec_Recep_Hiso_Entero").notna()
    viral_sample = _text(df, "MuestraVirus").str.casefold().str.contains("si|sí|1|positivo|tom", regex=True)
    viral_received = _date(df, "Fec_Recep_Muest_Virus").notna()

    under5 = age.notna() & age.lt(5) & modsev
    if under5.any():
        good = under5 & bacterial_sample & bacterial_received & viral_sample & viral_received
        rows.append(_result("Muestreo EDA moderada/severa <5 años", int(good.sum()), int(under5.sum()), 80.0, "Requiere muestra bacteriana y viral con recepción registrada."))
    else:
        rows.append(_result("Muestreo EDA moderada/severa <5 años", None, None, 80.0, "No se identificó denominador elegible o faltan edad/severidad."))

    age5 = age.notna() & age.ge(5) & modsev
    if age5.any():
        good = age5 & bacterial_sample & bacterial_received
        rows.append(_result("Muestreo EDA moderada/severa ≥5 años", int(good.sum()), int(age5.sum()), 80.0, "Requiere muestra bacteriana con recepción registrada."))
    else:
        rows.append(_result("Muestreo EDA moderada/severa ≥5 años", None, None, 80.0, "No se identificó denominador elegible o faltan edad/severidad."))

    # Probable cólera, usando diagnóstico probable como selector cuando existe.
    probable = _text(df, "Diag_Prob", "DES_DIAG_PROBABLE").str.casefold().str.contains("coler", regex=False)
    if probable.any() and available.any():
        delta = (capture - first_contact).dt.days
        eligible = probable & available
        rows.append(_result("Notificación oportuna de probable cólera ≤24 h", int((eligible & delta.between(0, 1)).sum()), int(eligible.sum()), 100.0, "Selector basado en diagnóstico probable registrado."))
    else:
        rows.append(_result("Notificación oportuna de probable cólera ≤24 h", None, None, 100.0, "Sin casos identificables como probable cólera o sin fechas completas."))

    rows.append(_result("Porcentaje de muestreo 2% EDA", None, None, None, "Requiere el denominador mensual de vigilancia convencional SUIVE/SUAVE y la meta de monitoreo definida con el histórico de cinco años; POPIS no la fabrica cuando falta esa fuente."))
    rows.append(_result("Notificación de Red Negativa", None, None, 80.0, "Requiere bitácora diaria de red negativa, no inferible de la base nominal SINAVE."))

    out = pd.DataFrame(rows)
    return out
