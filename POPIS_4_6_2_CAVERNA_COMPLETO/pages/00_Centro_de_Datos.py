from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import streamlit as st

from modulos.io_utils import classify_file, discover_assets, ensure_structure, file_sha256, process_inbox
from modulos.runtime import load_runtime, system_status
from modulos.tema_caverna import apply_theme, hero, section

st.set_page_config(page_title="POPIS · Centro de Datos", page_icon="🧠", layout="wide")
apply_theme()
root = ensure_structure()
ctx = load_runtime(process_updates=False)
hero("Centro de Datos", subtitle="Fuentes automáticas, actualización semanal, respaldos y trazabilidad",
     cutoff=ctx.cutoff_label, badges=["Auto-detección", "data/entrada", "Backups"])

section("Estado de fuentes")
st.dataframe(system_status(ctx), use_container_width=True, hide_index=True)

with st.expander("📁 Rutas de trabajo", expanded=False):
    st.code(
        "\n".join([
            f"Proyecto:      {root}",
            f"Históricos:    {root / 'data/historicos'}",
            f"Actual:        {root / 'data/actual'}",
            f"SUIVE:         {root / 'data/suive'}",
            f"Población:     {root / 'data/poblacion'}",
            f"Geografía:     {root / 'data/geografia'}",
            f"Entrada:       {root / 'data/entrada'}",
            f"Respaldos:     {root / 'data/backups'}",
        ])
    )

section("Actualizar desde la interfaz")
st.write("Puedes cargar una nueva fuente. POPIS la coloca primero en `data/entrada`, identifica su tipo y conserva respaldo de la fuente operativa anterior antes de sustituirla.")
upload = st.file_uploader("Nueva fuente", type=["xls", "xlsx", "csv", "txt", "json", "geojson"])
if upload is not None:
    safe_name = re.sub(r"[^A-Za-z0-9._() -]+", "_", Path(upload.name).name)
    target = root / "data/entrada" / safe_name
    target.write_bytes(upload.getvalue())
    kind = classify_file(target)
    st.info(f"Fuente detectada: **{kind}** · {safe_name} · SHA256 `{file_sha256(target)[:16]}…`")
    if st.button("🔄 Integrar fuente en POPIS", type="primary"):
        messages = process_inbox(root)
        for message in messages:
            st.success(message)
        st.rerun()

section("Bandeja vigilada")
inbox = root / "data/entrada"
rows = []
for path in sorted(inbox.iterdir()):
    if path.is_file():
        rows.append({"Archivo": path.name, "Tipo detectado": classify_file(path), "Tamaño KB": round(path.stat().st_size / 1024, 1)})
if rows:
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    if st.button("Procesar todo data/entrada"):
        for message in process_inbox(root):
            st.success(message)
        st.rerun()
else:
    st.success("La bandeja está vacía. Puedes copiar archivos directamente a data/entrada y abrir de nuevo POPIS.")

section("Bases SINAVE identificadas")
assets = discover_assets(root)
if assets.sinave_by_year:
    detail = pd.DataFrame([{"Año": y, "Archivo": p.name, "Ubicación": str(p.parent.relative_to(root))} for y, p in sorted(assets.sinave_by_year.items())])
    st.dataframe(detail, use_container_width=True, hide_index=True)
else:
    st.info("Aún no se detectan bases SINAVE.")

st.caption("El Centro de Datos no elimina archivos históricos. Las sustituciones operativas generan respaldo local en data/backups.")
