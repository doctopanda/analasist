from __future__ import annotations

import re
from typing import Any, Iterable

import numpy as np
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from .autocarga import (
    ProjectAssets,
    discover_project_assets,
    first_existing,
    load_coordinate_table,
    load_optional_geojson,
    load_sinave_bundle,
    norm_key,
    normalize_population_table,
    process_inbox,
)
from .mapa_espacial import (
    build_folium_map,
    build_municipal_incidence_table,
    detect_coordinate_columns,
    detect_geojson_name_property,
    map_to_html_bytes,
    merge_coordinate_supplement,
    municipal_table_to_excel_bytes,
    prepare_map_points,
)


MUNICIPALITY_CANDIDATES = [
    "Mun_Res",
    "Municipio residencia",
    "Municipio_Residencia",
    "MUNICIPIO_RESIDENCIA",
    "Municipio",
    "MUNICIPIO",
]
WEEK_CANDIDATES = ["SemanaInicio", "Semana de inicio", "Semana", "SEMANA_INICIO"]
YEAR_CANDIDATES = ["Año", "ANIO", "ANO", "Anio", "anio"]
DATE_CANDIDATES = ["Fec_captura", "Fecha_Inicio", "Fecha de inicio"]


# -----------------------------------------------------------------------------
# Derivaciones epidemiológicas ligeras, sin modificar la base original
# -----------------------------------------------------------------------------


def _text(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def _col(df: pd.DataFrame, name: str) -> pd.Series:
    if name not in df.columns:
        return pd.Series([""] * len(df), index=df.index, dtype="object")
    return _text(df[name])


def _positive(series: pd.Series) -> pd.Series:
    return series.str.casefold().str.startswith("positivo")


def add_pathogen_label(df: pd.DataFrame) -> pd.DataFrame:
    if "Patógenos identificados" in df.columns:
        return df

    out = df.copy()
    salmonella = _positive(_col(out, "Salmonella"))
    shigella = _positive(_col(out, "Shigella"))
    rotavirus = _positive(_col(out, "Rotavirus")) | _positive(_col(out, "Rotavirus_InDRE"))
    vpara = _positive(_col(out, "VibrioParahaemolyticus"))

    vibrio = _positive(_col(out, "VibrioCholerae"))
    serogroup = _col(out, "SerogrupoVibrioCholerae").str.casefold()
    vchol_no_o1 = vibrio & serogroup.str.contains("no o1", regex=False)

    ecoli_pathotype = _col(out, "Patotipo_EColi_InDRE")
    ecoli = ecoli_pathotype.ne("") & ~ecoli_pathotype.str.casefold().str.contains("no pat", regex=False)

    other_virus = _col(out, "OtroVirus_InDRE").str.casefold()
    norovirus = other_virus.str.contains("norovirus", regex=False)
    astrovirus = other_virus.str.contains("astrovirus", regex=False)

    flags = {
        "Salmonella": salmonella,
        "Shigella": shigella,
        "E. coli patógena": ecoli,
        "Rotavirus": rotavirus,
        "V. cholerae no O1": vchol_no_o1,
        "V. parahaemolyticus": vpara,
        "Norovirus": norovirus,
        "Astrovirus": astrovirus,
    }

    labels: list[str] = []
    for idx in out.index:
        labels.append(" | ".join(name for name, mask in flags.items() if bool(mask.loc[idx])))
    out["Patógenos identificados"] = labels
    return out


# -----------------------------------------------------------------------------
# Centroides cartográficos para rescatar registros sin coordenada
# -----------------------------------------------------------------------------


def _iter_coordinate_pairs(value: Any):
    if isinstance(value, (list, tuple)):
        if len(value) >= 2 and isinstance(value[0], (int, float)) and isinstance(value[1], (int, float)):
            yield float(value[0]), float(value[1])
            return
        for item in value:
            yield from _iter_coordinate_pairs(item)


def _feature_centroid(feature: dict[str, Any]) -> tuple[float, float] | None:
    geometry = (feature or {}).get("geometry") or {}
    pairs = list(_iter_coordinate_pairs(geometry.get("coordinates")))
    if not pairs:
        return None
    lons = np.array([p[0] for p in pairs], dtype=float)
    lats = np.array([p[1] for p in pairs], dtype=float)
    if not np.isfinite(lons).any() or not np.isfinite(lats).any():
        return None
    # Centro del bounding box. Es deliberadamente una aproximación territorial,
    # no una coordenada de domicilio.
    return float((lats.min() + lats.max()) / 2), float((lons.min() + lons.max()) / 2)


def municipal_centroids(geojson: dict[str, Any] | None) -> dict[str, tuple[float, float, str]]:
    if not geojson:
        return {}
    name_prop = detect_geojson_name_property(geojson)
    if not name_prop:
        return {}

    result: dict[str, tuple[float, float, str]] = {}
    for feature in geojson.get("features") or []:
        properties = feature.get("properties") or {}
        name = str(properties.get(name_prop, "")).strip()
        center = _feature_centroid(feature)
        if not name or center is None:
            continue
        result[norm_key(name)] = (center[0], center[1], name)
    return result


def _numeric_coord(series: pd.Series | None, index: pd.Index) -> pd.Series:
    if series is None:
        return pd.Series(np.nan, index=index, dtype=float)
    return pd.to_numeric(series.astype(str).str.replace(",", ".", regex=False), errors="coerce")


def prepare_integrated_coordinates(
    base: pd.DataFrame,
    geojson_municipios: dict[str, Any] | None,
    coordinates: pd.DataFrame | None = None,
) -> pd.DataFrame:
    work = base.copy()

    if coordinates is not None and not coordinates.empty:
        try:
            work = merge_coordinate_supplement(work, coordinates)
        except Exception:
            # La ausencia de un Folio compatible no debe impedir abrir el mapa.
            pass

    own_lat, own_lon, own_source = detect_coordinate_columns(work)
    lat = _numeric_coord(work[own_lat] if own_lat else None, work.index)
    lon = _numeric_coord(work[own_lon] if own_lon else None, work.index)

    if own_source and own_source in work.columns:
        source = _text(work[own_source]).copy()
    else:
        source = pd.Series("", index=work.index, dtype="object")

    # Coordenada institucional tiene prioridad cuando existe.
    if "Latitud_institucional" in work.columns and "Longitud_institucional" in work.columns:
        inst_lat = _numeric_coord(work["Latitud_institucional"], work.index)
        inst_lon = _numeric_coord(work["Longitud_institucional"], work.index)
        valid_inst = inst_lat.notna() & inst_lon.notna()
        lat.loc[valid_inst] = inst_lat.loc[valid_inst]
        lon.loc[valid_inst] = inst_lon.loc[valid_inst]
        if "Fuente_Coordenada_institucional" in work.columns:
            inst_source = _text(work["Fuente_Coordenada_institucional"])
            source.loc[valid_inst] = inst_source.loc[valid_inst].replace("", "Exacta institucional")
        else:
            source.loc[valid_inst] = "Exacta institucional"

    own_valid = lat.notna() & lon.notna() & source.str.strip().eq("")
    source.loc[own_valid] = "Exacta SINAVE"

    # Rescate territorial: los casos sin coordenada se colocan únicamente en el
    # centroide del municipio, claramente marcados como aproximados.
    municipality_col = first_existing(work.columns, MUNICIPALITY_CANDIDATES)
    centers = municipal_centroids(geojson_municipios)
    if municipality_col and centers:
        missing = lat.isna() | lon.isna()
        for idx in work.index[missing]:
            key = norm_key(work.at[idx, municipality_col])
            center = centers.get(key)
            if center is None:
                continue
            lat.at[idx] = center[0]
            lon.at[idx] = center[1]
            source.at[idx] = "Centroide municipal GeoJSON"

    work["__lat_auto"] = lat
    work["__lon_auto"] = lon
    work["__src_auto"] = source.replace("", "Coordenada sin clasificación")
    return work


# -----------------------------------------------------------------------------
# Filtros del mapa
# -----------------------------------------------------------------------------


def _infer_year_series(df: pd.DataFrame) -> pd.Series:
    year_col = first_existing(df.columns, YEAR_CANDIDATES)
    if year_col:
        return pd.to_numeric(df[year_col], errors="coerce")
    date_col = first_existing(df.columns, DATE_CANDIDATES)
    if date_col:
        return pd.to_datetime(df[date_col], dayfirst=True, errors="coerce").dt.year
    return pd.Series(np.nan, index=df.index)


def _filter_ui(df: pd.DataFrame, default_year: int | None, default_cutoff: int | None, key: str) -> tuple[pd.DataFrame, int | None, int | None]:
    out = df.copy()
    years = _infer_year_series(out)
    available_years = sorted(years.dropna().astype(int).unique().tolist())
    selected_year: int | None = None

    c1, c2 = st.columns(2)
    with c1:
        if available_years:
            preferred = default_year if default_year in available_years else max(available_years)
            selected_year = st.selectbox(
                "Año",
                available_years,
                index=available_years.index(preferred),
                key=f"{key}_year",
            )
            out = out.loc[years.eq(selected_year)].copy()

    week_col = first_existing(out.columns, WEEK_CANDIDATES)
    selected_cutoff: int | None = None
    with c2:
        if week_col:
            weeks = pd.to_numeric(out[week_col], errors="coerce")
            valid_weeks = weeks[weeks.between(1, 53)].dropna().astype(int)
            if not valid_weeks.empty:
                detected = int(valid_weeks.max())
                initial = default_cutoff if default_cutoff and default_cutoff <= detected else detected
                selected_cutoff = st.slider(
                    "Corte epidemiológico",
                    1,
                    53,
                    int(initial),
                    key=f"{key}_week",
                )
                out = out.loc[weeks.between(1, selected_cutoff, inclusive="both")].copy()

    c3, c4 = st.columns(2)
    municipality_col = first_existing(out.columns, MUNICIPALITY_CANDIDATES)
    with c3:
        if municipality_col:
            municipalities = sorted(
                x for x in out[municipality_col].fillna("").astype(str).str.strip().unique().tolist() if x
            )
            selected = st.multiselect("Municipios", municipalities, key=f"{key}_municipios")
            if selected:
                out = out[out[municipality_col].isin(selected)].copy()

    with c4:
        if "Patógenos identificados" in out.columns:
            available = sorted(
                {
                    p.strip()
                    for value in out["Patógenos identificados"].fillna("").astype(str)
                    for p in value.split("|")
                    if p.strip()
                }
            )
            selected_pathogens = st.multiselect("Patógenos", available, key=f"{key}_pathogens")
            if selected_pathogens:
                pattern = "|".join(re.escape(x) for x in selected_pathogens)
                out = out[out["Patógenos identificados"].fillna("").astype(str).str.contains(pattern, regex=True)]

    return out, selected_year, selected_cutoff


# -----------------------------------------------------------------------------
# Render integrado
# -----------------------------------------------------------------------------


def render_integrated_map(assets: ProjectAssets | None = None, key_prefix: str = "popis47") -> None:
    assets = assets or discover_project_assets()

    # Procesa automáticamente cualquier archivo que el usuario haya depositado
    # en data/entrada y redescubre las fuentes una vez por sesión.
    inbox_key = f"{key_prefix}_inbox_processed"
    if not st.session_state.get(inbox_key):
        actions = process_inbox(assets.root)
        st.session_state[inbox_key] = True
        if any(a.status == "instalado" for a in actions):
            assets = discover_project_assets(assets.root)

    st.title("🗺️ POPIS · Territorio integrado")
    st.caption(
        "Autocarga activa: esta página reutiliza las bases, población y cartografía del proyecto. "
        "No es necesario volver a cargar esos archivos."
    )

    if not assets.sinave_by_year:
        st.error("No encontré bases SINAVE dentro del proyecto POPIS.")
        st.code(str(assets.root / "data"), language=None)
        st.stop()

    try:
        base = add_pathogen_label(load_sinave_bundle(assets))
    except Exception as exc:
        st.error(f"No fue posible preparar SINAVE automáticamente: {exc}")
        st.stop()

    geo_mun = load_optional_geojson(assets.municipal_geojson)
    geo_dist = load_optional_geojson(assets.district_geojson)
    coords = load_coordinate_table(assets.coordinates_file)
    population = normalize_population_table(assets.population_file, year=assets.current_year)

    with st.expander("🧠 Fuentes detectadas automáticamente", expanded=False):
        rows = [
            ("Raíz POPIS", str(assets.root)),
            ("SINAVE", ", ".join(f"{y}: {p.name}" for y, p in sorted(assets.sinave_by_year.items()))),
            ("SUIVE/SUAVE", assets.suive_file.name if assets.suive_file else "No detectado"),
            ("Población", assets.population_file.name if assets.population_file else "No detectada"),
            ("Municipios", assets.municipal_geojson.name if assets.municipal_geojson else "No detectado"),
            ("Distritos", assets.district_geojson.name if assets.district_geojson else "No detectado"),
            ("Coordenadas", assets.coordinates_file.name if assets.coordinates_file else "No se requiere archivo adicional"),
        ]
        st.dataframe(pd.DataFrame(rows, columns=["Fuente", "Archivo"]), hide_index=True, use_container_width=True)

    if assets.current_year and assets.cutoff_week:
        st.success(f"Corte detectado automáticamente: **SE {assets.cutoff_week} · {assets.current_year}**")

    with st.expander("🔎 Filtros epidemiológicos", expanded=True):
        filtered, selected_year, selected_cutoff = _filter_ui(
            base,
            default_year=assets.current_year,
            default_cutoff=assets.cutoff_week,
            key=key_prefix,
        )

    work = prepare_integrated_coordinates(filtered, geo_mun, coordinates=coords)
    points = prepare_map_points(work, "__lat_auto", "__lon_auto", "__src_auto", only_sonora_bounds=True)

    st.markdown("#### Configuración cartográfica")
    c1, c2, c3 = st.columns([1.15, 1.0, 1.0])
    with c1:
        view_mode = st.radio(
            "Vista",
            ["Concentración + puntos", "Solo concentración", "Solo puntos"],
            key=f"{key_prefix}_view",
        )
    with c2:
        heat_opacity = st.slider("Opacidad de concentración", 0.10, 0.60, 0.25, 0.05, key=f"{key_prefix}_opacity")
        heat_radius = st.slider("Radio", 8, 45, 22, key=f"{key_prefix}_radius")
        heat_blur = st.slider("Difuminado", 5, 35, 18, key=f"{key_prefix}_blur")
    with c3:
        show_municipios = st.checkbox("Límites municipales", value=geo_mun is not None, key=f"{key_prefix}_mun")
        show_distritos = st.checkbox("Límites distritales", value=geo_dist is not None, key=f"{key_prefix}_dist")
        only_exact = st.checkbox("Mostrar solo puntos exactos", value=False, key=f"{key_prefix}_only_exact")
        exact_heat = st.checkbox("Concentración solo con exactos", value=False, key=f"{key_prefix}_exact_heat")
        cluster = st.checkbox("Agrupar puntos cercanos", value=False, key=f"{key_prefix}_cluster")

    if only_exact and not points.empty:
        points = points[points["__precision_coord"].eq("Exacta")].copy()

    total = len(filtered)
    mapped = len(points)
    exact = int(points["__precision_coord"].eq("Exacta").sum()) if mapped else 0
    approx = int(points["__precision_coord"].eq("Aproximada").sum()) if mapped else 0
    unclassified = int(points["__precision_coord"].eq("Coordenada sin clasificación").sum()) if mapped else 0

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Casos", f"{total:,}")
    k2.metric("Mapeados", f"{mapped:,}")
    k3.metric("Exactos", f"{exact:,}")
    k4.metric("Aproximados", f"{approx:,}")
    k5.metric("Sin clasificar", f"{unclassified:,}")

    if total:
        coverage = mapped / total * 100
        st.caption(f"Cobertura cartográfica: {coverage:.1f}% · los centroides municipales se identifican siempre como aproximados.")

    m = build_folium_map(
        points,
        geojson_municipios=geo_mun,
        geojson_distritos=geo_dist,
        view_mode=view_mode,
        heat_opacity=heat_opacity,
        heat_radius=heat_radius,
        heat_blur=heat_blur,
        show_exact=True,
        show_approx=not only_exact,
        show_unclassified=not only_exact,
        show_municipios=show_municipios,
        show_distritos=show_distritos,
        only_exact_for_heat=exact_heat,
        cluster_points=cluster,
    )
    st_folium(m, width=None, height=680, returned_objects=[], key=f"{key_prefix}_folium")

    c_download1, c_download2 = st.columns(2)
    with c_download1:
        st.download_button(
            "⬇️ Mapa interactivo HTML",
            data=map_to_html_bytes(m),
            file_name=f"POPIS_mapa_SE{selected_cutoff or 'corte'}_{selected_year or 'anio'}.html",
            mime="text/html",
            key=f"{key_prefix}_html",
            use_container_width=True,
        )

    municipality_col = first_existing(filtered.columns, MUNICIPALITY_CANDIDATES)
    if municipality_col:
        st.markdown("#### Incidencia municipal")
        multiplier = st.selectbox(
            "Tasa por habitantes",
            [1000, 10000, 100000],
            index=2,
            format_func=lambda x: f"{x:,}".replace(",", " "),
            key=f"{key_prefix}_multiplier",
        )

        if population is None:
            st.info(
                "POPIS encontró los casos por municipio, pero no una tabla poblacional normalizada compatible. "
                "La incidencia queda deshabilitada para evitar fabricar denominadores."
            )
            table = build_municipal_incidence_table(
                filtered,
                None,
                municipio_col_casos=municipality_col,
                multiplier=multiplier,
            )
        else:
            table = build_municipal_incidence_table(
                filtered,
                population,
                municipio_col_casos=municipality_col,
                multiplier=multiplier,
                poblacion_municipio_col="Municipio",
                poblacion_valor_col="Poblacion",
                poblacion_anio_col="Año" if "Año" in population.columns else None,
                anio=selected_year,
            )

        st.dataframe(table, hide_index=True, use_container_width=True)
        with c_download2:
            st.download_button(
                "⬇️ Incidencia municipal Excel",
                data=municipal_table_to_excel_bytes(table),
                file_name=f"POPIS_incidencia_municipal_SE{selected_cutoff or 'corte'}_{selected_year or 'anio'}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"{key_prefix}_xlsx",
                use_container_width=True,
            )
