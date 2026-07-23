from __future__ import annotations

from io import BytesIO
from pathlib import Path
import json
import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from popis_core import (
    audit_operational_definitions,
    build_comparison,
    combine_sinave,
    endemic_channel,
    laboratory_indicators,
    make_excel_report,
    nutrave_indicators,
    parse_suive_history,
    pathogen_summary,
    read_any_table,
    sinave_channel,
    sinave_summary,
    sinave_weekly,
    suive_summary,
    territorial_summary,
    zip_images,
)

st.set_page_config(page_title="POPIS 4.0", page_icon="🧪", layout="wide")

st.markdown(
    """
<style>
:root { --popis:#0f766e; --ink:#12353b; }
.block-container {padding-top: 1.4rem; padding-bottom: 3rem;}
[data-testid="stMetric"] {background:rgba(15,118,110,.07); border:1px solid rgba(15,118,110,.22); padding:14px; border-radius:14px;}
.popis-title {font-size:2.25rem; font-weight:800; color:#12353b; margin-bottom:0;}
.popis-sub {color:#52656a; margin-top:-.3rem;}
.note {padding:.8rem 1rem;border-radius:12px;background:#f4f8f8;border-left:4px solid #0f766e;}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown('<p class="popis-title">🧪 POPIS 4.0</p>', unsafe_allow_html=True)
st.markdown('<p class="popis-sub">Procesador Operativo de Patógenos e Indicadores Sanitarios · Sonora</p>', unsafe_allow_html=True)


def fig_to_png(fig, dpi=180) -> bytes:
    bio = BytesIO()
    fig.savefig(bio, format="png", dpi=dpi, bbox_inches="tight", facecolor="white")
    return bio.getvalue()


def download_fig(label: str, filename: str, fig, key: str, registry: dict[str, bytes]):
    payload = fig_to_png(fig)
    registry[filename] = payload
    st.download_button(label, payload, file_name=filename, mime="image/png", key=key)


def line_fig(data: pd.DataFrame, x: str, ys: list[str], title: str, ylabel: str = "Casos"):
    fig, ax = plt.subplots(figsize=(10, 4.8))
    for y in ys:
        if y in data.columns:
            ax.plot(data[x], data[y], marker="o" if len(data) <= 15 else None, linewidth=2, label=y)
    ax.set_title(title, fontweight="bold")
    ax.set_xlabel("Semana epidemiológica" if x == "SE" else x)
    ax.set_ylabel(ylabel)
    ax.grid(alpha=.2)
    if len(ys) > 1:
        ax.legend(frameon=False, ncol=2)
    fig.tight_layout()
    return fig


def bar_fig(data: pd.DataFrame, x: str, y: str, title: str, horizontal=False):
    fig, ax = plt.subplots(figsize=(9, 5))
    if horizontal:
        d = data.sort_values(y)
        ax.barh(d[x].astype(str), d[y])
    else:
        ax.bar(data[x].astype(str), data[y])
    ax.set_title(title, fontweight="bold")
    ax.set_ylabel(y if not horizontal else "")
    ax.grid(axis="y" if not horizontal else "x", alpha=.2)
    fig.tight_layout()
    return fig


def channel_fig(ch: pd.DataFrame, title: str):
    fig, ax = plt.subplots(figsize=(11, 5.2))
    x = ch["SE"]
    ax.fill_between(x, 0, ch["Q1"], alpha=.12, label="Éxito ≤ Q1")
    ax.fill_between(x, ch["Q1"], ch["Mediana"], alpha=.13, label="Seguridad")
    ax.fill_between(x, ch["Mediana"], ch["Q3"], alpha=.14, label="Alarma")
    ax.plot(x, ch["Q1"], linewidth=1.3, label="Q1")
    ax.plot(x, ch["Mediana"], linewidth=1.8, label="Mediana")
    ax.plot(x, ch["Q3"], linewidth=1.3, label="Q3")
    ax.plot(x, ch["Actual"], linewidth=2.7, marker="o", markersize=3, label="Año actual")
    ax.set_title(title, fontweight="bold")
    ax.set_xlabel("Semana epidemiológica")
    ax.set_ylabel("Casos")
    ax.set_xlim(1, 53)
    ax.grid(alpha=.18)
    ax.legend(frameon=False, ncol=4, fontsize=8)
    fig.tight_layout()
    return fig


def safe_num(v):
    try:
        return int(round(float(v)))
    except Exception:
        return 0


@st.cache_data(show_spinner=False)
def fetch_sonora_geojson():
    url = "https://gaia.inegi.org.mx/wscatgeo/v2/geo/mgem/26"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()


with st.sidebar:
    st.header("📥 Fuentes")
    st.caption("Los archivos se procesan en tu sesión. POPIS no requiere modificar las bases históricas.")
    suive_file = st.file_uploader("Histórico SUIVE/SUAVE", type=["xlsx", "xls"], key="suive")
    sinave_files = st.file_uploader(
        "Bases SINAVE EDA (uno o varios años)",
        type=["xls", "xlsx", "csv", "txt"], accept_multiple_files=True, key="sinave"
    )
    population_file = st.file_uploader("Población CONAPO (opcional)", type=["csv", "xlsx", "xls"], key="pop")
    st.divider()
    st.caption("💡 Rutina semanal: conserva históricos y sustituye/agrega solamente la base del año en curso.")

suive = pd.DataFrame()
sinave = pd.DataFrame()
population = pd.DataFrame()
errors = []

if suive_file:
    try:
        suive = parse_suive_history(suive_file, suive_file.name)
    except Exception as exc:
        errors.append(f"SUIVE: {exc}")

if sinave_files:
    try:
        sinave = combine_sinave([(f, f.name) for f in sinave_files])
    except Exception as exc:
        errors.append(f"SINAVE: {exc}")

if population_file:
    try:
        population = read_any_table(population_file, population_file.name)
    except Exception as exc:
        errors.append(f"Población: {exc}")

if errors:
    for err in errors:
        st.error(err)

available_years = sorted(
    set(suive["Año"].unique().tolist() if not suive.empty else []) |
    set(pd.to_numeric(sinave["year"], errors="coerce").dropna().astype(int).unique().tolist() if not sinave.empty else [])
)
current_year = max(available_years) if available_years else 2026

c1, c2, c3 = st.columns([1.3, 1, 1])
with c1:
    year = st.selectbox("Año de análisis", available_years or [2026], index=(len(available_years)-1 if available_years else 0))
with c2:
    week = st.number_input("Semana epidemiológica", min_value=1, max_value=53, value=26, step=1)
with c3:
    month = st.number_input("Mes para indicadores", min_value=1, max_value=12, value=6, step=1)
week = int(week); month = int(month)

if suive.empty and sinave.empty:
    st.info("Carga el histórico SUIVE y/o las bases SINAVE desde la barra lateral para iniciar.")
    st.markdown(
        """
<div class="note"><b>POPIS 4.0</b> separa tres preguntas: <b>SUIVE</b> mide magnitud y tendencia convencional; <b>SINAVE</b> caracteriza casos, laboratorio y etiología; el <b>Comparador</b> estudia su relación sin asumir que ambos universos deben ser idénticos.</div>
""", unsafe_allow_html=True)

images: dict[str, bytes] = {}
export_tables: dict[str, pd.DataFrame] = {}

TABS = st.tabs(["🏠 Resumen", "📘 SUIVE", "🧬 SINAVE", "🔄 Comparador", "📈 Canal endémico", "🗺️ Territorio", "☠️ Mortalidad", "🧮 Indicadores", "🔍 Auditoría", "📦 Exportar"])

# -----------------------------------------------------------------------------
# Resumen
# -----------------------------------------------------------------------------
with TABS[0]:
    st.subheader(f"Panorama integrado · {year} · corte SE{week}")
    su = suive_summary(suive, year, week) if not suive.empty else {"acumulado": np.nan, "semana": np.nan}
    si = sinave_summary(sinave, year, week) if not sinave.empty else {k: np.nan for k in ["acumulado","semana","positivos_acum","positivos_semana","defunciones_acum","defunciones_semana","letalidad"]}
    cols = st.columns(6)
    cols[0].metric("SUIVE acumulado", f"{safe_num(su['acumulado']):,}" if not pd.isna(su['acumulado']) else "—")
    cols[1].metric(f"SUIVE SE{week}", f"{safe_num(su['semana']):,}" if not pd.isna(su['semana']) else "—")
    cols[2].metric("SINAVE acumulado", f"{safe_num(si['acumulado']):,}" if not pd.isna(si['acumulado']) else "—")
    cols[3].metric(f"SINAVE SE{week}", f"{safe_num(si['semana']):,}" if not pd.isna(si['semana']) else "—")
    cols[4].metric("Patógeno identificado", f"{safe_num(si['positivos_acum']):,}" if not pd.isna(si['positivos_acum']) else "—")
    cols[5].metric("Defunciones SINAVE", f"{safe_num(si['defunciones_acum']):,}" if not pd.isna(si['defunciones_acum']) else "—")

    if not suive.empty:
        cur = suive[(suive["Año"] == year) & (suive["SE"] <= week)].copy()
        fig = line_fig(cur, "SE", ["Casos"], f"SUIVE · casos semanales {year}")
        st.pyplot(fig, use_container_width=True)
        download_fig("⬇️ PNG · curva SUIVE", f"SUIVE_curva_{year}_SE{week}.png", fig, "png_res_suive", images)
        plt.close(fig)
    if not sinave.empty:
        p = pathogen_summary(sinave, year, week)
        export_tables["Patogenos"] = p
        if not p.empty:
            fig = bar_fig(p.head(12), "Patógeno", "Casos", f"SINAVE · patógenos acumulados a SE{week}", horizontal=True)
            st.pyplot(fig, use_container_width=True)
            download_fig("⬇️ PNG · patógenos", f"SINAVE_patogenos_{year}_SE{week}.png", fig, "png_res_path", images)
            plt.close(fig)

# -----------------------------------------------------------------------------
# SUIVE
# -----------------------------------------------------------------------------
with TABS[1]:
    st.subheader("Vigilancia convencional · SUIVE/SUAVE")
    if suive.empty:
        st.warning("Carga el histórico SUIVE/SUAVE.")
    else:
        years_su = sorted(suive["Año"].unique())
        export_tables["SUIVE semanal"] = suive
        rows = []
        for yy in years_su:
            sm = suive_summary(suive, int(yy), week)
            rows.append({"Año": int(yy), f"Acumulado ≤SE{week}": sm["acumulado"], f"SE{week}": sm["semana"]})
        hist_table = pd.DataFrame(rows)
        st.dataframe(hist_table, use_container_width=True, hide_index=True)
        export_tables["SUIVE historico"] = hist_table
        fig = bar_fig(hist_table, "Año", f"SE{week}", f"Comparativo histórico SUIVE · SE{week}")
        st.pyplot(fig, use_container_width=True)
        download_fig("⬇️ PNG · comparativo SUIVE", f"SUIVE_comparativo_SE{week}.png", fig, "png_suive_compare", images)
        plt.close(fig)

# -----------------------------------------------------------------------------
# SINAVE
# -----------------------------------------------------------------------------
with TABS[2]:
    st.subheader("Vigilancia nominal y etiológica · SINAVE EDA")
    if sinave.empty:
        st.warning("Carga una o más bases SINAVE EDA.")
    else:
        sm = sinave_summary(sinave, year, week)
        m = st.columns(5)
        m[0].metric("Acumulado", f"{sm['acumulado']:,}")
        m[1].metric(f"SE{week}", f"{sm['semana']:,}")
        m[2].metric("Positivos", f"{sm['positivos_acum']:,}")
        m[3].metric("Defunciones", f"{sm['defunciones_acum']:,}")
        m[4].metric("Letalidad cruda", f"{sm['letalidad']:.2f}%" if not pd.isna(sm['letalidad']) else "—")
        p = pathogen_summary(sinave, year, week)
        st.dataframe(p, use_container_width=True, hide_index=True)
        wk = sinave_weekly(sinave, year)
        export_tables["SINAVE semanal"] = wk
        fig = line_fig(wk[wk["SE"] <= week], "SE", ["Casos"], f"SINAVE · registros por semana · {year}")
        st.pyplot(fig, use_container_width=True)
        download_fig("⬇️ PNG · curva SINAVE", f"SINAVE_curva_{year}_SE{week}.png", fig, "png_sinave_curve", images)
        plt.close(fig)

# -----------------------------------------------------------------------------
# Comparador
# -----------------------------------------------------------------------------
with TABS[3]:
    st.subheader("Concordancia de sistemas · SUIVE ↔ SINAVE")
    st.caption("La razón SINAVE/SUIVE describe la relación entre dos sistemas con propósitos diferentes; no se interpreta automáticamente como subregistro.")
    if suive.empty or sinave.empty:
        st.warning("Este módulo necesita SUIVE y SINAVE.")
    else:
        comp = build_comparison(suive, sinave, year, week)
        export_tables["Comparador"] = comp
        st.dataframe(comp, use_container_width=True, hide_index=True)
        fig = line_fig(comp, "SE", ["SUIVE", "SINAVE"], f"SUIVE vs SINAVE · {year}")
        st.pyplot(fig, use_container_width=True)
        download_fig("⬇️ PNG · SUIVE vs SINAVE", f"SUIVE_vs_SINAVE_{year}_SE{week}.png", fig, "png_compare", images)
        plt.close(fig)
        if comp["SUIVE"].std() > 0 and comp["SINAVE"].std() > 0:
            pearson = comp[["SUIVE", "SINAVE"]].corr(method="pearson").iloc[0,1]
            spearman = comp[["SUIVE", "SINAVE"]].corr(method="spearman").iloc[0,1]
            a,b = st.columns(2)
            a.metric("Correlación Pearson", f"{pearson:.3f}")
            b.metric("Correlación Spearman", f"{spearman:.3f}")

# -----------------------------------------------------------------------------
# Canal endémico
# -----------------------------------------------------------------------------
with TABS[4]:
    st.subheader("Canal endémico dinámico")
    source = st.radio("Fuente", ["SUIVE", "SINAVE"], horizontal=True, key="channel_source")
    if source == "SUIVE":
        if suive.empty:
            st.warning("Carga el histórico SUIVE.")
        else:
            years_hist = [int(y) for y in sorted(suive["Año"].unique()) if int(y) < year]
            default_hist = [y for y in years_hist if y not in (2020, 2021)] or years_hist
            selected = st.multiselect("Años históricos", years_hist, default=default_hist)
            if selected:
                ch = endemic_channel(suive, year, selected, week)
                export_tables["Canal SUIVE"] = ch
                fig = channel_fig(ch, f"Canal endémico SUIVE · {year}")
                st.pyplot(fig, use_container_width=True)
                download_fig("⬇️ PNG · canal SUIVE", f"Canal_SUIVE_{year}_SE{week}.png", fig, "png_channel_suive", images)
                plt.close(fig)
                row = ch[ch["SE"] == week]
                if not row.empty:
                    st.metric(f"Situación SE{week}", row.iloc[0]["Zona"])
    else:
        if sinave.empty:
            st.warning("Carga las bases históricas SINAVE.")
        else:
            path_options = ["Todos los casos"] + sorted(c.replace("path_", "") for c in sinave.columns if c.startswith("path_"))
            pathogen = st.selectbox("Patógeno / indicador", path_options)
            years_hist = [int(y) for y in sorted(pd.to_numeric(sinave["year"], errors="coerce").dropna().astype(int).unique()) if y < year]
            selected = st.multiselect("Años históricos SINAVE", years_hist, default=years_hist, key="hist_sinave")
            municipalities = ["Todos"] + sorted(sinave["municipality"].dropna().astype(str).unique().tolist())
            mun = st.selectbox("Territorio", municipalities)
            if selected:
                ch = sinave_channel(sinave, year, selected, pathogen, week, mun)
                export_tables["Canal SINAVE"] = ch
                fig = channel_fig(ch, f"Canal SINAVE · {pathogen} · {mun}")
                st.pyplot(fig, use_container_width=True)
                slug = re.sub(r"[^A-Za-z0-9]+", "_", pathogen)
                download_fig("⬇️ PNG · canal SINAVE", f"Canal_SINAVE_{slug}_{year}_SE{week}.png", fig, "png_channel_sinave", images)
                plt.close(fig)

# -----------------------------------------------------------------------------
# Territorio
# -----------------------------------------------------------------------------
with TABS[5]:
    st.subheader("Análisis territorial")
    if sinave.empty:
        st.warning("Carga SINAVE para analizar municipio de residencia.")
    else:
        terr = territorial_summary(sinave, year, week, population if not population.empty else None)
        export_tables["Territorio"] = terr
        st.dataframe(terr, use_container_width=True, hide_index=True)
        if not terr.empty:
            metric_options = [c for c in ["Casos", "Positivos", "Defunciones", "Incidencia /100k", "Mortalidad /100k"] if c in terr.columns]
            metric = st.selectbox("Variable del mapa", metric_options)
            try:
                geo = fetch_sonora_geojson()
                # INEGI returns FeatureCollection; match municipal name using properties.nomgeo.
                fig_map = px.choropleth(
                    terr, geojson=geo, locations="Municipio", color=metric,
                    featureidkey="properties.nomgeo", hover_name="Municipio",
                    projection="mercator", title=f"Sonora · {metric} · {year} ≤SE{week}"
                )
                fig_map.update_geos(fitbounds="locations", visible=False)
                fig_map.update_layout(height=650, margin=dict(l=0,r=0,t=45,b=0))
                st.plotly_chart(fig_map, use_container_width=True, config={"displaylogo":False, "toImageButtonOptions":{"format":"png","filename":f"Mapa_POPIS_{metric}_{year}_SE{week}"}})
                st.caption("📸 Usa el ícono de cámara de la gráfica para descargar el mapa como PNG.")
            except Exception as exc:
                st.info(f"No fue posible cargar la geometría INEGI en esta sesión: {exc}")
            fig = bar_fig(terr.head(20), "Municipio", metric, f"Top municipios · {metric}", horizontal=True)
            st.pyplot(fig, use_container_width=True)
            download_fig("⬇️ PNG · ranking territorial", f"Territorio_{metric}_{year}_SE{week}.png", fig, "png_territory", images)
            plt.close(fig)

# -----------------------------------------------------------------------------
# Mortalidad
# -----------------------------------------------------------------------------
with TABS[6]:
    st.subheader("Mortalidad y letalidad")
    if sinave.empty:
        st.warning("Carga SINAVE.")
    else:
        years = sorted(pd.to_numeric(sinave["year"], errors="coerce").dropna().astype(int).unique())
        rows = []
        for yy in years:
            sm = sinave_summary(sinave, int(yy), week)
            rows.append({"Año": int(yy), "Casos": sm["acumulado"], "Defunciones": sm["defunciones_acum"], "Letalidad %": sm["letalidad"]})
        mort = pd.DataFrame(rows)
        export_tables["Mortalidad"] = mort
        st.dataframe(mort, use_container_width=True, hide_index=True)
        fig = bar_fig(mort, "Año", "Defunciones", f"Defunciones acumuladas hasta SE{week}")
        st.pyplot(fig, use_container_width=True)
        download_fig("⬇️ PNG · mortalidad", f"Mortalidad_historica_SE{week}.png", fig, "png_mortality", images)
        plt.close(fig)

# -----------------------------------------------------------------------------
# Indicadores
# -----------------------------------------------------------------------------
with TABS[7]:
    st.subheader("Indicadores normativos EDA")
    st.caption("Calculados mensualmente. Cada resultado conserva numerador, denominador, meta y cumplimiento.")
    if sinave.empty:
        st.warning("Carga SINAVE.")
    else:
        ind = nutrave_indicators(sinave, year, month)
        lab = laboratory_indicators(sinave, year, month)
        export_tables["Indicadores NuTraVE"] = ind
        export_tables["Indicadores Lab"] = lab
        st.markdown("#### 🏥 NuTraVE")
        st.dataframe(ind, use_container_width=True, hide_index=True)
        st.markdown("#### 🔬 Calidad de laboratorio")
        st.dataframe(lab, use_container_width=True, hide_index=True)
        combined = pd.concat([ind.assign(Grupo="NuTraVE"), lab.assign(Grupo="Laboratorio")], ignore_index=True)
        chart = combined.dropna(subset=["Resultado %"]).copy()
        if not chart.empty:
            fig = bar_fig(chart, "Indicador", "Resultado %", f"Indicadores EDA · {year}-{month:02d}", horizontal=True)
            ax = fig.axes[0]
            ax.axvline(80, linestyle="--", linewidth=1.5, label="Referencia 80%")
            ax.legend(frameon=False)
            st.pyplot(fig, use_container_width=True)
            download_fig("⬇️ PNG · indicadores", f"Indicadores_EDA_{year}_{month:02d}.png", fig, "png_indicators", images)
            plt.close(fig)

# -----------------------------------------------------------------------------
# Auditoría
# -----------------------------------------------------------------------------
with TABS[8]:
    st.subheader("Auditor normativo y calidad de datos")
    if sinave.empty:
        st.warning("Carga SINAVE.")
    else:
        audit = audit_operational_definitions(sinave, year, week)
        export_tables["Auditoria EDA"] = audit
        reviewed = audit[audit["Concordante"] == "Revisar"]
        a,b,c = st.columns(3)
        a.metric("Registros evaluados", f"{len(audit):,}")
        b.metric("Revisar clasificación", f"{len(reviewed):,}")
        c.metric("% a revisar", f"{len(reviewed)/len(audit)*100:.1f}%" if len(audit) else "—")
        st.dataframe(reviewed if not reviewed.empty else audit.head(50), use_container_width=True, hide_index=True)
        st.caption("La auditoría recalcula la definición operacional con las variables disponibles; no sustituye la validación epidemiológica profesional.")

# -----------------------------------------------------------------------------
# Exportar
# -----------------------------------------------------------------------------
with TABS[9]:
    st.subheader("Centro de exportación")
    st.caption("Las gráficas generadas durante esta sesión se registran automáticamente aquí.")
    if export_tables:
        excel = make_excel_report(export_tables)
        st.download_button("📊 Descargar reporte Excel", excel, file_name=f"POPIS_4_{year}_SE{week}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("Navega por los módulos para generar tablas exportables.")
    if images:
        st.download_button("🖼️ Descargar TODAS las gráficas (ZIP)", zip_images(images), file_name=f"POPIS_4_graficas_{year}_SE{week}.zip", mime="application/zip")
        st.write(f"Gráficas disponibles: **{len(images)}**")
        for name, payload in images.items():
            st.download_button(f"⬇️ {name}", payload, file_name=name, mime="image/png", key=f"export_{name}")
    else:
        st.info("Las gráficas aparecerán aquí después de visitar los módulos que las generan.")

st.divider()
st.caption("POPIS 4.0 · SUIVE + SINAVE + Canal endémico + Indicadores + Territorio + Exportación · uso epidemiológico")
