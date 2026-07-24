"""Arranque POPIS 4.3.5 con parches seguros antes de cargar la interfaz."""
from pathlib import Path

from popis_runtime import activate

activate()

app_path = Path(__file__).with_name("app_v44.py")
code = compile(app_path.read_text(encoding="utf-8"), str(app_path), "exec")
exec(code, {"__name__": "__main__", "__file__": str(app_path)})
