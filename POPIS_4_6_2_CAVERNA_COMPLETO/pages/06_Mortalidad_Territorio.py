from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_folium import st_folium

from modulos.runtime import load_runtime
from modulos.sinave import cutoff_base, mortality_registered
from modulos.tema_caverna import PLOTLY_COLORS, apply_theme, hero, section, style_plotly
from modulos.territorio import build_centroid_map, incidence_excel_bytes, incidence_table, map_html_bytes, normalize_population

st.set_page_config(page_title="POPIS · Mortalidad y territorio", page_icon="🗺️", layout="wide")
apply_theme()
ctx = load_runtime(process_updates=False)
hero("Mortalidad y territorio", subtitle="Defunciones registradas · residencia · incidencia · centroides municipales",
     cutoff=ctx.cutoff_label, badges=["Mun_Res", "Centroide municipal", "Sonora"])

if not ctx.has_sinave:
    st.warning("No hay fuente SINAVE disponible.")
    st.stop()

years = sorted(pd.to_numeric(ctx.sinave["Año"], errors="coerce").dropna().astype(int).unique())
year = st.sidebar.selectbox("Año", years, index=len(years) - 1)
base_year = ctx.sinave[pd.to_numeric(ctx.sinave["Año"], errors="coerce").eq(year)]
weeks = pd.to_numeric(base_year.get("SemanaInicio"), errors="coerce")
def_cut = int(weeks[weeks.between(1, 53)].max()) if weeks[weeks.between(1, 53)].notna().any() else 53
cutoff = st.sidebar.slider("Semana de corte", 1, 53, def_cut)
multiplier = st.sidebar.selectbox("Tasa por habitantes", [1000, 10000, 100000], index=2,
                                  format_func=lambda x: f"{x:,}".replace(",", " "))
heat = st.sidebar.checkbox("Capa de concentración", value=True)
show_boundaries = st.sidebar.checkbox("Límites municipales", value=True)

work = cutoff_base(ctx.sinave, year, cutoff)

section("Defunciones registradas en SINAVE")
mort = mortality_registered(ctx.sinave, cutoff_week=cutoff)
if mort.empty:
    st.info("No hay fechas de defunción registradas para mostrar al corte seleccionado.")
else:
    left, right = st.columns([1, 1.6])
    with left:
        st.dataframe(mort, use_container_width=True, hide_index=True)
    with right:
        fig = px.bar(mort, x="Año", y="Defunciones registradas", color="Año",
                     color_discrete_sequence=PLOTLY_COLORS, title=f"Defunciones registradas ≤ SE{cutoff}")
        st.plotly_chart(style_plotly(fig), use_container_width=True)
st.warning("FecDefuncion se presenta como defunción registrada en la base. No se clasifica automáticamente como defunción normativa por EDA sin validación clínica y epidemiológica adicional.")

section("Incidencia municipal")
population = normalize_population(ctx.assets.population_file, year) if ctx.assets.population_file else None
incidence = incidence_table(work, population, multiplier=multiplier)
if population is None:
    st.warning("No hay un denominador poblacional municipal compatible para este año. POPIS conserva los conteos y deja la incidencia como no calculable.")
st.dataframe(incidence, use_container_width=True, hide_index=True, height=420)
st.download_button("⬇️ Descargar incidencia municipal Excel", incidence_excel_bytes(incidence),
                   file_name=f"POPIS_incidencia_municipal_{year}_SE{cutoff}.xlsx",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

section("Mapa epidemiológico por centroides")
st.info("Cada marcador representa el centroide aproximado del municipio de residencia. No representa el domicilio ni la ubicación exacta de una persona.")
if not ctx.geojson:
    st.warning("No se dispone de cartografía municipal. POPIS intentará descargarla en el siguiente arranque con conexión a internet; también puede colocarse un GeoJSON de Sonora en data/geografia.")
else:
    map_obj = build_centroid_map(work, ctx.geojson, heat=heat, show_boundaries=show_boundaries)
    st_folium(map_obj, width=None, height=680, returned_objects=[])
    st.download_button("⬇️ Descargar mapa interactivo HTML", map_html_bytes(map_obj),
                       file_name=f"POPIS_mapa_centroides_{year}_SE{cutoff}.html", mime="text/html")
