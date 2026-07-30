from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_folium import st_folium

from modulos.redve import death_metrics
from modulos.runtime import load_runtime
from modulos.sinave import cutoff_base, mortality_registered, observed_cutoff_week
from modulos.tema_caverna import PLOTLY_COLORS, apply_theme, hero, section, style_plotly
from modulos.territorio import build_centroid_map, incidence_excel_bytes, incidence_table, map_html_bytes, normalize_population

st.set_page_config(page_title="POPIS · Mortalidad y territorio", page_icon="🗺️", layout="wide")
apply_theme()
ctx = load_runtime(process_updates=False)
hero(
    "Mortalidad y territorio",
    subtitle="SINAVE + REDVE · residencia · incidencia · centroides municipales",
    cutoff=ctx.cutoff_label,
    badges=["Mun_Res", "Centroide municipal", "Sonora", "REDVE"],
)

if not ctx.has_sinave:
    st.warning("No hay fuente SINAVE disponible.")
    st.stop()

years = sorted(pd.to_numeric(ctx.sinave["Año"], errors="coerce").dropna().astype(int).unique())
year = st.sidebar.selectbox("Año", years, index=len(years) - 1)
def_cut = observed_cutoff_week(ctx.sinave, year) or 53
cutoff = st.sidebar.slider("Semana de corte", 1, 53, min(def_cut, 53))
multiplier = st.sidebar.selectbox(
    "Tasa por habitantes", [1000, 10000, 100000], index=2,
    format_func=lambda x: f"{x:,}".replace(",", " "),
)
heat = st.sidebar.checkbox("Capa de concentración", value=True)
show_boundaries = st.sidebar.checkbox("Límites municipales", value=True)
work = cutoff_base(ctx.sinave, year, cutoff)

section("Defunciones integradas SINAVE + REDVE")
metrics = death_metrics(work)
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("SINAVE con fecha", metrics["defunciones_sinave_con_fecha"])
k2.metric("SINAVE total", metrics["defunciones_sinave"])
k3.metric("REDVE recuperadas", metrics["defunciones_redve_recuperadas"])
k4.metric("Integradas", metrics["defunciones_integradas"])
k5.metric("EDA dictaminadas", metrics["muertes_eda_dictaminadas_redve"])

mortality = mortality_registered(ctx.sinave, cutoff_week=cutoff)
if mortality.empty:
    st.info("No hay evidencia de defunción para mostrar al corte seleccionado.")
else:
    left, right = st.columns([1.15, 1.5], gap="large")
    with left:
        st.dataframe(mortality, use_container_width=True, hide_index=True)
    with right:
        fig = px.bar(
            mortality, x="Año", y=["SINAVE", "REDVE recuperadas"], barmode="stack",
            color_discrete_sequence=PLOTLY_COLORS,
            title=f"Defunciones integradas en casos ≤ SE{cutoff}",
            labels={"value": "Defunciones", "variable": "Fuente"},
        )
        st.plotly_chart(style_plotly(fig), use_container_width=True)

if ctx.has_redve:
    st.caption(
        f"Fuente REDVE: {ctx.assets.redve_file.name}. Los enlaces se aceptan uno a uno por folio, CURP o identidad única y conservan su criterio de cruce."
    )
else:
    st.warning("No hay REDVE cargado. Coloque la base en data/redve o data/entrada para complementar las defunciones.")

integrated = work[work.get("Defunción integrada", pd.Series(False, index=work.index)).fillna(False).astype(bool)].copy()
if not integrated.empty:
    with st.expander("🔍 Ver auditoría de defunciones", expanded=False):
        columns = [c for c in [
            "Folio", "SemanaInicio", "Mun_Res", "FecDefuncion", "MotivoDeEgreso",
            "Defunción SINAVE", "Defunción REDVE", "Fuente defunción",
            "Fecha defunción integrada", "Criterio cruce REDVE", "Confianza cruce REDVE",
            "REDVE_DEFFOLIO", "REDVE_CAUSASUJVIGCVE", "REDVE_CAUSASUJVIGDES",
            "REDVE_DEFUNCION_DICTAMINADA", "Muerte atribuida a EDA REDVE",
            "Muerte EDA pendiente REDVE",
        ] if c in integrated.columns]
        st.dataframe(integrated[columns], use_container_width=True, hide_index=True, height=360)

st.info(
    "La cifra integrada confirma evidencia de fallecimiento, pero no atribuye automáticamente la muerte a EDA. "
    "La atribución normativa se reserva para cruces REDVE con causa final A00–A09 y dictamen correspondiente."
)

section("Incidencia municipal")
population = normalize_population(ctx.assets.population_file, year) if ctx.assets.population_file else None
incidence = incidence_table(work, population, multiplier=multiplier)
if population is None:
    st.warning("No hay un denominador poblacional municipal compatible para este año. POPIS conserva los conteos y deja la incidencia como no calculable.")
st.dataframe(incidence, use_container_width=True, hide_index=True, height=420)
st.download_button(
    "⬇️ Descargar incidencia municipal Excel", incidence_excel_bytes(incidence),
    file_name=f"POPIS_incidencia_municipal_{year}_SE{cutoff}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

section("Mapa epidemiológico por centroides")
st.info("Cada marcador representa el centroide aproximado del municipio de residencia. No representa el domicilio ni la ubicación exacta de una persona.")
if not ctx.geojson:
    st.warning("No se dispone de cartografía municipal. POPIS intentará descargarla en el siguiente arranque con conexión a internet; también puede colocarse un GeoJSON de Sonora en data/geografia.")
else:
    map_obj = build_centroid_map(work, ctx.geojson, heat=heat, show_boundaries=show_boundaries)
    st_folium(map_obj, width=None, height=680, returned_objects=[])
    st.download_button(
        "⬇️ Descargar mapa interactivo HTML", map_html_bytes(map_obj),
        file_name=f"POPIS_mapa_centroides_{year}_SE{cutoff}.html", mime="text/html",
    )
