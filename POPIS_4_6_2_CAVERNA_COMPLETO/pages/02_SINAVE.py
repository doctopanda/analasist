from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from modulos.runtime import load_runtime
from modulos.sinave import PATHOGENS, cutoff_base, pathogen_table, weekly_series
from modulos.tema_caverna import PLOTLY_COLORS, apply_theme, hero, section, style_plotly

st.set_page_config(page_title="POPIS · SINAVE", page_icon="🧫", layout="wide")
apply_theme()
ctx = load_runtime(process_updates=False)
hero("SINAVE", subtitle="Vigilancia nominal EDA · caracterización clínica y de laboratorio",
     cutoff=ctx.cutoff_label, badges=["SemanaInicio", "Nominal", "Patógenos"])

if not ctx.has_sinave:
    st.warning("No hay bases SINAVE en data/historicos o data/actual.")
    st.stop()

years = sorted(pd.to_numeric(ctx.sinave["Año"], errors="coerce").dropna().astype(int).unique())
year = st.sidebar.selectbox("Año", years, index=len(years) - 1)
year_base = ctx.sinave[pd.to_numeric(ctx.sinave["Año"], errors="coerce").eq(year)]
valid_weeks = pd.to_numeric(year_base["SemanaInicio"], errors="coerce")
max_week = int(valid_weeks[valid_weeks.between(1, 53)].max()) if valid_weeks[valid_weeks.between(1, 53)].notna().any() else 53
cutoff = st.sidebar.slider("Corte SE", 1, 53, max_week)
mun_col = "Mun_Res" if "Mun_Res" in year_base.columns else None
if mun_col:
    municipalities = sorted(x for x in year_base[mun_col].fillna("").astype(str).str.strip().unique() if x)
    selected_mun = st.sidebar.multiselect("Municipios de residencia", municipalities)
else:
    selected_mun = []

work = cutoff_base(ctx.sinave, year, cutoff)
if selected_mun and mun_col:
    work = work[work[mun_col].isin(selected_mun)]

section("Base nominal del corte")
a, b, c, d = st.columns(4)
a.metric("Registros", f"{len(work):,}")
b.metric("Con patógeno identificado", f"{int(work['Patógeno identificado'].sum()):,}")
c.metric("Pendientes", f"{int(work['Estado del resultado'].eq('Pendiente / sin diagnóstico final').sum()):,}")
d.metric("Rechazados", f"{int(work['Estado del resultado'].eq('Muestra rechazada / sin diagnóstico').sum()):,}")

left, right = st.columns(2)
with left:
    status = work["Estado del resultado"].value_counts().rename_axis("Estado").reset_index(name="Casos")
    fig = px.pie(status, values="Casos", names="Estado", hole=.48,
                 color_discrete_sequence=PLOTLY_COLORS, title="Estado de resultados")
    st.plotly_chart(style_plotly(fig), use_container_width=True)
with right:
    ptab = []
    for pathogen in PATHOGENS:
        ptab.append({"Patógeno": pathogen, "Detecciones": int(work[pathogen].sum())})
    ptab = pd.DataFrame(ptab).query("Detecciones > 0").sort_values("Detecciones")
    if ptab.empty:
        st.info("No hay detecciones positivas en este corte.")
    else:
        fig = px.bar(ptab, x="Detecciones", y="Patógeno", orientation="h",
                     color="Patógeno", color_discrete_sequence=PLOTLY_COLORS, title="Patógenos identificados")
        st.plotly_chart(style_plotly(fig), use_container_width=True)

section("Serie semanal")
series = weekly_series(ctx.sinave, [year])
fig = px.line(series, x="Semana", y="Casos", markers=True, title=f"SINAVE {year} · casos por semana")
st.plotly_chart(style_plotly(fig), use_container_width=True)

section("Detalle nominal")
preferred = [c for c in ["Folio", "Fecha_Inicio", "SemanaInicio", "Mun_Res", "Diag_Prob", "Diag_Final", "Estado del resultado", "Patógenos identificados", "Archivo de origen"] if c in work.columns]
show_cols = preferred + [c for c in work.columns if c not in preferred][:12]
st.dataframe(work[show_cols], use_container_width=True, hide_index=True, height=520)
st.download_button("⬇️ Exportar corte SINAVE CSV", work.to_csv(index=False).encode("utf-8-sig"),
                   file_name=f"POPIS_SINAVE_{year}_SE{cutoff}.csv", mime="text/csv")
