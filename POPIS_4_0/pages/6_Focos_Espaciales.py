from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from popis_runtime import activate
activate()

from popis_core_patch import DISTRICTS, canonical_municipality
from popis_data import load_preloaded_sources
from popis_spatial import (
    address_table, coverage, detect_clusters, grid_concentration,
    pending_geocoding_export, save_exact_geocodes, spatial_subset,
)

st.set_page_config(page_title="POPIS 4.3 · Focos espaciales", page_icon="🔥", layout="wide")
st.title("🔥 Focos espaciales y detección de conglomerados")
st.caption("Dirección/localidad → municipio → Distrito de Salud. Los domicilios nominales permanecen en la computadora local.")

bundle = load_preloaded_sources()
sinave = bundle.sinave
if sinave.empty:
    st.error("No hay una base SINAVE disponible.")
    st.stop()

# ------------------------- geocodificación exacta -------------------------
with st.expander("📍 Precisión de las coordenadas", expanded=False):
    st.markdown("""
**POPIS no envía automáticamente domicilios a geocodificadores públicos.**

Para puntos exactos puede importar un archivo generado por un SIG/geocodificador institucional con
`Folio, Latitud, Longitud`. POPIS guarda localmente solo folio/hash y coordenadas, no el domicilio en texto plano.
Cuando no existe punto exacto, usa centroides de localidad/cabecera de INEGI únicamente como contexto.
    """)
    geo_upload = st.file_uploader("Importar coordenadas geocodificadas", type=["csv","xlsx","xls"], key="spatial_geocodes")
    if geo_upload and st.button("Guardar coordenadas exactas", use_container_width=True):
        try:
            save_exact_geocodes(geo_upload); st.success("Coordenadas guardadas localmente."); st.cache_data.clear(); st.rerun()
        except Exception as exc:
            st.error(str(exc))

    st.download_button(
        "⬇️ Exportar domicilios pendientes para SIG institucional",
        pending_geocoding_export(sinave),
        file_name="POPIS_domicilios_pendientes_geocodificacion.csv",
        mime="text/csv",
        help="Este archivo contiene domicilios sensibles. Úsalo solo dentro del entorno institucional autorizado.",
    )

# ------------------------- filtros -------------------------
ycol = "epi_year" if "epi_year" in sinave.columns else "year"
years = sorted(pd.to_numeric(sinave[ycol], errors="coerce").dropna().astype(int).unique().tolist())
def_year = years[-1] if years else 2026

f1,f2,f3,f4 = st.columns([1,1,1.4,1.5])
with f1:
    year = int(st.selectbox("Año epidemiológico", years or [2026], index=len(years)-1 if years else 0))
week_values = pd.to_numeric(sinave.loc[pd.to_numeric(sinave[ycol],errors="coerce").eq(year),"epi_week"],errors="coerce").dropna()
max_week = int(week_values[week_values.between(1,53)].max()) if len(week_values) else 26
with f2:
    period = st.slider("Semanas", 1, 53, (max(1,max_week-3), max_week))
with f3:
    districts = ["Todos"] + list(DISTRICTS.keys())
    district = st.selectbox("Distrito de Salud", districts)
with f4:
    pathogens = ["Todos los casos"] + sorted(c.replace("path_","") for c in sinave.columns if c.startswith("path_"))
    pathogen = st.selectbox("Evento / patógeno", pathogens)

all_municipalities = sorted({canonical_municipality(x) for x in sinave.get("municipality",pd.Series(dtype=str)).dropna().astype(str) if canonical_municipality(x)})
if district == "Todos":
    mun_options = ["Todos"] + all_municipalities
else:
    allowed = {canonical_municipality(x) for x in DISTRICTS[district]}
    mun_options = ["Todos"] + sorted(m for m in all_municipalities if m in allowed)
municipality = st.selectbox("Municipio", mun_options)

with st.spinner("Preparando geografía y centroides INEGI…"):
    points = spatial_subset(sinave, year, int(period[0]), int(period[1]), district, municipality, pathogen)

if points.empty:
    st.warning("No hay casos con coordenadas disponibles para los filtros seleccionados.")
    st.stop()

cov = coverage(points)
exact_n = int(points["Precisión"].str.startswith("Exacta",na=False).sum())
approx_n = int(len(points)-exact_n)
m1,m2,m3,m4 = st.columns(4)
m1.metric("Casos con coordenada", f"{len(points):,}")
m2.metric("Coordenada exacta", f"{exact_n:,}")
m3.metric("Contexto INEGI", f"{approx_n:,}")
m4.metric("Cobertura exacta", f"{(exact_n/len(points)*100):.1f}%" if len(points) else "—")

with st.expander("🔎 Calidad de geolocalización", expanded=False):
    st.dataframe(cov, hide_index=True, use_container_width=True)
    st.info("Los centroides de localidad/cabecera sirven para panorama territorial, pero NO deben interpretarse como concentraciones domiciliarias exactas.")

# ------------------------- mapa de calor -------------------------
st.subheader("🌡️ Concentración geográfica")
map_precision = st.radio(
    "Puntos usados en el mapa de calor",
    ["Exactos solamente", "Exactos + centroides INEGI"],
    horizontal=True,
    index=0 if exact_n else 1,
)
map_points = points[points["Precisión"].str.startswith("Exacta",na=False)].copy() if map_precision.startswith("Exactos solamente") else points.copy()

if map_points.empty:
    st.info("Todavía no hay coordenadas exactas. Importa un archivo geocodificado o usa temporalmente el contexto INEGI.")
else:
    center={"lat":float(map_points["Latitud"].mean()),"lon":float(map_points["Longitud"].mean())}
    density = px.density_mapbox(
        map_points, lat="Latitud", lon="Longitud", radius=24,
        center=center, zoom=5 if district=="Todos" and municipality=="Todos" else 9 if municipality=="Todos" else 12,
        mapbox_style="open-street-map",
        title=f"Concentración de casos · {pathogen} · SE{period[0]}–SE{period[1]}",
    )
    density.update_layout(height=690,margin=dict(l=0,r=0,t=45,b=0))
    st.plotly_chart(density,use_container_width=True,config={"displaylogo":False,"toImageButtonOptions":{"format":"png","filename":f"POPIS_mapa_concentracion_{year}_SE{period[0]}_{period[1]}"}})
    st.caption("Mapa base © OpenStreetMap contributors. La capa de densidad se calcula localmente con las coordenadas disponibles.")

# ------------------------- detector de clusters -------------------------
st.subheader("🚨 Detector de conglomerados espacio-temporales")
c1,c2,c3,c4 = st.columns(4)
with c1: radius = st.slider("Radio máximo",0.25,5.0,1.0,0.25,format="%.2f km")
with c2: min_cases = st.slider("Mínimo de casos",2,20,3)
with c3: max_days = st.slider("Ventana temporal",1,30,7,help="Máxima separación temporal entre casos conectados")
with c4: exact_only = st.toggle("Solo coordenadas exactas",value=True)

cluster_points, clusters = detect_clusters(points,radius,min_cases,max_days,exact_only)
if exact_only and exact_n < min_cases:
    st.info("Hay pocas coordenadas exactas para aplicar este detector. El sistema evita usar centroides como si fueran domicilios.")
elif clusters.empty:
    st.success("No se detectaron conglomerados que cumplan los parámetros seleccionados.")
else:
    alert = int((clusters["Señal"].isin(["Alerta","Alta"])).sum())
    a,b,c = st.columns(3); a.metric("Conglomerados",len(clusters)); b.metric("Señales Alerta/Alta",alert); c.metric("Casos en conglomerados",int(clusters["Casos"].sum()))
    st.dataframe(clusters,hide_index=True,use_container_width=True)
    st.download_button("⬇️ Descargar conglomerados CSV",clusters.to_csv(index=False).encode("utf-8-sig"),file_name=f"POPIS_conglomerados_{year}_SE{period[0]}_{period[1]}.csv",mime="text/csv")

    cm = px.scatter_mapbox(
        clusters,lat="Latitud centro",lon="Longitud centro",size="Casos",color="Señal",
        hover_name="Cluster",hover_data=["Casos","Inicio","Fin","Distrito","Municipio"],
        center={"lat":float(clusters["Latitud centro"].mean()),"lon":float(clusters["Longitud centro"].mean())},
        zoom=6 if district=="Todos" else 9,mapbox_style="open-street-map",title="Conglomerados detectados"
    )
    cm.update_layout(height=620,margin=dict(l=0,r=0,t=45,b=0))
    st.plotly_chart(cm,use_container_width=True,config={"displaylogo":False,"toImageButtonOptions":{"format":"png","filename":f"POPIS_clusters_{year}"}})
    st.warning("Una señal espacial es un disparador de investigación epidemiológica; no confirma por sí sola un brote.")

# ------------------------- rejilla -------------------------
st.subheader("🧱 Concentración por celdas")
cell = st.select_slider("Resolución espacial",options=[0.25,0.5,1.0,2.0,5.0],value=0.5,format_func=lambda x:f"{x:g} km")
grid_source = points[points["Precisión"].str.startswith("Exacta",na=False)] if exact_n else points
grid = grid_concentration(grid_source,float(cell))
if not grid.empty:
    st.dataframe(grid.head(30),hide_index=True,use_container_width=True)
    st.download_button("⬇️ Descargar concentración por celdas",grid.to_csv(index=False).encode("utf-8-sig"),file_name=f"POPIS_celdas_{cell}km_{year}.csv",mime="text/csv")

st.divider()
st.caption("POPIS 4.3 · análisis espacial local. Los mapas compartidos deben evitar mostrar domicilios o identificadores personales.")
