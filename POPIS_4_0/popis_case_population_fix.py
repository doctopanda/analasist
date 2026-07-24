"""Correcciones de cruce SINAVE ↔ población para POPIS 4.3.x.

Resuelve dos problemas observados con las bases reales:
1) SINAVE usa Edo_Res, mientras el motor base buscaba Ent_Res. Eso marcaba a
   todos los registros como no residentes de Sonora y dejaba territorio/tasas
   en cero.
2) La proyección municipal usa códigos de grupo como pobm_65_mm / pobh_65_mm,
   equivalentes a 65 y más. Las tasas deben asignar cualquier edad >=65 al
   grupo 65+ cuando ése sea el último estrato disponible.
"""
from __future__ import annotations

import re
import numpy as np
import pandas as pd

import popis_core as core
import popis_population as popmod


def _blank(series: pd.Series) -> pd.Series:
    return series.isna() | series.astype(str).str.strip().isin(["", "nan", "None", "<NA>"])


def fix_sinave_residence(df: pd.DataFrame) -> pd.DataFrame:
    """Completa estado de residencia desde Edo_Res y recalcula residencia Sonora."""
    if df is None or df.empty:
        return df
    out = df.copy()

    state_source = core._first_existing(
        out,
        ["Edo_Res", "EDO_RES", "Estado_Residencia", "Estado Residencia", "Ent_Res", "Entidad_Residencia"],
    )
    if "state_residence" not in out:
        out["state_residence"] = pd.Series(pd.NA, index=out.index, dtype="object")
    else:
        # pandas 3 ya no permite introducir strings de forma implícita en una
        # columna float creada originalmente con NaN.
        out["state_residence"] = out["state_residence"].astype("object")
    if state_source:
        missing = _blank(out["state_residence"])
        out.loc[missing, "state_residence"] = out.loc[missing, state_source].astype("object")

    out["state_key"] = out["state_residence"].fillna("").map(core._norm_text)
    out["sonora_resident"] = out["state_key"].eq("SONORA")
    return out


def _fixed_age_group(value: object) -> str:
    """Normaliza grupos etarios, incluidos códigos pobm/pobh_*_mm."""
    x = popmod._norm(value)
    # Ejemplos reales: pobm_65_mm, pobh_65_mm, 65_mm.
    m = re.search(r"(?:POB[MH]?[_\s-]*)?(\d{1,3})[_\s-]*(?:MM|MAS|Y[_\s-]*MAS|Y MAS)$", x)
    if m:
        return f"{int(m.group(1))}+"
    return _ORIGINAL_AGE_GROUP(value)


def _parse_population_group(group: object):
    text = str(group).strip()
    m = re.fullmatch(r"(\d+)\s*-\s*(\d+)", text)
    if m:
        return int(m.group(1)), int(m.group(2)), False
    m = re.fullmatch(r"(\d+)\s*\+", text)
    if m:
        return int(m.group(1)), None, True
    return None


def _case_group_for_population(age: float, available_groups: list[str]) -> str:
    if pd.isna(age) or float(age) < 0:
        return ""
    a = int(float(age))
    parsed = []
    for g in available_groups:
        p = _parse_population_group(g)
        if p:
            parsed.append((str(g), *p))

    # Primero intervalos cerrados, después el grupo abierto final.
    for label, lo, hi, is_plus in parsed:
        if not is_plus and hi is not None and lo <= a <= hi:
            return label
    plus = sorted([(lo, label) for label, lo, hi, is_plus in parsed if is_plus], reverse=True)
    for lo, label in plus:
        if a >= lo:
            return label
    return popmod.age_group_from_years(a)


def _fixed_age_sex_rates(
    sinave: pd.DataFrame,
    pop: pd.DataFrame,
    year: int,
    week_cutoff: int,
    municipality: str = "Todos",
    pathogen: str = "Todos los casos",
    multiplier: int = 100_000,
) -> pd.DataFrame:
    if sinave is None or sinave.empty or pop is None or pop.empty:
        return pd.DataFrame()

    ycol = "epi_year" if "epi_year" in sinave.columns else "year"
    x = sinave[
        pd.to_numeric(sinave[ycol], errors="coerce").eq(year)
        & pd.to_numeric(sinave["epi_week"], errors="coerce").between(1, week_cutoff)
    ].copy()
    if "sonora_resident" in x:
        x = x[x["sonora_resident"].fillna(False)]
    if municipality != "Todos":
        mk = popmod._municipality_key(municipality)
        x = x[x["municipality"].map(popmod._municipality_key).eq(mk)]
    if pathogen != "Todos los casos":
        col = f"path_{pathogen}"
        x = x[x[col].fillna(False)] if col in x else x.iloc[0:0]

    den_rows = popmod._sex_age_rows(pop, year, municipality).copy()
    if den_rows.empty:
        return pd.DataFrame()
    available_groups = den_rows["Grupo edad"].dropna().astype(str).unique().tolist()

    age = pd.to_numeric(x.get("age_years"), errors="coerce")
    if "age_months" in x:
        months = pd.to_numeric(x["age_months"], errors="coerce")
        age = age.where(age.notna(), np.where(months.notna(), 0, np.nan))
    x["Grupo edad"] = pd.Series(age, index=x.index).map(lambda v: _case_group_for_population(v, available_groups))
    x["Sexo std"] = x.get("sex", pd.Series(index=x.index, dtype=object)).map(popmod._sex)
    x["Municipio key"] = x["municipality"].map(popmod._municipality_key)
    x = x[x["Grupo edad"].ne("") & x["Sexo std"].isin(["Hombres", "Mujeres"])]

    cases = (
        x.groupby(["Municipio key", "Grupo edad", "Sexo std"], as_index=False)
        .size()
        .rename(columns={"size": "Casos", "Sexo std": "Sexo"})
    )
    den = (
        den_rows.groupby(["Municipio key", "Grupo edad", "Sexo"], as_index=False)["Población"]
        .sum()
    )
    out = den.merge(cases, on=["Municipio key", "Grupo edad", "Sexo"], how="left")
    out["Casos"] = out["Casos"].fillna(0).astype(int)
    out["Incidencia /100k"] = np.where(
        out["Población"] > 0,
        out["Casos"] / out["Población"] * multiplier,
        np.nan,
    )
    if municipality == "Todos":
        out = out.groupby(["Grupo edad", "Sexo"], as_index=False).agg({"Población": "sum", "Casos": "sum"})
        out["Incidencia /100k"] = np.where(
            out["Población"] > 0,
            out["Casos"] / out["Población"] * multiplier,
            np.nan,
        )
    return out


_ORIGINAL_AGE_GROUP = popmod._age_group


def activate_case_population_fixes() -> None:
    """Aplica parches después de popis_core_patch.apply_patches()."""
    original_normalize = core.normalize_sinave
    original_combine = core.combine_sinave

    def normalize_sinave(df: pd.DataFrame, source_name: str = "") -> pd.DataFrame:
        return fix_sinave_residence(original_normalize(df, source_name))

    def combine_sinave(files):
        return fix_sinave_residence(original_combine(files))

    core.normalize_sinave = normalize_sinave
    core.combine_sinave = combine_sinave
    popmod._age_group = _fixed_age_group
    popmod.age_sex_rates = _fixed_age_sex_rates
