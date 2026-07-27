from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def _num(v: Any) -> float | None:
    try:
        if pd.isna(v):
            return None
        text = str(v).replace(",", "").strip()
        if not text:
            return None
        return float(text)
    except Exception:
        return None


def read_suive(path: str | Path, sheet_name: str | None = None) -> pd.DataFrame:
    """Extrae una serie larga Año-Semana-Casos desde formatos SUIVE comunes.

    Soporta años en filas con semanas en columnas y años en columnas con semanas en filas.
    Ignora fórmulas rotas y usa valores visibles/raw cuando son numéricos.
    """
    p = Path(path)
    xls = pd.ExcelFile(p)
    sheets = [sheet_name] if sheet_name else [s for s in xls.sheet_names if "SUIVE" in s.upper()]
    if not sheets:
        sheets = xls.sheet_names

    best = pd.DataFrame(columns=["Año", "Semana", "Casos"])
    for sheet in sheets:
        raw = pd.read_excel(p, sheet_name=sheet, header=None)
        candidate = _parse_year_rows(raw)
        if len(candidate) < 50:
            candidate2 = _parse_year_columns(raw)
            if len(candidate2) > len(candidate):
                candidate = candidate2
        if len(candidate) > len(best):
            best = candidate
    if best.empty:
        raise ValueError("No se pudo reconocer la tabla semanal SUIVE.")
    best["Año"] = best["Año"].astype(int)
    best["Semana"] = best["Semana"].astype(int)
    best["Casos"] = pd.to_numeric(best["Casos"], errors="coerce").fillna(0)
    return best.sort_values(["Año", "Semana"]).reset_index(drop=True)


def _parse_year_rows(raw: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for r in range(len(raw)):
        for c in range(min(raw.shape[1], 12)):
            value = _num(raw.iat[r, c])
            if value is None or not (2000 <= value <= 2100) or int(value) != value:
                continue
            year = int(value)
            # Busca encabezado de semanas en las filas cercanas superiores.
            header_row = None
            week_cols: dict[int, int] = {}
            for hr in range(max(0, r - 8), r + 1):
                temp = {}
                for cc in range(c + 1, raw.shape[1]):
                    w = _num(raw.iat[hr, cc])
                    if w is not None and 1 <= w <= 53 and int(w) == w:
                        temp[int(w)] = cc
                if len(temp) >= 10:
                    header_row, week_cols = hr, temp
            if not week_cols:
                # Fallback: primeras 53 celdas después del año.
                for offset in range(1, min(54, raw.shape[1] - c)):
                    week_cols[offset] = c + offset
            for week, cc in week_cols.items():
                cases = _num(raw.iat[r, cc])
                if cases is not None and cases >= 0:
                    rows.append({"Año": year, "Semana": week, "Casos": cases})
            break
    if not rows:
        return pd.DataFrame(columns=["Año", "Semana", "Casos"])
    out = pd.DataFrame(rows)
    out = out[(out["Semana"] >= 1) & (out["Semana"] <= 53)]
    return out.drop_duplicates(["Año", "Semana"], keep="last")


def _parse_year_columns(raw: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for r in range(min(len(raw), 20)):
        year_cols = {}
        for c in range(raw.shape[1]):
            value = _num(raw.iat[r, c])
            if value is not None and 2000 <= value <= 2100 and int(value) == value:
                year_cols[int(value)] = c
        if len(year_cols) < 2:
            continue
        for rr in range(r + 1, len(raw)):
            week = None
            for wc in range(min(min(year_cols.values()), 8)):
                v = _num(raw.iat[rr, wc])
                if v is not None and 1 <= v <= 53 and int(v) == v:
                    week = int(v)
                    break
            if week is None:
                continue
            for year, c in year_cols.items():
                cases = _num(raw.iat[rr, c])
                if cases is not None and cases >= 0:
                    rows.append({"Año": year, "Semana": week, "Casos": cases})
        if rows:
            break
    if not rows:
        return pd.DataFrame(columns=["Año", "Semana", "Casos"])
    return pd.DataFrame(rows).drop_duplicates(["Año", "Semana"], keep="last")


def cumulative_at_cutoff(weekly: pd.DataFrame, cutoff_week: int) -> pd.DataFrame:
    work = weekly[pd.to_numeric(weekly["Semana"], errors="coerce").between(1, cutoff_week)].copy()
    return work.groupby("Año", as_index=False)["Casos"].sum().rename(columns={"Casos": f"Acumulado ≤ SE{cutoff_week}"})


def week_at_cutoff(weekly: pd.DataFrame, cutoff_week: int) -> pd.DataFrame:
    return weekly[weekly["Semana"].eq(int(cutoff_week))][["Año", "Casos"]].rename(columns={"Casos": f"Casos SE{cutoff_week}"}).copy()


def endemic_channel(weekly: pd.DataFrame, historical_years: list[int], current_year: int | None = None) -> pd.DataFrame:
    hist = weekly[weekly["Año"].isin(historical_years)]
    rows = []
    for week in range(1, 54):
        vals = pd.to_numeric(hist.loc[hist["Semana"].eq(week), "Casos"], errors="coerce").dropna().to_numpy(dtype=float)
        if vals.size:
            q1, med, q3 = np.quantile(vals, [0.25, 0.5, 0.75])
        else:
            q1 = med = q3 = np.nan
        rows.append({"Semana": week, "Q1": q1, "Mediana": med, "Q3": q3, "n_historico": len(vals)})
    out = pd.DataFrame(rows)
    if current_year is not None:
        cur = weekly[weekly["Año"].eq(int(current_year))][["Semana", "Casos"]].rename(columns={"Casos": "Actual"})
        out = out.merge(cur, on="Semana", how="left")
    return out


def compare_sinave_suive(sinave_weekly: pd.DataFrame, suive_weekly: pd.DataFrame, year: int, cutoff_week: int) -> pd.DataFrame:
    a = sinave_weekly[(sinave_weekly["Año"].eq(year)) & (sinave_weekly["Semana"].between(1, cutoff_week))][["Semana", "Casos"]].rename(columns={"Casos": "SINAVE"})
    b = suive_weekly[(suive_weekly["Año"].eq(year)) & (suive_weekly["Semana"].between(1, cutoff_week))][["Semana", "Casos"]].rename(columns={"Casos": "SUIVE"})
    out = pd.DataFrame({"Semana": range(1, cutoff_week + 1)}).merge(a, on="Semana", how="left").merge(b, on="Semana", how="left").fillna(0)
    out["Razón de registro SINAVE/SUIVE"] = np.where(out["SUIVE"].gt(0), out["SINAVE"] / out["SUIVE"], np.nan)
    return out
