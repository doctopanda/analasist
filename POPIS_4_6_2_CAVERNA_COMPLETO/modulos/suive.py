from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .io_utils import first_existing, read_excel_raw, read_table


def _long_from_standard(df: pd.DataFrame) -> pd.DataFrame | None:
    year_col = first_existing(df.columns, ["Año", "ANIO", "ANO", "Anio", "year"])
    week_col = first_existing(df.columns, ["Semana", "SE", "SEMANA", "week"])
    cases_col = first_existing(df.columns, ["Casos", "CASOS", "Total", "TOTAL", "cases"])
    if not (year_col and week_col and cases_col):
        return None
    out = pd.DataFrame({
        "Año": pd.to_numeric(df[year_col], errors="coerce"),
        "Semana": pd.to_numeric(df[week_col], errors="coerce"),
        "Casos": pd.to_numeric(df[cases_col], errors="coerce"),
    }).dropna(subset=["Año", "Semana", "Casos"])
    out = out[out["Semana"].between(1, 53) & out["Año"].between(2000, 2100)]
    out[["Año", "Semana"]] = out[["Año", "Semana"]].astype(int)
    return out.sort_values(["Año", "Semana"]).reset_index(drop=True)


def _scan_wide(raw: pd.DataFrame) -> pd.DataFrame:
    """Reconoce filas Año + 53 semanas, incluso en libros con títulos/formato visual."""
    rows: list[dict[str, float | int]] = []
    for r in range(len(raw)):
        values = raw.iloc[r].tolist()
        for c, value in enumerate(values):
            year = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
            if pd.isna(year) or not 2000 <= float(year) <= 2100:
                continue
            year_i = int(year)
            after = values[c + 1:c + 60]
            numeric = pd.to_numeric(pd.Series(after), errors="coerce")
            # Una fila semanal útil suele contener al menos 20 valores válidos y hasta 53 semanas.
            if numeric.iloc[:53].notna().sum() < 20:
                continue
            weeks = numeric.iloc[:53]
            for week, cases in enumerate(weeks, start=1):
                if pd.notna(cases):
                    rows.append({"Año": year_i, "Semana": week, "Casos": float(cases)})
            break
    if not rows:
        return pd.DataFrame(columns=["Año", "Semana", "Casos"])
    out = pd.DataFrame(rows)
    # Si el escaneo encontró duplicados de la misma tabla, conserva la última ocurrencia por año/semana.
    return out.drop_duplicates(["Año", "Semana"], keep="last").sort_values(["Año", "Semana"]).reset_index(drop=True)


def load_suive(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    # Primero intenta formato tabular normal.
    try:
        df = read_table(path)
        standard = _long_from_standard(df)
        if standard is not None and not standard.empty:
            return standard
    except Exception:
        pass

    if path.suffix.lower() in {".xlsx", ".xls"}:
        # Preferencia por hoja SUIVE, luego primera hoja.
        for sheet in ("SUIVE", 0):
            try:
                raw = read_excel_raw(path, sheet_name=sheet)
                result = _scan_wide(raw)
                if not result.empty:
                    return result
            except Exception:
                continue
    raise ValueError(f"No fue posible reconocer la estructura SUIVE/SUAVE de {path.name}.")


def cumulative_at_cutoff(suive: pd.DataFrame, cutoff_week: int) -> pd.DataFrame:
    if suive.empty:
        return pd.DataFrame(columns=["Año", "Acumulado", "Casos semana"])
    work = suive.copy()
    work = work[work["Semana"].between(1, cutoff_week)]
    cumulative = work.groupby("Año", as_index=False)["Casos"].sum().rename(columns={"Casos": "Acumulado"})
    week = suive[suive["Semana"].eq(cutoff_week)][["Año", "Casos"]].rename(columns={"Casos": "Casos semana"})
    return cumulative.merge(week, on="Año", how="left").fillna({"Casos semana": 0})


def current_cutoff(suive: pd.DataFrame, year: int | None = None) -> int | None:
    if suive.empty:
        return None
    if year is None:
        year = int(suive["Año"].max())
    weeks = suive.loc[suive["Año"].eq(year) & suive["Casos"].notna(), "Semana"]
    return int(weeks.max()) if not weeks.empty else None


def matrix(suive: pd.DataFrame) -> pd.DataFrame:
    if suive.empty:
        return pd.DataFrame()
    return suive.pivot_table(index="Año", columns="Semana", values="Casos", aggfunc="sum", fill_value=0).sort_index()
