from __future__ import annotations

import pandas as pd
import streamlit as st

from modulos.calidad import audit_base
from modulos.comparativo import compare_systems
from modulos.exportacion import excel_bytes, graphics_zip, html_bytes, word_bytes
from modulos.indicadores import calculate_indicators
from modulos.runtime import load_runtime
from modulos.sinave import comparison_at_week, cutoff_base, pathogen_table, summary, weekly_series
from modulos.suive import cumulative_at_cutoff
from modulos.tema_caverna import apply_theme, hero, section
from modulos.territorio import incidence_table, normalize_population

st.set_page_config(page_title="POPIS · Exportación", page_icon="📦", layout="wide")
apply_theme()
ctx = load_runtime(process_updates=False)
hero("Exportación", subtitle="Productos reproducibles · Excel · Word · HTML · PNG",
     cutoff=ctx.cutoff_label, badges=["Reporte", "Tablas", "Gráficas", "Auditoría"])

if not ctx.has_sinave:
    st.warning("No hay una base SINAVE para construir productos.")
    st.stop()

years = sorted(pd.to_numeric(ctx.sinave["Año"], errors="coerce").dropna().astype(int).unique())
year = st.sidebar.selectbox("Año", years, index=len(years) - 1)
year_base = ctx.sinave[pd.to_numeric(ctx.sinave["Año"], errors="coerce").eq(year)]
weeks = pd.to_numeric(year_base.get("SemanaInicio"), errors="coerce")
def_cut = int(weeks[weeks.between(1, 53)].max()) if weeks[weeks.between(1, 53)].notna().any() else 53
cutoff = st.sidebar.slider("Corte SE", 1, 53, def_cut)

work = cutoff_base(ctx.sinave, year, cutoff)
metrics = summary(ctx.sinave, year, cutoff)
summary_df = pd.DataFrame([{"Indicador": k, "Valor": v} for k, v in metrics.items()])
pathogens = pathogen_table(ctx.sinave, year, cutoff)
history = comparison_at_week(ctx.sinave, cutoff)
weekly_sin = weekly_series(ctx.sinave)
audit_summary, audit_issues = audit_base(work)
indicators = calculate_indicators(work)
pop = normalize_population(ctx.assets.population_file, year) if ctx.assets.population_file else None
incidence = incidence_table(work, pop, 100000)

tables = {
    "Resumen": summary_df,
    "Patogenos": pathogens,
    "Comparativo_SE": history,
    "Incidencia_municipal": incidence,
    "Indicadores_normativos": indicators,
    "Calidad": audit_summary,
    "Incidencias_QA": audit_issues,
    "SINAVE_corte": work,
}

weekly_suive = None
if ctx.has_suive:
    weekly_suive = ctx.suive
    tables["SUIVE_mismo_corte"] = cumulative_at_cutoff(ctx.suive, cutoff)
    common = set(pd.to_numeric(ctx.sinave["Año"], errors="coerce").dropna().astype(int)) & set(ctx.suive["Año"].astype(int))
    if year in common:
        comp_weekly, comp_acc = compare_systems(ctx.sinave, ctx.suive, cutoff, year)
        tables["SINAVE_vs_SUIVE"] = comp_weekly
        tables["Comparativo_acumulado"] = comp_acc

section("Paquete de productos")
st.caption(f"Año {year} · corte SE{cutoff} · {len(work):,} registros SINAVE en el corte.")

excel = excel_bytes(tables)
word = word_bytes(
    f"POPIS · Informe epidemiológico EDA · {year} · SE{cutoff}",
    {k: v for k, v in tables.items() if k != "SINAVE_corte"},
    notes=[
        "SUIVE/SUAVE y SINAVE se presentan como sistemas complementarios y no se suman.",
        "Las defunciones derivadas de FecDefuncion se consideran registros en la base y no muertes normativas EDA sin validación adicional.",
        "Las localizaciones cartográficas de POPIS 4.6.2 corresponden a centroides municipales aproximados.",
    ],
)
html = html_bytes(f"POPIS · {year} · SE{cutoff}", {k: v for k, v in tables.items() if k != "SINAVE_corte"})
png_zip = graphics_zip(weekly_sin, weekly_suive, pathogens)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.download_button("📊 Excel completo", excel, file_name=f"POPIS_{year}_SE{cutoff}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
with c2:
    st.download_button("📝 Word", word, file_name=f"POPIS_{year}_SE{cutoff}.docx",
                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
with c3:
    st.download_button("🌐 HTML", html, file_name=f"POPIS_{year}_SE{cutoff}.html",
                       mime="text/html", use_container_width=True)
with c4:
    st.download_button("🖼️ Gráficas PNG", png_zip, file_name=f"POPIS_graficas_{year}_SE{cutoff}.zip",
                       mime="application/zip", use_container_width=True)

section("Contenido del Excel")
st.dataframe(pd.DataFrame([{"Hoja": k, "Filas": len(v), "Columnas": len(v.columns)} for k, v in tables.items()]),
             use_container_width=True, hide_index=True)
