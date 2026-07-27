"""Lector robusto del histórico SUIVE usado por POPIS.

El libro de canal endémico contiene varias tablas con los mismos años (casos,
incidencias, cuartiles). El lector anterior podía elegir la fila de incidencia
para el año en curso porque tenía más celdas no vacías que la fila de casos.
Este módulo identifica y prioriza la tabla de CASOS y recorta ceros futuros del
año más reciente.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import math
import re
import unicodedata

import numpy as np
import pandas as pd


def _norm(value: object) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", text.strip()).upper()


def _context(raw: pd.DataFrame, row: int, col: int) -> str:
    r0 = max(0, row - 5)
    c0 = max(0, col - 3)
    block = raw.iloc[r0:row + 1, c0:min(raw.shape[1], col + 8)]
    return " ".join(_norm(v) for v in block.to_numpy().ravel() if _norm(v))


def parse_suive_history(file_obj, filename: str, preferred_sheet: str = "SUIVE") -> pd.DataFrame:
    data = file_obj.read() if hasattr(file_obj, "read") else Path(file_obj).read_bytes()
    suffix = Path(filename).suffix.lower()
    engine = "openpyxl" if suffix in {".xlsx", ".xlsm"} else "xlrd"
    xl = pd.ExcelFile(BytesIO(data), engine=engine)

    # Coincidencia tolerante para nombres como 'SUIVE ', 'SUIVE-SUAVE', etc.
    sheet_map = {_norm(s): s for s in xl.sheet_names}
    preferred_key = _norm(preferred_sheet)
    sheet = sheet_map.get(preferred_key)
    if sheet is None:
        candidates_sheet = [s for s in xl.sheet_names if "SUIVE" in _norm(s) or "SUAVE" in _norm(s)]
        sheet = candidates_sheet[0] if candidates_sheet else xl.sheet_names[0]

    raw = pd.read_excel(BytesIO(data), sheet_name=sheet, header=None, engine=engine)
    candidates: list[dict] = []

    for r in range(len(raw)):
        row = raw.iloc[r]
        for c, value in enumerate(row):
            try:
                year = int(float(value))
            except Exception:
                continue
            if not 1990 <= year <= 2100:
                continue

            vals = pd.to_numeric(row.iloc[c + 1:c + 54], errors="coerce")
            plausible = vals.dropna()
            if len(plausible) < 4 or (plausible < 0).any():
                continue

            ctx = _context(raw, r, c)
            integer_ratio = float(np.isclose(plausible, np.round(plausible), atol=1e-8).mean())
            median = float(plausible.median()) if len(plausible) else 0.0
            maximum = float(plausible.max()) if len(plausible) else 0.0
            nonzero = int((plausible > 0).sum())

            # La señal de sección pesa más que el número de celdas llenas.
            section_bonus = 0.0
            if re.search(r"\bCASOS?\b", ctx):
                section_bonus += 6000.0
            if any(word in ctx for word in ["INCIDENCIA", "TASA", "CUARTIL", "QUARTIL", "MEDIANA", "ALARMA", "EPIDEMIA"]):
                section_bonus -= 6000.0

            # Los conteos SUIVE son enteros y, para el total estatal de EDA, de
            # escala mucho mayor que una tasa. Esto evita que 53 fórmulas de
            # incidencia ganen contra 26 semanas reales de casos en 2026.
            scale_score = math.log1p(max(median, 0.0)) * 180.0 + math.log1p(max(maximum, 0.0)) * 40.0
            integer_score = integer_ratio * 1800.0
            density_score = min(len(plausible), 53) * 3.0 + min(nonzero, 53) * 2.0
            small_rate_penalty = -1200.0 if median < 10 and maximum < 100 else 0.0
            score = section_bonus + scale_score + integer_score + density_score + small_rate_penalty

            candidates.append({
                "year": year,
                "row": r,
                "col": c,
                "vals": vals.reset_index(drop=True),
                "score": score,
                "context": ctx,
                "integer_ratio": integer_ratio,
                "median": median,
            })
            break

    if not candidates:
        raise ValueError("No se detectaron series semanales SUIVE con año y semanas en la hoja seleccionada.")

    selected: dict[int, dict] = {}
    for candidate in candidates:
        year = candidate["year"]
        if year not in selected or candidate["score"] > selected[year]["score"]:
            selected[year] = candidate

    latest_year = max(selected)
    records: list[dict] = []
    for year, candidate in sorted(selected.items()):
        vals = candidate["vals"].copy()

        # En el año en curso algunos libros tienen fórmulas que devuelven 0 en
        # semanas futuras. No deben interpretarse como semanas ya reportadas.
        if year == latest_year:
            nonnull = vals.dropna()
            positive_positions = [i for i, v in enumerate(vals.tolist()) if pd.notna(v) and float(v) > 0]
            if positive_positions:
                last_real = max(positive_positions)
                vals.iloc[last_real + 1:] = np.nan

        for se, value in enumerate(vals, start=1):
            if pd.notna(value):
                records.append({
                    "Año": int(year),
                    "SE": int(se),
                    "Casos": float(value),
                    "_suive_row": int(candidate["row"] + 1),
                    "_suive_score": float(candidate["score"]),
                })

    out = pd.DataFrame(records)
    if out.empty:
        raise ValueError("La tabla de casos SUIVE detectada quedó vacía.")

    # Validación defensiva: no aceptar una serie estatal que parezca una tasa.
    latest = out[out["Año"].eq(latest_year)]
    if not latest.empty and latest["Casos"].median() < 10 and latest["Casos"].max() < 100:
        raise ValueError(
            f"La serie detectada para {latest_year} parece una tasa/incidencia, no conteos de casos. "
            "Revise la estructura de la hoja SUIVE."
        )

    return out
