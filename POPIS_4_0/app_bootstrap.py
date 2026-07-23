"""Arranque de POPIS 4.0 con correcciones de lógica aplicadas antes de cargar la UI."""
from pathlib import Path

from popis_core_patch import apply_patches

apply_patches()

app_path = Path(__file__).with_name("app.py")
code = compile(app_path.read_text(encoding="utf-8"), str(app_path), "exec")
exec(code, {"__name__": "__main__", "__file__": str(app_path)})
