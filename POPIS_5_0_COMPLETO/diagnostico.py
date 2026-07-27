from __future__ import annotations

import os
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

print("=" * 68)
print(" POPIS 5.0 · DIAGNÓSTICO")
print("=" * 68)
print("Python:", sys.version.replace("\n", " "))
print("Ejecutable:", sys.executable)
print("Sistema:", platform.platform())
print("Carpeta POPIS:", ROOT)
print("LOCALAPPDATA:", os.environ.get("LOCALAPPDATA", ""))

try:
    import pandas, numpy, streamlit, folium, openpyxl, matplotlib
    print("Dependencias principales: OK")
    print("streamlit:", streamlit.__version__)
    print("pandas:", pandas.__version__)
except Exception as exc:
    print("Dependencias: ERROR", exc)

try:
    from modulos.autocarga import discover_project_assets, status_table
    assets = discover_project_assets(ROOT)
    print("\nFuentes detectadas:")
    print(status_table(assets).to_string(index=False))
    if assets.warnings:
        print("\nAvisos:")
        for w in assets.warnings:
            print("-", w)
except Exception as exc:
    print("Motor de autocarga: ERROR", exc)

try:
    from modulos.centroides import CENTROIDES_SONORA
    print("\nCentroides internos:", len(CENTROIDES_SONORA))
except Exception as exc:
    print("Centroides: ERROR", exc)

print("\nDiagnóstico terminado.")
