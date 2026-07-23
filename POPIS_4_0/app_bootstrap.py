"""Arranque POPIS 4.1 con parches de vigilancia antes de cargar la interfaz."""
from pathlib import Path

from popis_core_patch import apply_patches

apply_patches()

app_path = Path(__file__).with_name("app_v41.py")
code = compile(app_path.read_text(encoding="utf-8"), str(app_path), "exec")
exec(code, {"__name__": "__main__", "__file__": str(app_path)})
