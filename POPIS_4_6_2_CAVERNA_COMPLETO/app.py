from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from modulos.runtime import load_runtime, system_status
from modulos.sinave import comparison_at_week, pathogen_table, summary, weekly_series
from modulos.tema_caverna import PLOTLY_COLORS, apply_theme, hero, section, style_plotly

st.set_page_config(
    page_title="POPIS 4.6.2 · CAVERNA",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()

ctx = load_runtime()
hero(
    "POPIS",
    cutoff=ctx.cutoff_label,
    badges=["v4.6.2", "VIGILANCIA EDA", "CAVERNA UI", "CENTROIDES", "REDVE"],
)

st.sidebar.markdown("### 🧬 POPIS 4.6.2")
st.sidebar.caption("SUIVE · SINAVE · REDVE · Indicadores · Territorio")
st.sidebar.info("Usa el menú superior de la barra lateral para abrir cada módulo. Las actualizaciones nuevas pueden colocarse en `data/entrada`.")

for message in ctx.inbox_messages:
    st.success(message)
for warning in ctx.warnings:
    st.warning(warning)

section("Estado del sistema")
st.dataframe(system_status(ctx), width="stretch", hide_index=True)

if not ctx.has_sinave:
    st.info(
        "POPIS está instalado y listo, pero todavía no encuentra una base SINAVE. "
        "Coloca históricos en `data/historicos`, la base vigente en `data/actual`, "
        "o deja la actualización nueva en `data/entrada`."
    )
    st.stop()

current_year = ctx.current_year or int(pd.to_numeric(ctx.sinave["Año"], errors="coerce").max())
cutoff = ctx.cutoff_week or 53
metrics = summary(ctx.sinave, current_year, cutoff)

section("Panorama epidemiológico")
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric(f"Acumulado ≤ SE{cutoff}", f"{metrics['casos_acumulados']:,}")
k2.metric(f"Casos SE{cutoff}", f"{metrics['casos_semana']:,}")
k3.metric("Positivos acumulados", f"{metrics['positivos_acumulados']:,}")
k4.metric("Positivos de la semana", f"{metrics['positivos_semana']:,}")
k5.metric(
    "Defunciones integradas",
    f"{metrics['defunciones_integradas']:,}",
    help=(
        "Unión sin duplicados de evidencia de defunción en SINAVE y casos vinculados con REDVE. "
        "No equivale por sí sola a defunción normativa atribuida a EDA."
    ),
)
st.caption(
    f"Defunciones del corte: {metrics['defunciones_sinave_con_fecha']} con fecha en SINAVE · "
    f"{metrics['defunciones_redve_recuperadas']} recuperada(s) únicamente por REDVE · "
    f"{metrics['muertes_eda_dictaminadas_redve']} atribuida(s) a EDA y dictaminada(s) en REDVE."
)

weekly = weekly_series(ctx.sinave)
pathogens = pathogen_table(ctx.sinave, current_year, cutoff)
left, right = st.columns([1.7, 1], gap="large")
with left:
    section("Tendencia semanal")
    years = sorted(pd.to_numeric(weekly["Año"], errors="coerce").dropna().astype(int).unique())
    selected_years = st.multiselect("Años a mostrar", years, default=years[-5:] if len(years) > 5 else years)
    view = weekly[weekly["Año"].isin(selected_years)] if selected_years else weekly
    fig = px.line(
        view, x="Semana", y="Casos", color="Año", markers=True,
        color_discrete_sequence=PLOTLY_COLORS,
        title="Casos SINAVE por semana epidemiológica",
    )
    fig.update_layout(hovermode="x unified")
    fig.update_yaxes(rangemode="tozero")
    st.plotly_chart(style_plotly(fig), width="stretch")
with right:
    section("Patógenos acumulados")
    positive = pathogens[pathogens["Detecciones"].gt(0)].sort_values("Detecciones")
    if positive.empty:
        st.info("Sin detecciones positivas en el corte seleccionado.")
    else:
        fig = px.bar(
            positive, x="Detecciones", y="Patógeno", orientation="h",
            color="Patógeno", color_discrete_sequence=PLOTLY_COLORS,
            title=f"Detecciones acumuladas ≤ SE{cutoff}",
        )
        fig.update_layout(showlegend=False)
        fig.update_yaxes(title=None)
        st.plotly_chart(style_plotly(fig), width="stretch")

section(f"Comparación histórica al mismo corte · SE{cutoff}")
comparison = comparison_at_week(ctx.sinave, cutoff)
st.dataframe(comparison, width="stretch", hide_index=True)

st.caption(
    "POPIS usa SemanaInicio como eje temporal principal de SINAVE. Las semanas posteriores al último dato observado no se convierten en cero. "
    "SUIVE/SUAVE y SINAVE son sistemas complementarios: se comparan y nunca se suman."
)
