"""Correcciones y enriquecimiento para POPIS 4.x con datos reales EDA Sonora."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import calendar
import re

import numpy as np
import pandas as pd

import popis_core as _base

_ORIGINAL_NORMALIZE = _base.normalize_sinave
_ORIGINAL_READ = _base.read_any_table
_ORIGINAL_PARSE_SUIVE = _base.parse_suive_history
_ORIGINAL_AUDIT = _base.audit_operational_definitions

DISTRICTS = {
    "01 Hermosillo": ["Aconchi","Arivechi","Bacadéhuachi","Bacanora","Banámichi","Baviácora","Carbó","La Colorada","Cumpas","Divisaderos","Granados","Hermosillo","Huásabas","Huépac","Mazatán","Moctezuma","Nácori Chico","Nacozari de García","Ónavas","Opodepe","Rayón","Sahuaripa","San Felipe de Jesús","San Javier","San Miguel de Horcasitas","San Pedro de la Cueva","Soyopa","Suaqui Grande","Tepache","Ures","Villa Hidalgo","Villa Pesqueira"],
    "02 Caborca": ["Altar","Átil","Caborca","Oquitoa","Pitiquito","Sáric","Tubutama"],
    "03 Santa Ana": ["Agua Prieta","Arizpe","Bacerac","Bacoachi","Bavispe","Benjamín Hill","Cananea","Cucurpe","Fronteras","Huachinera","Ímuris","Magdalena","Naco","Nogales","Santa Ana","Santa Cruz","Trincheras"],
    "04 Ciudad Obregón": ["Bácum","Cajeme","Empalme","Guaymas","Quiriego","Rosario","San Ignacio Río Muerto","Yécora"],
    "05 Navojoa": ["Álamos","Benito Juárez","Etchojoa","Huatabampo","Navojoa"],
    "06 San Luis Río Colorado": ["San Luis Río Colorado","General Plutarco Elías Calles","Puerto Peñasco"],
}

REGIONS = {
    "Capital": ["Hermosillo"],
    "Alto Golfo": ["Puerto Peñasco","San Luis Río Colorado","General Plutarco Elías Calles"],
    "Gran Desierto": ["Altar","Átil","Benjamín Hill","Caborca","Carbó","Magdalena","Oquitoa","Pitiquito","Santa Ana","Sáric","Trincheras","Tubutama"],
    "Frontera": ["Cucurpe","Ímuris","Nogales","Santa Cruz"],
    "Puerto": ["La Colorada","Empalme","Guaymas","Ónavas","San Javier","Suaqui Grande"],
    "Río Yaqui": ["Bácum","Cajeme","Benito Juárez"],
    "Río Mayo": ["Álamos","Etchojoa","Huatabampo","Navojoa","Quiriego","Rosario","San Ignacio Río Muerto"],
    "Tres Ríos": ["Aconchi","Arivechi","Bacanora","Banámichi","Baviácora","Huépac","Mazatán","Opodepe","Rayón","Sahuaripa","San Felipe de Jesús","San Miguel de Horcasitas","San Pedro de la Cueva","Soyopa","Ures","Villa Pesqueira","Yécora"],
    "Cuatro Sierras": ["Agua Prieta","Arizpe","Bacoachi","Cananea","Fronteras","Naco"],
    "Sierra Alta": ["Bacadéhuachi","Bacerac","Bavispe","Cumpas","Divisaderos","Granados","Huachinera","Huásabas","Moctezuma","Nácori Chico","Nacozari de García","Tepache","Villa Hidalgo"],
}


def _reverse_catalog(catalog: dict[str, list[str]]) -> dict[str, str]:
    return {_base._norm_text(m): group for group, municipalities in catalog.items() for m in municipalities}


def _municipality_display() -> dict[str, str]:
    values = {}
    for municipalities in DISTRICTS.values():
        for municipality in municipalities:
            values[_base._norm_text(municipality)] = municipality
    return values


_DISTRICT_BY_MUN = _reverse_catalog(DISTRICTS)
_REGION_BY_MUN = _reverse_catalog(REGIONS)
_MUN_DISPLAY = _municipality_display()

_MUN_ALIASES = {
    "BENITO JUAREZ SON": "BENITO JUAREZ",
    "BENITO JUAREZ SONORA": "BENITO JUAREZ",
    "ROSARIO SON": "ROSARIO",
    "ROSARIO SONORA": "ROSARIO",
    "ROSARIO TESOPACO": "ROSARIO",
    "COLORADA LA": "LA COLORADA",
    "HEROICA NOGALES": "NOGALES",
    "HEROICA CABORCA": "CABORCA",
    "PLUTARCO ELIAS CALLES": "GENERAL PLUTARCO ELIAS CALLES",
}


def canonical_municipality(value: object) -> str:
    key = _base._norm_text(value)
    key = re.sub(r"\s+", " ", key).strip()
    key = re.sub(r"\s+(SON|SONORA)$", "", key).strip()
    key = _MUN_ALIASES.get(key, key)
    return _MUN_DISPLAY.get(key, str(value).strip() if value is not None else "")


def normalize_sinave(df: pd.DataFrame, source_name: str = "") -> pd.DataFrame:
    """Normaliza SINAVE y separa año calendario de año epidemiológico.

    Importante: SemanaInicio=52/53 en los primeros días de enero NO se corrige.
    Se conserva la semana capturada y se asigna al año epidemiológico previo.
    """
    out = _ORIGINAL_NORMALIZE(df, source_name)
    out["calendar_year"] = pd.to_numeric(out["year"], errors="coerce").astype("Int64")

    onset_year = out["onset_date"].dt.year.astype("Int64")
    onset_month = out["onset_date"].dt.month
    capture_year = out["capture_date"].dt.year.astype("Int64")
    epi_year = onset_year.fillna(capture_year).fillna(out["calendar_year"]).astype("Int64")
    week = pd.to_numeric(out["epi_week"], errors="coerce")
    jan_previous = week.ge(52) & onset_month.eq(1) & epi_year.notna()
    dec_next = week.eq(1) & onset_month.eq(12) & epi_year.notna()
    epi_year = epi_year.copy()
    epi_year.loc[jan_previous] = epi_year.loc[jan_previous] - 1
    epi_year.loc[dec_next] = epi_year.loc[dec_next] + 1
    out["epi_year"] = epi_year
    out["epi_boundary"] = jan_previous | dec_next

    out["municipality_raw"] = out["municipality"]
    out["municipality"] = out["municipality"].map(canonical_municipality)
    out["municipality_key"] = out["municipality"].map(_base._norm_text)
    out["state_key"] = out["state_residence"].fillna("").map(_base._norm_text)
    out["sonora_resident"] = out["state_key"].eq("SONORA")
    out["municipality_known"] = out["municipality_key"].isin(_MUN_DISPLAY)

    # Variables de calidad que no estaban en el motor base.
    exp_col = _base._first_existing(out, ["Fecha_Consumo", "Fecha Consumo"])
    out["exposure_date"] = pd.to_datetime(out[exp_col], errors="coerce", dayfirst=True) if exp_col else pd.NaT
    dx = out["final_dx"].fillna("").map(_base._norm_text)
    qv = out["quality_vibrio"].fillna("").map(_base._norm_text)
    qe = out["quality_entero"].fillna("").map(_base._norm_text)
    qvirus = out["quality_virus"].fillna("").map(_base._norm_text)
    out["sample_rejected"] = dx.str.contains("MUESTRAS RECHAZ") | qv.str.contains("RECHAZ") | qe.str.contains("RECHAZ") | qvirus.str.contains("RECHAZ")
    out["pending_result"] = dx.eq("") | dx.str.contains("EN PROCESO")
    return out


def combine_sinave(files: list[tuple[object, str]]) -> pd.DataFrame:
    frames = []
    for order, (obj, name) in enumerate(files):
        frame = normalize_sinave(_base.read_any_table(obj, name), source_name=name)
        frame["_source_order"] = order
        frames.append(frame)
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True, sort=False)
    folio = out["folio"].fillna("").astype(str).str.strip()
    dup = folio.ne("") & folio.duplicated(keep=False)
    out["duplicate_folio_source"] = dup
    if dup.any():
        # Mantener una sola versión por folio. El archivo más reciente en la lista gana.
        nonblank = out[folio.ne("")].sort_values(["_source_order", "capture_date", "final_dx_date"], na_position="first")
        keep_idx = nonblank.drop_duplicates("folio", keep="last").index
        blank_idx = out[folio.eq("")].index
        out = out.loc[keep_idx.union(blank_idx)].sort_index().copy()
        out["duplicate_folio_source"] = out["folio"].astype(str).isin(set(folio[dup]))
    return out.reset_index(drop=True)


def _year_col(df: pd.DataFrame) -> str:
    return "epi_year" if "epi_year" in df.columns else "year"


def sinave_weekly(df: pd.DataFrame, year: int, pathogen: str | None = None, municipality: str | None = None, deaths: bool = False) -> pd.DataFrame:
    ycol = _year_col(df)
    x = df[pd.to_numeric(df[ycol], errors="coerce").eq(year)].copy()
    if municipality and municipality != "Todos":
        x = x[x["municipality"].map(canonical_municipality).eq(canonical_municipality(municipality))]
    if deaths:
        x = x[x["death"]]
    if pathogen and pathogen != "Todos los casos":
        col = f"path_{pathogen}"
        x = x[x[col].fillna(False)] if col in x else x.iloc[0:0]
    counts = x.dropna(subset=["epi_week"]).groupby("epi_week").size().reindex(range(1, 54), fill_value=0)
    return pd.DataFrame({"SE": range(1, 54), "Casos": counts.to_numpy()})


def pathogen_summary(df: pd.DataFrame, year: int, week_cutoff: int) -> pd.DataFrame:
    ycol = _year_col(df)
    x = df[pd.to_numeric(df[ycol], errors="coerce").eq(year) & df["epi_week"].between(1, week_cutoff, inclusive="both")]
    rows = [{"Patógeno": c.replace("path_", ""), "Casos": int(x[c].fillna(False).sum())} for c in sorted(c for c in x.columns if c.startswith("path_"))]
    return pd.DataFrame(rows).sort_values("Casos", ascending=False, ignore_index=True) if rows else pd.DataFrame(columns=["Patógeno", "Casos"])


def sinave_summary(df: pd.DataFrame, year: int, week_cutoff: int) -> dict:
    ycol = _year_col(df)
    mask_year = pd.to_numeric(df[ycol], errors="coerce").eq(year)
    x = df[mask_year & df["epi_week"].between(1, week_cutoff, inclusive="both")]
    w = df[mask_year & df["epi_week"].eq(week_cutoff)]
    return {
        "acumulado": int(len(x)), "semana": int(len(w)),
        "positivos_acum": int(x["pathogen_positive"].sum()) if not x.empty else 0,
        "positivos_semana": int(w["pathogen_positive"].sum()) if not w.empty else 0,
        "defunciones_acum": int(x["death"].sum()) if not x.empty else 0,
        "defunciones_semana": int(w["death"].sum()) if not w.empty else 0,
        "letalidad": float(x["death"].sum() / len(x) * 100) if len(x) else np.nan,
    }


def _prepare_population(population: pd.DataFrame, year: int) -> pd.DataFrame:
    if population is None or population.empty:
        return pd.DataFrame(columns=["Municipio", "Población"])
    pop = population.copy()
    pop.columns = [str(c).strip() for c in pop.columns]
    mcol = _base._first_existing(pop, ["Municipio", "NOM_MUN", "NOM_MUNICIPIO", "MUNICIPIO", "NOMBRE_MUNICIPIO"])
    ycol = _base._first_existing(pop, ["Año", "ANIO", "YEAR", "AÑO"])
    pcol = _base._first_existing(pop, ["Poblacion", "POBLACION", "Pob", "POB_TOTAL", "POBLACIÓN"])

    # Formato ancho: una columna por año.
    if not pcol:
        for c in pop.columns:
            try:
                if int(float(str(c))) == year:
                    pcol = c
                    break
            except Exception:
                pass
    if not mcol or not pcol:
        return pd.DataFrame(columns=["Municipio", "Población"])
    if ycol:
        pop = pop[pd.to_numeric(pop[ycol], errors="coerce").eq(year)].copy()

    sex_col = _base._first_existing(pop, ["SEXO", "Sexo"])
    if sex_col and not pop.empty:
        sex = pop[sex_col].fillna("").map(_base._norm_text)
        total_mask = sex.str.contains(r"TOTAL|AMBOS|AMBAS", regex=True)
        if total_mask.any():
            pop = pop[total_mask].copy()

    age_col = _base._first_existing(pop, ["EDAD_QUIN", "GRUPO_EDAD", "EDAD", "Edad"])
    if age_col and not pop.empty:
        age = pop[age_col].fillna("").map(_base._norm_text)
        total_age = age.str.fullmatch(r"TOTAL|TODAS|TODOS|0-\+|0 Y MAS", na=False)
        if total_age.any():
            pop = pop[total_age].copy()

    out = pd.DataFrame({"Municipio": pop[mcol].map(canonical_municipality), "Población": pd.to_numeric(pop[pcol], errors="coerce")})
    out = out[out["Municipio"].ne("") & out["Población"].notna()]
    return out.groupby("Municipio", as_index=False)["Población"].sum()


def territorial_summary(df: pd.DataFrame, year: int, week_cutoff: int, population: pd.DataFrame | None = None, multiplier: int = 100_000) -> pd.DataFrame:
    ycol = _year_col(df)
    x = df[pd.to_numeric(df[ycol], errors="coerce").eq(year) & df["epi_week"].between(1, week_cutoff)].copy()
    # Tasas de Sonora: numerador solo de residentes de Sonora.
    if "sonora_resident" in x:
        x = x[x["sonora_resident"]]
    x = x[x["municipality"].notna() & x["municipality"].astype(str).str.strip().ne("")]
    x["Municipio"] = x["municipality"].map(canonical_municipality)
    agg = x.groupby("Municipio", dropna=False).agg(Casos=("folio", "size"), Positivos=("pathogen_positive", "sum"), Defunciones=("death", "sum")).reset_index()
    agg["Positividad %"] = np.where(agg["Casos"] > 0, agg["Positivos"] / agg["Casos"] * 100, np.nan)
    agg["Letalidad %"] = np.where(agg["Casos"] > 0, agg["Defunciones"] / agg["Casos"] * 100, np.nan)
    pop = _prepare_population(population, year)
    if not pop.empty:
        agg = agg.merge(pop, on="Municipio", how="left")
        agg["Incidencia /100k"] = _base.incidence(agg["Casos"], agg["Población"], multiplier)
        agg["Mortalidad /100k"] = _base.incidence(agg["Defunciones"], agg["Población"], multiplier)
    keys = agg["Municipio"].map(_base._norm_text)
    agg.insert(1, "Distrito", keys.map(_DISTRICT_BY_MUN).fillna("No asignado / revisar"))
    agg.insert(2, "Región", keys.map(_REGION_BY_MUN).fillna("No asignada / revisar"))
    return agg.sort_values("Casos", ascending=False, ignore_index=True)


def aggregate_territory(territorial: pd.DataFrame, level: str) -> pd.DataFrame:
    if level not in {"Distrito", "Región"}:
        raise ValueError("level debe ser 'Distrito' o 'Región'.")
    numeric = [c for c in ["Casos", "Positivos", "Defunciones", "Población"] if c in territorial.columns]
    result = territorial.groupby(level, as_index=False)[numeric].sum(min_count=1)
    if "Casos" in result:
        result["Positividad %"] = np.where(result["Casos"] > 0, result.get("Positivos", 0) / result["Casos"] * 100, np.nan)
        result["Letalidad %"] = np.where(result["Casos"] > 0, result.get("Defunciones", 0) / result["Casos"] * 100, np.nan)
    if "Población" in result:
        result["Incidencia /100k"] = np.where(result["Población"] > 0, result["Casos"] / result["Población"] * 100_000, np.nan)
        result["Mortalidad /100k"] = np.where(result["Población"] > 0, result.get("Defunciones", 0) / result["Población"] * 100_000, np.nan)
    return result


def build_comparison(suive: pd.DataFrame, sinave: pd.DataFrame, year: int, week_cutoff: int) -> pd.DataFrame:
    ycol = _year_col(sinave)
    rows = []
    for week in range(1, week_cutoff + 1):
        s = suive[(suive["Año"] == year) & (suive["SE"] == week)]["Casos"].sum()
        n = len(sinave[pd.to_numeric(sinave[ycol], errors="coerce").eq(year) & sinave["epi_week"].eq(week)])
        rows.append({"SE": week, "SUIVE": float(s), "SINAVE": int(n), "Diferencia": float(s) - n, "Razón SINAVE/SUIVE %": (n / s * 100) if s else np.nan})
    return pd.DataFrame(rows)


def nutrave_indicators(df: pd.DataFrame, year: int, month: int) -> pd.DataFrame:
    # Indicadores mensuales usan año/mes calendario de captura, no año epidemiológico.
    x = _base.month_filter(df, year, month)
    nflag = x["nutrave"].fillna("").map(_base._norm_text).isin(_base.YES)
    if nflag.any():
        x = x[nflag].copy()
    valid = x["capture_date"].notna() & x["first_contact"].notna()
    delta = (x["capture_date"] - x["first_contact"]).dt.days
    den_notif, num_notif = int((valid & delta.ge(0)).sum()), int((valid & delta.between(0, 1)).sum())
    qv, qe = x["quality_vibrio"].fillna("").map(_base._norm_text), x["quality_entero"].fillna("").map(_base._norm_text)
    processed = _base._yes(x["sample_vibrio"]) & _base._yes(x["sample_entero"]) & x["recv_vibrio"].notna() & x["recv_entero"].notna() & ~qv.str.contains("RECHAZ") & ~qe.str.contains("RECHAZ")
    den_class = int(processed.sum())
    dclass = (x["final_dx_date"] - x["first_contact"]).dt.days
    num_class = int((processed & x["final_dx_date"].notna() & dclass.between(0, 9)).sum())
    days, days_month = int(x["capture_date"].dropna().dt.normalize().nunique()), calendar.monthrange(year, month)[1]
    age = x["age_years"]; age_known = age.notna(); type_norm = x["eda_type"].fillna("").map(_base._norm_text)
    moderate_severe = type_norm.str.contains("MODER") | type_norm.str.contains("GRAV")
    eligible_u5 = age_known & age.lt(5) & moderate_severe
    eligible_5 = age_known & age.ge(5) & moderate_severe
    sampled_u5 = eligible_u5 & _base._yes(x["sample_vibrio"]) & _base._yes(x["sample_entero"]) & _base._yes(x["sample_virus"]) & x["recv_vibrio"].notna() & x["recv_entero"].notna() & x["recv_virus"].notna()
    sampled_5 = eligible_5 & _base._yes(x["sample_vibrio"]) & _base._yes(x["sample_entero"]) & x["recv_vibrio"].notna() & x["recv_entero"].notna()
    rows = [_base._indicator("Notificación oportuna de EDA", num_notif, den_notif, 100), _base._indicator("Clasificación oportuna de EDA", num_class, den_class, 80), _base._indicator("Cobertura de notificación de EDA", days, days_month, 80), _base._indicator("Muestreo EDA <5 años", int(sampled_u5.sum()), int(eligible_u5.sum()), 80), _base._indicator("Muestreo EDA ≥5 años", int(sampled_5.sum()), int(eligible_5.sum()), 80)]
    result = pd.DataFrame(rows); result["Nota"] = ""
    missing_age = int((~age_known & moderate_severe).sum())
    if missing_age:
        result.loc[result["Indicador"].str.startswith("Muestreo EDA"), "Nota"] = f"{missing_age} caso(s) moderado/grave sin edad excluidos"
    return result


def laboratory_indicators(df: pd.DataFrame, year: int, month: int) -> pd.DataFrame:
    result = _base.laboratory_indicators(df, year, month).copy()
    reject = result["Indicador"].eq("Muestras rechazadas")
    if reject.any():
        result.loc[reject, "Escala"] = np.where(result.loc[reject, "Cumple"].eq("Sí"), "Cumple estándar ≤10%", "Alarma >10%")
    return result


def audit_operational_definitions(df: pd.DataFrame, year: int, week_cutoff: int) -> pd.DataFrame:
    ycol = _year_col(df)
    subset = df[pd.to_numeric(df[ycol], errors="coerce").eq(year) & df["epi_week"].between(1, week_cutoff)].copy()
    # La función base espera 'year'; usar una copia permite reutilizar su lógica sin tocar el original.
    subset["year"] = year
    return _ORIGINAL_AUDIT(subset, year, week_cutoff)


def quality_issues(df: pd.DataFrame, year: int | None = None, week_cutoff: int | None = None) -> pd.DataFrame:
    """Devuelve una bitácora auditable de anomalías sin modificar la base fuente."""
    if df is None or df.empty:
        return pd.DataFrame(columns=["Folio", "Archivo", "Año epi", "SE", "Severidad", "Tipo", "Detalle"])
    x = df.copy(); ycol = _year_col(x)
    if year is not None:
        x = x[pd.to_numeric(x[ycol], errors="coerce").eq(year)]
    if week_cutoff is not None:
        x = x[x["epi_week"].between(1, week_cutoff, inclusive="both")]
    rows = []
    def add(mask, severity, kind, detail):
        for _, r in x[mask.fillna(False)].iterrows():
            rows.append({"Folio": r.get("folio", ""), "Archivo": r.get("_source", ""), "Año epi": r.get(ycol, np.nan), "SE": r.get("epi_week", np.nan), "Severidad": severity, "Tipo": kind, "Detalle": detail})
    add(x["epi_week"].isna() | ~x["epi_week"].between(1, 53), "Error", "Semana inválida", "SemanaInicio vacío o fuera de 1–53")
    add(x.get("epi_boundary", pd.Series(False, index=x.index)), "Info", "Cruce de año epidemiológico", "Semana 52/53 en enero o SE1 en diciembre: se conserva la semana y se ajusta el año epidemiológico")
    d = (x["capture_date"] - x["first_contact"]).dt.days
    add(x["capture_date"].notna() & x["first_contact"].notna() & d.lt(0), "Error", "Cronología captura", "Fec_captura anterior a Fec_Primer_Contacto")
    ddx = (x["final_dx_date"] - x["first_contact"]).dt.days
    add(x["final_dx_date"].notna() & x["first_contact"].notna() & ddx.lt(0), "Error", "Cronología diagnóstico", "Diagnóstico final anterior al primer contacto")
    dex = (x["exposure_date"] - x["onset_date"]).dt.days
    add(x["exposure_date"].notna() & x["onset_date"].notna() & dex.gt(1), "Revisar", "Fecha de consumo", "Fecha_Consumo posterior al inicio de síntomas")
    add(x["sonora_resident"] & ~x["municipality_known"] & x["municipality"].astype(str).str.strip().ne(""), "Revisar", "Municipio no homologado", "Municipio de residencia de Sonora no coincide con catálogo de 72 municipios")
    add(~x["sonora_resident"] & x["state_key"].ne(""), "Info", "Residente fuera de Sonora", "Se conserva en vigilancia, pero se excluye de tasas con denominador Sonora")
    add(x["sample_rejected"], "Operativo", "Muestra rechazada", "Rechazo detectado en diagnóstico o calidad de muestra")
    add(x["pending_result"], "Info", "Resultado pendiente", "Sin diagnóstico final o estudio aún en proceso")
    add(x.get("duplicate_folio_source", pd.Series(False, index=x.index)), "Revisar", "Folio repetido entre fuentes", "Se detectó el folio en más de un archivo; POPIS conserva la versión más reciente")
    return pd.DataFrame(rows)


def quality_summary(issues: pd.DataFrame) -> pd.DataFrame:
    if issues is None or issues.empty:
        return pd.DataFrame(columns=["Severidad", "Tipo", "Registros"])
    return issues.groupby(["Severidad", "Tipo"], as_index=False).size().rename(columns={"size": "Registros"}).sort_values(["Severidad", "Registros"], ascending=[True, False])


def parse_suive_history(file_obj, filename: str, preferred_sheet: str = "SUIVE") -> pd.DataFrame:
    """Parser más estricto: favorece series semanales enteras y de mayor escala (casos, no tasas)."""
    data = file_obj.read() if hasattr(file_obj, "read") else Path(file_obj).read_bytes()
    suffix = Path(filename).suffix.lower(); engine = "openpyxl" if suffix in {".xlsx", ".xlsm"} else "xlrd"
    xl = pd.ExcelFile(BytesIO(data), engine=engine); sheet = preferred_sheet if preferred_sheet in xl.sheet_names else xl.sheet_names[0]
    raw = pd.read_excel(BytesIO(data), sheet_name=sheet, header=None, engine=engine)
    candidates = []
    for r in range(len(raw)):
        row = raw.iloc[r]
        for c, value in enumerate(row):
            try: yr = int(float(value))
            except Exception: continue
            if not 1990 <= yr <= 2100: continue
            vals = pd.to_numeric(row.iloc[c+1:c+54], errors="coerce")
            plausible = vals.dropna()
            if len(plausible) < 4 or (plausible < 0).any(): continue
            integer_ratio = float(np.isclose(plausible, np.round(plausible), atol=1e-6).mean())
            median = float(plausible.median()) if len(plausible) else 0
            score = integer_ratio * 1000 + min(len(plausible), 53) * 10 + np.log1p(max(median, 0))
            candidates.append((yr, score, vals))
            break
    if not candidates:
        return _ORIGINAL_PARSE_SUIVE(BytesIO(data), filename, preferred_sheet)
    selected = {}
    for yr, score, vals in candidates:
        if yr not in selected or score > selected[yr][0]: selected[yr] = (score, vals)
    records = []
    for yr, (_, vals) in sorted(selected.items()):
        for se, value in enumerate(vals, 1):
            if pd.notna(value): records.append({"Año": int(yr), "SE": int(se), "Casos": float(value)})
    out = pd.DataFrame(records)
    if out.empty: raise ValueError("No se detectó una serie semanal SUIVE válida")
    return out


def apply_patches() -> None:
    """Instala las funciones corregidas antes de cargar la UI."""
    _base.normalize_sinave = normalize_sinave
    _base.combine_sinave = combine_sinave
    _base.sinave_weekly = sinave_weekly
    _base.pathogen_summary = pathogen_summary
    _base.sinave_summary = sinave_summary
    _base.territorial_summary = territorial_summary
    _base.build_comparison = build_comparison
    _base.nutrave_indicators = nutrave_indicators
    _base.laboratory_indicators = laboratory_indicators
    _base.audit_operational_definitions = audit_operational_definitions
    _base.parse_suive_history = parse_suive_history
    _base.quality_issues = quality_issues
    _base.quality_summary = quality_summary
    _base.aggregate_territory = aggregate_territory
