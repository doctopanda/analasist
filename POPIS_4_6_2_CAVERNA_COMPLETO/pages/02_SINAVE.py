from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from modulos.redve import death_metrics
from modulos.runtime import load_runtime
from modulos.sinave import (
    PATHOGENS,
    comparison_at_week,
    cutoff_base,
    death_comparison_by_year,
    observed_cutoff_week,
    weekly_series,
)
from modulos.tema_caverna import PLOTLY_COLORS, apply_theme, hero, section, style_plotly

st.set_page_config(page_title="POPIS · SINAVE", page_icon="🧫", layout="wide")
apply_theme()
ctx = load_runtime(process_updates=False)
hero(
    "SINAVE",
    subtitle="Vigilancia nominal EDA · comparaciones históricas · laboratorio · mortalidad vinculada",
    cutoff=ctx.cutoff_label,
    badges=["SemanaInicio", "Nominal", "Patógenos", "REDVE"],
)

if not ctx.has_sinave:
    st.warning("No hay bases SINAVE en data/historicos o data/actual.")
    st.stop()

years = sorted(pd.to_numeric(ctx.sinave["Año"], errors="coerce").dropna().astype(int).unique())
year = st.sidebar.selectbox("Año", years, index=len(years) - 1)
year_base = ctx.sinave[pd.to_numeric(ctx.sinave["Año"], errors="coerce").eq(year)]
max_week = observed_cutoff_week(ctx.sinave, year) or 53
cutoff = st.sidebar.slider("Corte SE", 1, 53, min(max_week, 53))

mun_col = "Mun_Res" if "Mun_Res" in ctx.sinave.columns else None
if mun_col:
    municipalities = sorted(x for x in year_base[mun_col].fillna("").astype(str).str.strip().unique() if x)
    selected_mun = st.sidebar.multiselect("Municipios de residencia", municipalities)
else:
    selected_mun = []

analysis_base = ctx.sinave.copy()
if selected_mun and mun_col:
    analysis_base = analysis_base[analysis_base[mun_col].isin(selected_mun)]
work = cutoff_base(analysis_base, year, cutoff)

section("Base nominal del corte")
a, b, c, d = st.columns(4)
a.metric("Registros", f"{len(work):,}")
b.metric("Con patógeno identificado", f"{int(work['Patógeno identificado'].sum()):,}")
c.metric("Pendientes", f"{int(work['Estado del resultado'].eq('Pendiente / sin diagnóstico final').sum()):,}")
d.metric("Rechazados", f"{int(work['Estado del resultado'].eq('Muestra rechazada / sin diagnóstico').sum()):,}")

left, right = st.columns(2, gap="large")
with left:
    status = work["Estado del resultado"].value_counts().rename_axis("Estado").reset_index(name="Casos")
    fig = px.pie(status, values="Casos", names="Estado", hole=.48,
                 color_discrete_sequence=PLOTLY_COLORS, title="Estado de resultados")
    st.plotly_chart(style_plotly(fig), use_container_width=True)
with right:
    ptab = pd.DataFrame([
        {"Patógeno": pathogen, "Detecciones": int(work[pathogen].sum())}
        for pathogen in PATHOGENS
    ]).query("Detecciones > 0").sort_values("Detecciones")
    if ptab.empty:
        st.info("No hay detecciones positivas en este corte.")
    else:
        fig = px.bar(
            ptab, x="Detecciones", y="Patógeno", orientation="h",
            color="Patógeno", color_discrete_sequence=PLOTLY_COLORS,
            title="Patógenos identificados",
        )
        fig.update_layout(showlegend=False)
        fig.update_yaxes(title=None)
        st.plotly_chart(style_plotly(fig), use_container_width=True)

section("Comparador por semana epidemiológica y año")
comparison = comparison_at_week(analysis_base, cutoff)
week_col = f"Casos SE{cutoff}"
cumulative_col = f"Acumulado ≤ SE{cutoff}"
chart_left, chart_right = st.columns(2, gap="large")
with chart_left:
    exact_view = comparison.dropna(subset=[week_col])
    fig = px.bar(
        exact_view, x="Año", y=week_col, text_auto=True,
        color="Año", color_discrete_sequence=PLOTLY_COLORS,
        title=f"Casos de la SE{cutoff} por año",
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(style_plotly(fig), use_container_width=True)
with chart_right:
    cumulative_view = comparison.dropna(subset=[cumulative_col])
    fig = px.bar(
        cumulative_view, x="Año", y=cumulative_col, text_auto=True,
        color="Año", color_discrete_sequence=PLOTLY_COLORS,
        title=f"Casos acumulados hasta SE{cutoff} por año",
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(style_plotly(fig), use_container_width=True)

comparison_columns = [
    "Año", "Cobertura", week_col, cumulative_col,
    f"Variación SE{cutoff} vs año previo %", "Variación acumulada vs año previo %",
    "Positivos semana", "Positivos acumulados",
]
st.dataframe(
    comparison[[column for column in comparison_columns if column in comparison.columns]],
    use_container_width=True, hide_index=True,
)
st.caption(
    "Cuando un año no tiene cobertura hasta la semana seleccionada, POPIS deja el valor vacío. "
    "La ausencia de información no se convierte en cero."
)

section("Defunciones: cruce SINAVE + REDVE")
deaths = death_metrics(work)
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("SINAVE con fecha", deaths["defunciones_sinave_con_fecha"],
          help="Registros con FecDefuncion capturada en SINAVE.")
k2.metric("SINAVE total", deaths["defunciones_sinave"],
          help="Fecha de defunción o motivo de egreso compatible con defunción.")
k3.metric("Recuperadas por REDVE", deaths["defunciones_redve_recuperadas"],
          help="Casos SINAVE sin evidencia directa de defunción que sí fueron vinculados a REDVE.")
k4.metric("Defunciones integradas", deaths["defunciones_integradas"],
          help="Unión sin duplicados de evidencia SINAVE y REDVE.")
k5.metric("EDA dictaminadas REDVE", deaths["muertes_eda_dictaminadas_redve"],
          help="Cruces REDVE con causa final A00–A09 y defunción dictaminada. No equivale al total integrado.")

if not ctx.has_redve:
    st.warning(
        "No hay fuente REDVE disponible. Colócala en data/redve o data/entrada para realizar el cruce de mortalidad."
    )
else:
    st.caption(
        f"REDVE activo: {ctx.assets.redve_file.name}. Cruce uno a uno por folio, CURP o identidad demográfica única. "
        "Los registros REDVE sin vínculo con un caso SINAVE no se agregan al numerador."
    )

mortality_by_year = death_comparison_by_year(analysis_base, cutoff)
if not mortality_by_year.empty:
    mort_left, mort_right = st.columns([1.25, 1], gap="large")
    with mort_left:
        st.dataframe(mortality_by_year, use_container_width=True, hide_index=True)
    with mort_right:
        plot_mort = mortality_by_year.dropna(subset=["Integradas"])
        fig = px.bar(
            plot_mort, x="Año", y=["SINAVE", "REDVE recuperadas"],
            barmode="stack", color_discrete_sequence=PLOTLY_COLORS,
            title=f"Defunciones integradas en casos ≤ SE{cutoff}",
            labels={"value": "Defunciones", "variable": "Fuente"},
        )
        st.plotly_chart(style_plotly(fig), use_container_width=True)

integrated_deaths = work[_bool := work.get("Defunción integrada", pd.Series(False, index=work.index)).fillna(False).astype(bool)].copy()
if integrated_deaths.empty:
    st.info("No hay defunciones integradas en el corte y filtros seleccionados.")
else:
    with st.expander("🔍 Auditoría de defunciones vinculadas", expanded=False):
        preferred_death = [
            "Folio", "SemanaInicio", "Mun_Res", "FecDefuncion", "MotivoDeEgreso",
            "Defunción SINAVE con fecha", "Defunción SINAVE", "Defunción REDVE",
            "Fuente defunción", "Fecha defunción integrada", "Criterio cruce REDVE",
            "Confianza cruce REDVE", "REDVE_DEFFOLIO", "REDVE_CAUSASUJVIGCVE",
            "REDVE_CAUSASUJVIGDES", "REDVE_DEFUNCION_DICTAMINADA",
            "REDVE_DEFUNCION_PROCESO_DICTAMINACION", "Muerte atribuida a EDA REDVE",
            "Muerte EDA pendiente REDVE", "Archivo de origen", "Archivo REDVE",
        ]
        audit_cols = [column for column in preferred_death if column in integrated_deaths.columns]
        st.dataframe(integrated_deaths[audit_cols], use_container_width=True, hide_index=True, height=360)
        st.download_button(
            "⬇️ Exportar auditoría de defunciones CSV",
            integrated_deaths[audit_cols].to_csv(index=False).encode("utf-8-sig"),
            file_name=f"POPIS_defunciones_integradas_{year}_SE{cutoff}.csv",
            mime="text/csv",
        )

st.info(
    "Defunción integrada significa evidencia de fallecimiento en SINAVE o REDVE. "
    "La atribución normativa a EDA se presenta por separado y exige el dictamen/código final de REDVE."
)

section("Serie semanal")
series = weekly_series(analysis_base, [year])
fig = px.line(series, x="Semana", y="Casos", markers=True, title=f"SINAVE {year} · casos por semana")
fig.update_layout(hovermode="x unified", showlegend=False)
fig.update_yaxes(rangemode="tozero")
st.plotly_chart(style_plotly(fig), use_container_width=True)
st.caption(f"Cobertura observada: hasta SE{max_week}. Las semanas posteriores sin registros no se dibujan como cero.")

section("Detalle nominal")
preferred = [c for c in [
    "Folio", "Fecha_Inicio", "SemanaInicio", "Mun_Res", "Diag_Prob", "Diag_Final",
    "Estado del resultado", "Patógenos identificados", "Defunción integrada", "Fuente defunción",
    "Archivo de origen",
] if c in work.columns]
show_cols = preferred + [c for c in work.columns if c not in preferred][:12]
st.dataframe(work[show_cols], use_container_width=True, hide_index=True, height=520)
st.download_button(
    "⬇️ Exportar corte SINAVE CSV", work.to_csv(index=False).encode("utf-8-sig"),
    file_name=f"POPIS_SINAVE_{year}_SE{cutoff}.csv", mime="text/csv",
)
