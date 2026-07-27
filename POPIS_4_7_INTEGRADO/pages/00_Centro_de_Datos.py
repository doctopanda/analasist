from __future__ import annotations

import streamlit as st

from modulos.autocarga import (
    discover_project_assets,
    inbox_dir,
    install_source_file,
    process_inbox,
    save_uploaded_to_inbox,
    status_table,
)


st.title("🧠 POPIS · Centro de Datos")
st.caption("Descubrimiento, actualización y enrutamiento automático de fuentes epidemiológicas.")

assets = discover_project_assets()

# La carpeta data/entrada funciona como bandeja vigilada. Solo se mueven archivos
# reconocidos; los desconocidos permanecen intactos para revisión.
actions = process_inbox(assets.root)
if any(action.status == "instalado" for action in actions):
    assets = discover_project_assets(assets.root)
    st.success("POPIS encontró nuevas fuentes en data/entrada y las integró automáticamente.")
    for action in actions:
        if action.status == "instalado":
            st.caption(f"✓ {action.source.name} → {action.destination}")

st.markdown("### Estado de fuentes")
st.dataframe(status_table(assets), hide_index=True, use_container_width=True)

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Año SINAVE actual", assets.current_year or "—")
with c2:
    st.metric("Corte detectado", f"SE {assets.cutoff_week}" if assets.cutoff_week else "—")
with c3:
    st.metric("Años SINAVE disponibles", len(assets.sinave_by_year))

st.markdown("### 📥 Actualizar POPIS")
st.write(
    "Arrastra una nueva fuente. POPIS examina su estructura y decide si corresponde a SINAVE, "
    "SUIVE/SUAVE, población, cartografía o coordenadas. Antes de reemplazar una fuente operativa "
    "crea una copia de respaldo."
)

upload = st.file_uploader(
    "Nueva fuente",
    type=["xls", "xlsx", "csv", "txt", "geojson", "json"],
    key="popis47_data_upload",
)

if upload is not None:
    staged = save_uploaded_to_inbox(upload.getvalue(), upload.name, assets.root)
    st.info(f"Archivo recibido en la bandeja: {staged.name}")
    if st.button("⚙️ Clasificar e integrar", type="primary", use_container_width=True):
        action = install_source_file(staged, assets.root, move=True)
        if action.status == "instalado":
            st.success(f"{action.kind}: fuente integrada como {action.destination.name}")
            st.rerun()
        elif action.status == "sin_cambios":
            st.info(action.message)
        else:
            st.warning(action.message)

with st.expander("📂 Bandeja automática", expanded=False):
    folder = inbox_dir(assets.root)
    st.write("También puedes copiar archivos directamente a esta carpeta:")
    st.code(str(folder), language=None)
    st.caption(
        "Al abrir el Centro de Datos o el mapa, POPIS revisa la bandeja. Los archivos reconocidos "
        "se enrutan automáticamente; los desconocidos no se eliminan."
    )

with st.expander("🔎 Inventario detectado", expanded=False):
    if assets.sinave_by_year:
        for year, path in sorted(assets.sinave_by_year.items()):
            st.write(f"**SINAVE {year}:** `{path}`")
    if assets.suive_file:
        st.write(f"**SUIVE/SUAVE:** `{assets.suive_file}`")
    if assets.population_file:
        st.write(f"**Población:** `{assets.population_file}`")
    if assets.municipal_geojson:
        st.write(f"**Mapa municipal:** `{assets.municipal_geojson}`")
    if assets.district_geojson:
        st.write(f"**Mapa distrital:** `{assets.district_geojson}`")
    if assets.coordinates_file:
        st.write(f"**Coordenadas:** `{assets.coordinates_file}`")

if assets.warnings:
    with st.expander("⚠️ Observaciones", expanded=False):
        for warning in assets.warnings:
            st.write(f"• {warning}")

if st.button("🔄 Reescanear proyecto", use_container_width=True):
    st.rerun()
