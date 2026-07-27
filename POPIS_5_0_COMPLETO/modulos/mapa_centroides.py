from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import folium
import numpy as np
import pandas as pd
from folium.plugins import HeatMap

try:
    import streamlit as st
    from streamlit_folium import st_folium
except Exception:  # pragma: no cover
    st = None
    st_folium = None

from .centroides import apply_centroids, centroids_from_geojson, norm, resolve_centroid


def load_geojson(path: str | Path | None) -> dict | None:
    if path is None:
        return None
    import json
    p = Path(path)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8-sig"))


def _detect_exact(df: pd.DataFrame) -> tuple[str | None, str | None]:
    lat_candidates = ["Latitud", "LATITUD", "latitud", "LAT", "Lat", "lat", "Latitud_Res", "Latitud_Domicilio"]
    lon_candidates = ["Longitud", "LONGITUD", "longitud", "LON", "Lon", "lon", "LONG", "Long", "long", "Longitud_Res", "Longitud_Domicilio"]
    lat = next((c for c in lat_candidates if c in df.columns), None)
    lon = next((c for c in lon_candidates if c in df.columns), None)
    return lat, lon


def prepare_map_dataframe(df: pd.DataFrame, geojson: dict | None = None, use_exact: bool = False) -> pd.DataFrame:
    work = df.copy()
    municipality_col = "Municipio_POPIS" if "Municipio_POPIS" in work.columns else ("Mun_Res" if "Mun_Res" in work.columns else None)
    if not municipality_col:
        work["Municipio_POPIS"] = ""
        municipality_col = "Municipio_POPIS"
    work = apply_centroids(work, municipio_col=municipality_col, geojson=geojson)
    work["__lat_mapa"] = work["__lat_centroide"]
    work["__lon_mapa"] = work["__lon_centroide"]
    work["__fuente_mapa"] = work["__fuente_centroide"]

    if use_exact:
        lat_col, lon_col = _detect_exact(work)
        if lat_col and lon_col:
            lat = pd.to_numeric(work[lat_col].astype(str).str.replace(",", ".", regex=False), errors="coerce")
            lon = pd.to_numeric(work[lon_col].astype(str).str.replace(",", ".", regex=False), errors="coerce")
            valid = lat.between(25.0, 33.5) & lon.between(-115.5, -108.0)
            work.loc[valid, "__lat_mapa"] = lat[valid]
            work.loc[valid, "__lon_mapa"] = lon[valid]
            work.loc[valid, "__fuente_mapa"] = "Coordenada exacta de la base"

    work["__lat_mapa"] = pd.to_numeric(work["__lat_mapa"], errors="coerce")
    work["__lon_mapa"] = pd.to_numeric(work["__lon_mapa"], errors="coerce")
    return work[work["__lat_mapa"].notna() & work["__lon_mapa"].notna()].copy()


def build_incidence_table(cases: pd.DataFrame, population: pd.DataFrame | None, multiplier: int = 100000) -> pd.DataFrame:
    mun_col = "Municipio_POPIS" if "Municipio_POPIS" in cases.columns else "Mun_Res"
    c = cases.copy()
    c["Municipio"] = c[mun_col].fillna("").astype(str).str.strip()
    c = c[c["Municipio"].ne("")]
    c["__key"] = c["Municipio"].map(norm)
    counts = c.groupby("__key", as_index=False).size().rename(columns={"size": "Casos"})
    labels = c.groupby("__key", as_index=False)["Municipio"].first()
    counts = counts.merge(labels, on="__key", how="left")
    if population is None or population.empty:
        counts["Poblacion"] = np.nan
        counts[f"Incidencia x {multiplier:,}".replace(",", " ")] = np.nan
        return counts[["Municipio", "Casos", "Poblacion", f"Incidencia x {multiplier:,}".replace(",", " ")]].sort_values("Casos", ascending=False)

    p = population.copy()
    munp = next((x for x in ["Municipio", "MUNICIPIO", "municipio", "NOM_MUN", "NOMGEO"] if x in p.columns), None)
    popc = next((x for x in ["Poblacion", "POBLACION", "Población", "POB", "Total"] if x in p.columns), None)
    if not munp or not popc:
        return build_incidence_table(cases, None, multiplier)
    p["Municipio"] = p[munp].astype(str).str.strip()
    p["__key"] = p["Municipio"].map(norm)
    p["Poblacion"] = pd.to_numeric(p[popc].astype(str).str.replace(",", "", regex=False), errors="coerce")
    p = p.dropna(subset=["Poblacion"]).groupby("__key", as_index=False).agg(Municipio=("Municipio", "first"), Poblacion=("Poblacion", "sum"))
    out = p.merge(counts[["__key", "Casos"]], on="__key", how="outer")
    out["Casos"] = out["Casos"].fillna(0).astype(int)
    out["Municipio"] = out["Municipio"].fillna(out["__key"])
    rate_col = f"Incidencia x {multiplier:,}".replace(",", " ")
    out[rate_col] = np.where(out["Poblacion"].gt(0), out["Casos"] / out["Poblacion"] * multiplier, np.nan)
    return out[["Municipio", "Casos", "Poblacion", rate_col]].sort_values([rate_col, "Casos"], ascending=[False, False], na_position="last")


def build_map(points: pd.DataFrame, geojson: dict | None = None, heat_opacity: float = 0.28, show_heat: bool = True, show_points: bool = True) -> folium.Map:
    if points.empty:
        return folium.Map(location=[29.1, -110.9], zoom_start=6, tiles="CartoDB positron")
    m = folium.Map(location=[float(points["__lat_mapa"].median()), float(points["__lon_mapa"].median())], zoom_start=6, tiles="CartoDB positron", control_scale=True)
    if geojson:
        folium.GeoJson(
            geojson,
            name="Límites municipales",
            style_function=lambda _: {"fillOpacity": 0.0, "color": "#475569", "weight": 1.1, "opacity": 0.8},
        ).add_to(m)
    if show_heat:
        HeatMap(points[["__lat_mapa", "__lon_mapa"]].values.tolist(), name="Concentración", radius=24, blur=20, min_opacity=max(0.08, heat_opacity * 0.4), max_zoom=12).add_to(m)
    if show_points:
        grp = folium.FeatureGroup(name="Centroides / puntos", show=True).add_to(m)
        mun_col = "Municipio_POPIS" if "Municipio_POPIS" in points.columns else "Mun_Res"
        grouped = points.groupby([mun_col, "__lat_mapa", "__lon_mapa", "__fuente_mapa"], dropna=False).size().reset_index(name="Casos")
        for _, row in grouped.iterrows():
            source = str(row["__fuente_mapa"])
            exact = source.startswith("Coordenada exacta")
            color = "#9d2235" if exact else "#2563eb"
            folium.CircleMarker(
                location=[float(row["__lat_mapa"]), float(row["__lon_mapa"])],
                radius=min(5 + np.sqrt(float(row["Casos"])), 18),
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.78 if exact else 0.62,
                popup=folium.Popup(f"<b>Municipio:</b> {row[mun_col]}<br><b>Casos:</b> {int(row['Casos'])}<br><b>Ubicación:</b> {source}", max_width=320),
                tooltip=f"{row[mun_col]} · {int(row['Casos'])} casos",
            ).add_to(grp)
    folium.LayerControl(collapsed=False).add_to(m)
    return m


def map_html_bytes(m: folium.Map) -> bytes:
    return m.get_root().render().encode("utf-8")


def table_excel_bytes(table: pd.DataFrame) -> bytes:
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        table.to_excel(writer, index=False, sheet_name="Incidencia municipal")
        ws = writer.book["Incidencia municipal"]
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions
        for cell in ws[1]:
            cell.font = cell.font.copy(bold=True)
    return out.getvalue()


def render_centroid_map(base: pd.DataFrame, geojson: dict | None = None, population: pd.DataFrame | None = None, key_prefix: str = "mapa") -> None:
    if st is None or st_folium is None:
        raise RuntimeError("Se requiere Streamlit + streamlit-folium.")
    st.subheader("🗺️ Territorio por centroides")
    st.caption("Por defecto POPIS usa centroides municipales. Las coordenadas exactas quedan desactivadas y solo se usan cuando se habilitan explícitamente.")
    use_exact = st.toggle("Usar coordenadas exactas cuando estén disponibles", value=False, key=f"{key_prefix}_exact")
    c1, c2, c3 = st.columns(3)
    with c1:
        show_heat = st.checkbox("Concentración", True, key=f"{key_prefix}_heat")
    with c2:
        show_points = st.checkbox("Puntos/centroides", True, key=f"{key_prefix}_pts")
    with c3:
        opacity = st.slider("Opacidad", 0.10, 0.60, 0.28, 0.05, key=f"{key_prefix}_op")

    points = prepare_map_dataframe(base, geojson=geojson, use_exact=use_exact)
    st.metric("Casos territorializados", f"{len(points):,}")
    if points.empty:
        st.warning("No fue posible territorializar registros con el municipio de residencia disponible.")
        return
    m = build_map(points, geojson=geojson, heat_opacity=opacity, show_heat=show_heat, show_points=show_points)
    st_folium(m, width=None, height=650, returned_objects=[], key=f"{key_prefix}_folium")
    st.download_button("⬇️ Descargar mapa HTML", map_html_bytes(m), "POPIS_mapa_centroides.html", "text/html", key=f"{key_prefix}_html")
    mult = st.selectbox("Incidencia por habitantes", [1000, 10000, 100000], index=2, key=f"{key_prefix}_mult")
    table = build_incidence_table(base, population, mult)
    st.dataframe(table, use_container_width=True, hide_index=True)
    st.download_button("⬇️ Descargar tabla municipal", table_excel_bytes(table), "POPIS_incidencia_municipal.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"{key_prefix}_xlsx")
