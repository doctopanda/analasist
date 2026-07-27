"""POPIS 4.6.1: Cubo SUIVE automático + corrección espacial de domicilios numéricos."""
from pathlib import Path

_original_read_text = Path.read_text


def _patch_v45(text: str) -> str:
    text = text.replace("4.4.0-reports", "4.6.1-spatialfix")
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

    marker = '''                    st.success("SUIVE actualizado y validado"); st.cache_data.clear(); st.rerun()'''
    auto = '''                    st.success("SUIVE actualizado y validado"); st.cache_data.clear(); st.rerun()

        st.divider()
        st.markdown("**⚡ Cubo SUIVE automático**")
        st.caption("Registra una sola vez el libro que Excel actualiza desde el cubo. Después POPIS puede ejecutar Refresh All, guardar y releer SUIVE con un clic.")
        from popis_excel_refresh import get_cube_source, register_cube_path, save_cube_copy, inspect_cube, refresh_and_promote
        _cube=get_cube_source()
        if _cube:
            st.caption(f"📌 Fuente registrada: {_cube}")
        _cube_path=st.text_input("Ruta local del cubo",value=str(_cube) if _cube else "",key="cube_registered_path",help="Recomendado si el libro depende de rutas/conexiones locales. POPIS no mueve el archivo.")
        _c1,_c2=st.columns(2)
        with _c1:
            if st.button("📌 Registrar ruta",use_container_width=True,key="register_cube_path_btn"):
                try:
                    _p=register_cube_path(_cube_path); st.success(f"Cubo registrado: {_p.name}"); st.rerun()
                except Exception as _exc: st.error(str(_exc))
        with _c2:
            if st.button("🔎 Validar cubo",use_container_width=True,key="inspect_cube_btn",disabled=not bool(_cube)):
                try:
                    _i=inspect_cube(); st.success(f"{_i['latest_year']} · SE{_i['last_se']} · acumulado {_i['accumulated']:,.0f}")
                except Exception as _exc: st.error(str(_exc))

        _cube_upload=st.file_uploader("O copiar un Cubo SUIVE a POPIS",type=["xlsx","xlsm"],key="cube_source_upload",help="Úsalo si el libro funciona correctamente aunque se copie a la carpeta local de POPIS.")
        if _cube_upload and st.button("💾 Guardar copia como cubo automático",use_container_width=True,key="save_cube_copy_btn"):
            try:
                _p=save_cube_copy(_cube_upload); st.success(f"Cubo guardado: {_p.name}"); st.rerun()
            except Exception as _exc: st.error(str(_exc))

        _visible=st.checkbox("Mostrar Excel durante la actualización",value=False,key="cube_excel_visible",help="Actívalo si Excel necesita mostrar credenciales, avisos o preguntas de conexión.")
        _timeout=st.slider("Tiempo máximo de actualización",60,900,300,30,key="cube_excel_timeout",format="%d s")
        _last=st.session_state.pop("cube_refresh_result",None)
        if _last:
            st.success(f"✅ SUIVE actualizado: {_last['year']} · SE{_last['last_se']} · acumulado {_last['accumulated']:,.0f}")
            st.caption(f"Última semana: {_last['last_week_cases']:,.0f} casos · Excel: {_last['elapsed']:.1f} s")
        if st.button("🔄 Actualizar SUIVE desde Excel",type="primary",use_container_width=True,key="refresh_cube_excel_btn",disabled=not bool(_cube)):
            try:
                with st.spinner("Excel está actualizando el cubo, recalculando y guardando..."):
                    _r=refresh_and_promote(visible=_visible,timeout=int(_timeout))
                _a=_r['after']; _e=_r['excel']
                st.session_state['cube_refresh_result']={"year":int(_a['latest_year']),"last_se":int(_a['last_se']),"accumulated":float(_a['accumulated']),"last_week_cases":float(_a['last_week_cases']),"elapsed":float(_e.get('elapsed_seconds',0))}
                st.cache_data.clear(); st.rerun()
            except Exception as _exc:
                st.error(f"No se actualizó SUIVE: {_exc}")'''
    if marker in text:
        text = text.replace(marker, auto, 1)
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
