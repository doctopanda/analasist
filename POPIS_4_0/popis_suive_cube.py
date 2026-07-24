"""Lector multiformato para fuentes SUIVE de POPIS 4.5.

Acepta:
1) el libro histórico/canal endémico usado previamente por POPIS;
2) tablas largas con Año + Semana + Casos;
3) matrices con semanas en filas y años en columnas (frecuentes en cubos/pivotes);
4) matrices con años en filas y semanas en columnas mediante el lector legado.

El objetivo es leer los VALORES YA CALCULADOS del XLSX. La actualización de
conexiones externas/Power Query/OLAP pertenece a Excel y se trata por separado.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re
import unicodedata
from typing import Iterable

import numpy as np
import pandas as pd

from popis_suive_fix import parse_suive_history as parse_legacy_channel

YEAR_ALIASES = {"ANO", "ANIO", "YEAR", "EJERCICIO"}
WEEK_ALIASES = {"SE", "SEM", "SEMANA", "SEMANA EPIDEMIOLOGICA", "SEM EPIDEMIOLOGICA", "SEMANA EPIDEMIOL"}
CASE_ALIASES = {"CASOS", "CASO", "CASOS NUEVOS", "TOTAL CASOS", "NUM CASOS", "NUMERO CASOS", "FRECUENCIA", "CUENTA", "COUNT"}
STATE_ALIASES = {"ENTIDAD", "ESTADO", "ENTIDAD FEDERATIVA", "EDO", "NOM ENT", "NOMBRE ENTIDAD"}


def _norm(v: object) -> str:
    text = "" if v is None else str(v)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[_\-]+", " ", text.upper().strip())
    return re.sub(r"\s+", " ", text)


def _as_year(v: object):
    try:
        n = int(float(v))
        return n if 1990 <= n <= 2100 else None
    except Exception:
        m = re.search(r"\b(19\d{2}|20\d{2}|2100)\b", _norm(v))
        return int(m.group(1)) if m else None


def _as_week(v: object):
    try:
        n = int(float(v))
        return n if 1 <= n <= 53 else None
    except Exception:
        m = re.search(r"(?:SE|SEMANA|SEM)?\s*0?([1-9]|[1-4]\d|5[0-3])\b", _norm(v))
        return int(m.group(1)) if m else None


def _clean_series(df: pd.DataFrame) -> pd.DataFrame:
    out = df[["Año", "SE", "Casos"]].copy()
    out["Año"] = pd.to_numeric(out["Año"], errors="coerce")
    out["SE"] = pd.to_numeric(out["SE"], errors="coerce")
    out["Casos"] = pd.to_numeric(out["Casos"], errors="coerce")
    out = out.dropna(subset=["Año", "SE", "Casos"])
    out = out[out["Año"].between(1990, 2100) & out["SE"].between(1, 53) & out["Casos"].ge(0)]
    if out.empty:
        return out
    out["Año"] = out["Año"].astype(int)
    out["SE"] = out["SE"].astype(int)
    # Un cubo puede traer más de una fila aditiva por semana (p. ej. municipios).
    out = out.groupby(["Año", "SE"], as_index=False)["Casos"].sum()
    return out.sort_values(["Año", "SE"]).reset_index(drop=True)


def _score(df: pd.DataFrame, explicit_cases: bool = False, source_bonus: float = 0) -> float:
    if df.empty:
        return -1e12
    years = sorted(df["Año"].unique())
    latest = df[df["Año"].eq(max(years))]
    positive = latest[latest["Casos"].gt(0)]
    vals = df["Casos"]
    integer_ratio = float(np.isclose(vals, np.round(vals), atol=1e-8).mean()) if len(vals) else 0
    med = float(vals[vals.gt(0)].median()) if vals.gt(0).any() else 0
    score = len(years) * 120 + len(df) * 1.5 + len(positive) * 12 + integer_ratio * 900 + source_bonus
    if explicit_cases:
        score += 2200
    if max(years) >= 2025:
        score += 500
    if positive.empty:
        score -= 6000
    if med < 1:
        score -= 1200
    return score


def _find_header_alias(headers: list[str], aliases: set[str]) -> int | None:
    for i, h in enumerate(headers):
        if h in aliases:
            return i
    # tolerancia con encabezados compuestos, evitando coincidencias demasiado vagas
    for i, h in enumerate(headers):
        if any(len(a) >= 4 and a in h for a in aliases):
            return i
    return None


def _long_candidates(raw: pd.DataFrame, sheet: str) -> Iterable[tuple[float, pd.DataFrame, dict]]:
    max_header = min(50, len(raw))
    for hr in range(max_header):
        headers = [_norm(v) for v in raw.iloc[hr].tolist()]
        iy = _find_header_alias(headers, YEAR_ALIASES)
        iw = _find_header_alias(headers, WEEK_ALIASES)
        ic = _find_header_alias(headers, CASE_ALIASES)
        if iy is None or iw is None or ic is None:
            continue
        body = raw.iloc[hr + 1:, :].copy()
        year = body.iloc[:, iy].map(_as_year)
        week = body.iloc[:, iw].map(_as_week)
        cases = pd.to_numeric(body.iloc[:, ic], errors="coerce")

        # Si existe una dimensión Entidad/Estado, restringir a Sonora cuando la
        # tabla contenga múltiples entidades. Código 26 también se reconoce.
        istate = _find_header_alias(headers, STATE_ALIASES)
        keep = pd.Series(True, index=body.index)
        if istate is not None:
            state_raw = body.iloc[:, istate]
            normalized = state_raw.map(_norm)
            has_sonora = normalized.str.contains(r"\bSONORA\b", regex=True, na=False) | pd.to_numeric(state_raw, errors="coerce").eq(26)
            if has_sonora.any():
                keep &= has_sonora

        cand = _clean_series(pd.DataFrame({"Año": year[keep], "SE": week[keep], "Casos": cases[keep]}))
        if not cand.empty:
            meta = {"sheet": sheet, "layout": "tabla larga Año-Semana-Casos", "header_row": hr + 1}
            yield _score(cand, explicit_cases=True, source_bonus=500), cand, meta


def _year_columns_candidates(raw: pd.DataFrame, sheet: str) -> Iterable[tuple[float, pd.DataFrame, dict]]:
    # Detecta pivotes/matrices: una fila contiene varios años y las filas
    # siguientes representan SE1..SE53.
    for hr in range(min(60, len(raw))):
        row = raw.iloc[hr]
        year_cols = [(i, _as_year(v)) for i, v in enumerate(row)]
        year_cols = [(i, y) for i, y in year_cols if y is not None]
        distinct = sorted({y for _, y in year_cols})
        if len(distinct) < 3:
            continue
        first_year_col = min(i for i, _ in year_cols)
        # La columna de semana suele estar antes del primer año. Probar hasta 5 columnas.
        week_cols = list(range(max(0, first_year_col - 5), first_year_col))
        for wc in reversed(week_cols):
            records = []
            valid_weeks = 0
            for r in range(hr + 1, min(len(raw), hr + 70)):
                w = _as_week(raw.iat[r, wc])
                if w is None:
                    continue
                valid_weeks += 1
                for c, y in year_cols:
                    val = pd.to_numeric(pd.Series([raw.iat[r, c]]), errors="coerce").iloc[0]
                    if pd.notna(val) and float(val) >= 0:
                        records.append({"Año": y, "SE": w, "Casos": float(val)})
            if valid_weeks < 4:
                continue
            cand = _clean_series(pd.DataFrame(records))
            if not cand.empty:
                ctx = " ".join(_norm(v) for v in raw.iloc[max(0,hr-4):hr+1].to_numpy().ravel())
                explicit = "CASO" in ctx
                meta = {"sheet": sheet, "layout": "matriz/pivote semanas×años", "header_row": hr + 1, "week_column": wc + 1}
                yield _score(cand, explicit_cases=explicit, source_bonus=900), cand, meta


def parse_suive_auto(file_obj, filename: str) -> pd.DataFrame:
    payload = file_obj.read() if hasattr(file_obj, "read") else Path(file_obj).read_bytes()
    suffix = Path(filename).suffix.lower()
    engine = "openpyxl" if suffix in {".xlsx", ".xlsm"} else "xlrd"
    candidates: list[tuple[float, pd.DataFrame, dict]] = []

    # Estrategias de cubo/pivote.
    try:
        xl = pd.ExcelFile(BytesIO(payload), engine=engine)
        for sheet in xl.sheet_names:
            try:
                raw = pd.read_excel(BytesIO(payload), sheet_name=sheet, header=None, engine=engine)
            except Exception:
                continue
            sheet_bonus = 700 if any(k in _norm(sheet) for k in ["SUIVE", "CUBO", "CANAL", "RIO SONORA", "EDA"]) else 0
            for score, df, meta in _long_candidates(raw, sheet):
                candidates.append((score + sheet_bonus, df, meta))
            for score, df, meta in _year_columns_candidates(raw, sheet):
                candidates.append((score + sheet_bonus, df, meta))
    except Exception:
        pass

    # Estrategia histórica/canal conocida por POPIS.
    try:
        legacy = parse_legacy_channel(BytesIO(payload), filename)
        legacy = _clean_series(legacy)
        if not legacy.empty:
            candidates.append((_score(legacy, explicit_cases=True, source_bonus=1000), legacy, {"sheet": "auto", "layout": "canal/histórico años×semanas"}))
    except Exception:
        pass

    if not candidates:
        raise ValueError(
            "No pude identificar una serie SUIVE. POPIS buscó tabla larga Año-Semana-Casos, "
            "matriz semanas×años y el formato histórico del canal endémico."
        )

    score, out, meta = max(candidates, key=lambda x: x[0])
    years = sorted(out["Año"].unique())
    latest_year = max(years)
    latest = out[out["Año"].eq(latest_year)].copy()
    positive = latest[latest["Casos"].gt(0)]
    if positive.empty:
        raise ValueError(f"La mejor serie detectada termina en {latest_year}, pero no contiene casos positivos.")

    # Ceros posteriores a la última semana positiva suelen ser fórmulas futuras.
    last_real = int(positive["SE"].max())
    out = out[~(out["Año"].eq(latest_year) & out["SE"].gt(last_real) & out["Casos"].eq(0))].copy()
    out.attrs.update({
        "popis_source_type": "Cubo/pivote SUIVE" if "matriz" in meta["layout"] or "tabla larga" in meta["layout"] else "Canal histórico SUIVE",
        "popis_sheet": meta.get("sheet", ""),
        "popis_layout": meta.get("layout", ""),
        "popis_score": float(score),
    })
    return out.reset_index(drop=True)
