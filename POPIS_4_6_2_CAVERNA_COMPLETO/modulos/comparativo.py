from __future__ import annotations

import numpy as np
import pandas as pd

from .sinave import weekly_series as sinave_weekly_series


def compare_systems(sinave_base: pd.DataFrame, suive: pd.DataFrame, cutoff_week: int,
                    year: int | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compara sistemas sin sumarlos.

    La razón se etiqueta como Razón de registro SINAVE/SUIVE. No se interpreta automáticamente
    como subregistro porque ambos sistemas tienen propósitos y universos distintos.
    """
    sin_weekly = sinave_weekly_series(sinave_base)
    if year is None:
        candidates = []
        if not sin_weekly.empty:
            candidates.append(int(sin_weekly["Año"].max()))
        if not suive.empty:
            candidates.append(int(suive["Año"].max()))
        year = max(candidates) if candidates else None
    if year is None:
        return pd.DataFrame(), pd.DataFrame()

    s1 = sin_weekly[sin_weekly["Año"].eq(year)][["Semana", "Casos"]].rename(columns={"Casos": "SINAVE"})
    s2 = suive[suive["Año"].eq(year)][["Semana", "Casos"]].rename(columns={"Casos": "SUIVE"})
    weekly = pd.DataFrame({"Semana": range(1, 54)}).merge(s1, on="Semana", how="left").merge(s2, on="Semana", how="left")
    weekly[["SINAVE", "SUIVE"]] = weekly[["SINAVE", "SUIVE"]].fillna(0)
    weekly = weekly[weekly["Semana"].between(1, cutoff_week)].copy()
    weekly["Razón de registro SINAVE/SUIVE"] = np.where(weekly["SUIVE"].gt(0), weekly["SINAVE"] / weekly["SUIVE"], np.nan)
    weekly["Diferencia SUIVE - SINAVE"] = weekly["SUIVE"] - weekly["SINAVE"]

    cumulative = weekly.copy()
    cumulative["SINAVE acumulado"] = cumulative["SINAVE"].cumsum()
    cumulative["SUIVE acumulado"] = cumulative["SUIVE"].cumsum()
    cumulative["Razón acumulada SINAVE/SUIVE"] = np.where(
        cumulative["SUIVE acumulado"].gt(0), cumulative["SINAVE acumulado"] / cumulative["SUIVE acumulado"], np.nan
    )
    return weekly, cumulative


def paired_pathogen_note() -> pd.DataFrame:
    return pd.DataFrame([
        {"SUIVE/SUAVE": "A02 Salmonelosis", "SINAVE": "Salmonella positiva", "Interpretación": "Diagnóstico reportado vs identificación nominal/laboratorial"},
        {"SUIVE/SUAVE": "A03 Shigelosis", "SINAVE": "Shigella positiva", "Interpretación": "Diagnóstico reportado vs identificación nominal/laboratorial"},
        {"SUIVE/SUAVE": "A08.0 Rotavirus", "SINAVE": "Rotavirus positivo", "Interpretación": "Diagnóstico reportado vs identificación nominal/laboratorial"},
        {"SUIVE/SUAVE": "A00 Cólera", "SINAVE": "V. cholerae toxigénico", "Interpretación": "Solo comparable con definición y laboratorio compatibles"},
    ])
