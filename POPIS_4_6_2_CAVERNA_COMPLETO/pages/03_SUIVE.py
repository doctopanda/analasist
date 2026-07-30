from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from modulos.runtime import load_runtime
from modulos.suive import cumulative_at_cutoff, current_cutoff, matrix
from modulos.tema_caverna import PLOTLY_COLORS, apply_theme, hero, section, style_plotly

st.set_page_config(page_title="POPIS · SUIVE/SUAVE", page_icon="📈", layout="wide")
apply_theme()
ctx = load_runtime(process_updates=False)

if not ctx.has_suive:
    hero("SUIVE / SUAVE", subtitle="Vigilancia convencional · magnitud poblacional y tendencias",
         cutoff="Sin fuente", badges=["Convencional", "Semanal", "No sumar con SINAVE"])
    st.warning("No se encontró una fuente SUIVE/SUAVE en data/suive.")
    st.stop()

years = sorted(ctx.suive["Año"].astype(int).unique())
latest = years[-1]
def_cut = current_cutoff(ctx.suive, latest) or 53
hero(
    "SUIVE / SUAVE",
    subtitle="Vigilancia convencional · magnitud poblacional y tendencias",
    cutoff=f"SE {def_cut} · {latest}",
    badges=["Convencional", "Semanal", "No sumar con SINAVE"],
)

st.info(
    f"Fuente activa: `{ctx.assets.suive_file.name if ctx.assets.suive_file else 'sin fuente'}` · "
    f"año más reciente {latest} · última semana con dato SE{def_cut}."
)
cutoff = st.sidebar.slider("Semana de corte", 1, 53, min(def_cut, 53))
selected = st.sidebar.multiselect("Años", years, default=years[-5:] if len(years) > 5 else years)
view = ctx.suive[ctx.suive["Año"].isin(selected)] if selected else ctx.suive

section("Tendencia semanal convencional")
fig = px.line(view, x="Semana", y="Casos", color="Año", markers=True,
              color_discrete_sequence=PLOTLY_COLORS, title="SUIVE/SUAVE · casos por semana epidemiológica")
fig.update_layout(hovermode="x unified")
st.plotly_chart(style_plotly(fig), use_container_width=True)

section(f"Comparativo al mismo corte · SE{cutoff}")
cut = cumulative_at_cutoff(ctx.suive, cutoff)
left, right = st.columns([1.2, 1])
with left:
    st.dataframe(cut, use_container_width=True, hide_index=True)
with right:
    fig = px.bar(cut, x="Año", y="Acumulado", color="Año",
                 color_discrete_sequence=PLOTLY_COLORS, title=f"Acumulado SUIVE ≤ SE{cutoff}")
    st.plotly_chart(style_plotly(fig), use_container_width=True)

section("Matriz año × semana")
mat = matrix(ctx.suive)
st.dataframe(mat, use_container_width=True, height=430)
st.caption("Una celda vacía significa ausencia de dato. POPIS no la convierte automáticamente en cero.")
st.download_button("⬇️ Descargar SUIVE normalizado CSV", ctx.suive.to_csv(index=False).encode("utf-8-sig"),
                   file_name="POPIS_SUIVE_normalizado.csv", mime="text/csv")
