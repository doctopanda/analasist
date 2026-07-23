"""Correcciones y enriquecimiento territorial para POPIS 4.0."""
from __future__ import annotations

import calendar
import numpy as np
import pandas as pd

import popis_core as _base

_ORIGINAL_TERRITORIAL = _base.territorial_summary

DISTRICTS = {
    "01 Hermosillo": ["Aconchi","Arivechi","Bacadéhuachi","Bacanora","Banámichi","Baviácora","Carbó","La Colorada","Cumpas","Divisaderos","Granados","Hermosillo","Huásabas","Huépac","Mazatán","Moctezuma","Nácori Chico","Nacozari de García","Ónavas","Opodepe","Rayón","Sahuaripa","San Felipe de Jesús","San Javier","San Miguel de Horcasitas","San Pedro de la Cueva","Soyopa","Suaqui Grande","Tepache","Ures","Villa Hidalgo","Villa Pesqueira"],
    "02 Caborca": ["Altar","Átil","Caborca","Oquitoa","Pitiquito","Sáric","Tubutama"],
    "03 Santa Ana": ["Agua Prieta","Arizpe","Bacerac","Bacoachi","Bavispe","Benjamín Hill","Cananea","Cucurpe","Fronteras","Huachinera","Ímuris","Magdalena","Naco","Nogales","Santa Ana","Santa Cruz","Trincheras"],
    "04 Ciudad Obregón": ["Bácum","Cajeme","Empalme","Guaymas","Quiriego","Rosario","San Ignacio Río Muerto","Yécora"],
    "05 Navojoa": ["Álamos","Benito Juárez","Etchojoa","Huatabampo","Navojoa"],
    "06 San Luis Río Colorado": ["San Luis Río Colorado","General Plutarco Elías Calles","Puerto Peñasco"],
}

REGIONS = {
    "Capital": ["Hermosillo"],
    "Alto Golfo": ["Puerto Peñasco","San Luis Río Colorado","General Plutarco Elías Calles"],
    "Gran Desierto": ["Altar","Átil","Benjamín Hill","Caborca","Carbó","Magdalena","Oquitoa","Pitiquito","Santa Ana","Sáric","Trincheras","Tubutama"],
    "Frontera": ["Cucurpe","Ímuris","Nogales","Santa Cruz"],
    "Puerto": ["La Colorada","Empalme","Guaymas","Ónavas","San Javier","Suaqui Grande"],
    "Río Yaqui": ["Bácum","Cajeme","Benito Juárez"],
    "Río Mayo": ["Álamos","Etchojoa","Huatabampo","Navojoa","Quiriego","Rosario","San Ignacio Río Muerto"],
    "Tres Ríos": ["Aconchi","Arivechi","Bacanora","Banámichi","Baviácora","Huépac","Mazatán","Opodepe","Rayón","Sahuaripa","San Felipe de Jesús","San Miguel de Horcasitas","San Pedro de la Cueva","Soyopa","Ures","Villa Pesqueira","Yécora"],
    "Cuatro Sierras": ["Agua Prieta","Arizpe","Bacoachi","Cananea","Fronteras","Naco"],
    "Sierra Alta": ["Bacadéhuachi","Bacerac","Bavispe","Cumpas","Divisaderos","Granados","Huachinera","Huásabas","Moctezuma","Nácori Chico","Nacozari de García","Tepache","Villa Hidalgo"],
}


def _reverse_catalog(catalog: dict[str, list[str]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for group, municipalities in catalog.items():
        for municipality in municipalities:
            result[_base._norm_text(municipality)] = group
    return result


_DISTRICT_BY_MUN = _reverse_catalog(DISTRICTS)
_REGION_BY_MUN = _reverse_catalog(REGIONS)


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
    processed = sample_v & sample_e & x["recv_vibrio"].notna() & x["recv_entero"].notna() & ~qv.str.contains("RECHAZ") & ~qe.str.contains("RECHAZ")
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
    sampled_u5 = eligible_u5 & _base._yes(x["sample_vibrio"]) & _base._yes(x["sample_entero"]) & _base._yes(x["sample_virus"]) & x["recv_vibrio"].notna() & x["recv_entero"].notna() & x["recv_virus"].notna()
    eligible_5 = age5plus & moderate_severe
    sampled_5 = eligible_5 & _base._yes(x["sample_vibrio"]) & _base._yes(x["sample_entero"]) & x["recv_vibrio"].notna() & x["recv_entero"].notna()

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
        result.loc[reject, "Escala"] = np.where(result.loc[reject, "Cumple"].eq("Sí"), "Cumple estándar ≤10%", "Alarma >10%")
    return result


def territorial_summary(df: pd.DataFrame, year: int, week_cutoff: int, population: pd.DataFrame | None = None, multiplier: int = 100_000) -> pd.DataFrame:
    result = _ORIGINAL_TERRITORIAL(df, year, week_cutoff, population, multiplier).copy()
    keys = result["Municipio"].fillna("").map(_base._norm_text)
    result.insert(1, "Distrito", keys.map(_DISTRICT_BY_MUN).fillna("No asignado / fuera de Sonora"))
    result.insert(2, "Región", keys.map(_REGION_BY_MUN).fillna("No asignada / fuera de Sonora"))
    return result


def aggregate_territory(territorial: pd.DataFrame, level: str) -> pd.DataFrame:
    if level not in {"Distrito", "Región"}:
        raise ValueError("level debe ser 'Distrito' o 'Región'.")
    numeric = [c for c in ["Casos", "Positivos", "Defunciones", "Población"] if c in territorial.columns]
    result = territorial.groupby(level, as_index=False)[numeric].sum(min_count=1)
    if "Casos" in result:
        result["Positividad %"] = np.where(result["Casos"] > 0, result.get("Positivos", 0) / result["Casos"] * 100, np.nan)
        result["Letalidad %"] = np.where(result["Casos"] > 0, result.get("Defunciones", 0) / result["Casos"] * 100, np.nan)
    if "Población" in result:
        result["Incidencia /100k"] = np.where(result["Población"] > 0, result["Casos"] / result["Población"] * 100_000, np.nan)
        result["Mortalidad /100k"] = np.where(result["Población"] > 0, result.get("Defunciones", 0) / result["Población"] * 100_000, np.nan)
    return result


def apply_patches() -> None:
    """Instala funciones corregidas y enriquecidas sobre el módulo base antes de cargar la UI."""
    _base.nutrave_indicators = nutrave_indicators
    _base.laboratory_indicators = laboratory_indicators
    _base.territorial_summary = territorial_summary
