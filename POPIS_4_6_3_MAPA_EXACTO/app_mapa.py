from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from modulos.mapa_espacial import read_table, render_mapa_espacial


st.set_page_config(
    page_title="POPIS 4.6.3 · Mapa Exacto",
    page_icon="🗺️",
    layout="wide",
)

st.title("POPIS 4.6.3 · Mapa Exacto")
st.caption("Procesador Operativo de Patógenos e Indicadores Sanitarios · módulo territorial")

st.markdown(
    """
Esta vista sirve para probar el nuevo motor espacial sin reemplazar el POPIS principal.
Carga una o varias bases SINAVE y, opcionalmente, coordenadas institucionales, población y capas GeoJSON.
"""
)

uploads = st.file_uploader(
    "Bases SINAVE EDA",
    type=["xls", "xlsx", "csv", "txt"],
    accept_multiple_files=True,
)

frames: list[pd.DataFrame] = []
errors: list[str] = []

for uploaded in uploads or []:
    try:
        frame = read_table(uploaded.getvalue(), uploaded.name)
        frame["Archivo de origen"] = uploaded.name
        frames.append(frame)
    except Exception as exc:
        errors.append(f"{uploaded.name}: {exc}")

if errors:
    for error in errors:
        st.error(error)

if not frames:
    st.info("Carga al menos una base SINAVE para abrir el mapa.")
    st.stop()

base = pd.concat(frames, ignore_index=True, sort=False)
st.success(f"Base lista: {len(base):,} registros en {len(frames)} archivo(s).")

render_mapa_espacial(base, key_prefix="popis463")
