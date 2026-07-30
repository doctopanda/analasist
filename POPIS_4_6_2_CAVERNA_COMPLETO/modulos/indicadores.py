from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

from .io_utils import first_existing


@dataclass
class IndicatorResult:
    codigo: str
    indicador: str
    numerador: int | float | None
    denominador: int | float | None
    resultado: float | None
    meta: float
    estado: str
    formula: str
    detalle: str = ""

    def as_dict(self) -> dict:
        return {
            "Código": self.codigo,
            "Indicador": self.indicador,
            "Numerador": self.numerador,
            "Denominador": self.denominador,
            "Resultado %": self.resultado,
            "Meta %": self.meta,
            "Estado": self.estado,
            "Fórmula": self.formula,
            "Detalle / limitación": self.detalle,
        }


def _date(df: pd.DataFrame, candidates: Iterable[str]) -> tuple[pd.Series, str | None]:
    col = first_existing(df.columns, candidates)
    if not col:
        return pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]"), None
    return pd.to_datetime(df[col], dayfirst=True, errors="coerce"), col


def _num(df: pd.DataFrame, candidates: Iterable[str]) -> tuple[pd.Series, str | None]:
    col = first_existing(df.columns, candidates)
    if not col:
        return pd.Series(np.nan, index=df.index, dtype=float), None
    return pd.to_numeric(df[col], errors="coerce"), col


def _text(df: pd.DataFrame, candidates: Iterable[str]) -> tuple[pd.Series, str | None]:
    col = first_existing(df.columns, candidates)
    if not col:
        return pd.Series("", index=df.index, dtype="object"), None
    return df[col].fillna("").astype(str).str.strip(), col


def _pct(num: int | float, den: int | float) -> float | None:
    return float(num / den * 100) if den else None


def _state(value: float | None, goal: float) -> str:
    if value is None or pd.isna(value):
        return "No calculable"
    if value >= goal:
        return "Cumple"
    return "No cumple"


def _result(code: str, name: str, num, den, goal: float, formula: str, detail: str = "") -> IndicatorResult:
    value = _pct(num, den) if num is not None and den is not None else None
    return IndicatorResult(code, name, num, den, value, goal, _state(value, goal), formula, detail)


def _probable_cholera_mask(df: pd.DataFrame) -> pd.Series:
    diag, diag_col = _text(df, ["Diag_Prob", "Diagnóstico probable", "Diagnostico probable"])
    if diag_col:
        return diag.str.upper().str.contains("COLER", regex=False)
    # Alternativa conservadora: solo usa regla clínica si existen todas las señales necesarias.
    age, age_col = _num(df, ["Edad", "EDAD", "Años", "Anios", "Edad_Anios"])
    stools, stools_col = _num(df, ["NumEvacuaciones", "NumeroEvacuaciones", "NoEvacuaciones", "Evacuaciones24h"])
    evolution, evo_col = _num(df, ["DiasEvolucion", "Días evolución", "Dias_Evolucion"])
    if age_col and stools_col and evo_col:
        return age.ge(5) & stools.ge(5) & evolution.le(5)
    return pd.Series(False, index=df.index)


def calculate_indicators(df: pd.DataFrame, monthly_vibrio_target: int | float | None = None) -> pd.DataFrame:
    """Calcula indicadores solo cuando la base contiene la evidencia mínima.

    No rellena variables ausentes con supuestos. Cada indicador conserva numerador,
    denominador, fórmula y una nota de limitación para auditoría.
    """
    if df.empty:
        return pd.DataFrame(columns=list(IndicatorResult("", "", None, None, None, 0, "", "").as_dict()))

    results: list[IndicatorResult] = []
    first_contact, fc_col = _date(df, ["Fec_Prim_Contacto", "FecPrimContacto", "Fecha_Primer_Contacto", "FecAtencion", "FechaAtencion"])
    capture, cap_col = _date(df, ["Fec_captura", "FEC_CAP", "Fecha_Captura"])
    final_date, final_col = _date(df, ["Fec_Dx_Final", "Fecha_Dx_Final", "Fec_Clasificacion", "FEC_CLASIFICACION"])
    probable_cholera = _probable_cholera_mask(df)

    # 1. Cólera: notificación en 24h. El manual operacionaliza diferencia 0 o 1 día natural.
    if fc_col and cap_col and probable_cholera.any():
        diff = (capture - first_contact).dt.total_seconds() / 86400
        valid = probable_cholera & diff.ge(0)
        timely = valid & diff.le(1)
        results.append(_result(
            "COL-01", "Notificación oportuna de cólera", int(timely.sum()), int(valid.sum()), 100,
            "Probables de cólera notificados ≤24 h / probables válidos ×100",
            f"Primer contacto: {fc_col}; captura/notificación: {cap_col}. Cronologías negativas excluidas.",
        ))
    else:
        results.append(_result("COL-01", "Notificación oportuna de cólera", None, None, 100,
                               "Probables de cólera notificados ≤24 h / probables válidos ×100",
                               "Faltan columnas de primer contacto/captura o no hay casos probables identificables."))

    # Muestra de Vibrio y recepción.
    vibrio_sample, sample_col = _text(df, ["MuestraVibrio", "TipoMuestraVibrio", "TomaHisopo", "Muestra_Vibrio"])
    reception, reception_col = _date(df, ["FecRecepLab", "Fec_Recepcion_Lab", "FecRecepLESP", "Fecha_Recepcion"])
    if probable_cholera.any() and sample_col and reception_col:
        eligible = probable_cholera
        sampled = eligible & vibrio_sample.ne("") & reception.notna()
        results.append(_result("COL-02", "Casos probables de cólera con muestra", int(sampled.sum()), int(eligible.sum()), 80,
                               "Probables con muestra de Vibrio y recepción / probables ×100",
                               f"Muestra: {sample_col}; recepción: {reception_col}."))
    else:
        results.append(_result("COL-02", "Casos probables de cólera con muestra", None, None, 80,
                               "Probables con muestra de Vibrio y recepción / probables ×100",
                               "No se identificaron todas las variables requeridas."))

    # Clasificación cólera en 14 días entre primer contacto y resultado/clasificación.
    if probable_cholera.any() and fc_col and final_col:
        delta = (final_date - first_contact).dt.days
        processed = probable_cholera & first_contact.notna() & final_date.notna() & delta.ge(0)
        timely = processed & delta.le(14)
        results.append(_result("COL-03", "Clasificación oportuna de cólera", int(timely.sum()), int(processed.sum()), 80,
                               "Probables procesados clasificados en 0–14 días / probables procesados ×100",
                               f"Primer contacto: {fc_col}; clasificación/resultado: {final_col}."))
    else:
        results.append(_result("COL-03", "Clasificación oportuna de cólera", None, None, 80,
                               "Probables procesados clasificados en 0–14 días / probables procesados ×100",
                               "Falta fecha de primer contacto o clasificación/resultado."))

    # Reporte negativo diario: solo calculable si existe variable de fecha de notificación diaria.
    report_date, report_col = _date(df, ["Fecha_Reporte_Negativo", "FecReporteNegativo", "FechaNotificacionDiaria"])
    if report_col:
        valid_dates = report_date.dropna().dt.normalize().drop_duplicates()
        if not valid_dates.empty:
            month = valid_dates.dt.to_period("M").mode().iloc[0]
            observed = int((valid_dates.dt.to_period("M") == month).sum())
            expected = int(month.days_in_month)
            results.append(_result("COL-04", "Cobertura de reporte negativo", observed, expected, 80,
                                   "Días con reporte / días calendario esperados ×100",
                                   f"Mes evaluado automáticamente: {month}; campo: {report_col}."))
        else:
            results.append(_result("COL-04", "Cobertura de reporte negativo", 0, 0, 80,
                                   "Días con reporte / días calendario esperados ×100", "No hay fechas válidas."))
    else:
        results.append(_result("COL-04", "Cobertura de reporte negativo", None, None, 80,
                               "Días con reporte / días calendario esperados ×100",
                               "SINAVE nominal no contiene necesariamente el calendario de reporte negativo."))

    # NuTraVE notificación 24h para toda EDA.
    if fc_col and cap_col:
        diff = (capture - first_contact).dt.total_seconds() / 86400
        valid = first_contact.notna() & capture.notna() & diff.ge(0)
        timely = valid & diff.le(1)
        results.append(_result("NUT-01", "Notificación oportuna EDA NuTraVE", int(timely.sum()), int(valid.sum()), 100,
                               "EDA notificadas ≤24 h / EDA con cronología válida ×100",
                               f"Primer contacto: {fc_col}; captura/notificación: {cap_col}."))
    else:
        results.append(_result("NUT-01", "Notificación oportuna EDA NuTraVE", None, None, 100,
                               "EDA notificadas ≤24 h / EDA con cronología válida ×100",
                               "Faltan fechas para reconstruir oportunidad."))

    if fc_col and final_col:
        delta = (final_date - first_contact).dt.days
        processed = first_contact.notna() & final_date.notna() & delta.ge(0)
        timely = processed & delta.le(9)
        results.append(_result("NUT-02", "Clasificación oportuna EDA NuTraVE", int(timely.sum()), int(processed.sum()), 80,
                               "EDA procesadas clasificadas en 0–9 días / EDA procesadas ×100",
                               f"Primer contacto: {fc_col}; clasificación/resultado: {final_col}."))
    else:
        results.append(_result("NUT-02", "Clasificación oportuna EDA NuTraVE", None, None, 80,
                               "EDA procesadas clasificadas en 0–9 días / EDA procesadas ×100",
                               "Faltan fechas para reconstruir clasificación."))

    # Cobertura de notificación diaria NuTraVE.
    notif_date, notif_col = _date(df, ["Fec_captura", "Fecha_Notificacion", "FecNotif"])
    if notif_col:
        valid_dates = notif_date.dropna().dt.normalize().drop_duplicates()
        if not valid_dates.empty:
            month = valid_dates.dt.to_period("M").mode().iloc[0]
            observed = int((valid_dates.dt.to_period("M") == month).sum())
            expected = int(month.days_in_month)
            results.append(_result("NUT-03", "Cobertura de notificación NuTraVE", observed, expected, 80,
                                   "Días con notificación / días calendario del mes ×100",
                                   f"Mes modal evaluado: {month}; campo: {notif_col}."))
        else:
            results.append(_result("NUT-03", "Cobertura de notificación NuTraVE", 0, 0, 80,
                                   "Días con notificación / días calendario del mes ×100", "Sin fechas válidas."))
    else:
        results.append(_result("NUT-03", "Cobertura de notificación NuTraVE", None, None, 80,
                               "Días con notificación / días calendario del mes ×100", "No existe fecha de notificación utilizable."))

    # Muestreo por edad y gravedad: fórmula conservadora y solo cuando existen señales.
    age, age_col = _num(df, ["Edad", "EDAD", "Años", "Anios", "Edad_Anios"])
    severity, severity_col = _text(df, ["Gravedad", "CLASIFICACION_EDA", "Clasificacion", "Deshidratacion"])
    swab1, swab1_col = _text(df, ["TomaHisopo1", "Hisopo1", "MuestraBacteriana1", "TomaHisopo"])
    swab2, swab2_col = _text(df, ["TomaHisopo2", "Hisopo2", "MuestraBacteriana2"])
    virus, virus_col = _text(df, ["MuestraVirus", "MuestraViral", "MuestraFecalVirus"])
    if age_col and severity_col:
        sev = severity.str.upper().str.contains("MODER|SEVER|GRAV", regex=True)
        for code, label, mask_age, need_virus in [
            ("NUT-04", "Muestreo <5 años moderada/severa", age.lt(5), True),
            ("NUT-05", "Muestreo ≥5 años moderada/severa", age.ge(5), False),
        ]:
            eligible = sev & mask_age
            if swab1_col and swab2_col and reception_col and (virus_col or not need_virus):
                complete = eligible & swab1.ne("") & swab2.ne("") & reception.notna()
                if need_virus:
                    complete &= virus.ne("")
                results.append(_result(code, label, int(complete.sum()), int(eligible.sum()), 80,
                                       "Muestreo completo / EDA moderada-severa elegible ×100",
                                       "Se exige recepción de laboratorio; en <5 años además muestra viral."))
            else:
                results.append(_result(code, label, None, None, 80,
                                       "Muestreo completo / EDA moderada-severa elegible ×100",
                                       "Faltan campos de hisopos, recepción o muestra viral requeridos."))
    else:
        results.append(_result("NUT-04", "Muestreo <5 años moderada/severa", None, None, 80,
                               "Muestreo completo / EDA moderada-severa elegible ×100", "Falta edad o gravedad."))
        results.append(_result("NUT-05", "Muestreo ≥5 años moderada/severa", None, None, 80,
                               "Muestreo completo / EDA moderada-severa elegible ×100", "Falta edad o gravedad."))

    monitor, monitor_col = _text(df, ["Monitoreo", "Monitoreo2Porciento", "Monitoreo_2"])
    if monitor_col and monthly_vibrio_target is not None:
        positive_monitor = monitor.str.upper().isin(["SI", "SÍ", "1", "TRUE", "2%", "MONITOREO"])
        results.append(_result("MON-02", "Monitoreo del 2% de EDA", int(positive_monitor.sum()), float(monthly_vibrio_target), 80,
                               "Muestras de monitoreo 2% / meta mensual Vibrio ×100",
                               "La meta debe provenir de vigilancia convencional con la metodología normativa."))
    else:
        results.append(_result("MON-02", "Monitoreo del 2% de EDA", None, None, 80,
                               "Muestras de monitoreo 2% / meta mensual Vibrio ×100",
                               "No calculable sin meta mensual normativa derivada de SUIVE/SUAVE de cinco años previos."))

    return pd.DataFrame([r.as_dict() for r in results])
