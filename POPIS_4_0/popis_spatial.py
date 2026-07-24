"""Motor espacial POPIS 4.3.

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


def _norm(value: object) -> str:
    text = "" if value is None or (isinstance(value, float) and math.isnan(value)) else str(value)
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


def address_table(df: pd.DataFrame) -> pd.DataFrame:
    """Extrae campos geográficos sin incluir nombre, CURP, teléfono u otros identificadores."""
    if df is None or df.empty:
        return pd.DataFrame()
    out = pd.DataFrame(index=df.index)
    out["Folio"] = _series(df, "folio", "Folio").astype(str).str.strip()
    out["Calle"] = _series(df, "Calle").astype(str).str.strip()
    out["Num exterior"] = _series(df, "Num_Exterior", "Num Exterior").astype(str).str.strip()
    out["Num interior"] = _series(df, "Num_Interior", "Num Interior").astype(str).str.strip()
    out["Colonia"] = _series(df, "Colonia").astype(str).str.strip()
    out["CP"] = _series(df, "CP", "Codigo Postal", "Código Postal").astype(str).str.strip()
    out["Localidad"] = _series(df, "Loc_Res", "Localidad_Residencia", "locality").astype(str).str.strip()
    mun = _series(df, "municipality", "Mun_Res", "Municipio_Residencia", "Municipio")
    out["Municipio"] = mun.map(canonical_municipality)
    out["Estado"] = _series(df, "state_residence", "Edo_Res", "Ent_Res", "Entidad").astype(str).str.strip()
    out["Entre calle"] = _series(df, "Entre_Calle").astype(str).str.strip()
    out["Y calle"] = _series(df, "Y_Calle").astype(str).str.strip()

    def full_address(r):
        street = " ".join(x for x in [r["Calle"], r["Num exterior"]] if x and x.lower() != "nan")
        return ", ".join(x for x in [street, r["Colonia"], r["Localidad"], r["Municipio"], "Sonora", r["CP"]] if x and str(x).lower() != "nan")

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
        "Folio": df[fcol].astype(str).str.strip() if fcol else "",
        "address_key": df[acol].astype(str).str.strip() if acol else "",
        "Latitud": pd.to_numeric(df[lat], errors="coerce"),
        "Longitud": pd.to_numeric(df[lon], errors="coerce"),
        "Precisión": df[_col(df, "Precisión", "Precision")].astype(str) if _col(df, "Precisión", "Precision") else "Exacta institucional",
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
    # Coordenadas ya presentes en la base, si aparecen en futuras exportaciones.
    lat_raw = _col(df, "Latitud", "Latitude", "LAT")
    lon_raw = _col(df, "Longitud", "Longitude", "LON", "LNG")
    if lat_raw and lon_raw:
        latv=pd.to_numeric(df[lat_raw],errors="coerce"); lonv=pd.to_numeric(df[lon_raw],errors="coerce"); ok=latv.notna()&lonv.notna(); a.loc[ok,"Latitud"]=latv[ok]; a.loc[ok,"Longitud"]=lonv[ok]; a.loc[ok,"Precisión"]="Exacta en SINAVE"
    exact = load_exact_geocodes()
    if not exact.empty:
        by_f = exact[exact["Folio"].astype(str).str.strip().ne("")].drop_duplicates("Folio",keep="last").set_index("Folio")
        by_a = exact[exact["address_key"].astype(str).str.strip().ne("")].drop_duplicates("address_key",keep="last").set_index("address_key")
        for idx,r in a.iterrows():
            match = None
            if r["Folio"] in by_f.index: match=by_f.loc[r["Folio"]]
            elif r["address_key"] in by_a.index: match=by_a.loc[r["address_key"]]
            if match is not None:
                a.at[idx,"Latitud"]=float(match["Latitud"]); a.at[idx,"Longitud"]=float(match["Longitud"]); a.at[idx,"Precisión"]=str(match.get("Precisión","Exacta institucional"))
    a["Distrito"] = a["Municipio"].map(district_for_municipality)
    return a


def spatial_subset(sinave: pd.DataFrame, year: int, week_start: int, week_end: int, district: str="Todos", municipality: str="Todos", pathogen: str="Todos los casos") -> pd.DataFrame:
    ycol = "epi_year" if "epi_year" in sinave.columns else "year"
    mask = pd.to_numeric(sinave[ycol],errors="coerce").eq(year) & pd.to_numeric(sinave["epi_week"],errors="coerce").between(week_start,week_end)
    x=sinave[mask].copy()
    if pathogen != "Todos los casos":
        col=f"path_{pathogen}"; x=x[x[col].fillna(False)] if col in x else x.iloc[0:0]
    geo=merge_coordinates(x,True)
    geo["_row_index"] = x.index
    if district!="Todos": geo=geo[geo["Distrito"].eq(district)]
    if municipality!="Todos": geo=geo[geo["Municipio"].map(canonical_municipality).eq(canonical_municipality(municipality))]
    onset = x.loc[geo["_row_index"],"onset_date"] if "onset_date" in x else pd.Series(pd.NaT,index=geo.index)
    geo["Fecha inicio"] = pd.to_datetime(onset.values,errors="coerce")
    return geo.dropna(subset=["Latitud","Longitud"]).reset_index(drop=True)


def coverage(points: pd.DataFrame) -> pd.DataFrame:
    if points is None or points.empty: return pd.DataFrame(columns=["Precisión","Casos"])
    return points.groupby("Precisión",as_index=False).size().rename(columns={"size":"Casos"}).sort_values("Casos",ascending=False)


def haversine_km(lat1,lon1,lat2,lon2):
    R=6371.0088
    p1,p2=math.radians(lat1),math.radians(lat2); dp=math.radians(lat2-lat1); dl=math.radians(lon2-lon1)
    a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))


def detect_clusters(points: pd.DataFrame, radius_km: float=1.0, min_cases: int=3, max_days: int=7, exact_only: bool=True) -> tuple[pd.DataFrame,pd.DataFrame]:
    if points is None or points.empty: return pd.DataFrame(),pd.DataFrame()
    p=points.copy()
    if exact_only: p=p[p["Precisión"].str.startswith("Exacta",na=False)].copy()
    p=p.dropna(subset=["Latitud","Longitud","Fecha inicio"]).reset_index(drop=True)
    n=len(p)
    if n==0: return p,pd.DataFrame()
    parent=list(range(n))
    def find(a):
        while parent[a]!=a: parent[a]=parent[parent[a]]; a=parent[a]
        return a
    def union(a,b):
        ra,rb=find(a),find(b)
        if ra!=rb: parent[rb]=ra
    dates=pd.to_datetime(p["Fecha inicio"])
    for i in range(n):
        for j in range(i+1,n):
            if abs((dates.iloc[i]-dates.iloc[j]).days)>max_days: continue
            if haversine_km(float(p.at[i,"Latitud"]),float(p.at[i,"Longitud"]),float(p.at[j,"Latitud"]),float(p.at[j,"Longitud"]))<=radius_km: union(i,j)
    groups={}
    for i in range(n): groups.setdefault(find(i),[]).append(i)
    groups=[g for g in groups.values() if len(g)>=min_cases]
    rows=[]
    p["Cluster"]=""
    for k,g in enumerate(sorted(groups,key=len,reverse=True),1):
        label=f"C{k:02d}"; p.loc[g,"Cluster"]=label; q=p.loc[g]
        rows.append({"Cluster":label,"Casos":len(q),"Inicio":q["Fecha inicio"].min(),"Fin":q["Fecha inicio"].max(),"Días":int((q["Fecha inicio"].max()-q["Fecha inicio"].min()).days)+1,"Distrito":q["Distrito"].mode().iloc[0] if not q["Distrito"].mode().empty else "","Municipio":q["Municipio"].mode().iloc[0] if not q["Municipio"].mode().empty else "","Latitud centro":q["Latitud"].mean(),"Longitud centro":q["Longitud"].mean(),"Señal":"Alta" if len(q)>=10 else "Alerta" if len(q)>=5 else "Vigilar"})
    return p[p["Cluster"].ne("")].copy(),pd.DataFrame(rows)


def grid_concentration(points: pd.DataFrame, cell_km: float=0.5) -> pd.DataFrame:
    if points is None or points.empty: return pd.DataFrame()
    p=points.dropna(subset=["Latitud","Longitud"]).copy(); lat0=float(p["Latitud"].mean()); cos0=max(math.cos(math.radians(lat0)),0.1)
    p["_x"] = p["Longitud"]*111.320*cos0; p["_y"] = p["Latitud"]*110.574
    p["Celda X"] = np.floor(p["_x"]/cell_km).astype(int); p["Celda Y"] = np.floor(p["_y"]/cell_km).astype(int)
    g=p.groupby(["Celda X","Celda Y"],as_index=False).agg(Casos=("Folio","size"),Latitud=("Latitud","mean"),Longitud=("Longitud","mean"),Distrito=("Distrito",lambda x:x.mode().iloc[0] if not x.mode().empty else ""),Municipio=("Municipio",lambda x:x.mode().iloc[0] if not x.mode().empty else ""))
    return g.sort_values("Casos",ascending=False,ignore_index=True)
