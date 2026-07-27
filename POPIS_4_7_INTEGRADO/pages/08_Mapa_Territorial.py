from __future__ import annotations

import streamlit as st

from modulos.autocarga import discover_project_assets
from modulos.mapa_integrado import render_integrated_map


assets = discover_project_assets()
render_integrated_map(assets, key_prefix="popis47_map")
