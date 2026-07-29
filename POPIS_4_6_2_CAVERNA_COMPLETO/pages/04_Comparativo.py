from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from modulos.comparativo import compare_systems, paired_pathogen_note
from modulos.runtime import load_runtime
from modulos.tema_caverna import PLOTLY_COLORS, apply_theme, hero, section, style_plotly

st.set_page_config(page_title="POPIS · Comparativo", page_icon="⚖️", layout="wide")
apply_theme()
ctx = load_runtime(process_updates=False)
hero("Comparativo", subtitle="SUIVE/SUAVE ↔ SINAVE · lectura complementaria sin sumar sistemas",
     cutoff=ctx.cutoff_label, badges=["Razón de registro", "Discordancia", "Mismo corte"])

if not ctx.has_sinave or not ctx.has_suive:
    st.warning("Este módulo requiere simultáneamente una fuente SINAVE y una fuente SUIVE/SUAVE.")
    st.stop()

years_sin = set(pd.to_numeric(ctx.sinave["Año"], errors="coerce").dropna().astype(int))
years_sui = set(pd.to_numeric(ctx.suive["Año"], errors="coerce").dropna().astype(int))
years = sorted(years_sin & years_sui)
if not years:
    st.error("No hay años comunes entre los dos sistemas.")
    st.stop()
year = st.sidebar.selectbox("Año común", years, index=len(years) - 1)
def_cut = ctx.cutoff_week if year == ctx.current_year and ctx.cutoff_week else int(ctx.suive.loc[ctx.suive["Año"].eq(year), "Semana"].max())
cutoff = st.sidebar.slider("Semana de corte", 1, 53, min(int(def_cut or 53), 53))
weekly, cumulative = compare_systems(ctx.sinave, ctx.suive, cutoff, year)

sin_total = int(weekly["SINAVE"].sum())
sui_total = int(weekly["SUIVE"].sum())
ratio = sin_total / sui_total if sui_total else np.nan
c1, c2, c3, c4 = st.columns(4)
c1.metric("SINAVE acumulado", f"{sin_total:,}")
c2.metric("SUIVE acumulado", f"{sui_total:,.0f}")
c3.metric("Razón SINAVE/SUIVE", "NA" if pd.isna(ratio) else f"{ratio:.3f}")
c4.metric("Diferencia", f"{sui_total - sin_total:,.0f}")

section("Series semanales superpuestas")
long = weekly.melt(id_vars="Semana", value_vars=["SINAVE", "SUIVE"], var_name="Sistema", value_name="Casos")
fig = px.line(long, x="Semana", y="Casos", color="Sistema", markers=True,
              color_discrete_sequence=PLOTLY_COLORS, title=f"Sistemas al mismo corte · {year}")
st.plotly_chart(style_plotly(fig), use_container_width=True)

left, right = st.columns(2)
with left:
    section("Razón de registro semanal")
    fig = px.bar(weekly, x="Semana", y="Razón de registro SINAVE/SUIVE",
                 title="Razón de registro SINAVE/SUIVE")
    st.plotly_chart(style_plotly(fig), use_container_width=True)
with right:
    section("Razón acumulada")
    fig = px.line(cumulative, x="Semana", y="Razón acumulada SINAVE/SUIVE", markers=True,
                  title="Razón acumulada SINAVE/SUIVE")
    st.plotly_chart(style_plotly(fig), use_container_width=True)

st.info(
    "La razón de registro es descriptiva. POPIS no la etiqueta automáticamente como subregistro: "
    "SUIVE/SUAVE y SINAVE tienen objetivos, mecanismos y universos de captura distintos."
)
section("Correspondencias orientativas por agente")
st.dataframe(paired_pathogen_note(), use_container_width=True, hide_index=True)
