from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

import folium
import numpy as np
import pandas as pd
import requests
from folium.plugins import HeatMap

from .io_utils import first_existing, norm_key, read_table

INEGI_SONORA_MUNICIPIOS = "https://gaia.inegi.org.mx/wscatgeo/v2/geo/mgem/26"
MUNICIPALITY_CANDIDATES = ["Mun_Res", "Municipio residencia", "Municipio_Residencia", "MUNICIPIO_RESIDENCIA", "Municipio", "MUNICIPIO"]


def load_geojson(path: str | Path | None) -> dict[str, Any] | None:
    if not path:
        return None
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def ensure_sonora_geojson(root: str | Path, timeout: int = 20) -> Path | None:
    """Descarga únicamente cartografía oficial. No envía datos de pacientes."""
    root = Path(root)
    target = root / "data/geografia/municipios_sonora.geojson"
    if target.exists() and target.stat().st_size > 500:
        return target
    try:
        response = requests.get(INEGI_SONORA_MUNICIPIOS, timeout=timeout)
        response.raise_for_status()
        obj = response.json()
        if isinstance(obj, list) and len(obj) == 1 and isinstance(obj[0], dict) and obj[0].get("type") == "FeatureCollection":
            obj = obj[0]
        if isinstance(obj, dict) and "data" in obj and isinstance(obj["data"], dict):
            obj = obj["data"]
        if not (isinstance(obj, dict) and obj.get("type") == "FeatureCollection"):
            return None
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
        return target
    except Exception:
        return None


def _iter_pairs(value: Any):
    if isinstance(value, (list, tuple)):
        if len(value) >= 2 and isinstance(value[0], (int, float)) and isinstance(value[1], (int, float)):
            yield float(value[0]), float(value[1])
        else:
            for item in value:
                yield from _iter_pairs(item)


def detect_geo_name_property(geojson: dict[str, Any]) -> str | None:
    features = geojson.get("features") or []
    if not features:
        return None
    props = features[0].get("properties") or {}
    return first_existing(props.keys(), ["nomgeo", "NOMGEO", "NOM_MUN", "Municipio", "MUNICIPIO", "name"])


def municipal_centroids(geojson: dict[str, Any] | None) -> dict[str, tuple[float, float, str]]:
    if not geojson:
        return {}
    prop = detect_geo_name_property(geojson)
    if not prop:
        return {}
    centers: dict[str, tuple[float, float, str]] = {}
    for feature in geojson.get("features") or []:
        name = str((feature.get("properties") or {}).get(prop, "")).strip()
        pairs = list(_iter_pairs((feature.get("geometry") or {}).get("coordinates")))
        if not name or not pairs:
            continue
        lons = np.asarray([x for x, _ in pairs], dtype=float)
        lats = np.asarray([y for _, y in pairs], dtype=float)
        lat = float((np.nanmin(lats) + np.nanmax(lats)) / 2)
        lon = float((np.nanmin(lons) + np.nanmax(lons)) / 2)
        centers[norm_key(name)] = (lat, lon, name)
    return centers


def filter_sonora_residents(base: pd.DataFrame) -> pd.DataFrame:
    work = base.copy()
    ent_col = first_existing(work.columns, ["Cve_Edo_Res", "CVE_EDO_RES", "Entidad_Res", "Entidad residencia"])
    mun_code = first_existing(work.columns, ["Cve_Mun_Res", "CVE_MPO_RES", "CVE_MUN_RES", "Mun_Res_Clave", "CVE_MUN"])
    if ent_col:
        ent = pd.to_numeric(work[ent_col], errors="coerce")
        if ent.notna().any():
            work = work[ent.eq(26)].copy()
    if mun_code:
        mun = pd.to_numeric(work[mun_code], errors="coerce")
        if mun.notna().any():
            work = work[mun.between(1, 72)].copy()
    return work


def _read_population_source(path: Path) -> pd.DataFrame | None:
    """Lee población simple o el libro oficial municipal cuya hoja útil es `Sonora`."""
    attempts: list[str | int] = []
    if path.suffix.lower() in {".xlsx", ".xls", ".xlsm"}:
        # Intento directo primero. Así funciona aunque README/Portada sea la hoja activa.
        attempts.extend(["Sonora", "SONORA"])
    attempts.append(0)

    seen: set[str] = set()
    for sheet in attempts:
        key = str(sheet)
        if key in seen:
            continue
        seen.add(key)
        try:
            df = read_table(path, sheet_name=sheet)
        except Exception:
            continue
        mun_col = first_existing(df.columns, ["MUN", "Municipio", "MUNICIPIO", "NOM_MUN", "NOMGEO", "DES_MPO_RES"])
        pop_col = first_existing(df.columns, ["POB", "Poblacion", "POBLACION", "Población", "Total", "TOTAL"])
        age_cols = [c for c in df.columns if str(c).lower().startswith(("pobm_", "pobh_"))]
        if mun_col and (pop_col or age_cols):
            return df
    return None


def normalize_population(path: str | Path | None, year: int | None = None) -> pd.DataFrame | None:
    """Normaliza población municipal para incidencia.

    Admite dos familias de fuente:
    1) tabla simple Municipio/Población/Año;
    2) `Sonora.ProyeccionesPoblacionMunicipales2015-2030.xlsx`, hoja `Sonora`,
       con CLAVE, CLAVE_ENT, NOM_ENT, MUN, SEXO, AÑO, EDAD_QUIN y POB.
    """
    if not path:
        return None
    path = Path(path)
    df = _read_population_source(path)
    if df is None or df.empty:
        return None

    mun_col = first_existing(df.columns, ["MUN", "Municipio", "MUNICIPIO", "NOM_MUN", "NOMGEO", "DES_MPO_RES"])
    pop_col = first_existing(df.columns, ["POB", "Poblacion", "POBLACION", "Población", "Total", "TOTAL"])
    year_col = first_existing(df.columns, ["Año", "AÑO", "ANIO", "ANO", "Anio", "year"])
    entity_col = first_existing(df.columns, ["CLAVE_ENT", "CVE_ENT", "ENTIDAD", "CVE_EDO"])
    sex_col = first_existing(df.columns, ["SEXO", "Sexo", "sex"])
    key_col = first_existing(df.columns, ["CLAVE", "CVE_GEO", "CVE_MUN", "CLAVE_MUN"])

    if not mun_col:
        return None

    work = df.copy()

    if entity_col:
        entity = pd.to_numeric(work[entity_col], errors="coerce")
        if entity.notna().any():
            sonora = work[entity.eq(26)]
            if not sonora.empty:
                work = sonora

    if year_col and year is not None:
        years = pd.to_numeric(work[year_col], errors="coerce")
        exact = work[years.eq(int(year))]
        if not exact.empty:
            work = exact
        else:
            return None

    if sex_col:
        sex_norm = work[sex_col].fillna("").astype(str).map(norm_key)
        hm = {"HOMBRES", "HOMBRE", "MUJERES", "MUJER", "MASCULINO", "FEMENINO"}
        if sex_norm.isin(hm).any():
            work = work[sex_norm.isin(hm)].copy()

    if pop_col:
        work["Poblacion"] = pd.to_numeric(
            work[pop_col].astype(str).str.replace(",", "", regex=False).str.replace(" ", "", regex=False),
            errors="coerce",
        )
    else:
        age_cols = [c for c in work.columns if str(c).lower().startswith(("pobm_", "pobh_"))]
        if not age_cols:
            return None
        numeric = work[age_cols].apply(pd.to_numeric, errors="coerce")
        work["Poblacion"] = numeric.sum(axis=1, min_count=1)

    work["Municipio"] = work[mun_col].fillna("").astype(str).str.strip()
    work["__mun_key"] = work["Municipio"].map(norm_key)

    if key_col:
        code = work[key_col].fillna("").astype(str).str.extract(r"(\d+)", expand=False)
        code = code.str.zfill(5)
        work["CVE_GEO"] = code
        work["CVE_MUN"] = pd.to_numeric(code.str[-3:], errors="coerce").astype("Int64")

    work = work[work["Municipio"].ne("") & work["Poblacion"].notna() & work["Poblacion"].ge(0)]
    if work.empty:
        return None

    result = work.groupby(["__mun_key", "Municipio"], as_index=False)["Poblacion"].sum(min_count=1)

    if "CVE_GEO" in work.columns:
        result = result.merge(work.groupby("__mun_key", as_index=False)["CVE_GEO"].first(), on="__mun_key", how="left")
    if "CVE_MUN" in work.columns:
        result = result.merge(work.groupby("__mun_key", as_index=False)["CVE_MUN"].first(), on="__mun_key", how="left")

    return result.sort_values("Municipio").reset_index(drop=True)


def municipal_counts(base: pd.DataFrame) -> pd.DataFrame:
    work = filter_sonora_residents(base)
    mun_col = first_existing(work.columns, MUNICIPALITY_CANDIDATES)
    if not mun_col:
        return pd.DataFrame(columns=["Municipio", "Casos", "__mun_key"])
    work["Municipio"] = work[mun_col].fillna("").astype(str).str.strip()
    work = work[work["Municipio"].ne("")]
    work["__mun_key"] = work["Municipio"].map(norm_key)
    counts = work.groupby("__mun_key", as_index=False).size().rename(columns={"size": "Casos"})
    labels = work.groupby("__mun_key", as_index=False)["Municipio"].first()
    return counts.merge(labels, on="__mun_key", how="left")[["Municipio", "Casos", "__mun_key"]]


def incidence_table(base: pd.DataFrame, population: pd.DataFrame | None,
                    multiplier: int = 100000) -> pd.DataFrame:
    counts = municipal_counts(base)
    total_cases = int(counts["Casos"].sum()) if not counts.empty else 0
    if population is None or population.empty:
        out = counts.copy()
        out["Poblacion"] = np.nan
    else:
        out = population.merge(counts[["__mun_key", "Casos"]], on="__mun_key", how="outer")
        out["Casos"] = out["Casos"].fillna(0).astype(int)
        out["Municipio"] = out["Municipio"].fillna(out["__mun_key"])
    if "Poblacion" not in out.columns:
        out["Poblacion"] = np.nan
    total_pop = float(out["Poblacion"].sum(skipna=True))
    rate_col = f"Incidencia x {multiplier:,}".replace(",", " ")
    out[rate_col] = np.where(out["Poblacion"].gt(0), out["Casos"] / out["Poblacion"] * multiplier, np.nan)
    out["% casos estatales"] = np.where(total_cases > 0, out["Casos"] / total_cases * 100, np.nan)
    out["% población estatal"] = np.where(total_pop > 0, out["Poblacion"] / total_pop * 100, np.nan)
    out["Razón casos/población"] = np.where(out["% población estatal"].gt(0), out["% casos estatales"] / out["% población estatal"], np.nan)
    columns = ["Municipio", "Casos", "Poblacion", rate_col, "% casos estatales", "% población estatal", "Razón casos/población"]
    return out[columns].sort_values([rate_col, "Casos"], ascending=[False, False], na_position="last").reset_index(drop=True)


def build_centroid_map(base: pd.DataFrame, geojson: dict[str, Any] | None,
                       heat: bool = True, show_boundaries: bool = True) -> folium.Map:
    centers = municipal_centroids(geojson)
    counts = municipal_counts(base)
    map_obj = folium.Map(location=[29.2, -110.9], zoom_start=6, tiles="CartoDB positron", control_scale=True)
    if geojson and show_boundaries:
        prop = detect_geo_name_property(geojson)
        tooltip = folium.GeoJsonTooltip(fields=[prop], aliases=["Municipio:"]) if prop else None
        folium.GeoJson(
            geojson, name="Límites municipales",
            style_function=lambda _: {"fillColor": "#ffffff", "color": "#475569", "weight": 1.0, "fillOpacity": 0.02},
            highlight_function=lambda _: {"weight": 2.0, "color": "#14213D", "fillOpacity": 0.05},
            tooltip=tooltip,
        ).add_to(map_obj)

    heat_points: list[list[float]] = []
    max_cases = max(int(counts["Casos"].max()), 1) if not counts.empty else 1
    for _, row in counts.iterrows():
        center = centers.get(str(row["__mun_key"]))
        if not center:
            continue
        lat, lon, canonical = center
        cases = int(row["Casos"])
        heat_points.extend([[lat, lon]] * min(cases, 500))
        radius = 5 + 16 * np.sqrt(cases / max_cases)
        popup = f"<b>{canonical}</b><br>Casos: {cases}<br>Ubicación: centroide municipal aproximado"
        folium.CircleMarker(
            [lat, lon], radius=float(radius), color="#14213D", weight=1.3,
            fill=True, fill_color="#E76F76", fill_opacity=0.72,
            popup=folium.Popup(popup, max_width=280), tooltip=f"{canonical}: {cases} casos",
        ).add_to(map_obj)
    if heat and heat_points:
        HeatMap(heat_points, name="Concentración por centroides", radius=24, blur=19, min_opacity=0.20).add_to(map_obj)
    folium.LayerControl(collapsed=False).add_to(map_obj)
    return map_obj


def map_html_bytes(map_obj: folium.Map) -> bytes:
    return map_obj.get_root().render().encode("utf-8")


def incidence_excel_bytes(table: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        table.to_excel(writer, sheet_name="Incidencia municipal", index=False)
        ws = writer.book["Incidencia municipal"]
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions
        for cell in ws[1]:
            cell.font = cell.font.copy(bold=True)
        for col in ws.columns:
            width = min(max(max(len(str(c.value or "")) for c in col[:2000]) + 2, 11), 34)
            ws.column_dimensions[col[0].column_letter].width = width
    return output.getvalue()
