from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from modulos.autocarga import (
    discover_project_assets,
    inbox_dir,
    load_optional_geojson,
    normalize_population_table,
    process_inbox,
    save_uploaded_to_inbox,
    status_table,
)
from modulos.exportacion import excel_report, graphics_zip
from modulos.indicadores_eda import calculate_indicators
from modulos.mapa_centroides import build_incidence_table, render_centroid_map
from modulos.motor_epidemiologico import (
    PATHOGENS,
    endemic_channel as sinave_channel,
    filter_cutoff,
    historical_comparison,
    load_sinave,
    mortality_by_year,
    pathogen_table,
    pathogen_weekly,
    summary,
    weekly_counts,
)
from modulos.motor_suive import (
    compare_sinave_suive,
    cumulative_at_cutoff,
    endemic_channel as suive_channel,
    read_suive,
    week_at_cutoff,
)

ROOT = Path(__file__).resolve().parent
for folder in [
    ROOT / "data" / "historicos",
    ROOT / "data" / "actual",
    ROOT / "data" / "entrada",
    ROOT / "data" / "backups",
    ROOT / "data" / "suive",
    ROOT / "data" / "poblacion",
    ROOT / "data" / "geografia",
    ROOT / "salidas",
]:
    folder.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="POPIS 5.0 · Todo en Uno", page_icon="🧬", layout="wide")
st.title("🧬 POPIS 5.0 · Todo en Uno")
st.caption("Procesador Operativo de Patógenos e Indicadores Sanitarios · SUIVE + SINAVE + canales + territorio + indicadores + exportación")

# La bandeja vigilada se procesa al abrir. Es el corazón de la actualización sin menús innecesarios.
actions = process_inbox(ROOT)
if actions:
    installed = [a for a in actions if a.status == "instalado"]
    if installed:
        st.toast(f"POPIS instaló {len(installed)} fuente(s) nueva(s) desde data/entrada.", icon="✅")

assets = discover_project_assets(ROOT)

with st.sidebar:
    st.header("Centro de Datos")
    st.dataframe(status_table(assets), use_container_width=True, hide_index=True)
    st.caption(f"Bandeja automática: {inbox_dir(ROOT)}")
    uploaded = st.file_uploader(
        "Actualizar fuente",
        type=["xls", "xlsx", "csv", "txt", "json", "geojson"],
        accept_multiple_files=True,
        help="POPIS reconoce SINAVE, SUIVE, población, cartografía o coordenadas y las coloca en su carpeta operativa.",
    )
    if uploaded and st.button("Instalar archivos y recalcular", type="primary", use_container_width=True):
        for item in uploaded:
            save_uploaded_to_inbox(item.getvalue(), item.name, ROOT)
        result = process_inbox(ROOT)
        for item in result:
            if item.status == "instalado":
                st.success(item.message)
            elif item.status == "omitido":
                st.warning(item.message)
        st.rerun()

if not assets.sinave_by_year:
    st.warning("POPIS está instalado, pero todavía no encontró bases SINAVE. Coloca una base en data/entrada o usa 'Actualizar fuente' en el panel lateral.")
    st.info("El instalador intenta migrar automáticamente las bases de una instalación POPIS anterior. Si no existe una instalación previa, basta con cargar la base vigente una vez.")
    st.stop()

@st.cache_data(show_spinner="Leyendo bases SINAVE...")
def load_base(paths: tuple[str, ...]) -> pd.DataFrame:
    return load_sinave([Path(p) for p in paths])

base = load_base(tuple(str(p) for p in assets.sinave_files))
years = sorted(pd.to_numeric(base["Año"], errors="coerce").dropna().astype(int).unique())
current_year = max(years)
weeks_current = pd.to_numeric(base.loc[pd.to_numeric(base["Año"], errors="coerce").eq(current_year), "SemanaInicio_POPIS"], errors="coerce")
default_cut = int(weeks_current[weeks_current.between(1, 53)].max()) if weeks_current[weeks_current.between(1, 53)].notna().any() else 1

with st.sidebar:
    st.divider()
    selected_year = st.selectbox("Año de análisis", years, index=len(years) - 1)
    cutoff = st.slider("Corte epidemiológico", 1, 53, min(default_cut, 53))

current_cum = filter_cutoff(base, selected_year, cutoff)
current_week = filter_cutoff(base, selected_year, cutoff, exact_week=True)
metrics = summary(base, selected_year, cutoff)
weekly = weekly_counts(base)
historical = historical_comparison(base, cutoff)
mortality = mortality_by_year(base, cutoff)
path_cum = pathogen_table(current_cum)
path_week = pathogen_table(current_week)
indicators = calculate_indicators(current_cum)
geojson = load_optional_geojson(assets.municipal_geojson)
population = normalize_population_table(assets.population_file, selected_year)
incidence = build_incidence_table(current_cum, population, 100000)

suive = None
suive_error = None
if assets.suive_file:
    try:
        suive = read_suive(assets.suive_file)
    except Exception as exc:
        suive_error = str(exc)

# -----------------------------------------------------------------------------
# Resumen
# -----------------------------------------------------------------------------
tabs = st.tabs([
    "🏠 Resumen",
    "🧫 SINAVE",
    "📈 SUIVE",
    "🔁 Comparativo",
    "🌡️ Canal endémico",
    "🗺️ Mortalidad y territorio",
    "📋 Indicadores",
    "📦 Exportación",
])

with tabs[0]:
    st.subheader(f"Panorama epidemiológico · {selected_year} · SE{cutoff}")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Casos acumulados", f"{metrics['casos_acumulados']:,}")
    c2.metric(f"Casos SE{cutoff}", f"{metrics['casos_semana']:,}")
    c3.metric("Patógeno identificado", f"{metrics['positivos_acumulados']:,}")
    c4.metric(f"Positivos SE{cutoff}", f"{metrics['positivos_semana']:,}")
    c5.metric("Defunciones registradas", f"{metrics['defunciones_registradas']:,}")

    st.markdown("#### Casos por semana epidemiológica")
    pivot = weekly.pivot(index="Semana", columns="Año", values="Casos").fillna(0)
    st.line_chart(pivot)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Comparación al mismo corte")
        st.dataframe(historical, use_container_width=True, hide_index=True)
    with c2:
        st.markdown("#### Patógenos acumulados")
        st.dataframe(path_cum, use_container_width=True, hide_index=True)

with tabs[1]:
    st.subheader("SINAVE · vigilancia nominal y laboratorio")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"#### Patógenos acumulados ≤ SE{cutoff}")
        st.bar_chart(path_cum.set_index("Patógeno")["Detecciones"])
        st.dataframe(path_cum, use_container_width=True, hide_index=True)
    with c2:
        st.markdown(f"#### Patógenos en SE{cutoff}")
        st.bar_chart(path_week.set_index("Patógeno")["Detecciones"])
        st.dataframe(path_week, use_container_width=True, hide_index=True)
    with st.expander("Detalle nominal del corte", expanded=False):
        safe_cols = [c for c in ["Año", "Folio_POPIS", "Fecha_Inicio_POPIS", "SemanaInicio_POPIS", "Municipio_POPIS", "DiagFinal_POPIS", "EstadoResultado_POPIS", "Patógenos identificados"] if c in current_cum.columns]
        st.dataframe(current_cum[safe_cols], use_container_width=True, hide_index=True)

with tabs[2]:
    st.subheader("SUIVE/SUAVE · magnitud poblacional")
    if suive is None:
        st.warning("No hay una serie SUIVE utilizable." + (f" Detalle: {suive_error}" if suive_error else ""))
        st.caption("POPIS no inventa la vigilancia convencional. Coloca el libro SUIVE/SUAVE en data/entrada y será reconocido automáticamente.")
    else:
        sy = sorted(suive["Año"].astype(int).unique())
        st.caption(f"Años detectados: {min(sy)}–{max(sy)} · {len(suive):,} observaciones semanales")
        st.line_chart(suive.pivot(index="Semana", columns="Año", values="Casos").fillna(0))
        c1, c2 = st.columns(2)
        with c1:
            st.dataframe(cumulative_at_cutoff(suive, cutoff), use_container_width=True, hide_index=True)
        with c2:
            st.dataframe(week_at_cutoff(suive, cutoff), use_container_width=True, hide_index=True)

with tabs[3]:
    st.subheader("Comparativo SUIVE ↔ SINAVE")
    if suive is None:
        st.info("El comparativo se habilita automáticamente cuando POPIS detecta SUIVE/SUAVE.")
    else:
        comparison = compare_sinave_suive(weekly, suive, selected_year, cutoff)
        st.caption("La razón SINAVE/SUIVE se presenta como razón de registro. No se interpreta automáticamente como subregistro porque los universos de vigilancia son diferentes.")
        st.line_chart(comparison.set_index("Semana")[["SINAVE", "SUIVE"]])
        st.dataframe(comparison, use_container_width=True, hide_index=True)
        corr = comparison[["SINAVE", "SUIVE"]].corr().iloc[0, 1] if len(comparison) > 1 else float("nan")
        st.metric("Correlación semanal", "N/A" if pd.isna(corr) else f"{corr:.3f}")

with tabs[4]:
    st.subheader("Canal endémico")
    source_options = ["SINAVE EDA", "SINAVE por patógeno"] + (["SUIVE EDA"] if suive is not None else [])
    source = st.selectbox("Fuente", source_options)
    if source == "SUIVE EDA":
        source_weekly = suive.copy()
        available = sorted(source_weekly["Año"].astype(int).unique())
        default_hist = [y for y in available if y < selected_year]
        exclude_pandemic = st.checkbox("Excluir 2020–2021 del histórico", value=False)
        if exclude_pandemic:
            default_hist = [y for y in default_hist if y not in (2020, 2021)]
        hist_years = st.multiselect("Años históricos", available, default=default_hist)
        channel = suive_channel(source_weekly, hist_years, selected_year)
    elif source == "SINAVE por patógeno":
        pathogen = st.selectbox("Patógeno", list(PATHOGENS))
        source_weekly = pathogen_weekly(base, pathogen)
        available = sorted(source_weekly["Año"].astype(int).unique())
        hist_years = st.multiselect("Años históricos", available, default=[y for y in available if y < selected_year])
        channel = sinave_channel(source_weekly, hist_years, selected_year)
    else:
        source_weekly = weekly.copy()
        available = sorted(source_weekly["Año"].astype(int).unique())
        hist_years = st.multiselect("Años históricos", available, default=[y for y in available if y < selected_year])
        channel = sinave_channel(source_weekly, hist_years, selected_year)

    if not hist_years:
        st.warning("Selecciona al menos un año histórico.")
    else:
        st.area_chart(channel.set_index("Semana")[["Q1", "Mediana", "Q3"]])
        if "Actual" in channel.columns:
            st.line_chart(channel.set_index("Semana")[["Actual", "Mediana"]])
        st.dataframe(channel, use_container_width=True, hide_index=True)
        if len(hist_years) < 5:
            st.caption("⚠️ Referencia histórica corta. Interpreta el canal con cautela; cinco o más años ofrece una base más robusta.")

with tabs[5]:
    st.subheader("Mortalidad y territorio")
    st.caption("'Defunciones registradas' proviene de FecDefuncion. No equivale automáticamente a defunción normativa por EDA sin verificación de causa.")
    st.dataframe(mortality, use_container_width=True, hide_index=True)
    st.bar_chart(mortality.set_index("Año")["Defunciones registradas"])
    st.divider()
    render_centroid_map(current_cum, geojson=geojson, population=population, key_prefix="popis50")

with tabs[6]:
    st.subheader("Indicadores del Manual EDA")
    st.caption("POPIS muestra numerador, denominador, resultado, meta y nota metodológica. Cuando la base no contiene el denominador normativo, el resultado permanece N/A.")
    st.dataframe(indicators, use_container_width=True, hide_index=True)
    with st.expander("Interpretación de metas"):
        st.write("Notificación oportuna: 100%. Clasificación/muestreo/cobertura: ≥80% cuando el indicador es calculable. El rechazo preanalítico se interpreta inversamente: ≤10%.")

with tabs[7]:
    st.subheader("Exportación y actualización")
    st.write("Para la actualización semanal basta con colocar el nuevo archivo en `data/entrada` o usar el cargador lateral. POPIS hace respaldo de la fuente anterior antes de instalar la nueva.")
    sheets = {
        "Resumen": pd.DataFrame([metrics]),
        "Comparativo historico": historical,
        "Patogenos acumulados": path_cum,
        "Patogenos semana": path_week,
        "Mortalidad": mortality,
        "Indicadores": indicators,
        "Incidencia municipal": incidence,
        "Semanal SINAVE": weekly,
    }
    if suive is not None:
        sheets["Semanal SUIVE"] = suive
        sheets["Comparativo SUIVE SINAVE"] = compare_sinave_suive(weekly, suive, selected_year, cutoff)
    report = excel_report(sheets)
    graphs = graphics_zip(weekly, historical, path_cum, mortality, cutoff)
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("⬇️ Reporte Excel completo", report, f"POPIS_{selected_year}_SE{cutoff}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    with c2:
        st.download_button("⬇️ Todas las gráficas PNG", graphs, f"POPIS_graficas_{selected_year}_SE{cutoff}.zip", "application/zip", use_container_width=True)

    st.markdown("#### Fuentes activas")
    st.dataframe(status_table(assets), use_container_width=True, hide_index=True)
    if assets.warnings:
        for warning in assets.warnings:
            st.warning(warning)
