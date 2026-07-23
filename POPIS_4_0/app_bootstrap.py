"""Arranque de POPIS 4.0.1 con correcciones de lógica aplicadas antes de cargar la UI."""
from pathlib import Path

from popis_core_patch import apply_patches

apply_patches()

app_path = Path(__file__).with_name("app.py")
code = compile(app_path.read_text(encoding="utf-8"), str(app_path), "exec")
exec(code, {"__name__": "__main__", "__file__": str(app_path)})

# Marca visible para evitar confundir esta compilación con POPIS 1/2.
import streamlit as st
st.sidebar.divider()
st.sidebar.success("✅ POPIS 4.0.1 · SUIVE + SINAVE")
st.sidebar.caption("Build independiente · puerto 8504–8514")
