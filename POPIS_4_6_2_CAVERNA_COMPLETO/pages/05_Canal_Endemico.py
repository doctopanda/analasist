from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from modulos.canal_endemico import attach_current, build_endemic_channel, pathogen_weekly_series
from modulos.runtime import load_runtime
from modulos.sinave import PATHOGENS, observed_cutoff_week, weekly_series
from modulos.suive import current_cutoff
from modulos.tema_caverna import CORAL, GREEN, NAVY, apply_theme, hero, section, style_plotly

st.set_page_config(page_title="POPIS · Canal endémico", page_icon="📉", layout="wide")
apply_theme()
ctx = load_runtime(process_updates=False)
mode = st.sidebar.radio("Motor", ["SUIVE/SUAVE", "SINAVE total", "SINAVE por patógeno"])

source_cutoff_label = ctx.cutoff_label
if mode == "SUIVE/SUAVE" and ctx.has_suive:
    suive_years = sorted(ctx.suive["Año"].astype(int).unique())
    suive_current_year = suive_years[-1]
    suive_last_week = current_cutoff(ctx.suive, suive_current_year)
    source_cutoff_label = f"SE {suive_last_week} · {suive_current_year}" if suive_last_week else str(suive_current_year)

hero(
    "Canal endémico",
    subtitle="Referencia histórica semanal · cuartiles Q1, mediana y Q3",
    cutoff=source_cutoff_label,
    badges=["Cuartílico", "SUIVE", "SINAVE", "Patógenos"],
)


def draw_channel(frame: pd.DataFrame, current_col: str | None, title: str):
    fig = go.Figure()
    if not frame.empty:
        fig.add_trace(go.Scatter(x=frame["Semana"], y=frame["Q3"], mode="lines", line=dict(width=0), showlegend=False, connectgaps=False))
        fig.add_trace(go.Scatter(x=frame["Semana"], y=frame["Q1"], mode="lines", line=dict(width=0), fill="tonexty", fillcolor="rgba(231,111,118,.17)", name="Q1–Q3", connectgaps=False))
        fig.add_trace(go.Scatter(x=frame["Semana"], y=frame["Mediana"], mode="lines", line=dict(color=GREEN, width=2), name="Mediana", connectgaps=False))
        fig.add_trace(go.Scatter(x=frame["Semana"], y=frame["Q1"], mode="lines", line=dict(color="#89B0AE", dash="dot"), name="Q1", connectgaps=False))
        fig.add_trace(go.Scatter(x=frame["Semana"], y=frame["Q3"], mode="lines", line=dict(color=CORAL, dash="dot"), name="Q3", connectgaps=False))
        if current_col and current_col in frame:
            fig.add_trace(go.Scatter(
                x=frame["Semana"],
                y=frame[current_col],
                mode="lines+markers",
                line=dict(color=NAVY, width=3),
                marker=dict(size=6),
                name=current_col,
                connectgaps=False,
            ))
    fig.update_layout(hovermode="x unified")
    fig.update_yaxes(rangemode="tozero")
    return style_plotly(fig, title)


if mode == "SUIVE/SUAVE":
    if not ctx.has_suive:
        st.warning("No hay fuente SUIVE/SUAVE disponible.")
        st.stop()
    years = sorted(ctx.suive["Año"].astype(int).unique())
    current_year = years[-1]
    suive_cutoff = current_cutoff(ctx.suive, current_year)
    historical = [y for y in years if y != current_year]
    exclude_pandemic = st.sidebar.checkbox("Excluir 2020–2021 del histórico", value=False)
    excluded = [2020, 2021] if exclude_pandemic else []
    defaults = [y for y in historical if y not in excluded]
    selected = st.sidebar.multiselect("Años históricos", historical, default=defaults)
    channel, used = build_endemic_channel(ctx.suive, current_year=current_year, historical_years=selected, exclude_years=excluded)
    frame = attach_current(channel, ctx.suive, current_year, suive_cutoff)

    section("Fuente activa")
    st.info(
        f"SUIVE/SUAVE · `{ctx.assets.suive_file.name}` · año actual {current_year} · "
        f"última semana con dato: SE{suive_cutoff}. El corte de SINAVE no se usa para prolongar esta serie."
    )
    current = ctx.suive[ctx.suive["Año"].eq(current_year)].sort_values("Semana")
    if current.empty:
        st.warning(f"La fuente no produjo registros semanales para {current_year}.")
    else:
        nonzero = int(current["Casos"].gt(0).sum())
        c1, c2, c3 = st.columns(3)
        c1.metric("Semanas con dato", len(current))
        c2.metric("Semanas con casos > 0", nonzero)
        c3.metric("Acumulado disponible", f"{current['Casos'].sum():,.0f}")

    section("Canal endémico SUIVE/SUAVE")
    if len(used) < 3:
        st.warning("Historia insuficiente para un canal operativo robusto. POPIS muestra el cálculo exploratorio, pero recomienda al menos 3 años y preferentemente 5 o más.")
    st.plotly_chart(draw_channel(frame, f"Casos {current_year}", f"SUIVE/SUAVE · histórico {', '.join(map(str, used))}"), use_container_width=True)
    st.caption("Las semanas sin dato posterior al último corte de SUIVE permanecen vacías. POPIS no las transforma en cero.")
    st.dataframe(frame, use_container_width=True, hide_index=True)

elif mode == "SINAVE total":
    if not ctx.has_sinave:
        st.warning("No hay SINAVE disponible.")
        st.stop()
    series = weekly_series(ctx.sinave)
    years = sorted(series["Año"].astype(int).unique())
    current_year = years[-1]
    sinave_cutoff = observed_cutoff_week(ctx.sinave, current_year)
    historical = [y for y in years if y != current_year]
    selected = st.sidebar.multiselect("Años históricos", historical, default=historical)
    channel, used = build_endemic_channel(series, current_year=current_year, historical_years=selected)
    frame = attach_current(channel, series, current_year, sinave_cutoff)
    section("Fuente activa")
    st.info(
        f"SINAVE nominal · `{ctx.assets.current_sinave.name if ctx.assets.current_sinave else 'sin fuente'}` · "
        f"año {current_year} · última semana observada: SE{sinave_cutoff}."
    )
    section("Canal endémico SINAVE nominal")
    if len(used) < 3:
        st.warning("SINAVE no reúne todavía profundidad histórica suficiente para un canal robusto. La visualización es exploratoria.")
    st.plotly_chart(draw_channel(frame, f"Casos {current_year}", f"SINAVE total · histórico {', '.join(map(str, used))}"), use_container_width=True)
    st.caption("Después de la última semana observada, la serie actual queda en blanco. No se dibuja una cola de ceros.")
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
    sinave_cutoff = observed_cutoff_week(ctx.sinave, current_year)
    historical = [y for y in years if y != current_year]
    selected = st.sidebar.multiselect("Años históricos", historical, default=historical)
    channel, used = build_endemic_channel(series, current_year=current_year, historical_years=selected)
    frame = attach_current(channel, series, current_year, sinave_cutoff)
    section("Fuente activa")
    st.info(
        f"SINAVE por patógeno · `{ctx.assets.current_sinave.name if ctx.assets.current_sinave else 'sin fuente'}` · "
        f"{pathogen} · cobertura nominal hasta SE{sinave_cutoff}."
    )
    section(f"Canal por patógeno · {pathogen}")
    if len(used) < 3:
        st.warning("Profundidad histórica limitada. Interprete este canal como exploratorio.")
    st.plotly_chart(draw_channel(frame, f"Casos {current_year}", f"{pathogen} · histórico {', '.join(map(str, used))}"), use_container_width=True)
    st.caption("Los ceros solo se completan dentro del periodo cubierto por SINAVE; las semanas futuras sin información quedan ausentes.")
    st.dataframe(frame, use_container_width=True, hide_index=True)

st.caption("El año actual se representa contra el histórico seleccionado y no se incorpora automáticamente al cálculo de límites.")
