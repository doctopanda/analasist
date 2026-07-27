"""Motor espacial POPIS 4.6.1.

Principios:
- Los datos nominales permanecen locales.
- No se envían domicilios a servicios públicos de geocodificación.
- INEGI se usa para centroides de localidad/municipio enviando únicamente claves/nombres geográficos.
- Coordenadas exactas pueden provenir de la propia base o de un archivo geocodificado institucional.
- Los análisis de brote usan coordenadas exactas por defecto para evitar falsos conglomerados por centroides.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import json
import math
import re
import unicodedata

import numpy as np
import pandas as pd
import requests

from popis_core_patch import DISTRICTS, canonical_municipality

ROOT = Path(__file__).resolve().parent
GEO_DIR = ROOT / "data" / "geografia"
GEOCODE_FILE = GEO_DIR / "geocodificados.csv"
INEGI_DIR = GEO_DIR / "inegi"


def _is_missing(value: object) -> bool:
    """True para None/NaN/pd.NA/NaT sin romper con tipos escalares diversos."""
    if value is None:
        return True
    try:
        result = pd.isna(value)
        return bool(result) if np.isscalar(result) else False
    except Exception:
        return False


def _safe_text(value: object, numeric_identifier: bool = False) -> str:
    """Convierte de forma segura una celda de domicilio a texto.

    Excel suele convertir números exteriores y CP a float (123 -> 123.0). Para
    identificadores numéricos se elimina únicamente el .0 artificial.
    """
    if _is_missing(value):
        return ""
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if isinstance(value, (float, np.floating)):
        if not np.isfinite(float(value)):
            return ""
        return str(int(value)) if float(value).is_integer() else str(value).strip()
    text = str(value).strip()
    if text.upper() in {"NAN", "NONE", "<NA>", "NAT", "NULL"}:
        return ""
    if numeric_identifier and re.fullmatch(r"[+-]?\d+\.0+", text):
        return text.split(".", 1)[0]
    return text


def _norm(value: object) -> str:
    text = _safe_text(value)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", text.strip()).upper()


def _col(df: pd.DataFrame, *names: str):
    lookup = {_norm(c): c for c in df.columns}
    for name in names:
        if _norm(name) in lookup:
            return lookup[_norm(name)]
    return None


def ensure_geo_tree() -> None:
    GEO_DIR.mkdir(parents=True, exist_ok=True)
    INEGI_DIR.mkdir(parents=True, exist_ok=True)


def _series(df: pd.DataFrame, *names: str) -> pd.Series:
    c = _col(df, *names)
    return df[c] if c else pd.Series("", index=df.index, dtype="object")


def _text_series(df: pd.DataFrame, *names: str, numeric_identifier: bool = False) -> pd.Series:
    return _series(df, *names).map(lambda v: _safe_text(v, numeric_identifier=numeric_identifier))


def address_table(df: pd.DataFrame) -> pd.DataFrame:
    """Extrae campos geográficos sin incluir nombre, CURP, teléfono u otros identificadores."""
    if df is None or df.empty:
        return pd.DataFrame()
    out = pd.DataFrame(index=df.index)
    out["Folio"] = _text_series(df, "folio", "Folio", numeric_identifier=True)
    out["Calle"] = _text_series(df, "Calle")
    out["Num exterior"] = _text_series(df, "Num_Exterior", "Num Exterior", numeric_identifier=True)
    out["Num interior"] = _text_series(df, "Num_Interior", "Num Interior", numeric_identifier=True)
    out["Colonia"] = _text_series(df, "Colonia")
    out["CP"] = _text_series(df, "CP", "Codigo Postal", "Código Postal", numeric_identifier=True)
    out["Localidad"] = _text_series(df, "Loc_Res", "Localidad_Residencia", "locality")
    mun = _series(df, "municipality", "Mun_Res", "Municipio_Residencia", "Municipio")
    out["Municipio"] = mun.map(lambda v: _safe_text(canonical_municipality(v)))
    out["Estado"] = _text_series(df, "state_residence", "Edo_Res", "Ent_Res", "Entidad")
    out["Entre calle"] = _text_series(df, "Entre_Calle")
    out["Y calle"] = _text_series(df, "Y_Calle")

    def full_address(r):
        street_parts = [_safe_text(r.get("Calle")), _safe_text(r.get("Num exterior"), numeric_identifier=True)]
        street = " ".join(x for x in street_parts if x)
        parts = [
            street,
            _safe_text(r.get("Colonia")),
            _safe_text(r.get("Localidad")),
            _safe_text(r.get("Municipio")),
            "Sonora",
            _safe_text(r.get("CP"), numeric_identifier=True),
        ]
        return ", ".join(x for x in parts if x)

    out["Domicilio normalizado"] = out.apply(full_address, axis=1)
    out["address_key"] = out["Domicilio normalizado"].map(lambda x: sha256(_norm(x).encode("utf-8")).hexdigest()[:24] if _norm(x) else "")
    has_street = out["Calle"].map(_norm).ne("")
    has_num = out["Num exterior"].map(_norm).ne("") & ~out["Num exterior"].map(_norm).isin({"SN", "S/N", "SIN NUMERO", "NAN"})
    has_col = out["Colonia"].map(_norm).ne("")
    has_loc = out["Localidad"].map(_norm).ne("")
    has_mun = out["Municipio"].map(_norm).ne("")
    out["Calidad domicilio"] = np.select(
        [has_street & has_num & has_col & has_mun, has_street & has_col & has_mun, has_loc & has_mun, has_mun],
        ["Dirección completa", "Calle + colonia", "Localidad", "Municipio"],
        default="Insuficiente",
    )
    return out


def district_for_municipality(municipality: object) -> str:
    target = _norm(canonical_municipality(municipality))
    for district, municipalities in DISTRICTS.items():
        if target in {_norm(m) for m in municipalities}:
            return district
    return "No asignado / revisar"


def load_exact_geocodes() -> pd.DataFrame:
    ensure_geo_tree()
    if not GEOCODE_FILE.exists():
        return pd.DataFrame(columns=["Folio", "address_key", "Latitud", "Longitud", "Precisión"])
    try:
        x = pd.read_csv(GEOCODE_FILE, dtype={"Folio": str, "address_key": str})
    except Exception:
        return pd.DataFrame(columns=["Folio", "address_key", "Latitud", "Longitud", "Precisión"])
    for c in ["Latitud", "Longitud"]:
        if c in x: x[c] = pd.to_numeric(x[c], errors="coerce")
    return x.dropna(subset=["Latitud", "Longitud"])


def save_exact_geocodes(uploaded) -> Path:
    """Guarda solo folio/hash/coordenadas; nunca persiste el domicilio en texto plano."""
    ensure_geo_tree()
    name = getattr(uploaded, "name", "geocodificados.csv")
    data = uploaded.getvalue() if hasattr(uploaded, "getvalue") else uploaded.read()
    if Path(name).suffix.lower() in {".xlsx", ".xlsm", ".xls"}:
        engine = "openpyxl" if Path(name).suffix.lower() != ".xls" else "xlrd"
        df = pd.read_excel(BytesIO(data), engine=engine)
    else:
        df = pd.read_csv(BytesIO(data))
    fcol = _col(df, "Folio")
    acol = _col(df, "address_key", "Hash domicilio")
    lat = _col(df, "Latitud", "Latitude", "LAT")
    lon = _col(df, "Longitud", "Longitude", "LON", "LNG")
    if not lat or not lon or (not fcol and not acol):
        raise ValueError("El archivo debe incluir Latitud, Longitud y Folio o address_key.")
    out = pd.DataFrame({
        "Folio": df[fcol].map(lambda v: _safe_text(v, numeric_identifier=True)) if fcol else "",
        "address_key": df[acol].map(_safe_text) if acol else "",
        "Latitud": pd.to_numeric(df[lat], errors="coerce"),
        "Longitud": pd.to_numeric(df[lon], errors="coerce"),
        "Precisión": df[_col(df, "Precisión", "Precision")].map(_safe_text) if _col(df, "Precisión", "Precision") else "Exacta institucional",
    }).dropna(subset=["Latitud", "Longitud"])
    old = load_exact_geocodes()
    all_rows = pd.concat([old, out], ignore_index=True)
    key = np.where(all_rows["Folio"].astype(str).str.strip().ne(""), "F:" + all_rows["Folio"].astype(str), "A:" + all_rows["address_key"].astype(str))
    all_rows = all_rows.assign(_k=key).drop_duplicates("_k", keep="last").drop(columns="_k")
    all_rows.to_csv(GEOCODE_FILE, index=False, encoding="utf-8-sig")
    return GEOCODE_FILE


def pending_geocoding_export(df: pd.DataFrame) -> bytes:
    """CSV local para un SIG/geocodificador institucional; contiene domicilio sensible."""
    a = address_table(df)
    exact = load_exact_geocodes()
    known_f = set(exact["Folio"].dropna().astype(str))
    known_a = set(exact["address_key"].dropna().astype(str))
    pending = a[~a["Folio"].isin(known_f) & ~a["address_key"].isin(known_a)].copy()
    cols = ["Folio", "address_key", "Calle", "Num exterior", "Num interior", "Colonia", "CP", "Localidad", "Municipio", "Estado", "Entre calle", "Y calle", "Domicilio normalizado"]
    return pending[cols].to_csv(index=False).encode("utf-8-sig")


def _json_records(payload) -> list[dict]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in ["data", "datos", "features"]:
            value = payload.get(key)
            if isinstance(value, list):
                if key == "features":
                    return [x.get("properties", {}) | {"_geometry": x.get("geometry")} for x in value if isinstance(x, dict)]
                return [x for x in value if isinstance(x, dict)]
        for value in payload.values():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                return value
    return []


def _municipality_catalog() -> pd.DataFrame:
    ensure_geo_tree(); cache = INEGI_DIR / "municipios_sonora.json"
    if cache.exists():
        payload = json.loads(cache.read_text(encoding="utf-8"))
    else:
        r = requests.get("https://gaia.inegi.org.mx/wscatgeo/v2/mgem/26", timeout=30); r.raise_for_status(); payload = r.json(); cache.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    rows = _json_records(payload)
    return pd.DataFrame(rows)


def _localities_for(municipality: str) -> pd.DataFrame:
    cat = _municipality_catalog()
    if cat.empty: return pd.DataFrame()
    ncol = _col(cat, "nomgeo", "nombre") or cat.columns[0]
    ccol = _col(cat, "cve_mun", "cve_municipio")
    if not ccol: return pd.DataFrame()
    target = _norm(canonical_municipality(municipality))
    hit = cat[cat[ncol].map(_norm).eq(target)]
    if hit.empty: return pd.DataFrame()
    cve = str(hit.iloc[0][ccol]).zfill(3)
    cache = INEGI_DIR / f"localidades_26_{cve}.json"
    if cache.exists(): payload = json.loads(cache.read_text(encoding="utf-8"))
    else:
        r = requests.get(f"https://gaia.inegi.org.mx/wscatgeo/v2/localidades/26/{cve}", timeout=30); r.raise_for_status(); payload = r.json(); cache.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return pd.DataFrame(_json_records(payload))


def add_approximate_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    """Asigna centroides INEGI de localidad; si no coincide usa la localidad más poblada del municipio."""
    a = address_table(df)
    a["Latitud"] = np.nan; a["Longitud"] = np.nan; a["Precisión"] = "Sin coordenada"
    for municipality in sorted(x for x in a["Municipio"].dropna().astype(str).unique() if x):
        mask = a["Municipio"].eq(municipality)
        try: locs = _localities_for(municipality)
        except Exception: continue
        if locs.empty: continue
        ncol = _col(locs, "nomgeo", "nombre", "nom_loc")
        lat = _col(locs, "latitud", "lat")
        lon = _col(locs, "longitud", "lon", "lng")
        pcol = _col(locs, "pob_total", "poblacion")
        if not ncol or not lat or not lon: continue
        locs = locs.copy(); locs[lat]=pd.to_numeric(locs[lat],errors="coerce"); locs[lon]=pd.to_numeric(locs[lon],errors="coerce"); locs=locs.dropna(subset=[lat,lon])
        if locs.empty: continue
        if pcol: locs["_p"] = pd.to_numeric(locs[pcol],errors="coerce").fillna(0)
        else: locs["_p"] = 0
        fallback = locs.sort_values("_p",ascending=False).iloc[0]
        for idx in a.index[mask]:
            lname = _norm(a.at[idx,"Localidad"])
            match = locs[locs[ncol].map(_norm).eq(lname)] if lname else pd.DataFrame()
            row = match.iloc[0] if not match.empty else fallback
            a.at[idx,"Latitud"] = float(row[lat]); a.at[idx,"Longitud"] = float(row[lon])
            a.at[idx,"Precisión"] = "Localidad INEGI" if not match.empty else "Municipio/cabecera INEGI"
    return a


def merge_coordinates(df: pd.DataFrame, use_inegi_fallback: bool = True) -> pd.DataFrame:
    a = add_approximate_coordinates(df) if use_inegi_fallback else address_table(df).assign(Latitud=np.nan,Longitud=np.nan,Precisión="Sin coordenada")
    lat_raw = _col(df, "Latitud", "Latitude", "LAT")
    lon_raw = _col(df, "Longitud", "Longitude", "LON", "LNG")
    if lat_raw and lon_raw:
        latv=pd.to_numeric(df[lat_raw],errors="coerce"); lonv=pd.to_numeric(df[lon_raw],errors="coerce"); ok=latv.notna()&lonv.notna(); a.loc[ok,"Latitud"]=latv[ok]; a.loc[ok,"Longitud"]=lonv[ok]; a.loc[ok,"Precisión"]="Exacta SINAVE"
    exact=load_exact_geocodes()
    if not exact.empty:
        by_f={str(r.Folio):r for _,r in exact.iterrows() if str(r.Folio).strip() and str(r.Folio).lower()!="nan"}; by_a={str(r.address_key):r for _,r in exact.iterrows() if str(r.address_key).strip() and str(r.address_key).lower()!="nan"}
        for idx,r in a.iterrows():
            hit=by_f.get(str(r["Folio"])) or by_a.get(str(r["address_key"]))
            if hit is not None: a.at[idx,"Latitud"]=float(hit.Latitud); a.at[idx,"Longitud"]=float(hit.Longitud); a.at[idx,"Precisión"]=getattr(hit,"Precisión","Exacta institucional")
    return a


def haversine_km(lat1,lon1,lat2,lon2):
    R=6371.0088; p1,p2=math.radians(lat1),math.radians(lat2); dp=math.radians(lat2-lat1); dl=math.radians(lon2-lon1); q=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2; return 2*R*math.asin(math.sqrt(q))


def spatial_clusters(points: pd.DataFrame, radius_km: float=1.0, min_cases: int=3, days: int=7) -> pd.DataFrame:
    if points is None or points.empty: return pd.DataFrame()
    x=points.dropna(subset=["Latitud","Longitud"]).copy(); x["Fecha"]=pd.to_datetime(x.get("onset_date"),errors="coerce",dayfirst=True)
    if x.empty: return pd.DataFrame()
    idx=list(x.index); adj={i:set() for i in idx}
    for a_i,i in enumerate(idx):
        for j in idx[a_i+1:]:
            if x.at[i,"Fecha"] is not pd.NaT and x.at[j,"Fecha"] is not pd.NaT and pd.notna(x.at[i,"Fecha"]) and pd.notna(x.at[j,"Fecha"]):
                if abs((x.at[i,"Fecha"]-x.at[j,"Fecha"]).days)>days: continue
            if haversine_km(float(x.at[i,"Latitud"]),float(x.at[i,"Longitud"]),float(x.at[j,"Latitud"]),float(x.at[j,"Longitud"]))<=radius_km: adj[i].add(j); adj[j].add(i)
    seen=set(); rows=[]; cid=0
    for i in idx:
        if i in seen: continue
        stack=[i]; comp=[]
        while stack:
            q=stack.pop()
            if q in seen: continue
            seen.add(q); comp.append(q); stack.extend(adj[q]-seen)
        if len(comp)<min_cases: continue
        cid+=1; sub=x.loc[comp]; dates=sub["Fecha"].dropna();
        rows.append({"Cluster":f"C{cid:02d}","Casos":len(sub),"Inicio":dates.min() if len(dates) else pd.NaT,"Fin":dates.max() if len(dates) else pd.NaT,"Latitud":sub["Latitud"].mean(),"Longitud":sub["Longitud"].mean(),"Radio usado km":radius_km})
    return pd.DataFrame(rows).sort_values("Casos",ascending=False) if rows else pd.DataFrame()


def grid_counts(points: pd.DataFrame, cell_km: float=1.0) -> pd.DataFrame:
    if points is None or points.empty: return pd.DataFrame()
    x=points.dropna(subset=["Latitud","Longitud"]).copy()
    if x.empty: return pd.DataFrame()
    lat0=float(x["Latitud"].mean()); dy=cell_km/111.32; dx=cell_km/(111.32*max(math.cos(math.radians(lat0)),.01)); x["gy"]=np.floor(x["Latitud"]/dy).astype(int); x["gx"]=np.floor(x["Longitud"]/dx).astype(int); return x.groupby(["gx","gy"],as_index=False).agg(Casos=("Folio","size"),Latitud=("Latitud","mean"),Longitud=("Longitud","mean")).sort_values("Casos",ascending=False)
