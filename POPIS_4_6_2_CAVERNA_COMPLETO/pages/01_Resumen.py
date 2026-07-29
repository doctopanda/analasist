from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from modulos.runtime import load_runtime
from modulos.sinave import comparison_at_week, observed_cutoff_week, pathogen_table, summary, weekly_series
from modulos.tema_caverna import PLOTLY_COLORS, apply_theme, hero, section, style_plotly

st.set_page_config(page_title="POPIS · Resumen", page_icon="📊", layout="wide")
apply_theme()
ctx = load_runtime(process_updates=False)
hero("Resumen", subtitle="Panorama epidemiológico integrado de POPIS", cutoff=ctx.cutoff_label,
     badges=["POPIS 4.6.2", "CAVERNA UI"])

if not ctx.has_sinave:
    st.warning("No hay una fuente SINAVE disponible.")
    st.stop()

years = sorted(pd.to_numeric(ctx.sinave["Año"], errors="coerce").dropna().astype(int).unique())
def_year = ctx.current_year if ctx.current_year in years else years[-1]
year = st.sidebar.selectbox("Año de análisis", years, index=years.index(def_year))
def_cut = observed_cutoff_week(ctx.sinave, year) or 53
cutoff = st.sidebar.slider("Semana epidemiológica de corte", 1, 53, min(def_cut, 53))

m = summary(ctx.sinave, year, cutoff)
cols = st.columns(5)
for col, (label, value) in zip(cols, [
    (f"Acumulado ≤ SE{cutoff}", m["casos_acumulados"]),
    (f"SE{cutoff}", m["casos_semana"]),
    ("Positivos acumulados", m["positivos_acumulados"]),
    ("Positivos semana", m["positivos_semana"]),
    ("Defunciones registradas", m["defunciones_registradas"]),
]):
    col.metric(label, f"{int(value):,}")

section("Tendencia semanal")
weekly = weekly_series(ctx.sinave)
plot_years = st.multiselect("Comparar años", years, default=years[-5:] if len(years) > 5 else years)
view = weekly[weekly["Año"].isin(plot_years)] if plot_years else weekly
fig = px.line(
    view,
    x="Semana",
    y="Casos",
    color="Año",
    markers=True,
    color_discrete_sequence=PLOTLY_COLORS,
    title="Casos por semana epidemiológica",
)
fig.update_layout(hovermode="x unified")
fig.update_yaxes(rangemode="tozero")
st.plotly_chart(style_plotly(fig), use_container_width=True)
st.caption("Las semanas posteriores al último dato observado permanecen ausentes y no se grafican como cero.")

left, right = st.columns(2, gap="large")
with left:
    section("Patógenos acumulados")
    table = pathogen_table(ctx.sinave, year, cutoff)
    st.dataframe(table, use_container_width=True, hide_index=True)
with right:
    section("Mismo corte entre años")
    st.dataframe(comparison_at_week(ctx.sinave, cutoff), use_container_width=True, hide_index=True)
