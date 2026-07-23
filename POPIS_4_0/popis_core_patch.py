"""Correcciones de lógica para POPIS 4.0.

Este módulo mantiene el motor base estable y corrige reglas donde el sentido del
indicador o los datos faltantes requieren tratamiento explícito.
"""
from __future__ import annotations

import calendar
import numpy as np
import pandas as pd

import popis_core as _base


def nutrave_indicators(df: pd.DataFrame, year: int, month: int) -> pd.DataFrame:
    x = _base.month_filter(df, year, month)
    nflag = x["nutrave"].fillna("").map(_base._norm_text).isin(_base.YES)
    if nflag.any():
        x = x[nflag].copy()

    valid = x["capture_date"].notna() & x["first_contact"].notna()
    delta = (x["capture_date"] - x["first_contact"]).dt.days
    den_notif = int((valid & delta.ge(0)).sum())
    num_notif = int((valid & delta.between(0, 1)).sum())

    sample_v = _base._yes(x["sample_vibrio"])
    sample_e = _base._yes(x["sample_entero"])
    qv = x["quality_vibrio"].fillna("").map(_base._norm_text)
    qe = x["quality_entero"].fillna("").map(_base._norm_text)
    processed = (
        sample_v & sample_e
        & x["recv_vibrio"].notna() & x["recv_entero"].notna()
        & ~qv.str.contains("RECHAZ") & ~qe.str.contains("RECHAZ")
    )
    den_class = int(processed.sum())
    dclass = (x["final_dx_date"] - x["first_contact"]).dt.days
    num_class = int((processed & x["final_dx_date"].notna() & dclass.between(0, 9)).sum())

    days = int(x["capture_date"].dropna().dt.normalize().nunique())
    days_month = calendar.monthrange(year, month)[1]

    age = x["age_years"]
    age_known = age.notna()
    under5 = age_known & age.lt(5)
    age5plus = age_known & age.ge(5)

    type_norm = x["eda_type"].fillna("").map(_base._norm_text)
    moderate_severe = type_norm.str.contains("MODER") | type_norm.str.contains("GRAV")

    eligible_u5 = under5 & moderate_severe
    sampled_u5 = (
        eligible_u5
        & _base._yes(x["sample_vibrio"])
        & _base._yes(x["sample_entero"])
        & _base._yes(x["sample_virus"])
        & x["recv_vibrio"].notna()
        & x["recv_entero"].notna()
        & x["recv_virus"].notna()
    )

    eligible_5 = age5plus & moderate_severe
    sampled_5 = (
        eligible_5
        & _base._yes(x["sample_vibrio"])
        & _base._yes(x["sample_entero"])
        & x["recv_vibrio"].notna()
        & x["recv_entero"].notna()
    )

    rows = [
        _base._indicator("Notificación oportuna de EDA", num_notif, den_notif, 100),
        _base._indicator("Clasificación oportuna de EDA", num_class, den_class, 80),
        _base._indicator("Cobertura de notificación de EDA", days, days_month, 80),
        _base._indicator("Muestreo EDA <5 años", int(sampled_u5.sum()), int(eligible_u5.sum()), 80),
        _base._indicator("Muestreo EDA ≥5 años", int(sampled_5.sum()), int(eligible_5.sum()), 80),
    ]
    result = pd.DataFrame(rows)
    result["Nota"] = ""
    missing_age = int((~age_known & moderate_severe).sum())
    if missing_age:
        mask = result["Indicador"].str.startswith("Muestreo EDA")
        result.loc[mask, "Nota"] = f"{missing_age} caso(s) moderado/grave sin edad se excluyeron del denominador"
    return result


def laboratory_indicators(df: pd.DataFrame, year: int, month: int) -> pd.DataFrame:
    result = _base.laboratory_indicators(df, year, month).copy()
    reject = result["Indicador"].eq("Muestras rechazadas")
    if reject.any():
        result.loc[reject, "Escala"] = np.where(
            result.loc[reject, "Cumple"].eq("Sí"),
            "Cumple estándar ≤10%",
            "Alarma >10%",
        )
    return result


def apply_patches() -> None:
    """Instala las funciones corregidas sobre el módulo base."""
    _base.nutrave_indicators = nutrave_indicators
    _base.laboratory_indicators = laboratory_indicators
