"""POPIS 4.4.0: actualización SUIVE segura + tasas visibles + reportes Excel/Word.

Este wrapper mantiene compatibilidad con la interfaz 4.3.x, pero intercepta la
lectura de los wrappers previos para aplicar las mejoras finales sin duplicar el
motor epidemiológico.
"""
from pathlib import Path

_original_read_text = Path.read_text


def _patch_v42(text: str) -> str:
    text = text.replace(
        "from popis_data import add_historical, load_preloaded_sources, save_current, save_population",
        "from popis_data import add_historical, inspect_suive_upload, load_preloaded_sources, save_current, save_population",
    )
    text = text.replace(
        "from popis_population import demographic_profile, pyramid, age_sex_rates, population_for_year",
        "from popis_population import demographic_profile, pyramid, age_sex_rates, population_for_year\nfrom popis_reports import make_excel_report_with_images, make_word_report",
    )

    old_weekly = '''        new_suive=st.file_uploader("Nuevo SUIVE actual",type=["xls","xlsx"],key="weekly_suive")
        if new_suive and st.button("Guardar como SUIVE actual",use_container_width=True):
            save_current(new_suive,"SUIVE"); st.success("SUIVE actualizado"); st.cache_data.clear(); st.rerun()'''
    new_weekly = '''        new_suive=st.file_uploader("Nuevo SUIVE actual",type=["xls","xlsx"],key="weekly_suive")
        if new_suive:
            try:
                su_preview=inspect_suive_upload(new_suive)
                st.caption(f"Vista previa SUIVE: {su_preview['latest_year']} · última SE con casos {su_preview['last_se']} · acumulado {su_preview['accumulated']:,.0f} · última semana {su_preview['last_week_cases']:,.0f}")
                suive_preview_ok=su_preview['positive_weeks']>0 and su_preview['accumulated']>0
                if not suive_preview_ok:
                    st.error("El archivo fue interpretado con cero casos. POPIS no reemplazará el corte vigente.")
            except Exception as exc:
                suive_preview_ok=False
                st.error(f"No pude validar el SUIVE antes de guardarlo: {exc}")
            if st.button("Guardar como SUIVE actual",use_container_width=True,disabled=not suive_preview_ok):
                try:
                    save_current(new_suive,"SUIVE")
                except Exception as exc:
                    st.error(f"SUIVE NO fue reemplazado: {exc}")
                else:
                    st.success("SUIVE actualizado y validado"); st.cache_data.clear(); st.rerun()'''
    if old_weekly in text:
        text = text.replace(old_weekly, new_weekly)

    old_export = '''with TABS[10]:
    st.subheader("Centro de exportación")
    if not bundle.inventory.empty: export_tables["Fuentes"] = bundle.inventory
    if export_tables:
        excel=make_excel_report(export_tables); st.download_button("📊 Descargar reporte Excel",excel,file_name=f"POPIS_{BUILD}_{year}_SE{week}.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if images:
        st.download_button("🖼️ Descargar TODAS las gráficas (ZIP)",zip_images(images),file_name=f"POPIS_graficas_{year}_SE{week}.zip",mime="application/zip")
        for name,payload in images.items(): st.download_button(f"⬇️ {name}",payload,file_name=name,mime="image/png",key=f"all_{name}")'''
    new_export = '''with TABS[10]:
    st.subheader("Centro de exportación y reportes")
    if not bundle.inventory.empty: export_tables["Fuentes"] = bundle.inventory
    su_rep=suive_summary(suive,year,week) if not suive.empty else {"acumulado":np.nan,"semana":np.nan}
    si_rep=sinave_summary(sinave,year,week) if not sinave.empty else {"acumulado":np.nan,"positivos_acum":np.nan,"defunciones_acum":np.nan}
    state_prof=demographic_profile(population,year,"Todos") if not population.empty else {}
    state_pop=float(state_prof.get("Población",np.nan)) if state_prof else np.nan
    report_base=rate_base if "rate_base" in globals() else 100000
    state_inc=(float(si_rep.get("acumulado",np.nan))/state_pop*report_base) if pd.notna(state_pop) and state_pop>0 and pd.notna(si_rep.get("acumulado",np.nan)) else np.nan
    source_text="; ".join((bundle.inventory["Sistema"].astype(str)+": "+bundle.inventory["Archivo"].astype(str)).tolist()) if not bundle.inventory.empty else "Fuentes locales POPIS"
    report_context={"Año":year,"Semana":week,"SUIVE acumulado":su_rep.get("acumulado"),"SUIVE semana":su_rep.get("semana"),"SINAVE acumulado":si_rep.get("acumulado"),"SINAVE positivos":si_rep.get("positivos_acum"),"Defunciones registradas":si_rep.get("defunciones_acum"),"Población estatal":state_pop,"Incidencia estatal SINAVE":state_inc,"Base tasa":report_base,"Fuentes":source_text}
    export_tables["Resumen ejecutivo"]=pd.DataFrame([report_context])
    if export_tables:
        try:
            excel=make_excel_report_with_images(export_tables,images,report_context)
            st.download_button("📊 Reporte Excel completo · tablas + gráficas",excel,file_name=f"POPIS_Reporte_{year}_SE{week}.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except Exception as exc: st.error(f"No pude generar el Excel: {exc}")
        try:
            word=make_word_report(report_context,export_tables,images)
            st.download_button("📄 Reporte Word interpretado · tablas + gráficas",word,file_name=f"POPIS_Informe_Ejecutivo_{year}_SE{week}.docx",mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        except Exception as exc: st.error(f"No pude generar el Word: {exc}")
    if images:
        st.download_button("🖼️ Descargar TODAS las gráficas (ZIP)",zip_images(images),file_name=f"POPIS_graficas_{year}_SE{week}.zip",mime="application/zip")
        for name,payload in images.items(): st.download_button(f"⬇️ {name}",payload,file_name=name,mime="image/png",key=f"all_{name}")'''
    if old_export in text:
        text = text.replace(old_export, new_export)
    return text


def _patch_v44(text: str) -> str:
    text = text.replace("4.3.6-territory", "4.4.0-reports")
    old_display = '''        display_table=table.drop(columns=["Incidencia /100k","Mortalidad /100k"],errors="ignore")
        st.dataframe(display_table,hide_index=True,use_container_width=True)'''
    new_display = '''        display_table=table.drop(columns=["Incidencia /100k","Mortalidad /100k"],errors="ignore")
        lead=[level]
        if level=="Municipio": lead += [c for c in ["Población","Distrito","Región","Casos","Positivos","Defunciones"] if c in display_table.columns]
        else: lead += [c for c in ["Población","Casos","Positivos","Defunciones"] if c in display_table.columns]
        priority=[c for c in [inc_col,state_den_col,ratio_col,mort_col,"Positividad %","Letalidad %"] if c in display_table.columns]
        remaining=[c for c in display_table.columns if c not in lead+priority]
        display_table=display_table[[c for c in lead+priority+remaining if c in display_table.columns]]
        st.dataframe(display_table,hide_index=True,use_container_width=True)'''
    if old_display in text:
        text = text.replace(old_display, new_display)
    return text


def _patched_read_text(self: Path, *args, **kwargs):
    text = _original_read_text(self, *args, **kwargs)
    if self.name == "app_v42.py":
        return _patch_v42(text)
    if self.name == "app_v44.py":
        return _patch_v44(text)
    return text


Path.read_text = _patched_read_text
try:
    app = Path(__file__).with_name("app_v44.py")
    code = compile(app.read_text(encoding="utf-8"), str(app), "exec")
    exec(code, {"__name__": "__main__", "__file__": str(app)})
finally:
    Path.read_text = _original_read_text
