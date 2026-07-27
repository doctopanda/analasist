"""Arranque POPIS 4.6.2 con verificación estricta de interfaz."""
from pathlib import Path
from popis_runtime import activate

activate()
EXPECTED_BUILD = "4.6.2-spatialapi"
app_path = Path(__file__).with_name("app_v46.py")
if not app_path.exists():
    raise RuntimeError(f"No encuentro la interfaz requerida: {app_path.name}")
source = app_path.read_text(encoding="utf-8")
if EXPECTED_BUILD not in source:
    raise RuntimeError(
        f"La interfaz instalada no corresponde a {EXPECTED_BUILD}. "
        "Reemplaza los archivos del programa con el paquete completo más reciente."
    )
code = compile(source, str(app_path), "exec")
exec(code, {"__name__": "__main__", "__file__": str(app_path)})
