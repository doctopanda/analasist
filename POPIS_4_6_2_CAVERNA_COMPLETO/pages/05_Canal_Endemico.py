from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from modulos.canal_endemico import attach_current, build_endemic_channel, pathogen_weekly_series
from modulos.runtime import load_runtime
from modulos.sinave import PATHOGENS, weekly_series
from modulos.tema_caverna import CORAL, GREEN, NAVY, apply_theme, hero, section, style_plotly

st.set_page_config(page_title="POPIS · Canal endémico", page_icon="📉", layout="wide")
apply_theme()
ctx = load_runtime(process_updates=False)
hero("Canal endémico", subtitle="Referencia histórica semanal · cuartiles Q1, mediana y Q3",
     cutoff=ctx.cutoff_label, badges=["Cuartílico", "SUIVE", "SINAVE", "Patógenos"])


def draw_channel(frame: pd.DataFrame, current_col: str | None, title: str):
    fig = go.Figure()
    if not frame.empty:
        fig.add_trace(go.Scatter(x=frame["Semana"], y=frame["Q3"], mode="lines", line=dict(width=0), showlegend=False))
        fig.add_trace(go.Scatter(x=frame["Semana"], y=frame["Q1"], mode="lines", line=dict(width=0), fill="tonexty", fillcolor="rgba(231,111,118,.17)", name="Q1–Q3"))
        fig.add_trace(go.Scatter(x=frame["Semana"], y=frame["Mediana"], mode="lines", line=dict(color=GREEN, width=2), name="Mediana"))
        fig.add_trace(go.Scatter(x=frame["Semana"], y=frame["Q1"], mode="lines", line=dict(color="#89B0AE", dash="dot"), name="Q1"))
        fig.add_trace(go.Scatter(x=frame["Semana"], y=frame["Q3"], mode="lines", line=dict(color=CORAL, dash="dot"), name="Q3"))
        if current_col and current_col in frame:
            fig.add_trace(go.Scatter(x=frame["Semana"], y=frame[current_col], mode="lines+markers", line=dict(color=NAVY, width=3), name=current_col))
    return style_plotly(fig, title)

mode = st.sidebar.radio("Motor", ["SUIVE/SUAVE", "SINAVE total", "SINAVE por patógeno"])

if mode == "SUIVE/SUAVE":
    if not ctx.has_suive:
        st.warning("No hay fuente SUIVE/SUAVE disponible.")
        st.stop()
    years = sorted(ctx.suive["Año"].astype(int).unique())
    current_year = years[-1]
    historical = [y for y in years if y != current_year]
    exclude_pandemic = st.sidebar.checkbox("Excluir 2020–2021 del histórico", value=False)
    excluded = [2020, 2021] if exclude_pandemic else []
    defaults = [y for y in historical if y not in excluded]
    selected = st.sidebar.multiselect("Años históricos", historical, default=defaults)
    channel, used = build_endemic_channel(ctx.suive, current_year=current_year, historical_years=selected, exclude_years=excluded)
    frame = attach_current(channel, ctx.suive, current_year, ctx.cutoff_week if current_year == ctx.current_year else None)
    section("Canal endémico SUIVE/SUAVE")
    if len(used) < 3:
        st.warning("Historia insuficiente para un canal operativo robusto. POPIS muestra el cálculo exploratorio, pero recomienda al menos 3 años y preferentemente 5 o más.")
    st.plotly_chart(draw_channel(frame, f"Casos {current_year}", f"SUIVE/SUAVE · histórico {', '.join(map(str, used))}"), use_container_width=True)
    st.dataframe(frame, use_container_width=True, hide_index=True)

elif mode == "SINAVE total":
    if not ctx.has_sinave:
        st.warning("No hay SINAVE disponible.")
        st.stop()
    series = weekly_series(ctx.sinave)
    years = sorted(series["Año"].astype(int).unique())
    current_year = years[-1]
    historical = [y for y in years if y != current_year]
    selected = st.sidebar.multiselect("Años históricos", historical, default=historical)
    channel, used = build_endemic_channel(series, current_year=current_year, historical_years=selected)
    frame = attach_current(channel, series, current_year, ctx.cutoff_week)
    section("Canal endémico SINAVE nominal")
    if len(used) < 3:
        st.warning("SINAVE no reúne todavía profundidad histórica suficiente para un canal robusto. La visualización es exploratoria.")
    st.plotly_chart(draw_channel(frame, f"Casos {current_year}", f"SINAVE total · histórico {', '.join(map(str, used))}"), use_container_width=True)
    st.dataframe(frame, use_container_width=True, hide_index=True)

else:
    if not ctx.has_sinave:
        st.warning("No hay SINAVE disponible.")
        st.stop()
    pathogen = st.sidebar.selectbox("Patógeno", PATHOGENS)
    series = pathogen_weekly_series(ctx.sinave, pathogen)
    years = sorted(series["Año"].astype(int).unique()) if not series.empty else []
    if not years:
        st.info("Sin datos para este patógeno.")
        st.stop()
    current_year = years[-1]
    historical = [y for y in years if y != current_year]
    selected = st.sidebar.multiselect("Años históricos", historical, default=historical)
    channel, used = build_endemic_channel(series, current_year=current_year, historical_years=selected)
    frame = attach_current(channel, series, current_year, ctx.cutoff_week)
    section(f"Canal por patógeno · {pathogen}")
    if len(used) < 3:
        st.warning("Profundidad histórica limitada. Interprete este canal como exploratorio.")
    st.plotly_chart(draw_channel(frame, f"Casos {current_year}", f"{pathogen} · histórico {', '.join(map(str, used))}"), use_container_width=True)
    st.dataframe(frame, use_container_width=True, hide_index=True)

st.caption("El año actual se representa contra el histórico seleccionado y no se incorpora automáticamente al cálculo de límites.")
