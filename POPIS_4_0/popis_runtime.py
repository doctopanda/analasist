"""Activación segura de los parches POPIS."""
from __future__ import annotations

import numpy as np
import pandas as pd
import popis_core as core

_ORIGINAL_LABORATORY = core.laboratory_indicators


def activate() -> None:
    from popis_core_patch import apply_patches
    from popis_suive_fix import parse_suive_history as robust_parse_suive_history
    from popis_case_population_fix import activate_case_population_fixes

    apply_patches()
    activate_case_population_fixes()
    core.parse_suive_history = robust_parse_suive_history

    def safe_suive_summary(suive: pd.DataFrame, year: int, week_cutoff: int) -> dict:
        if suive is None or suive.empty:
            return {"acumulado": np.nan, "semana": np.nan, "ultima_se": np.nan}
        y = suive[pd.to_numeric(suive["Año"], errors="coerce").eq(year)].copy()
        if y.empty:
            return {"acumulado": np.nan, "semana": np.nan, "ultima_se": np.nan}
        y["SE"] = pd.to_numeric(y["SE"], errors="coerce")
        y["Casos"] = pd.to_numeric(y["Casos"], errors="coerce")
        available = y[y["SE"].between(1, 53) & y["Casos"].notna()]
        last = int(available["SE"].max()) if not available.empty else np.nan
        x = available[available["SE"].between(1, week_cutoff)]
        w = available[available["SE"].eq(week_cutoff)]
        # Una semana que no existe en la fuente es SIN DATO, no cero casos.
        week_value = float(w["Casos"].sum()) if not w.empty else np.nan
        accumulated = float(x["Casos"].sum()) if not x.empty else np.nan
        return {"acumulado": accumulated, "semana": week_value, "ultima_se": last}

    core.suive_summary = safe_suive_summary

    def laboratory_indicators(df, year: int, month: int):
        result = _ORIGINAL_LABORATORY(df, year, month).copy()
        reject = result["Indicador"].eq("Muestras rechazadas")
        if reject.any():
            result.loc[reject, "Escala"] = np.where(
                result.loc[reject, "Cumple"].eq("Sí"),
                "Cumple estándar ≤10%",
                "Alarma >10%",
            )
        return result

    core.laboratory_indicators = laboratory_indicators
