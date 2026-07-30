from __future__ import annotations

import numpy as np
import pandas as pd

from .io_utils import Assets, infer_cutoff_week, infer_year, read_table
from .redve import death_metrics

PATHOGENS = [
    "Salmonella", "Shigella", "E. coli patógena", "Rotavirus",
    "V. cholerae no O1", "V. parahaemolyticus", "Norovirus", "Astrovirus",
]


def _series(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series([""] * len(df), index=df.index, dtype="object")
    return df[col].fillna("").astype(str).str.strip()


def _positive(s: pd.Series) -> pd.Series:
    return s.str.casefold().str.startswith("positivo")


def _bool_series(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series(False, index=df.index, dtype=bool)
    return df[column].fillna(False).astype(bool)


def normalize_sinave(df: pd.DataFrame, source_name: str = "") -> pd.DataFrame:
    out = df.copy()
    year = infer_year(out, source_name)
    out["Año"] = year
    if "SemanaInicio" in out.columns:
        out["SemanaInicio"] = pd.to_numeric(out["SemanaInicio"], errors="coerce").astype("Int64")
    if "Sem_Notif" in out.columns:
        out["Sem_Notif"] = pd.to_numeric(out["Sem_Notif"], errors="coerce").astype("Int64")
    if "Fecha_Inicio" in out.columns:
        out["Fecha_Inicio_dt"] = pd.to_datetime(out["Fecha_Inicio"], dayfirst=True, errors="coerce")
    if "Fec_captura" in out.columns:
        out["Fec_captura_dt"] = pd.to_datetime(out["Fec_captura"], dayfirst=True, errors="coerce")
    if "FecDefuncion" in out.columns:
        out["FecDefuncion_dt"] = pd.to_datetime(out["FecDefuncion"], dayfirst=True, errors="coerce")

    flags: dict[str, pd.Series] = {}
    flags["Salmonella"] = _positive(_series(out, "Salmonella"))
    flags["Shigella"] = _positive(_series(out, "Shigella"))
    flags["Rotavirus"] = _positive(_series(out, "Rotavirus")) | _positive(_series(out, "Rotavirus_InDRE"))
    flags["V. parahaemolyticus"] = _positive(_series(out, "VibrioParahaemolyticus"))
    vibrio = _positive(_series(out, "VibrioCholerae"))
    serogroup = _series(out, "SerogrupoVibrioCholerae").str.casefold()
    flags["V. cholerae no O1"] = vibrio & serogroup.str.contains("no o1", regex=False)
    ecoli = _series(out, "Patotipo_EColi_InDRE")
    flags["E. coli patógena"] = ecoli.ne("") & ~ecoli.str.casefold().str.contains("no pat", regex=False)
    other = _series(out, "OtroVirus_InDRE").str.casefold()
    flags["Norovirus"] = other.str.contains("norovirus", regex=False)
    flags["Astrovirus"] = other.str.contains("astrovirus", regex=False)

    for name in PATHOGENS:
        out[name] = flags[name].astype(int)
    out["Patógenos identificados"] = [
        " | ".join(name for name in PATHOGENS if bool(flags[name].loc[idx]))
        for idx in out.index
    ]
    out["Patógeno identificado"] = out[PATHOGENS].sum(axis=1).gt(0)

    diag = _series(out, "Diag_Final").str.upper()
    state = pd.Series("Otro diagnóstico", index=out.index, dtype="object")
    state[diag.eq("")] = "Pendiente / sin diagnóstico final"
    state[diag.str.startswith("NEGATIVO")] = "Sin patógeno identificado"
    state[diag.str.contains("RECHAZ", regex=False)] = "Muestra rechazada / sin diagnóstico"
    state[out["Patógeno identificado"]] = "Patógeno identificado"
    out["Estado del resultado"] = state
    out["Archivo de origen"] = source_name
    return out


def load_bundle(assets: Assets) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for year, path in sorted(assets.sinave_by_year.items()):
        df = normalize_sinave(read_table(path), path.name)
        if df["Año"].isna().all():
            df["Año"] = year
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    base = pd.concat(frames, ignore_index=True, sort=False)
    sort_cols = [c for c in ["Año", "Fecha_Inicio_dt", "Folio"] if c in base.columns]
    if sort_cols:
        base = base.sort_values(sort_cols, na_position="last")
    return base.reset_index(drop=True)


def observed_cutoff_week(base: pd.DataFrame, year: int) -> int | None:
    if base.empty or "Año" not in base.columns:
        return None
    subset = base[pd.to_numeric(base["Año"], errors="coerce").eq(int(year))]
    if subset.empty:
        return None
    return infer_cutoff_week(subset, year=int(year))


def cutoff_base(base: pd.DataFrame, year: int, cutoff_week: int, exact_week: bool = False) -> pd.DataFrame:
    if base.empty:
        return base.copy()
    weeks = pd.to_numeric(base.get("SemanaInicio"), errors="coerce")
    mask = pd.to_numeric(base["Año"], errors="coerce").eq(int(year))
    if exact_week:
        mask &= weeks.eq(int(cutoff_week))
    else:
        mask &= weeks.between(1, int(cutoff_week), inclusive="both")
    return base.loc[mask].copy()


def summary(base: pd.DataFrame, year: int, cutoff_week: int) -> dict[str, int | float]:
    cumulative = cutoff_base(base, year, cutoff_week)
    week = cutoff_base(base, year, cutoff_week, exact_week=True)
    deaths = death_metrics(cumulative)
    return {
        "casos_acumulados": len(cumulative),
        "casos_semana": len(week),
        "positivos_acumulados": int(cumulative.get("Patógeno identificado", pd.Series(dtype=bool)).sum()),
        "positivos_semana": int(week.get("Patógeno identificado", pd.Series(dtype=bool)).sum()),
        **deaths,
        # Compatibilidad con páginas/exportaciones previas.
        "defunciones_registradas": deaths["defunciones_integradas"],
    }


def pathogen_table(base: pd.DataFrame, year: int, cutoff_week: int, exact_week: bool = False) -> pd.DataFrame:
    frame = cutoff_base(base, year, cutoff_week, exact_week)
    rows = []
    denominator = len(frame)
    for name in PATHOGENS:
        n = int(pd.to_numeric(frame.get(name, 0), errors="coerce").fillna(0).sum()) if not frame.empty else 0
        rows.append({"Patógeno": name, "Detecciones": n, "% de casos": (n / denominator * 100) if denominator else 0.0})
    return pd.DataFrame(rows).sort_values(["Detecciones", "Patógeno"], ascending=[False, True]).reset_index(drop=True)


def weekly_series(base: pd.DataFrame, years: list[int] | None = None) -> pd.DataFrame:
    """Cero solo dentro del periodo observado; semanas futuras permanecen ausentes."""
    if base.empty:
        return pd.DataFrame(columns=["Año", "Semana", "Casos"])
    work = base.copy()
    work["Año"] = pd.to_numeric(work["Año"], errors="coerce").astype("Int64")
    work["Semana"] = pd.to_numeric(work.get("SemanaInicio"), errors="coerce").astype("Int64")
    work = work[work["Semana"].between(1, 53) & work["Año"].notna()]
    if years:
        work = work[work["Año"].isin(years)]
    if work.empty:
        return pd.DataFrame(columns=["Año", "Semana", "Casos"])

    agg = work.groupby(["Año", "Semana"], as_index=False).size().rename(columns={"size": "Casos"})
    frames: list[pd.DataFrame] = []
    for year in sorted(int(y) for y in work["Año"].dropna().unique()):
        horizon = observed_cutoff_week(base, year)
        if horizon is None:
            continue
        skeleton = pd.DataFrame({"Año": year, "Semana": range(1, horizon + 1)})
        frames.append(skeleton.merge(agg[agg["Año"].eq(year)], on=["Año", "Semana"], how="left").fillna({"Casos": 0}))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=["Año", "Semana", "Casos"])


def comparison_at_week(base: pd.DataFrame, cutoff_week: int) -> pd.DataFrame:
    """Compara semana exacta y acumulado por año sin convertir falta de cobertura en cero."""
    years = sorted(pd.to_numeric(base.get("Año"), errors="coerce").dropna().astype(int).unique()) if not base.empty else []
    rows: list[dict[str, object]] = []
    week_col = f"Casos SE{cutoff_week}"
    cumulative_col = f"Acumulado ≤ SE{cutoff_week}"
    for year in years:
        horizon = observed_cutoff_week(base, year)
        covered = horizon is not None and horizon >= cutoff_week
        if covered:
            exact = cutoff_base(base, year, cutoff_week, exact_week=True)
            cumulative = cutoff_base(base, year, cutoff_week, exact_week=False)
            row: dict[str, object] = {
                "Año": year,
                "Cobertura": f"Sí · hasta SE{horizon}",
                week_col: len(exact),
                cumulative_col: len(cumulative),
                "Positivos semana": int(exact.get("Patógeno identificado", pd.Series(dtype=bool)).sum()),
                "Positivos acumulados": int(cumulative.get("Patógeno identificado", pd.Series(dtype=bool)).sum()),
            }
            for name in PATHOGENS:
                row[name] = int(pd.to_numeric(exact.get(name, 0), errors="coerce").fillna(0).sum()) if not exact.empty else 0
        else:
            row = {
                "Año": year,
                "Cobertura": f"No · hasta SE{horizon}" if horizon else "No disponible",
                week_col: np.nan,
                cumulative_col: np.nan,
                "Positivos semana": np.nan,
                "Positivos acumulados": np.nan,
            }
            for name in PATHOGENS:
                row[name] = np.nan
        rows.append(row)

    result = pd.DataFrame(rows)
    if result.empty:
        return result
    result[f"Variación SE{cutoff_week} vs año previo %"] = pd.to_numeric(result[week_col], errors="coerce").pct_change(fill_method=None) * 100
    result[f"Variación acumulada vs año previo %"] = pd.to_numeric(result[cumulative_col], errors="coerce").pct_change(fill_method=None) * 100
    return result


def death_comparison_by_year(base: pd.DataFrame, cutoff_week: int) -> pd.DataFrame:
    years = sorted(pd.to_numeric(base.get("Año"), errors="coerce").dropna().astype(int).unique()) if not base.empty else []
    rows: list[dict[str, object]] = []
    for year in years:
        horizon = observed_cutoff_week(base, year)
        if horizon is None or horizon < cutoff_week:
            rows.append({
                "Año": year, "Cobertura": f"No · hasta SE{horizon}" if horizon else "No disponible",
                "SINAVE": np.nan, "REDVE recuperadas": np.nan, "Integradas": np.nan,
                "EDA dictaminadas REDVE": np.nan, "EDA pendientes REDVE": np.nan,
            })
            continue
        metrics = death_metrics(cutoff_base(base, year, cutoff_week))
        rows.append({
            "Año": year,
            "Cobertura": f"Sí · hasta SE{horizon}",
            "SINAVE": metrics["defunciones_sinave"],
            "REDVE recuperadas": metrics["defunciones_redve_recuperadas"],
            "Integradas": metrics["defunciones_integradas"],
            "EDA dictaminadas REDVE": metrics["muertes_eda_dictaminadas_redve"],
            "EDA pendientes REDVE": metrics["muertes_eda_pendientes_redve"],
        })
    return pd.DataFrame(rows)


def mortality_registered(base: pd.DataFrame, cutoff_week: int | None = None) -> pd.DataFrame:
    """Serie de defunciones integradas, con desglose SINAVE y REDVE."""
    if base.empty:
        return pd.DataFrame(columns=["Año", "SINAVE", "REDVE recuperadas", "Defunciones integradas"])
    years = sorted(pd.to_numeric(base.get("Año"), errors="coerce").dropna().astype(int).unique())
    rows = []
    for year in years:
        frame = cutoff_base(base, year, cutoff_week or 53)
        metrics = death_metrics(frame)
        rows.append({
            "Año": year,
            "SINAVE": metrics["defunciones_sinave"],
            "REDVE recuperadas": metrics["defunciones_redve_recuperadas"],
            "Defunciones integradas": metrics["defunciones_integradas"],
            "EDA dictaminadas REDVE": metrics["muertes_eda_dictaminadas_redve"],
            "EDA pendientes REDVE": metrics["muertes_eda_pendientes_redve"],
        })
    return pd.DataFrame(rows)
