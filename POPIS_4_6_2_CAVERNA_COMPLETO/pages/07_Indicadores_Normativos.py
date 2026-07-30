from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from modulos.indicadores import calculate_indicators
from modulos.runtime import load_runtime
from modulos.sinave import cutoff_base
from modulos.tema_caverna import PLOTLY_COLORS, apply_theme, hero, section, style_plotly

st.set_page_config(page_title="POPIS · Indicadores normativos", page_icon="📋", layout="wide")
apply_theme()
ctx = load_runtime(process_updates=False)
hero("Indicadores normativos", subtitle="Manual EDA 2022 · cálculo auditable con evidencia disponible",
     cutoff=ctx.cutoff_label, badges=["Numerador", "Denominador", "Meta", "Limitaciones explícitas"])

if not ctx.has_sinave:
    st.warning("No hay fuente SINAVE disponible.")
    st.stop()

years = sorted(pd.to_numeric(ctx.sinave["Año"], errors="coerce").dropna().astype(int).unique())
year = st.sidebar.selectbox("Año", years, index=len(years) - 1)
year_base = ctx.sinave[pd.to_numeric(ctx.sinave["Año"], errors="coerce").eq(year)]
weeks = pd.to_numeric(year_base.get("SemanaInicio"), errors="coerce")
def_cut = int(weeks[weeks.between(1, 53)].max()) if weeks[weeks.between(1, 53)].notna().any() else 53
cutoff = st.sidebar.slider("Corte SE", 1, 53, def_cut)
use_target = st.sidebar.checkbox("Tengo meta mensual normativa de Vibrio para el 2%", value=False)
monthly_target = None
if use_target:
    monthly_target = st.sidebar.number_input("Meta mensual Vibrio", min_value=1, value=100, step=1,
                                             help="Debe provenir del denominador normativo de vigilancia convencional, no de una suposición de POPIS.")

work = cutoff_base(ctx.sinave, year, cutoff)
ind = calculate_indicators(work, monthly_vibrio_target=monthly_target)

section("Tablero de cumplimiento")
calculable = ind[ind["Resultado %"].notna()].copy()
if calculable.empty:
    st.info("La base no contiene evidencia suficiente para reconstruir automáticamente los indicadores. Revisa la columna de limitaciones.")
else:
    c1, c2, c3 = st.columns(3)
    c1.metric("Indicadores calculables", f"{len(calculable):,}")
    c2.metric("Cumplen meta", f"{int(calculable['Estado'].eq('Cumple').sum()):,}")
    c3.metric("No cumplen", f"{int(calculable['Estado'].eq('No cumple').sum()):,}")
    fig = px.bar(calculable, x="Indicador", y="Resultado %", color="Estado", barmode="group",
                 color_discrete_sequence=PLOTLY_COLORS, title="Resultado de indicadores calculables")
    fig.add_hline(y=80, line_dash="dot", annotation_text="Referencia 80%")
    st.plotly_chart(style_plotly(fig), use_container_width=True)

section("Matriz auditable")
st.dataframe(ind, use_container_width=True, hide_index=True, height=560)
st.download_button("⬇️ Descargar indicadores CSV", ind.to_csv(index=False).encode("utf-8-sig"),
                   file_name=f"POPIS_indicadores_EDA_{year}_SE{cutoff}.csv", mime="text/csv")

st.info(
    "POPIS no completa variables ausentes mediante inferencias silenciosas. Un indicador aparece como ‘No calculable’ cuando falta el numerador, "
    "el denominador o la temporalidad normativa necesaria. El monitoreo del 2% exige una meta mensual derivada de vigilancia convencional."
)
