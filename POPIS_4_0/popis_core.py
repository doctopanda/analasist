from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Iterable, Optional
import calendar
import math
import re
import unicodedata
import zipfile

import numpy as np
import pandas as pd

YES = {"SI", "SÍ", "1", "TRUE", "VERDADERO", "YES", "POSITIVO", "POSITIVA"}
NO = {"NO", "0", "FALSE", "FALSO", "NEGATIVO", "NEGATIVA"}

PATHOGEN_COLUMNS = {
    "Salmonella spp.": ["Salmonella"],
    "Shigella spp.": ["Shigella"],
    "Rotavirus": ["Rotavirus", "Rotavirus_InDRE"],
    "Vibrio parahaemolyticus": ["VibrioParahaemolyticus"],
}


def _norm_text(value: object) -> str:
    text = "" if value is None or (isinstance(value, float) and math.isnan(value)) else str(value)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", text.strip()).upper()


def _first_existing(df: pd.DataFrame, names: Iterable[str]) -> Optional[str]:
    normalized = {_norm_text(c): c for c in df.columns}
    for name in names:
        key = _norm_text(name)
        if key in normalized:
            return normalized[key]
    return None


def _to_date(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce", dayfirst=True)


def _to_num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def read_any_table(file_obj, filename: str) -> pd.DataFrame:
    """Read xlsx/xls/csv or the tab-delimited text files sometimes exported with .xls suffix."""
    data = file_obj.read() if hasattr(file_obj, "read") else Path(file_obj).read_bytes()
    suffix = Path(filename).suffix.lower()

    if suffix in {".xlsx", ".xlsm"}:
        return pd.read_excel(BytesIO(data), engine="openpyxl")

    if suffix == ".xls":
        # Real XLS files begin with OLE compound-document magic D0 CF 11 E0.
        if data[:4] == b"\xd0\xcf\x11\xe0":
            return pd.read_excel(BytesIO(data), engine="xlrd")
        for enc in ("utf-8-sig", "latin-1", "cp1252"):
            try:
                return pd.read_csv(BytesIO(data), sep="\t", encoding=enc, dtype=str, low_memory=False)
            except Exception:
                pass
        raise ValueError(f"No fue posible leer {filename} como XLS ni como tabla tabulada.")

    if suffix in {".csv", ".txt"}:
        for enc in ("utf-8-sig", "latin-1", "cp1252"):
            try:
                return pd.read_csv(BytesIO(data), encoding=enc, low_memory=False)
            except Exception:
                pass
        raise ValueError(f"No fue posible leer {filename}.")

    raise ValueError(f"Formato no compatible: {suffix}")


def read_excel_sheet(file_obj, filename: str, sheet_name: str | int = 0, header=None) -> pd.DataFrame:
    data = file_obj.read() if hasattr(file_obj, "read") else Path(file_obj).read_bytes()
    suffix = Path(filename).suffix.lower()
    engine = "openpyxl" if suffix in {".xlsx", ".xlsm"} else "xlrd"
    return pd.read_excel(BytesIO(data), sheet_name=sheet_name, header=header, engine=engine)


def infer_year(df: pd.DataFrame) -> Optional[int]:
    for candidate in ["Fec_captura", "Fecha_Inicio", "Fec_Primer_Contacto", "Fecha"]:
        col = _first_existing(df, [candidate])
        if col:
            dates = _to_date(df[col])
            years = dates.dt.year.dropna().astype(int)
            if not years.empty:
                return int(years.mode().iloc[0])
    return None


def _positive(series: pd.Series) -> pd.Series:
    s = series.fillna("").map(_norm_text)
    return s.str.startswith("POSITIV") | s.isin(YES)


def _yes(series: pd.Series) -> pd.Series:
    return series.fillna("").map(_norm_text).isin(YES)


def normalize_sinave(df: pd.DataFrame, source_name: str = "") -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]
    out["_source"] = source_name
    out["year"] = infer_year(out)

    aliases = {
        "folio": ["Folio", "FOLIO"],
        "onset_date": ["Fecha_Inicio", "Fecha inicio", "Fec_Inicio"],
        "epi_week": ["SemanaInicio", "Semana_Inicio", "SE", "Semana"],
        "notification_week": ["Sem_Notif", "Semana_Notificacion"],
        "capture_date": ["Fec_captura", "Fecha_Captura"],
        "first_contact": ["Fec_Primer_Contacto", "Fecha_Primer_Contacto"],
        "final_dx_date": ["Fec_Dx_Final", "Fecha_Dx_Final", "Fecha_Diagnostico_Final"],
        "final_dx": ["Diag_Final", "Diagnostico_Final"],
        "probable_dx": ["Diag_Prob", "Diagnostico_Probable"],
        "death_date": ["FecDefuncion", "Fecha_Defuncion"],
        "municipality": ["Mun_Res", "Municipio_Residencia", "Municipio"],
        "state_residence": ["Ent_Res", "Entidad_Residencia", "Entidad"],
        "unit_municipality": ["Mun_Unimed", "Municipio_Unidad"],
        "clues": ["CLUES", "Clues"],
        "zone": ["Residencia_Actual", "Zona_Residencia"],
        "sex": ["Sexo", "SEXO"],
        "age_years": ["Edad_Años", "Edad_Anos", "Edad"],
        "age_months": ["Edad_Meses"],
        "eda_type": ["Tipo_EDA", "Tipo EDA"],
        "evacuations": ["Num_Evac", "Numero_Evacuaciones"],
        "duration": ["Duracion_Diarrea", "Duracion"],
        "vomits": ["Num_Vomitos", "Numero_Vomitos"],
        "appearance": ["Aspecto"],
        "temperature": ["Temperatura"],
        "hydration": ["Edo_Hidratacion", "Estado_Hidratacion"],
        "nutrave": ["NuTraVE", "NUTRAVE"],
        "monitoring": ["Monitoreo", "MONITOREO"],
        "sample_vibrio": ["MuestraVibrio", "Muestra_Vibrio"],
        "sample_entero": ["MuestraEntero", "Muestra_Entero"],
        "sample_virus": ["MuestraVirus", "Muestra_Virus"],
        "take_vibrio": ["FecTomaMuestraVibrio", "Fecha_Toma_Vibrio"],
        "take_entero": ["FecTomaMuestraEntero", "Fecha_Toma_Entero"],
        "take_virus": ["FecTomaMuestraVirus", "Fec_Toma_Muest_Virus", "Fecha_Toma_Virus"],
        "recv_vibrio": ["Fec_Recep_Hiso_Vibrio", "Fecha_Recepcion_Vibrio"],
        "recv_entero": ["Fec_Recep_Hiso_Entero", "Fecha_Recepcion_Entero"],
        "recv_virus": ["Fec_Recep_Muest_Virus", "Fecha_Recepcion_Virus"],
        "quality_vibrio": ["Calidad_Hiso_Vibrio", "Calidad_Vibrio"],
        "quality_entero": ["Calidad_Hiso_Entero", "Calidad_Entero"],
        "quality_virus": ["Calidad_Muest_Virus", "Calidad_Virus"],
        "vibrio_result_date": ["FecResultVibrioCholerae", "Fecha_Resultado_Vibrio"],
    }

    for target, candidates in aliases.items():
        col = _first_existing(out, candidates)
        out[target] = out[col] if col else np.nan

    for c in ["onset_date", "capture_date", "first_contact", "final_dx_date", "death_date",
              "take_vibrio", "take_entero", "take_virus", "recv_vibrio", "recv_entero",
              "recv_virus", "vibrio_result_date"]:
        out[c] = _to_date(out[c])

    out["epi_week"] = _to_num(out["epi_week"])
    out["notification_week"] = _to_num(out["notification_week"])
    for c in ["age_years", "age_months", "evacuations", "duration", "vomits", "temperature"]:
        out[c] = _to_num(out[c])

    # Pathogens.
    for pathogen, candidates in PATHOGEN_COLUMNS.items():
        masks = []
        for candidate in candidates:
            col = _first_existing(out, [candidate])
            if col:
                masks.append(_positive(out[col]))
        out[f"path_{pathogen}"] = np.logical_or.reduce(masks) if masks else False

    # E. coli pathogenic only when a pathogenic pathotype is documented.
    ecoli = _first_existing(out, ["Patotipo_EColi_InDRE", "Patotipo_EColi"])
    if ecoli:
        txt = out[ecoli].fillna("").map(_norm_text)
        out["path_Escherichia coli patógena"] = txt.ne("") & ~txt.str.contains("NO PAT", regex=False)
    else:
        out["path_Escherichia coli patógena"] = False

    vc = _first_existing(out, ["VibrioCholerae", "Vibrio_Cholerae"])
    sg = _first_existing(out, ["SerogrupoVibrioCholerae", "Serogrupo_Vibrio_Cholerae"])
    if vc:
        pos = _positive(out[vc])
        if sg:
            sero = out[sg].fillna("").map(_norm_text)
            out["path_Vibrio cholerae no O1"] = pos & sero.str.contains("NO O1", regex=False)
            out["path_Vibrio cholerae"] = pos & ~sero.str.contains("NO O1", regex=False)
        else:
            out["path_Vibrio cholerae"] = pos
            out["path_Vibrio cholerae no O1"] = False
    else:
        out["path_Vibrio cholerae"] = False
        out["path_Vibrio cholerae no O1"] = False

    other_virus = _first_existing(out, ["OtroVirus_InDRE"])
    out["other_virus"] = out[other_virus] if other_virus else ""
    other_bacteria = _first_existing(out, ["OtraBacteria_InDRE"])
    out["other_bacteria"] = out[other_bacteria] if other_bacteria else ""
    parasites = _first_existing(out, ["ResultadoParasitos_InDRE"])
    out["other_parasite"] = out[parasites] if parasites else ""

    path_cols = [c for c in out.columns if c.startswith("path_")]
    out["pathogen_positive"] = out[path_cols].fillna(False).astype(bool).any(axis=1)
    out["death"] = out["death_date"].notna()
    return out


def combine_sinave(files: list[tuple[object, str]]) -> pd.DataFrame:
    frames = []
    for obj, name in files:
        df = read_any_table(obj, name)
        frames.append(normalize_sinave(df, source_name=name))
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True, sort=False)


def sinave_weekly(df: pd.DataFrame, year: int, pathogen: Optional[str] = None,
                  municipality: Optional[str] = None, deaths: bool = False) -> pd.DataFrame:
    x = df[df["year"].eq(year)].copy()
    if municipality and municipality != "Todos":
        x = x[x["municipality"].astype(str).eq(municipality)]
    if deaths:
        x = x[x["death"]]
    if pathogen and pathogen != "Todos los casos":
        col = f"path_{pathogen}"
        if col in x:
            x = x[x[col].fillna(False)]
        else:
            x = x.iloc[0:0]
    counts = x.dropna(subset=["epi_week"]).groupby("epi_week").size().reindex(range(1, 54), fill_value=0)
    return pd.DataFrame({"SE": range(1, 54), "Casos": counts.to_numpy()})


def pathogen_summary(df: pd.DataFrame, year: int, week_cutoff: int) -> pd.DataFrame:
    x = df[df["year"].eq(year) & df["epi_week"].between(1, week_cutoff, inclusive="both")]
    rows = []
    for col in sorted(c for c in x.columns if c.startswith("path_")):
        rows.append({"Patógeno": col.replace("path_", ""), "Casos": int(x[col].fillna(False).sum())})
    return pd.DataFrame(rows).sort_values("Casos", ascending=False, ignore_index=True)


def sinave_summary(df: pd.DataFrame, year: int, week_cutoff: int) -> dict:
    x = df[df["year"].eq(year) & df["epi_week"].between(1, week_cutoff, inclusive="both")]
    w = df[df["year"].eq(year) & df["epi_week"].eq(week_cutoff)]
    return {
        "acumulado": int(len(x)),
        "semana": int(len(w)),
        "positivos_acum": int(x["pathogen_positive"].sum()) if not x.empty else 0,
        "positivos_semana": int(w["pathogen_positive"].sum()) if not w.empty else 0,
        "defunciones_acum": int(x["death"].sum()) if not x.empty else 0,
        "defunciones_semana": int(w["death"].sum()) if not w.empty else 0,
        "letalidad": float(x["death"].sum() / len(x) * 100) if len(x) else np.nan,
    }


def parse_suive_history(file_obj, filename: str, preferred_sheet: str = "SUIVE") -> pd.DataFrame:
    """Extract weekly counts from historical SUIVE workbook.

    The parser is intentionally tolerant: it searches a sheet for rows containing a year and
    at least 20 plausible weekly values to the right. It returns long format Año/SE/Casos.
    """
    data = file_obj.read() if hasattr(file_obj, "read") else Path(file_obj).read_bytes()
    suffix = Path(filename).suffix.lower()
    engine = "openpyxl" if suffix in {".xlsx", ".xlsm"} else "xlrd"
    xl = pd.ExcelFile(BytesIO(data), engine=engine)
    sheet = preferred_sheet if preferred_sheet in xl.sheet_names else xl.sheet_names[0]
    raw = pd.read_excel(BytesIO(data), sheet_name=sheet, header=None, engine=engine)

    candidates = []
    for r in range(len(raw)):
        row = raw.iloc[r]
        for c, value in enumerate(row):
            try:
                year = int(float(value))
            except Exception:
                continue
            if not 1990 <= year <= 2100:
                continue
            nums = pd.to_numeric(row.iloc[c + 1:c + 60], errors="coerce")
            # Trim at most 53 weekly positions, preserving blanks as NA.
            vals = nums.iloc[:53]
            plausible = vals.dropna()
            if len(plausible) >= 20 and (plausible >= 0).all():
                candidates.append((year, r, c, vals))
                break

    if not candidates:
        raise ValueError("No se detectaron filas históricas SUIVE con año y semanas. Revise la hoja o use el editor manual.")

    # If a year is repeated, choose the candidate with the largest count of non-null weekly cells.
    selected = {}
    for year, r, c, vals in candidates:
        score = vals.notna().sum()
        if year not in selected or score > selected[year][0]:
            selected[year] = (score, vals)

    records = []
    for year, (_, vals) in sorted(selected.items()):
        for i, value in enumerate(vals, start=1):
            if pd.notna(value):
                records.append({"Año": year, "SE": i, "Casos": float(value)})
    out = pd.DataFrame(records)
    if out.empty:
        raise ValueError("La serie SUIVE detectada quedó vacía.")
    out["Año"] = out["Año"].astype(int)
    out["SE"] = out["SE"].astype(int)
    return out


def suive_summary(suive: pd.DataFrame, year: int, week_cutoff: int) -> dict:
    x = suive[(suive["Año"] == year) & (suive["SE"].between(1, week_cutoff))]
    w = suive[(suive["Año"] == year) & (suive["SE"] == week_cutoff)]
    return {"acumulado": float(x["Casos"].sum()), "semana": float(w["Casos"].sum())}


def endemic_channel(weekly: pd.DataFrame, current_year: int, historical_years: list[int],
                     current_week: int = 53) -> pd.DataFrame:
    hist = weekly[weekly["Año"].isin(historical_years)].copy()
    pivot = hist.pivot_table(index="SE", columns="Año", values="Casos", aggfunc="sum")
    result = pd.DataFrame({"SE": range(1, 54)})
    result["Q1"] = result["SE"].map(pivot.quantile(0.25, axis=1))
    result["Mediana"] = result["SE"].map(pivot.quantile(0.50, axis=1))
    result["Q3"] = result["SE"].map(pivot.quantile(0.75, axis=1))
    current = weekly[weekly["Año"].eq(current_year)].groupby("SE")["Casos"].sum()
    result["Actual"] = result["SE"].map(current)
    result.loc[result["SE"] > current_week, "Actual"] = np.nan
    result["Zona"] = np.select(
        [result["Actual"].isna(), result["Actual"] <= result["Q1"], result["Actual"] <= result["Mediana"], result["Actual"] <= result["Q3"]],
        ["Sin dato", "Éxito", "Seguridad", "Alarma"], default="Epidemia"
    )
    return result


def sinave_channel(df: pd.DataFrame, current_year: int, historical_years: list[int], pathogen: str,
                   current_week: int = 53, municipality: str = "Todos") -> pd.DataFrame:
    records = []
    for year in sorted(set(historical_years + [current_year])):
        wk = sinave_weekly(df, year, pathogen=pathogen, municipality=municipality)
        for row in wk.itertuples(index=False):
            records.append({"Año": year, "SE": int(row.SE), "Casos": float(row.Casos)})
    return endemic_channel(pd.DataFrame(records), current_year, historical_years, current_week)


def incidence(cases: pd.Series | float, population: pd.Series | float, multiplier: int = 100_000):
    return np.where(np.asarray(population, dtype=float) > 0, np.asarray(cases, dtype=float) / np.asarray(population, dtype=float) * multiplier, np.nan)


def territorial_summary(df: pd.DataFrame, year: int, week_cutoff: int,
                        population: Optional[pd.DataFrame] = None, multiplier: int = 100_000) -> pd.DataFrame:
    x = df[df["year"].eq(year) & df["epi_week"].between(1, week_cutoff)].copy()
    x = x[x["municipality"].notna()]
    agg = x.groupby("municipality", dropna=False).agg(
        Casos=("folio", "size"),
        Positivos=("pathogen_positive", "sum"),
        Defunciones=("death", "sum"),
    ).reset_index().rename(columns={"municipality": "Municipio"})
    agg["Positividad %"] = np.where(agg["Casos"] > 0, agg["Positivos"] / agg["Casos"] * 100, np.nan)
    agg["Letalidad %"] = np.where(agg["Casos"] > 0, agg["Defunciones"] / agg["Casos"] * 100, np.nan)

    if population is not None and not population.empty:
        pop = population.copy()
        pop.columns = [str(c).strip() for c in pop.columns]
        mcol = _first_existing(pop, ["Municipio", "NOM_MUN", "NOM_MUNICIPIO", "MUNICIPIO"])
        ycol = _first_existing(pop, ["Año", "ANIO", "YEAR"])
        pcol = _first_existing(pop, ["Poblacion", "POBLACION", "Pob", "POB_TOTAL"])
        if mcol and pcol:
            if ycol:
                pop = pop[pd.to_numeric(pop[ycol], errors="coerce").eq(year)]
            pop2 = pop[[mcol, pcol]].copy()
            pop2.columns = ["Municipio", "Población"]
            pop2["Población"] = pd.to_numeric(pop2["Población"], errors="coerce")
            pop2 = pop2.groupby("Municipio", as_index=False)["Población"].sum()
            agg = agg.merge(pop2, on="Municipio", how="left")
            agg["Incidencia /100k"] = incidence(agg["Casos"], agg["Población"], multiplier)
            agg["Mortalidad /100k"] = incidence(agg["Defunciones"], agg["Población"], multiplier)
    return agg.sort_values("Casos", ascending=False, ignore_index=True)


def build_comparison(suive: pd.DataFrame, sinave: pd.DataFrame, year: int, week_cutoff: int) -> pd.DataFrame:
    rows = []
    for week in range(1, week_cutoff + 1):
        s = suive[(suive["Año"] == year) & (suive["SE"] == week)]["Casos"].sum()
        n = len(sinave[(sinave["year"] == year) & (sinave["epi_week"] == week)])
        rows.append({
            "SE": week,
            "SUIVE": float(s),
            "SINAVE": int(n),
            "Diferencia": float(s) - n,
            "Razón SINAVE/SUIVE %": (n / s * 100) if s else np.nan,
        })
    return pd.DataFrame(rows)


def month_filter(df: pd.DataFrame, year: int, month: int) -> pd.DataFrame:
    return df[(df["year"] == year) & (df["capture_date"].dt.year == year) & (df["capture_date"].dt.month == month)].copy()


def qualitative(value: float) -> str:
    if pd.isna(value):
        return "Sin dato"
    if value >= 90:
        return "Sobresaliente"
    if value >= 80:
        return "Satisfactorio"
    if value >= 60:
        return "Mínimo"
    return "Precario"


def _indicator(name: str, numerator: int, denominator: int, target: float, target_operator: str = ">=") -> dict:
    value = numerator / denominator * 100 if denominator else np.nan
    if pd.isna(value):
        meets = False
    elif target_operator == "<=":
        meets = value <= target
    else:
        meets = value >= target
    return {
        "Indicador": name,
        "Numerador": int(numerator),
        "Denominador": int(denominator),
        "Resultado %": float(value) if not pd.isna(value) else np.nan,
        "Meta": target,
        "Cumple": "Sí" if meets else "No",
        "Escala": qualitative(value),
    }


def nutrave_indicators(df: pd.DataFrame, year: int, month: int) -> pd.DataFrame:
    x = month_filter(df, year, month)
    nflag = x["nutrave"].fillna("").map(_norm_text).isin(YES)
    if nflag.any():
        x = x[nflag].copy()

    # Notification opportunity.
    valid = x["capture_date"].notna() & x["first_contact"].notna()
    delta = (x["capture_date"] - x["first_contact"]).dt.days
    den_notif = int((valid & delta.ge(0)).sum())
    num_notif = int((valid & delta.between(0, 1)).sum())

    # Classification opportunity: processed bacterial specimens, non-rejected, diagnosis final, <=9 days.
    sample_v = _yes(x["sample_vibrio"])
    sample_e = _yes(x["sample_entero"])
    qv = x["quality_vibrio"].fillna("").map(_norm_text)
    qe = x["quality_entero"].fillna("").map(_norm_text)
    processed = sample_v & sample_e & x["recv_vibrio"].notna() & x["recv_entero"].notna() & ~qv.str.contains("RECHAZ") & ~qe.str.contains("RECHAZ")
    den_class = int(processed.sum())
    dclass = (x["final_dx_date"] - x["first_contact"]).dt.days
    num_class = int((processed & x["final_dx_date"].notna() & dclass.between(0, 9)).sum())

    # Coverage: days with captures / days in month.
    days = int(x["capture_date"].dropna().dt.normalize().nunique())
    days_month = calendar.monthrange(year, month)[1]

    # Under 5 and >=5 sampling.
    under5 = x["age_years"].fillna(0).lt(5)
    type_norm = x["eda_type"].fillna("").map(_norm_text)
    moderate_severe = type_norm.str.contains("MODER") | type_norm.str.contains("GRAV")
    eligible_u5 = under5 & moderate_severe
    sampled_u5 = eligible_u5 & _yes(x["sample_vibrio"]) & _yes(x["sample_entero"]) & _yes(x["sample_virus"]) & x["recv_vibrio"].notna() & x["recv_entero"].notna() & x["recv_virus"].notna()
    eligible_5 = ~under5 & moderate_severe
    sampled_5 = eligible_5 & _yes(x["sample_vibrio"]) & _yes(x["sample_entero"]) & x["recv_vibrio"].notna() & x["recv_entero"].notna()

    rows = [
        _indicator("Notificación oportuna de EDA", num_notif, den_notif, 100),
        _indicator("Clasificación oportuna de EDA", num_class, den_class, 80),
        _indicator("Cobertura de notificación de EDA", days, days_month, 80),
        _indicator("Muestreo EDA <5 años", int(sampled_u5.sum()), int(eligible_u5.sum()), 80),
        _indicator("Muestreo EDA ≥5 años", int(sampled_5.sum()), int(eligible_5.sum()), 80),
    ]
    return pd.DataFrame(rows)


def laboratory_indicators(df: pd.DataFrame, year: int, month: int) -> pd.DataFrame:
    x = month_filter(df, year, month)
    rows = []

    # Rejection among received bacterial samples.
    received = x["recv_vibrio"].notna() | x["recv_entero"].notna()
    rejected = x["quality_vibrio"].fillna("").map(_norm_text).str.contains("RECHAZ") | x["quality_entero"].fillna("").map(_norm_text).str.contains("RECHAZ")
    rows.append(_indicator("Muestras rechazadas", int((received & rejected).sum()), int(received.sum()), 10, "<="))

    # Timely collection bacterial <=5 days; viral <=2 days.
    onset = x["onset_date"]
    dt_b = (x["take_vibrio"].fillna(x["take_entero"]) - onset).dt.days
    eligible_b = onset.notna() & (x["take_vibrio"].notna() | x["take_entero"].notna()) & dt_b.ge(0)
    timely_b = eligible_b & dt_b.le(5)
    rows.append(_indicator("Toma oportuna bacteriana (≤5 días)", int(timely_b.sum()), int(eligible_b.sum()), 80))

    dt_v = (x["take_virus"] - onset).dt.days
    eligible_v = onset.notna() & x["take_virus"].notna() & dt_v.ge(0)
    timely_v = eligible_v & dt_v.le(2)
    rows.append(_indicator("Toma oportuna viral (≤2 días)", int(timely_v.sum()), int(eligible_v.sum()), 80))

    # Shipment/receipt: receipt - collection. Viral <=3; bacterial <=5.
    take_b = x["take_vibrio"].fillna(x["take_entero"])
    recv_b = x["recv_vibrio"].fillna(x["recv_entero"])
    ds_b = (recv_b - take_b).dt.days
    el_b = take_b.notna() & recv_b.notna() & ds_b.ge(0)
    rows.append(_indicator("Envío oportuno bacteriano (≤5 días)", int((el_b & ds_b.le(5)).sum()), int(el_b.sum()), 80))

    ds_v = (x["recv_virus"] - x["take_virus"]).dt.days
    el_v = x["take_virus"].notna() & x["recv_virus"].notna() & ds_v.ge(0)
    rows.append(_indicator("Envío oportuno viral (≤3 días)", int((el_v & ds_v.le(3)).sum()), int(el_v.sum()), 80))
    return pd.DataFrame(rows)


def audit_operational_definitions(df: pd.DataFrame, year: int, week_cutoff: int) -> pd.DataFrame:
    x = df[df["year"].eq(year) & df["epi_week"].between(1, week_cutoff)].copy()
    evac = x["evacuations"].fillna(-1)
    duration = x["duration"].fillna(-1)
    hyd = x["hydration"].fillna("").map(_norm_text)
    moderate = evac.ge(5) & duration.between(0, 5) & hyd.str.contains("MODER")

    vom = x["vomits"].fillna(0).gt(5)
    dys = x["appearance"].fillna("").map(_norm_text).str.contains("SANG|DISENT")
    fever = x["temperature"].fillna(-99).gt(38)
    dehydr = hyd.str.contains("MODER|GRAV")
    severe_signs = vom.astype(int) + dys.astype(int) + fever.astype(int) + dehydr.astype(int)
    severe = evac.ge(5) & duration.between(0, 5) & severe_signs.ge(2)

    calc = np.select([severe, moderate], ["GRAVE", "MODERADA"], default="NO CLASIFICABLE")
    captured = x["eda_type"].fillna("").map(_norm_text)
    out = pd.DataFrame({
        "Folio": x["folio"],
        "SE": x["epi_week"],
        "Tipo capturado": captured,
        "Tipo recalculado": calc,
    })
    out["Concordante"] = np.where(out["Tipo capturado"].str.contains("GRAV") & out["Tipo recalculado"].eq("GRAVE"), "Sí",
                           np.where(out["Tipo capturado"].str.contains("MODER") & out["Tipo recalculado"].eq("MODERADA"), "Sí", "Revisar"))
    return out


def make_excel_report(tables: dict[str, pd.DataFrame]) -> bytes:
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        for name, table in tables.items():
            safe = re.sub(r"[\\/*?:\[\]]", "_", name)[:31]
            table.to_excel(writer, sheet_name=safe, index=False)
            ws = writer.book[safe]
            ws.freeze_panes = "A2"
            for col in ws.columns:
                maxlen = max((len(str(cell.value)) if cell.value is not None else 0) for cell in col)
                ws.column_dimensions[col[0].column_letter].width = min(max(maxlen + 2, 10), 42)
    return bio.getvalue()


def zip_images(images: dict[str, bytes]) -> bytes:
    bio = BytesIO()
    with zipfile.ZipFile(bio, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, payload in images.items():
            z.writestr(name, payload)
    return bio.getvalue()
