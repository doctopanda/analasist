from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from modulos.calidad import audit_base, completeness_table
from modulos.runtime import load_runtime, system_status
from modulos.tema_caverna import PLOTLY_COLORS, apply_theme, hero, section, style_plotly

st.set_page_config(page_title="POPIS · Calidad y auditoría", page_icon="🔎", layout="wide")
apply_theme()
ctx = load_runtime(process_updates=False)
hero("Calidad y auditoría", subtitle="Trazabilidad de fuentes, completitud y alertas estructurales",
     cutoff=ctx.cutoff_label, badges=["No modifica la base", "Trazabilidad", "QA"])

section("Fuentes detectadas")
st.dataframe(system_status(ctx), use_container_width=True, hide_index=True)
if ctx.warnings:
    for warning in ctx.warnings:
        st.warning(warning)

if not ctx.has_sinave:
    st.info("No hay una base SINAVE disponible para auditar.")
    st.stop()

years = sorted(pd.to_numeric(ctx.sinave["Año"], errors="coerce").dropna().astype(int).unique())
year = st.sidebar.selectbox("Año", years, index=len(years) - 1)
work = ctx.sinave[pd.to_numeric(ctx.sinave["Año"], errors="coerce").eq(year)].copy()
summary, issues = audit_base(work)
completeness = completeness_table(work)

section("Indicadores de calidad")
cols = st.columns(min(4, len(summary)))
for idx, row in summary.head(4).iterrows():
    cols[idx].metric(str(row["Indicador"]), f"{int(row['Valor']):,}")
st.dataframe(summary, use_container_width=True, hide_index=True)

section("Completitud de campos")
fig = px.bar(completeness.head(25).sort_values("Completitud %"), x="Completitud %", y="Campo", orientation="h",
             color="Completitud %", color_continuous_scale="Blues", title="25 campos con menor completitud")
st.plotly_chart(style_plotly(fig), use_container_width=True)
st.dataframe(completeness, use_container_width=True, hide_index=True, height=420)

section("Incidencias estructurales")
if issues.empty:
    st.success("No se detectaron incidencias estructurales en las reglas básicas auditadas.")
else:
    st.dataframe(issues, use_container_width=True, hide_index=True, height=440)
    st.download_button("⬇️ Descargar incidencias CSV", issues.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"POPIS_auditoria_{year}.csv", mime="text/csv")

st.caption("El auditor reporta señales de calidad y no corrige ni elimina registros automáticamente.")
