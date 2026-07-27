"""Motor demográfico municipal para POPIS.

Diseñado para archivos CONAPO/proyecciones municipales en formato LONG con
municipio, año, sexo, grupo quinquenal y población. Tolera variantes de nombres
de columnas y también libros con varias hojas / encabezado desplazado.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re
import unicodedata

import numpy as np
import pandas as pd


def _norm(value: object) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", text.strip()).upper()


def _first(df: pd.DataFrame, aliases: list[str]):
    cols = {_norm(c): c for c in df.columns}
    for alias in aliases:
        if _norm(alias) in cols:
            return cols[_norm(alias)]
    return None


def _sex(value: object) -> str:
    x = _norm(value)
    if x in {"H", "HOMBRE", "HOMBRES", "MASCULINO", "MASC", "1"}:
        return "Hombres"
    if x in {"M", "MUJER", "MUJERES", "FEMENINO", "FEM", "2"}:
        return "Mujeres"
    if x in {"TOTAL", "AMBOS", "AMBAS", "AMBOS SEXOS", "0"}:
        return "Total"
    return str(value).strip() if value is not None else ""


def _age_group(value: object) -> str:
    x = _norm(value)
    if not x:
        return ""
    if x in {"TOTAL", "TODAS", "TODOS"}:
        return "Total"
    # 00-04, 0_4, 00 A 04, 0-4 AÑOS, etc.
    nums = [int(n) for n in re.findall(r"\d+", x)]
    if len(nums) >= 2:
        a, b = nums[0], nums[1]
        if a <= 120 and b <= 120:
            return f"{a}-{b}"
    if nums:
        a = nums[0]
        if any(token in x for token in ["MAS", "+", "Y MAS", "O MAS"]):
            return f"{a}+"
        if a >= 85:
            return f"{a}+"
    return str(value).strip()


def _municipality_key(value: object) -> str:
    x = _norm(value)
    x = re.sub(r"\s+(SON|SONORA)$", "", x).strip()
    aliases = {
        "COLORADA LA": "LA COLORADA",
        "HEROICA NOGALES": "NOGALES",
        "HEROICA CABORCA": "CABORCA",
        "BENITO JUAREZ SON": "BENITO JUAREZ",
        "ROSARIO SON": "ROSARIO",
        "ROSARIO TESOPACO": "ROSARIO",
        "PLUTARCO ELIAS CALLES": "GENERAL PLUTARCO ELIAS CALLES",
    }
    return aliases.get(x, x)


def _find_header(raw: pd.DataFrame) -> int | None:
    """Busca una fila con señales de municipio/año/sexo/edad/población."""
    signals = ["MUN", "MUNICIPIO", "ANO", "AÑO", "SEXO", "EDAD", "POB"]
    best = None
    best_score = -1
    for r in range(min(len(raw), 30)):
        values = {_norm(v) for v in raw.iloc[r].tolist() if _norm(v)}
        joined = " | ".join(values)
        score = sum(any(sig in item for item in values) for sig in signals)
        if "MUN" in joined and ("POB" in joined or "POBLACION" in joined):
            score += 3
        if score > best_score:
            best_score, best = score, r
    return best if best_score >= 4 else None


def _normalize_frame(df: pd.DataFrame, source: str = "") -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    mcol = _first(df, ["MUN", "MUNICIPIO", "NOM_MUN", "NOM_MUNICIPIO", "NOMBRE_MUNICIPIO"])
    ycol = _first(df, ["AÑO", "ANO", "YEAR"])
    scol = _first(df, ["SEXO", "SEX"])
    acol = _first(df, ["EDAD_QUIN", "EDAD QUIN", "EDAD_QUINQUENAL", "GRUPO_EDAD", "EDAD"])
    pcol = _first(df, ["POB", "POBLACION", "POBLACIÓN", "POB_TOTAL"])
    ccol = _first(df, ["CVE_GEO", "CLAVE", "CVE", "CVE_MUN", "CVEGEO"])

    if not all([mcol, ycol, scol, acol, pcol]):
        raise ValueError(
            "No se reconoció el formato demográfico LONG. Se requieren municipio, año, sexo, grupo de edad y población."
        )

    out = pd.DataFrame({
        "Municipio": df[mcol].astype(str).str.strip(),
        "Año": pd.to_numeric(df[ycol], errors="coerce"),
        "Sexo": df[scol].map(_sex),
        "Grupo edad": df[acol].map(_age_group),
        "Población": pd.to_numeric(df[pcol], errors="coerce"),
        "CVE": df[ccol].astype(str).str.strip() if ccol else "",
    })
    out["Municipio key"] = out["Municipio"].map(_municipality_key)
    out["_source"] = source
    out = out[
        out["Año"].notna()
        & out["Población"].notna()
        & out["Municipio key"].ne("")
        & out["Grupo edad"].ne("")
        & out["Sexo"].isin(["Hombres", "Mujeres", "Total"])
    ].copy()
    out["Año"] = out["Año"].astype(int)
    return out


def read_population_projection(file_obj, filename: str) -> pd.DataFrame:
    """Lee el archivo demográfico y devuelve Municipio/Año/Sexo/Grupo edad/Población."""
    data = file_obj.read() if hasattr(file_obj, "read") else Path(file_obj).read_bytes()
    suffix = Path(filename).suffix.lower()

    if suffix in {".csv", ".txt"}:
        for enc in ("utf-8-sig", "latin-1", "cp1252"):
            try:
                return _normalize_frame(pd.read_csv(BytesIO(data), encoding=enc, low_memory=False), filename)
            except Exception:
                continue
        raise ValueError(f"No se pudo leer {filename} como población municipal.")

    engine = "openpyxl" if suffix in {".xlsx", ".xlsm"} else "xlrd"
    xl = pd.ExcelFile(BytesIO(data), engine=engine)
    candidates = []
    errors = []
    for sheet in xl.sheet_names:
        # Primero encabezado estándar.
        try:
            df = pd.read_excel(BytesIO(data), sheet_name=sheet, engine=engine)
            norm = _normalize_frame(df, f"{filename}::{sheet}")
            candidates.append(norm)
            continue
        except Exception as exc:
            errors.append(f"{sheet}: {exc}")

        # Después detectar encabezado desplazado.
        try:
            raw = pd.read_excel(BytesIO(data), sheet_name=sheet, header=None, engine=engine)
            header = _find_header(raw)
            if header is not None:
                df = pd.read_excel(BytesIO(data), sheet_name=sheet, header=header, engine=engine)
                candidates.append(_normalize_frame(df, f"{filename}::{sheet}"))
        except Exception as exc:
            errors.append(f"{sheet}: {exc}")

    if not candidates:
        raise ValueError("No se encontró una hoja demográfica compatible. " + " | ".join(errors[:3]))

    # Preferir la hoja con más registros válidos; este archivo suele ser LONG.
    out = max(candidates, key=len).copy()

    # Evitar doble conteo cuando el archivo incluye TOTAL además de H/M.
    # Conservamos todas las filas, pero los agregadores escogerán H/M cuando existan.
    return out.reset_index(drop=True)


def population_for_year(pop: pd.DataFrame, year: int) -> pd.DataFrame:
    if pop is None or pop.empty:
        return pd.DataFrame(columns=["Municipio", "Año", "Sexo", "Grupo edad", "Población"])
    return pop[pd.to_numeric(pop["Año"], errors="coerce").eq(year)].copy()


def _sex_age_rows(pop: pd.DataFrame, year: int, municipality: str | None = None) -> pd.DataFrame:
    x = population_for_year(pop, year)
    if municipality and municipality != "Todos":
        x = x[x["Municipio key"].eq(_municipality_key(municipality))]
    # Si hay Hombres/Mujeres, excluir TOTAL para no duplicar población.
    if x["Sexo"].isin(["Hombres", "Mujeres"]).any():
        x = x[x["Sexo"].isin(["Hombres", "Mujeres"])]
    x = x[x["Grupo edad"].ne("Total")]
    return x


def municipal_totals(pop: pd.DataFrame, year: int) -> pd.DataFrame:
    x = _sex_age_rows(pop, year)
    if x.empty:
        return pd.DataFrame(columns=["Municipio", "Población"])
    return (
        x.groupby(["Municipio key"], as_index=False)["Población"].sum()
        .rename(columns={"Municipio key": "Municipio key"})
    )


def demographic_profile(pop: pd.DataFrame, year: int, municipality: str = "Todos") -> dict:
    x = _sex_age_rows(pop, year, municipality)
    if x.empty:
        return {}
    total = float(x["Población"].sum())
    men = float(x.loc[x["Sexo"].eq("Hombres"), "Población"].sum())
    women = float(x.loc[x["Sexo"].eq("Mujeres"), "Población"].sum())

    def lower(group: str):
        m = re.match(r"(\d+)", str(group))
        return int(m.group(1)) if m else np.nan

    ages = x["Grupo edad"].map(lower)
    under5 = float(x.loc[ages.lt(5), "Población"].sum())
    under15 = float(x.loc[ages.lt(15), "Población"].sum())
    over65 = float(x.loc[ages.ge(65), "Población"].sum())
    working = max(total - under15 - over65, 0)
    return {
        "Población": total,
        "Hombres": men,
        "Mujeres": women,
        "% mujeres": women / total * 100 if total else np.nan,
        "Razón H/M": men / women * 100 if women else np.nan,
        "% <5": under5 / total * 100 if total else np.nan,
        "% <15": under15 / total * 100 if total else np.nan,
        "% 65+": over65 / total * 100 if total else np.nan,
        "Índice envejecimiento": over65 / under15 * 100 if under15 else np.nan,
        "Razón dependencia": (under15 + over65) / working * 100 if working else np.nan,
    }


def pyramid(pop: pd.DataFrame, year: int, municipality: str = "Todos") -> pd.DataFrame:
    x = _sex_age_rows(pop, year, municipality)
    if x.empty:
        return pd.DataFrame(columns=["Grupo edad", "Hombres", "Mujeres"])
    p = x.pivot_table(index="Grupo edad", columns="Sexo", values="Población", aggfunc="sum", fill_value=0).reset_index()
    for c in ["Hombres", "Mujeres"]:
        if c not in p:
            p[c] = 0.0

    def age_order(g):
        m = re.match(r"(\d+)", str(g))
        return int(m.group(1)) if m else 999
    p["_order"] = p["Grupo edad"].map(age_order)
    return p.sort_values("_order").drop(columns="_order").reset_index(drop=True)


def age_group_from_years(age: float) -> str:
    if pd.isna(age) or age < 0:
        return ""
    age = int(age)
    if age >= 85:
        return "85+"
    lo = (age // 5) * 5
    return f"{lo}-{lo + 4}"


def age_sex_rates(sinave: pd.DataFrame, pop: pd.DataFrame, year: int, week_cutoff: int,
                  municipality: str = "Todos", pathogen: str = "Todos los casos",
                  multiplier: int = 100_000) -> pd.DataFrame:
    if sinave is None or sinave.empty or pop is None or pop.empty:
        return pd.DataFrame()
    ycol = "epi_year" if "epi_year" in sinave.columns else "year"
    x = sinave[
        pd.to_numeric(sinave[ycol], errors="coerce").eq(year)
        & pd.to_numeric(sinave["epi_week"], errors="coerce").between(1, week_cutoff)
    ].copy()
    if "sonora_resident" in x:
        x = x[x["sonora_resident"]]
    if municipality != "Todos":
        mk = _municipality_key(municipality)
        x = x[x["municipality"].map(_municipality_key).eq(mk)]
    if pathogen != "Todos los casos":
        col = f"path_{pathogen}"
        x = x[x[col].fillna(False)] if col in x else x.iloc[0:0]

    age = pd.to_numeric(x.get("age_years"), errors="coerce")
    if "age_months" in x:
        months = pd.to_numeric(x["age_months"], errors="coerce")
        age = age.where(age.notna(), np.where(months.notna(), 0, np.nan))
    x["Grupo edad"] = pd.Series(age, index=x.index).map(age_group_from_years)
    x["Sexo std"] = x.get("sex", "").map(_sex)
    x["Municipio key"] = x["municipality"].map(_municipality_key)
    x = x[x["Grupo edad"].ne("") & x["Sexo std"].isin(["Hombres", "Mujeres"])]

    cases = x.groupby(["Municipio key", "Grupo edad", "Sexo std"], as_index=False).size().rename(columns={"size": "Casos", "Sexo std": "Sexo"})
    den = _sex_age_rows(pop, year, municipality).groupby(["Municipio key", "Grupo edad", "Sexo"], as_index=False)["Población"].sum()
    out = den.merge(cases, on=["Municipio key", "Grupo edad", "Sexo"], how="left")
    out["Casos"] = out["Casos"].fillna(0).astype(int)
    out["Incidencia /100k"] = np.where(out["Población"] > 0, out["Casos"] / out["Población"] * multiplier, np.nan)
    if municipality == "Todos":
        out = out.groupby(["Grupo edad", "Sexo"], as_index=False).agg({"Población":"sum", "Casos":"sum"})
        out["Incidencia /100k"] = np.where(out["Población"] > 0, out["Casos"] / out["Población"] * multiplier, np.nan)
    return out
