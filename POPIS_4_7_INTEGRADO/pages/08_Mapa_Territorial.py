from __future__ import annotations

import streamlit as st

from modulos.autocarga import discover_project_assets
from modulos.mapa_integrado import render_integrated_map
from modulos.tema_caverna import aplicar_tema_caverna, cabecera_popis, nota_metodologica


aplicar_tema_caverna()
assets = discover_project_assets()
corte = (
    f"SE {assets.cutoff_week} · {assets.current_year}"
    if assets.current_year and assets.cutoff_week
    else "Corte automático"
)
cabecera_popis(corte=corte, etiqueta="GEOGRAFÍA · INCIDENCIA · CONCENTRACIÓN")

# render_integrated_map conserva su lógica epidemiológica. Se oculta únicamente
# su H1 interno porque la cabecera CAVERNA ya cumple la función de título principal.
st.markdown("<style>h1 {display:none !important;}</style>", unsafe_allow_html=True)
render_integrated_map(assets, key_prefix="popis48_map")

nota_metodologica(
    "La ubicación territorial utiliza la mejor georreferencia disponible. Los centroides municipales "
    "son aproximaciones analíticas y no representan domicilios individuales."
)
