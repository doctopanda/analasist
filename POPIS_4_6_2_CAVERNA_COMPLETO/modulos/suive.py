from __future__ import annotations

from pathlib import Path

import pandas as pd

from .io_utils import first_existing, norm_key, read_excel_raw, read_table


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


def _number(value) -> float | None:
    parsed = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return None if pd.isna(parsed) else float(parsed)


def _header_candidates(raw: pd.DataFrame) -> list[tuple[int, int, int]]:
    """Localiza bloques Año + SE1..SE53 y los puntúa.

    El libro institucional contiene varias matrices con los mismos años: casos brutos,
    incidencia y tablas derivadas. El bloque de casos brutos se distingue porque su
    encabezado incluye POBLACIÓN después de las 53 semanas.
    """
    candidates: list[tuple[int, int, int]] = []
    for r in range(len(raw)):
        values = raw.iloc[r].tolist()
        normalized = [norm_key(value) for value in values]
        for c, label in enumerate(normalized):
            if not label or not (label == "ANO" or label.startswith("ANO ") or "ANO SE" in label):
                continue
            right_raw = values[c + 1:c + 61]
            right_norm = normalized[c + 1:c + 61]
            week_labels = set()
            for value in right_raw:
                numeric = _number(value)
                if numeric is not None and 1 <= numeric <= 53 and float(numeric).is_integer():
                    week_labels.add(int(numeric))
            if len(week_labels) < 20:
                continue
            has_population = any("POBLACION" in text for text in right_norm)
            # POBLACIÓN es la firma más fuerte del bloque de casos crudos.
            score = (1000 if has_population else 0) + len(week_labels)
            candidates.append((score, r, c))
    # Mayor puntuación primero; si empatan, conservar el bloque superior de la hoja.
    return sorted(candidates, key=lambda item: (-item[0], item[1], item[2]))


def _read_year_block(raw: pd.DataFrame, header_row: int, year_col: int) -> pd.DataFrame:
    rows: list[dict[str, float | int]] = []
    started = False
    blank_run = 0
    for r in range(header_row + 1, min(len(raw), header_row + 40)):
        year_value = _number(raw.iat[r, year_col]) if year_col < raw.shape[1] else None
        if year_value is None or not 2000 <= year_value <= 2100 or not float(year_value).is_integer():
            if started:
                blank_run += 1
                if blank_run >= 2:
                    break
            continue
        started = True
        blank_run = 0
        year = int(year_value)
        weekly = pd.to_numeric(
            pd.Series(raw.iloc[r, year_col + 1:year_col + 54].tolist()),
            errors="coerce",
        )
        if weekly.notna().sum() == 0:
            continue
        for week, cases in enumerate(weekly, start=1):
            if pd.notna(cases):
                rows.append({"Año": year, "Semana": week, "Casos": float(cases)})
    if not rows:
        return pd.DataFrame(columns=["Año", "Semana", "Casos"])
    return pd.DataFrame(rows).sort_values(["Año", "Semana"]).reset_index(drop=True)


def _scan_wide(raw: pd.DataFrame) -> pd.DataFrame:
    """Reconoce el bloque semanal correcto sin confundirlo con incidencia/canales."""
    for _, header_row, year_col in _header_candidates(raw):
        result = _read_year_block(raw, header_row, year_col)
        if not result.empty and result["Año"].nunique() >= 2:
            return result

    # Respaldo para libros simples sin encabezado institucional.
    rows: list[dict[str, float | int]] = []
    for r in range(len(raw)):
        values = raw.iloc[r].tolist()
        for c, value in enumerate(values):
            year = _number(value)
            if year is None or not 2000 <= year <= 2100 or not float(year).is_integer():
                continue
            weekly = pd.to_numeric(pd.Series(values[c + 1:c + 54]), errors="coerce")
            if weekly.notna().sum() < 20:
                continue
            for week, cases in enumerate(weekly, start=1):
                if pd.notna(cases):
                    rows.append({"Año": int(year), "Semana": week, "Casos": float(cases)})
            break
    if not rows:
        return pd.DataFrame(columns=["Año", "Semana", "Casos"])
    # El primer bloque suele ser la tabla cruda; no permitir que matrices posteriores
    # de incidencia reemplacen los conteos semanales.
    return (
        pd.DataFrame(rows)
        .drop_duplicates(["Año", "Semana"], keep="first")
        .sort_values(["Año", "Semana"])
        .reset_index(drop=True)
    )


def load_suive(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    try:
        df = read_table(path)
        standard = _long_from_standard(df)
        if standard is not None and not standard.empty:
            return standard
    except Exception:
        pass

    if path.suffix.lower() in {".xlsx", ".xls"}:
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
    # Una semana no presente es dato ausente, no cero por definición.
    return cumulative.merge(week, on="Año", how="left")


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
    # Mantiene NaN donde el libro no trae observación. No inventa ceros.
    return suive.pivot_table(index="Año", columns="Semana", values="Casos", aggfunc="sum").sort_index()
