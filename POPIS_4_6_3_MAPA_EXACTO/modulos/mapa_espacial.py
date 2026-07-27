from __future__ import annotations

import copy
import html
import io
import json
import re
import unicodedata
from pathlib import Path
from typing import Any, BinaryIO, Iterable

import folium
import numpy as np
import pandas as pd
from folium.plugins import HeatMap, MarkerCluster

try:
    import streamlit as st
    from streamlit_folium import st_folium
except Exception:  # pragma: no cover - permite importar el motor fuera de Streamlit
    st = None
    st_folium = None


# -----------------------------------------------------------------------------
# Configuración y candidatos
# -----------------------------------------------------------------------------

SONORA_BOUNDS = {
    "lat_min": 25.0,
    "lat_max": 33.5,
    "lon_min": -115.5,
    "lon_max": -108.0,
}

LAT_CANDIDATES = [
    "Latitud",
    "LATITUD",
    "latitud",
    "Latitude",
    "latitude",
    "LAT",
    "Lat",
    "lat",
    "Y",
    "y",
    "Coord_Y",
    "Coordenada_Y",
    "Latitud_Res",
    "Latitud_Domicilio",
    "latitud_res",
    "latitud_domicilio",
]

LON_CANDIDATES = [
    "Longitud",
    "LONGITUD",
    "longitud",
    "Longitude",
    "longitude",
    "LON",
    "Lon",
    "lon",
    "LONG",
    "Long",
    "long",
    "X",
    "x",
    "Coord_X",
    "Coordenada_X",
    "Longitud_Res",
    "Longitud_Domicilio",
    "longitud_res",
    "longitud_domicilio",
]

SOURCE_CANDIDATES = [
    "Fuente_Coordenada",
    "Fuente coordenada",
    "Tipo_Coordenada",
    "Tipo coordenada",
    "Precision_Coordenada",
    "Precisión coordenada",
    "Origen_Coordenada",
    "Georreferencia",
]

FOLIO_CANDIDATES = ["Folio", "FOLIO", "folio", "ID", "Id", "id"]
MUNICIPIO_CANDIDATES = [
    "Mun_Res",
    "Municipio residencia",
    "Municipio_Residencia",
    "MUNICIPIO_RESIDENCIA",
    "Municipio",
    "MUNICIPIO",
    "municipio",
]
LOCALIDAD_CANDIDATES = ["Loc_Res", "Localidad residencia", "Localidad", "LOCALIDAD", "localidad"]
COLONIA_CANDIDATES = ["Colonia", "COLONIA", "colonia"]
FECHA_INICIO_CANDIDATES = ["Fecha_Inicio", "Fecha de inicio", "FECHA_INICIO"]
SEMANA_CANDIDATES = ["SemanaInicio", "Semana de inicio", "SEMANA_INICIO", "Semana"]
ANIO_CANDIDATES = ["Año", "ANO", "Anio", "ANIO", "anio"]
DIAG_CANDIDATES = ["Diag_Final", "Diagnóstico final", "Diagnostico final", "DIAGNOSTICO_FINAL"]
PATHOGEN_CANDIDATES = ["Patógenos identificados", "Patogenos identificados", "Patógeno", "Patogeno"]

GEOJSON_NAME_CANDIDATES = [
    "NOMGEO",
    "NOM_MUN",
    "NOM_MUNICIPIO",
    "MUNICIPIO",
    "Municipio",
    "municipio",
    "NAME_2",
    "name",
]


# -----------------------------------------------------------------------------
# Utilidades de lectura y normalización
# -----------------------------------------------------------------------------


def _ascii_text(value: Any) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text


def norm_key(value: Any) -> str:
    text = _ascii_text(value).upper().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^A-Z0-9 ]+", "", text)
    return text.strip()


def _first_existing(columns: Iterable[str], candidates: Iterable[str]) -> str | None:
    cols = list(columns)
    direct = {str(c): str(c) for c in cols}
    normalized = {norm_key(c): str(c) for c in cols}
    for candidate in candidates:
        if candidate in direct:
            return direct[candidate]
        key = norm_key(candidate)
        if key in normalized:
            return normalized[key]
    return None


def _decode_bytes(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "latin-1", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1", errors="replace")


def read_table(source: str | Path | bytes | BinaryIO, filename: str | None = None) -> pd.DataFrame:
    """Lee CSV, TSV, XLSX o los .xls de SINAVE que en realidad son texto tabulado."""
    if isinstance(source, (str, Path)):
        path = Path(source)
        raw = path.read_bytes()
        filename = filename or path.name
    elif isinstance(source, bytes):
        raw = source
    else:
        raw = source.read()

    suffix = Path(filename or "archivo").suffix.lower()
    head = _decode_bytes(raw[:8192])

    if "\t" in head:
        return pd.read_csv(io.StringIO(_decode_bytes(raw)), sep="\t", dtype=str, keep_default_na=False)

    if suffix in {".csv", ".txt"}:
        text = _decode_bytes(raw)
        sep = ";" if text[:4096].count(";") > text[:4096].count(",") else ","
        return pd.read_csv(io.StringIO(text), sep=sep, dtype=str, keep_default_na=False)

    engine = "xlrd" if suffix == ".xls" else "openpyxl"
    return pd.read_excel(io.BytesIO(raw), dtype=str, engine=engine).fillna("")


def load_geojson(source: Any) -> dict[str, Any] | None:
    if source is None:
        return None
    if isinstance(source, dict):
        return copy.deepcopy(source)
    if isinstance(source, (str, Path)):
        with open(source, "r", encoding="utf-8") as fh:
            return json.load(fh)
    raw = source.getvalue() if hasattr(source, "getvalue") else source.read()
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8-sig")
    return json.loads(raw)


# -----------------------------------------------------------------------------
# Coordenadas
# -----------------------------------------------------------------------------


def detect_coordinate_columns(df: pd.DataFrame) -> tuple[str | None, str | None, str | None]:
    return (
        _first_existing(df.columns, LAT_CANDIDATES),
        _first_existing(df.columns, LON_CANDIDATES),
        _first_existing(df.columns, SOURCE_CANDIDATES),
    )


def classify_coordinate_source(value: Any) -> str:
    text = norm_key(value)
    if not text:
        return "Coordenada sin clasificación"
    exact_terms = ("EXACT", "PRECIS", "GPS", "SINAVE", "INSTITUCIONAL", "DOMICILIO")
    approx_terms = ("CENTROID", "LOCALIDAD", "MUNICIPIO", "CABECERA", "APROX")
    if any(term in text for term in exact_terms):
        return "Exacta"
    if any(term in text for term in approx_terms):
        return "Aproximada"
    return "Coordenada sin clasificación"


def merge_coordinate_supplement(
    base: pd.DataFrame,
    coords: pd.DataFrame,
    base_folio_col: str | None = None,
    coords_folio_col: str | None = None,
    lat_col: str | None = None,
    lon_col: str | None = None,
    source_col: str | None = None,
) -> pd.DataFrame:
    """Une coordenadas institucionales por Folio sin incorporar datos identificadores extra."""
    out = base.copy()
    base_folio_col = base_folio_col or _first_existing(out.columns, FOLIO_CANDIDATES)
    coords_folio_col = coords_folio_col or _first_existing(coords.columns, FOLIO_CANDIDATES)
    lat_col = lat_col or _first_existing(coords.columns, LAT_CANDIDATES)
    lon_col = lon_col or _first_existing(coords.columns, LON_CANDIDATES)
    source_col = source_col or _first_existing(coords.columns, SOURCE_CANDIDATES)

    if not base_folio_col or not coords_folio_col:
        raise ValueError("No se encontró una columna Folio compatible para unir las coordenadas.")
    if not lat_col or not lon_col:
        raise ValueError("El archivo institucional requiere columnas de latitud y longitud.")

    keep = [coords_folio_col, lat_col, lon_col]
    if source_col:
        keep.append(source_col)

    c = coords[keep].copy()
    c[coords_folio_col] = c[coords_folio_col].astype(str).str.strip()
    c = c[c[coords_folio_col].ne("")].drop_duplicates(coords_folio_col, keep="last")

    ren = {
        coords_folio_col: "__folio_coord",
        lat_col: "Latitud_institucional",
        lon_col: "Longitud_institucional",
    }
    if source_col:
        ren[source_col] = "Fuente_Coordenada_institucional"
    c = c.rename(columns=ren)

    out["__folio_coord"] = out[base_folio_col].astype(str).str.strip()
    out = out.merge(c, on="__folio_coord", how="left")
    out = out.drop(columns=["__folio_coord"])

    if "Fuente_Coordenada_institucional" not in out.columns:
        out["Fuente_Coordenada_institucional"] = "Exacta institucional"
    else:
        out["Fuente_Coordenada_institucional"] = out["Fuente_Coordenada_institucional"].replace(
            "", "Exacta institucional"
        )

    return out


def prepare_map_points(
    df: pd.DataFrame,
    lat_col: str,
    lon_col: str,
    source_col: str | None = None,
    only_sonora_bounds: bool = True,
) -> pd.DataFrame:
    out = df.copy()
    out["__lat"] = pd.to_numeric(out[lat_col].astype(str).str.replace(",", ".", regex=False), errors="coerce")
    out["__lon"] = pd.to_numeric(out[lon_col].astype(str).str.replace(",", ".", regex=False), errors="coerce")

    valid = out["__lat"].between(-90, 90) & out["__lon"].between(-180, 180)
    if only_sonora_bounds:
        valid &= out["__lat"].between(SONORA_BOUNDS["lat_min"], SONORA_BOUNDS["lat_max"])
        valid &= out["__lon"].between(SONORA_BOUNDS["lon_min"], SONORA_BOUNDS["lon_max"])

    out = out.loc[valid].copy()
    if source_col and source_col in out.columns:
        out["__fuente_coord"] = out[source_col].fillna("").astype(str)
    else:
        out["__fuente_coord"] = "Coordenada sin clasificación"
    out["__precision_coord"] = out["__fuente_coord"].map(classify_coordinate_source)
    return out


# -----------------------------------------------------------------------------
# Tabla municipal e incidencia
# -----------------------------------------------------------------------------


def standardize_population_table(
    poblacion: pd.DataFrame,
    municipio_col: str,
    poblacion_col: str,
    anio_col: str | None = None,
    anio: int | None = None,
) -> pd.DataFrame:
    p = poblacion.copy()
    if anio_col and anio is not None and anio_col in p.columns:
        years = pd.to_numeric(p[anio_col], errors="coerce")
        p = p.loc[years.eq(int(anio))].copy()

    p["Municipio"] = p[municipio_col].astype(str).str.strip()
    p["__mun_key"] = p["Municipio"].map(norm_key)
    p["Poblacion"] = pd.to_numeric(
        p[poblacion_col].astype(str).str.replace(",", "", regex=False), errors="coerce"
    )
    p = p.dropna(subset=["Poblacion"])
    p = p[p["Poblacion"].ge(0)]
    p = (
        p.groupby(["__mun_key", "Municipio"], as_index=False)["Poblacion"]
        .sum()
        .sort_values("Municipio")
    )
    return p


def build_municipal_incidence_table(
    casos: pd.DataFrame,
    poblacion: pd.DataFrame | None,
    municipio_col_casos: str,
    multiplier: int = 100000,
    poblacion_municipio_col: str | None = None,
    poblacion_valor_col: str | None = None,
    poblacion_anio_col: str | None = None,
    anio: int | None = None,
) -> pd.DataFrame:
    c = casos.copy()
    c["Municipio"] = c[municipio_col_casos].fillna("").astype(str).str.strip()
    c = c[c["Municipio"].ne("")]
    c["__mun_key"] = c["Municipio"].map(norm_key)
    counts = c.groupby("__mun_key", as_index=False).size().rename(columns={"size": "Casos"})
    labels = c.groupby("__mun_key", as_index=False)["Municipio"].first()
    counts = counts.merge(labels, on="__mun_key", how="left")

    if poblacion is None or poblacion.empty:
        total_cases = int(counts["Casos"].sum()) if not counts.empty else 0
        counts["% casos estatales"] = counts["Casos"] / total_cases * 100 if total_cases else np.nan
        counts["Poblacion"] = np.nan
        counts[f"Incidencia x {multiplier:,}".replace(",", " ")] = np.nan
        counts["% población estatal"] = np.nan
        counts["Razón casos/población"] = np.nan
        return counts[[
            "Municipio", "Casos", "Poblacion",
            f"Incidencia x {multiplier:,}".replace(",", " "),
            "% casos estatales", "% población estatal", "Razón casos/población"
        ]].sort_values("Casos", ascending=False)

    poblacion_municipio_col = poblacion_municipio_col or _first_existing(
        poblacion.columns, ["Municipio", "MUNICIPIO", "municipio", "NOM_MUN", "NOMGEO"]
    )
    poblacion_valor_col = poblacion_valor_col or _first_existing(
        poblacion.columns, ["Poblacion", "POBLACION", "Población", "POB", "Total"]
    )
    if not poblacion_municipio_col or not poblacion_valor_col:
        raise ValueError("No se pudieron identificar las columnas de municipio y población.")

    pop = standardize_population_table(
        poblacion,
        municipio_col=poblacion_municipio_col,
        poblacion_col=poblacion_valor_col,
        anio_col=poblacion_anio_col,
        anio=anio,
    )

    # Outer join: mantiene todos los municipios de la tabla poblacional, incluso con cero casos.
    table = pop.merge(counts[["__mun_key", "Casos"]], on="__mun_key", how="outer")
    table["Casos"] = table["Casos"].fillna(0).astype(int)
    table["Municipio"] = table["Municipio"].fillna(table["__mun_key"])

    total_cases = int(table["Casos"].sum())
    total_pop = float(table["Poblacion"].sum(skipna=True))
    rate_col = f"Incidencia x {multiplier:,}".replace(",", " ")

    table[rate_col] = np.where(
        table["Poblacion"].gt(0),
        table["Casos"] / table["Poblacion"] * multiplier,
        np.nan,
    )
    table["% casos estatales"] = np.where(total_cases > 0, table["Casos"] / total_cases * 100, np.nan)
    table["% población estatal"] = np.where(total_pop > 0, table["Poblacion"] / total_pop * 100, np.nan)
    table["Razón casos/población"] = np.where(
        table["% población estatal"].gt(0),
        table["% casos estatales"] / table["% población estatal"],
        np.nan,
    )

    return table[[
        "Municipio",
        "Casos",
        "Poblacion",
        rate_col,
        "% casos estatales",
        "% población estatal",
        "Razón casos/población",
    ]].sort_values([rate_col, "Casos"], ascending=[False, False], na_position="last").reset_index(drop=True)


# -----------------------------------------------------------------------------
# GeoJSON y mapa
# -----------------------------------------------------------------------------


def detect_geojson_name_property(geojson: dict[str, Any] | None) -> str | None:
    if not geojson:
        return None
    features = geojson.get("features") or []
    if not features:
        return None
    props = (features[0] or {}).get("properties") or {}
    return _first_existing(props.keys(), GEOJSON_NAME_CANDIDATES)


def _safe_value(row: pd.Series, candidates: Iterable[str], default: str = "") -> str:
    col = _first_existing(row.index, candidates)
    if not col:
        return default
    value = row.get(col, default)
    if pd.isna(value):
        return default
    return str(value).strip()


def _popup_html(row: pd.Series) -> str:
    fields = [
        ("Folio", _safe_value(row, FOLIO_CANDIDATES, "Sin folio")),
        ("Municipio", _safe_value(row, MUNICIPIO_CANDIDATES)),
        ("Localidad", _safe_value(row, LOCALIDAD_CANDIDATES)),
        ("Colonia", _safe_value(row, COLONIA_CANDIDATES)),
        ("Inicio", _safe_value(row, FECHA_INICIO_CANDIDATES)),
        ("Diagnóstico final", _safe_value(row, DIAG_CANDIDATES)),
        ("Patógeno", _safe_value(row, PATHOGEN_CANDIDATES)),
        ("Coordenada", str(row.get("__precision_coord", ""))),
        ("Fuente", str(row.get("__fuente_coord", ""))),
    ]
    lines = []
    for label, value in fields:
        if value:
            lines.append(f"<b>{html.escape(label)}:</b> {html.escape(value)}")
    return "<br>".join(lines)


def _style_municipio(_: dict[str, Any]) -> dict[str, Any]:
    return {
        "fillColor": "#ffffff",
        "color": "#475569",
        "weight": 1.1,
        "fillOpacity": 0.0,
        "opacity": 0.75,
    }


def _style_distrito(_: dict[str, Any]) -> dict[str, Any]:
    return {
        "fillColor": "#ffffff",
        "color": "#111827",
        "weight": 2.2,
        "fillOpacity": 0.0,
        "opacity": 0.9,
        "dashArray": "7,5",
    }


def build_folium_map(
    points: pd.DataFrame,
    geojson_municipios: dict[str, Any] | None = None,
    geojson_distritos: dict[str, Any] | None = None,
    view_mode: str = "Concentración + puntos",
    heat_opacity: float = 0.30,
    heat_radius: int = 22,
    heat_blur: int = 18,
    show_exact: bool = True,
    show_approx: bool = True,
    show_unclassified: bool = True,
    show_municipios: bool = True,
    show_distritos: bool = True,
    only_exact_for_heat: bool = False,
    cluster_points: bool = False,
    tiles: str = "CartoDB positron",
) -> folium.Map:
    if points is not None and not points.empty:
        center = [float(points["__lat"].median()), float(points["__lon"].median())]
        zoom = 6
    else:
        center = [29.2, -110.9]
        zoom = 6

    m = folium.Map(location=center, zoom_start=zoom, tiles=tiles, control_scale=True, prefer_canvas=True)

    # Límites primero para que el control de capas los conserve disponibles.
    if geojson_municipios and show_municipios:
        prop = detect_geojson_name_property(geojson_municipios)
        tooltip = folium.GeoJsonTooltip(fields=[prop], aliases=["Municipio:"]) if prop else None
        folium.GeoJson(
            geojson_municipios,
            name="Límites municipales",
            style_function=_style_municipio,
            highlight_function=lambda _: {"weight": 2.2, "color": "#0f172a", "fillOpacity": 0.03},
            tooltip=tooltip,
            show=True,
        ).add_to(m)

    if geojson_distritos and show_distritos:
        prop = detect_geojson_name_property(geojson_distritos)
        tooltip = folium.GeoJsonTooltip(fields=[prop], aliases=["Distrito:"]) if prop else None
        folium.GeoJson(
            geojson_distritos,
            name="Límites distritales",
            style_function=_style_distrito,
            tooltip=tooltip,
            show=True,
        ).add_to(m)

    use_heat = view_mode in {"Solo concentración", "Concentración + puntos"}
    use_points = view_mode in {"Solo puntos", "Concentración + puntos"}

    if use_heat and points is not None and not points.empty:
        heat_points = points
        if only_exact_for_heat:
            heat_points = heat_points[heat_points["__precision_coord"].eq("Exacta")]
        if not heat_points.empty:
            alpha = min(max(float(heat_opacity), 0.05), 0.85)
            gradient = {
                0.20: f"rgba(49,130,189,{alpha})",
                0.45: f"rgba(65,182,196,{alpha})",
                0.70: f"rgba(253,174,97,{alpha})",
                1.00: f"rgba(178,24,43,{alpha})",
            }
            HeatMap(
                heat_points[["__lat", "__lon"]].values.tolist(),
                name="Concentración",
                radius=int(heat_radius),
                blur=int(heat_blur),
                min_opacity=max(0.05, alpha * 0.45),
                max_zoom=13,
                gradient=gradient,
                show=True,
            ).add_to(m)

    if use_points and points is not None and not points.empty:
        if cluster_points:
            parent = MarkerCluster(name="Puntos epidemiológicos", show=True).add_to(m)
        else:
            parent = folium.FeatureGroup(name="Puntos epidemiológicos", show=True).add_to(m)

        for _, row in points.iterrows():
            precision = str(row.get("__precision_coord", "Coordenada sin clasificación"))
            if precision == "Exacta" and not show_exact:
                continue
            if precision == "Aproximada" and not show_approx:
                continue
            if precision == "Coordenada sin clasificación" and not show_unclassified:
                continue

            if precision == "Exacta":
                color = "#9d2235"
                radius = 5.5
                fill_opacity = 0.90
            elif precision == "Aproximada":
                color = "#2563eb"
                radius = 4.5
                fill_opacity = 0.62
            else:
                color = "#6b7280"
                radius = 4.0
                fill_opacity = 0.55

            folium.CircleMarker(
                location=[float(row["__lat"]), float(row["__lon"])],
                radius=radius,
                color=color,
                weight=1.1,
                fill=True,
                fill_color=color,
                fill_opacity=fill_opacity,
                opacity=0.95,
                popup=folium.Popup(_popup_html(row), max_width=360),
                tooltip=precision,
            ).add_to(parent)

    folium.LayerControl(collapsed=False).add_to(m)
    return m


def map_to_html_bytes(m: folium.Map) -> bytes:
    return m.get_root().render().encode("utf-8")


def municipal_table_to_excel_bytes(table: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        table.to_excel(writer, sheet_name="Incidencia municipal", index=False)
        ws = writer.book["Incidencia municipal"]
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions
        for cell in ws[1]:
            cell.font = cell.font.copy(bold=True)
        for col in ws.columns:
            max_len = max(len(str(c.value or "")) for c in col[:2000])
            ws.column_dimensions[col[0].column_letter].width = min(max(max_len + 2, 11), 34)
        for row in range(2, ws.max_row + 1):
            for col in range(1, ws.max_column + 1):
                header = str(ws.cell(1, col).value or "")
                if header.startswith("Incidencia") or header == "Razón casos/población":
                    ws.cell(row, col).number_format = "0.00"
                elif header.startswith("%"):
                    ws.cell(row, col).number_format = "0.00"
    return output.getvalue()


# -----------------------------------------------------------------------------
# Interfaz Streamlit reutilizable
# -----------------------------------------------------------------------------


def _select_default(options: list[str], preferred: str | None) -> int:
    if preferred in options:
        return options.index(preferred)
    return 0


def _filter_dataframe_ui(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    # Año
    year_col = _first_existing(out.columns, ANIO_CANDIDATES)
    if year_col:
        years = pd.to_numeric(out[year_col], errors="coerce").dropna().astype(int)
    else:
        date_col = _first_existing(out.columns, ["Fec_captura", "Fecha_Inicio", "Fecha de inicio"])
        years = pd.to_datetime(out[date_col], dayfirst=True, errors="coerce").dt.year.dropna().astype(int) if date_col else pd.Series(dtype=int)
    if not years.empty:
        available_years = sorted(years.unique().tolist())
        selected_year = st.selectbox("Año", available_years, index=len(available_years) - 1)
        if year_col:
            out = out.loc[pd.to_numeric(out[year_col], errors="coerce").eq(selected_year)].copy()
        elif date_col:
            d = pd.to_datetime(out[date_col], dayfirst=True, errors="coerce")
            out = out.loc[d.dt.year.eq(selected_year)].copy()

    # Semana
    week_col = _first_existing(out.columns, SEMANA_CANDIDATES)
    if week_col:
        weeks = pd.to_numeric(out[week_col], errors="coerce")
        valid_weeks = sorted(weeks.dropna().astype(int).unique().tolist())
        if valid_weeks:
            max_week = int(max(valid_weeks))
            cutoff = st.slider("Corte de semana epidemiológica", 1, 53, max_week)
            out = out.loc[weeks.between(1, cutoff, inclusive="both")].copy()

    municipality_col = _first_existing(out.columns, MUNICIPIO_CANDIDATES)
    if municipality_col:
        municipalities = sorted(x for x in out[municipality_col].fillna("").astype(str).str.strip().unique() if x)
        selected = st.multiselect("Municipios", municipalities)
        if selected:
            out = out[out[municipality_col].isin(selected)].copy()

    return out


def render_mapa_espacial(
    base: pd.DataFrame,
    geojson_municipios: dict[str, Any] | None = None,
    geojson_distritos: dict[str, Any] | None = None,
    poblacion: pd.DataFrame | None = None,
    key_prefix: str = "popis_map",
) -> None:
    if st is None or st_folium is None:
        raise RuntimeError("render_mapa_espacial requiere streamlit y streamlit-folium.")

    st.subheader("🗺️ Territorio · mapa exacto y concentración")
    st.caption(
        "Las coordenadas exactas se dibujan solamente cuando ya existen en la base o en un archivo institucional. "
        "POPIS no envía domicilios a geocodificadores públicos."
    )

    work = base.copy()

    with st.expander("📍 Coordenadas institucionales y capas", expanded=False):
        coord_file = st.file_uploader(
            "Archivo institucional de coordenadas por Folio (CSV/XLS/XLSX)",
            type=["csv", "xls", "xlsx", "txt"],
            key=f"{key_prefix}_coords",
        )
        if coord_file is not None:
            try:
                coords = read_table(coord_file.getvalue(), coord_file.name)
                work = merge_coordinate_supplement(work, coords)
                st.success(f"Coordenadas institucionales vinculadas: {len(coords):,} registros de referencia.")
            except Exception as exc:
                st.error(f"No fue posible vincular el archivo de coordenadas: {exc}")

        muni_file = st.file_uploader(
            "GeoJSON de municipios", type=["geojson", "json"], key=f"{key_prefix}_mun_geo"
        )
        dist_file = st.file_uploader(
            "GeoJSON de distritos", type=["geojson", "json"], key=f"{key_prefix}_dist_geo"
        )
        if muni_file is not None:
            try:
                geojson_municipios = load_geojson(muni_file)
            except Exception as exc:
                st.error(f"GeoJSON municipal inválido: {exc}")
        if dist_file is not None:
            try:
                geojson_distritos = load_geojson(dist_file)
            except Exception as exc:
                st.error(f"GeoJSON distrital inválido: {exc}")

        pop_file = st.file_uploader(
            "Población municipal opcional (CSV/XLS/XLSX)",
            type=["csv", "xls", "xlsx", "txt"],
            key=f"{key_prefix}_pop",
        )
        if pop_file is not None:
            try:
                poblacion = read_table(pop_file.getvalue(), pop_file.name)
                st.success(f"Tabla poblacional cargada: {len(poblacion):,} filas.")
            except Exception as exc:
                st.error(f"No fue posible leer la población: {exc}")

    with st.expander("🔎 Filtros epidemiológicos", expanded=True):
        filtered = _filter_dataframe_ui(work)

    lat_detected, lon_detected, src_detected = detect_coordinate_columns(filtered)
    # Prioriza suplemento institucional cuando existe.
    if "Latitud_institucional" in filtered.columns and "Longitud_institucional" in filtered.columns:
        own_lat, own_lon, own_source = detect_coordinate_columns(filtered)
        if own_lat and own_lon and own_lat != "Latitud_institucional":
            filtered["__lat_final"] = pd.to_numeric(filtered["Latitud_institucional"], errors="coerce").combine_first(
                pd.to_numeric(filtered[own_lat], errors="coerce")
            )
            filtered["__lon_final"] = pd.to_numeric(filtered["Longitud_institucional"], errors="coerce").combine_first(
                pd.to_numeric(filtered[own_lon], errors="coerce")
            )
            filtered["__src_final"] = filtered["Fuente_Coordenada_institucional"].fillna("").astype(str)
            if own_source and own_source in filtered.columns:
                mask = filtered["__src_final"].str.strip().eq("")
                filtered.loc[mask, "__src_final"] = filtered.loc[mask, own_source].astype(str)
            lat_detected, lon_detected, src_detected = "__lat_final", "__lon_final", "__src_final"
        else:
            lat_detected, lon_detected = "Latitud_institucional", "Longitud_institucional"
            src_detected = "Fuente_Coordenada_institucional"

    st.markdown("#### Configuración cartográfica")
    c1, c2, c3 = st.columns([1.2, 1.0, 1.0])
    with c1:
        view_mode = st.radio(
            "Vista",
            ["Concentración + puntos", "Solo concentración", "Solo puntos"],
            horizontal=False,
            key=f"{key_prefix}_view",
        )
    with c2:
        heat_opacity = st.slider(
            "Opacidad de concentración",
            min_value=0.10,
            max_value=0.60,
            value=0.30,
            step=0.05,
            key=f"{key_prefix}_opacity",
        )
        heat_radius = st.slider("Radio", 8, 45, 22, key=f"{key_prefix}_radius")
        heat_blur = st.slider("Difuminado", 5, 35, 18, key=f"{key_prefix}_blur")
    with c3:
        show_municipios = st.checkbox("Límites municipales", value=True, key=f"{key_prefix}_mun")
        show_distritos = st.checkbox("Límites distritales", value=True, key=f"{key_prefix}_dist")
        only_exact = st.checkbox("Mostrar solo puntos exactos", value=False, key=f"{key_prefix}_only_exact")
        exact_heat = st.checkbox("Concentración solo con exactos", value=False, key=f"{key_prefix}_exact_heat")
        cluster = st.checkbox("Agrupar puntos cercanos", value=False, key=f"{key_prefix}_cluster")

    columns = list(filtered.columns)
    lat_options = [""] + columns
    lon_options = [""] + columns
    src_options = [""] + columns

    with st.expander("⚙️ Columnas de georreferencia", expanded=not bool(lat_detected and lon_detected)):
        lat_col = st.selectbox(
            "Latitud",
            lat_options,
            index=_select_default(lat_options, lat_detected),
            key=f"{key_prefix}_lat",
        )
        lon_col = st.selectbox(
            "Longitud",
            lon_options,
            index=_select_default(lon_options, lon_detected),
            key=f"{key_prefix}_lon",
        )
        src_col = st.selectbox(
            "Fuente/tipo de coordenada",
            src_options,
            index=_select_default(src_options, src_detected),
            key=f"{key_prefix}_src",
        )

    if not lat_col or not lon_col:
        st.warning(
            "No hay columnas de coordenadas seleccionadas. Puedes cargar un archivo institucional por Folio "
            "o elegir manualmente las columnas de latitud y longitud."
        )
        points = pd.DataFrame(columns=list(filtered.columns) + ["__lat", "__lon", "__precision_coord", "__fuente_coord"])
    else:
        points = prepare_map_points(filtered, lat_col, lon_col, src_col or None, only_sonora_bounds=True)

    if only_exact and not points.empty:
        points = points[points["__precision_coord"].eq("Exacta")].copy()

    total = len(filtered)
    mapped = len(points)
    exact = int(points["__precision_coord"].eq("Exacta").sum()) if mapped else 0
    approx = int(points["__precision_coord"].eq("Aproximada").sum()) if mapped else 0
    no_coords = max(total - mapped, 0)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Casos filtrados", f"{total:,}")
    k2.metric("Con coordenadas", f"{mapped:,}")
    k3.metric("Puntos exactos", f"{exact:,}")
    k4.metric("Sin coordenadas válidas", f"{no_coords:,}")
    if mapped and approx:
        st.caption(f"Coordenadas aproximadas identificadas: {approx:,}.")

    m = build_folium_map(
        points,
        geojson_municipios=geojson_municipios,
        geojson_distritos=geojson_distritos,
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

    st_folium(m, width=None, height=650, returned_objects=[], key=f"{key_prefix}_folium")
    st.download_button(
        "⬇️ Descargar mapa interactivo HTML",
        data=map_to_html_bytes(m),
        file_name="POPIS_mapa_espacial.html",
        mime="text/html",
        key=f"{key_prefix}_download_html",
    )

    municipality_col = _first_existing(filtered.columns, MUNICIPIO_CANDIDATES)
    if municipality_col:
        st.markdown("#### Incidencia municipal")
        multiplier = st.selectbox(
            "Tasa por habitantes",
            [1000, 10000, 100000],
            index=2,
            format_func=lambda x: f"{x:,}".replace(",", " "),
            key=f"{key_prefix}_multiplier",
        )

        pop_mun_col = None
        pop_value_col = None
        pop_year_col = None
        selected_year = None
        if poblacion is not None and not poblacion.empty:
            pop_cols = list(poblacion.columns)
            d_mun = _first_existing(pop_cols, ["Municipio", "MUNICIPIO", "municipio", "NOM_MUN", "NOMGEO"])
            d_pop = _first_existing(pop_cols, ["Poblacion", "POBLACION", "Población", "POB", "Total"])
            d_year = _first_existing(pop_cols, ["Año", "ANO", "ANIO", "Anio", "anio"])
            with st.expander("Columnas de población", expanded=not bool(d_mun and d_pop)):
                pop_mun_col = st.selectbox(
                    "Municipio en población",
                    pop_cols,
                    index=_select_default(pop_cols, d_mun),
                    key=f"{key_prefix}_pop_mun",
                )
                pop_value_col = st.selectbox(
                    "Población",
                    pop_cols,
                    index=_select_default(pop_cols, d_pop),
                    key=f"{key_prefix}_pop_value",
                )
                year_opts = [""] + pop_cols
                pop_year_col = st.selectbox(
                    "Año poblacional (opcional)",
                    year_opts,
                    index=_select_default(year_opts, d_year),
                    key=f"{key_prefix}_pop_year",
                )
                if pop_year_col:
                    years = pd.to_numeric(poblacion[pop_year_col], errors="coerce").dropna().astype(int)
                    if not years.empty:
                        year_values = sorted(years.unique().tolist())
                        selected_year = st.selectbox(
                            "Año de población",
                            year_values,
                            index=len(year_values) - 1,
                            key=f"{key_prefix}_pop_year_value",
                        )

        try:
            table = build_municipal_incidence_table(
                filtered,
                poblacion,
                municipio_col_casos=municipality_col,
                multiplier=int(multiplier),
                poblacion_municipio_col=pop_mun_col,
                poblacion_valor_col=pop_value_col,
                poblacion_anio_col=pop_year_col or None,
                anio=selected_year,
            )
            st.dataframe(table, use_container_width=True, hide_index=True)
            st.download_button(
                "⬇️ Descargar tabla municipal Excel",
                data=municipal_table_to_excel_bytes(table),
                file_name="POPIS_incidencia_municipal.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"{key_prefix}_download_xlsx",
            )
            st.caption(
                "Razón casos/población = porcentaje de casos estatales del municipio dividido entre su porcentaje de población estatal. "
                "Valores >1 indican sobrerrepresentación relativa, no causalidad."
            )
        except Exception as exc:
            st.error(f"No fue posible construir la tabla municipal: {exc}")
    else:
        st.info("No se identificó una columna de municipio de residencia para la tabla territorial.")
