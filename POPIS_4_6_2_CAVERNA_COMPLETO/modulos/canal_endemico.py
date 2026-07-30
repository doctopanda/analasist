from __future__ import annotations

import pandas as pd

from .sinave import observed_cutoff_week


def build_endemic_channel(series: pd.DataFrame, current_year: int | None = None,
                          historical_years: list[int] | None = None,
                          exclude_years: list[int] | None = None) -> tuple[pd.DataFrame, list[int]]:
    """Construye canal cuartílico semanal con Q1, mediana y Q3.

    `series` debe tener Año, Semana, Casos. El año actual no entra al histórico salvo que
    se solicite explícitamente mediante historical_years. Los faltantes permanecen como
    NaN y nunca se reinterpretan automáticamente como cero.
    """
    required = {"Año", "Semana", "Casos"}
    if not required.issubset(series.columns):
        raise ValueError("El canal requiere columnas Año, Semana y Casos.")
    work = series.copy()
    work["Año"] = pd.to_numeric(work["Año"], errors="coerce").astype("Int64")
    work["Semana"] = pd.to_numeric(work["Semana"], errors="coerce").astype("Int64")
    work["Casos"] = pd.to_numeric(work["Casos"], errors="coerce")
    work = work.dropna(subset=["Año", "Semana", "Casos"])
    work = work[work["Semana"].between(1, 53)]
    if current_year is None and not work.empty:
        current_year = int(work["Año"].max())
    exclude = set(exclude_years or [])
    if historical_years is None:
        historical_years = sorted(int(y) for y in work["Año"].unique() if int(y) != current_year and int(y) not in exclude)
    else:
        historical_years = sorted(int(y) for y in historical_years if int(y) not in exclude)
    hist = work[work["Año"].isin(historical_years)].copy()
    if hist.empty:
        return pd.DataFrame(columns=["Semana", "Q1", "Mediana", "Q3", "Años históricos"]), historical_years
    channel = hist.groupby("Semana")["Casos"].agg(
        Q1=lambda s: s.quantile(0.25, interpolation="linear"),
        Mediana=lambda s: s.quantile(0.50, interpolation="linear"),
        Q3=lambda s: s.quantile(0.75, interpolation="linear"),
        **{"Años históricos": "count"},
    ).reset_index()
    full = pd.DataFrame({"Semana": range(1, 54)})
    channel = full.merge(channel, on="Semana", how="left")
    return channel, historical_years


def attach_current(channel: pd.DataFrame, series: pd.DataFrame, year: int, cutoff_week: int | None = None) -> pd.DataFrame:
    """Une el año actual sin rellenar con cero las semanas posteriores al corte."""
    current = series[pd.to_numeric(series["Año"], errors="coerce").eq(year)].copy()
    current["Semana"] = pd.to_numeric(current["Semana"], errors="coerce")
    if cutoff_week is not None:
        current = current[current["Semana"].between(1, cutoff_week)]
    current = current.groupby("Semana", as_index=False)["Casos"].sum().rename(columns={"Casos": f"Casos {year}"})
    return channel.merge(current, on="Semana", how="left")


def pathogen_weekly_series(base: pd.DataFrame, pathogen: str) -> pd.DataFrame:
    """Serie de detecciones por patógeno limitada a la cobertura real de SINAVE.

    El horizonte se toma de la base completa, no de la última detección del patógeno.
    Así puede haber ceros reales dentro del periodo cubierto, pero no una cola de ceros
    después de la última semana con información disponible.
    """
    if base.empty or pathogen not in base.columns:
        return pd.DataFrame(columns=["Año", "Semana", "Casos"])
    work = base.copy()
    work["Año"] = pd.to_numeric(work["Año"], errors="coerce").astype("Int64")
    work["Semana"] = pd.to_numeric(work.get("SemanaInicio"), errors="coerce").astype("Int64")
    work["Casos"] = pd.to_numeric(work[pathogen], errors="coerce").fillna(0)
    work = work[work["Semana"].between(1, 53) & work["Año"].notna()]
    if work.empty:
        return pd.DataFrame(columns=["Año", "Semana", "Casos"])
    agg = work.groupby(["Año", "Semana"], as_index=False)["Casos"].sum()
    frames: list[pd.DataFrame] = []
    for year in sorted(int(y) for y in work["Año"].dropna().unique()):
        cutoff = observed_cutoff_week(base, year)
        if cutoff is None:
            continue
        skeleton = pd.DataFrame({"Año": year, "Semana": range(1, cutoff + 1)})
        year_agg = agg[agg["Año"].eq(year)]
        frames.append(skeleton.merge(year_agg, on=["Año", "Semana"], how="left").fillna({"Casos": 0}))
    if not frames:
        return pd.DataFrame(columns=["Año", "Semana", "Casos"])
    return pd.concat(frames, ignore_index=True)


def classify_zone(value: float | int | None, q1: float | None, median: float | None, q3: float | None) -> str:
    if value is None or pd.isna(value) or q1 is None or pd.isna(q1):
        return "Sin clasificación"
    if value < q1:
        return "Éxito"
    if value < median:
        return "Seguridad"
    if value <= q3:
        return "Alarma"
    return "Epidemia"
