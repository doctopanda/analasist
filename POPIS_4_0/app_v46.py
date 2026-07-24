"""POPIS 4.5.0: integración del Cubo SUIVE con lector multiformato."""
from pathlib import Path

_original_read_text = Path.read_text


def _patch_v45(text: str) -> str:
    text = text.replace("4.4.0-reports", "4.5.0-cubo")
    text = text.replace(
        'new_suive=st.file_uploader("Nuevo SUIVE actual",type=["xls","xlsx"],key="weekly_suive")',
        'new_suive=st.file_uploader("Cubo / SUIVE actual",type=["xls","xlsx","xlsm"],key="weekly_suive")'
    )
    old = '''                st.caption(f"Vista previa SUIVE: {su_preview['latest_year']} · última SE con casos {su_preview['last_se']} · acumulado {su_preview['accumulated']:,.0f} · última semana {su_preview['last_week_cases']:,.0f}")'''
    new = '''                _f=su_preview.get("frame")
                _attrs=getattr(_f,"attrs",{}) if _f is not None else {}
                _stype=_attrs.get("popis_source_type","SUIVE compatible")
                _sheet=_attrs.get("popis_sheet","")
                _layout=_attrs.get("popis_layout","")
                st.success(f"Fuente reconocida: {_stype}")
                if _sheet or _layout: st.caption(f"Lectura: hoja {_sheet or 'auto'} · {_layout or 'estructura compatible'}")
                st.caption(f"Vista previa SUIVE: {su_preview['latest_year']} · última SE con casos {su_preview['last_se']} · acumulado {su_preview['accumulated']:,.0f} · última semana {su_preview['last_week_cases']:,.0f}")'''
    if old in text:
        text = text.replace(old, new)
    return text


def _patched_read_text(self: Path, *args, **kwargs):
    text = _original_read_text(self, *args, **kwargs)
    if self.name == "app_v45.py":
        return _patch_v45(text)
    return text


Path.read_text = _patched_read_text
try:
    app = Path(__file__).with_name("app_v45.py")
    code = compile(app.read_text(encoding="utf-8"), str(app), "exec")
    exec(code, {"__name__": "__main__", "__file__": str(app)})
finally:
    Path.read_text = _original_read_text
