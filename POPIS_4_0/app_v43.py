"""POPIS 4.3.3: interfaz 4.2 + focos espaciales + tasas con ámbito y fuente explícitos."""
from pathlib import Path

app = Path(__file__).with_name("app_v42.py")
text = app.read_text(encoding="utf-8")
text = text.replace('BUILD = "4.2.0-pop"', 'BUILD = "4.3.3-incidence"')
text = text.replace(
    'SUIVE + SINAVE + demografía + indicadores + territorio · Sonora',
    'SUIVE + SINAVE + demografía + territorio + focos espaciales · Sonora',
)

# Corrección defensiva del selector de año.
old_selector = '''c1,c2,c3=st.columns([1.3,1,1])
with c1: year=st.selectbox("Año epidemiológico",available_years or [2026],index=(available_years.index(current_year) if current_year in available_years else len(available_years)-1))
with c2: week=st.number_input("Semana de corte",1,53,max_week_for(int(year)),1)
with c3: month=st.number_input("Mes para indicadores",1,12,latest_month(int(year)),1)
year,week,month=int(year),int(week),int(month)'''
new_selector = '''c1,c2,c3=st.columns([1.3,1,1])
year_options = available_years if available_years else [2026]
if current_year in year_options:
    year_index = year_options.index(current_year)
else:
    year_index = max(0, len(year_options)-1)
with c1: year=st.selectbox("Año epidemiológico", year_options, index=year_index)
with c2: week=st.number_input("Semana de corte",1,53,max_week_for(int(year)),1)
with c3: month=st.number_input("Mes para indicadores",1,12,latest_month(int(year)),1)
year,week,month=int(year),int(week),int(month)
if not available_years:
    st.warning("POPIS abrió en modo seguro porque todavía no detectó años válidos en SUIVE, SINAVE o población. Revisa 'Fuentes precargadas' en la barra lateral para ver qué archivo no fue reconocido.")'''
if old_selector not in text:
    raise RuntimeError("No encontré el bloque esperado del selector de año en app_v42.py")
text = text.replace(old_selector, new_selector)

# Territorio: mostrar claramente tasa municipal/distrital/regional y, además,
# tasas estatales SINAVE y SUIVE con el mismo denominador demográfico.
old_territory = '''with TABS[5]:
    st.subheader("Territorio · residencia habitual")
    if sinave.empty: st.warning("SINAVE no disponible.")
    else:
        terr=territorial_summary(sinave,year,week,population if not population.empty else None); export_tables["Territorio municipal"]=terr; level=st.radio("Nivel",["Municipio","Distrito","Región"],horizontal=True); table=terr if level=="Municipio" else aggregate_territory(terr,level); st.dataframe(table,hide_index=True,use_container_width=True)
        metrics=[c for c in ["Casos","Positivos","Defunciones","Incidencia /100k","Mortalidad /100k"] if c in table]
        if metrics:
            metric=st.selectbox("Indicador territorial",metrics); fig=bar_fig(table.head(25),level,metric,f"{level} · {metric}",True); st.pyplot(fig,use_container_width=True); register_fig("⬇️ PNG",f"Territorio_{level}_{metric}_{year}.png",fig,"terr",images); plt.close(fig)
            if level=="Municipio":
                try:
                    geo=fetch_sonora_geojson(); fmap=px.choropleth(terr,geojson=geo,locations="Municipio",color=metric,featureidkey="properties.nomgeo",hover_name="Municipio",projection="mercator",title=f"Sonora · {metric}"); fmap.update_geos(fitbounds="locations",visible=False); fmap.update_layout(height=650,margin=dict(l=0,r=0,t=45,b=0)); st.plotly_chart(fmap,use_container_width=True,config={"displaylogo":False,"toImageButtonOptions":{"format":"png","filename":f"Mapa_{metric}_{year}"}})
                except Exception as exc: st.info(f"Mapa INEGI no disponible: {exc}")
        if population.empty: st.info("Población municipal no cargada: se muestran conteos, no tasas.")'''

new_territory = '''with TABS[5]:
    st.subheader("Territorio · residencia habitual")
    if sinave.empty:
        st.warning("SINAVE no disponible.")
    else:
        terr=territorial_summary(sinave,year,week,population if not population.empty else None)
        export_tables["Territorio municipal"]=terr

        # Incidencia estatal SINAVE: solo residentes de Sonora, para mantener
        # coherencia entre numerador y denominador.
        sycol="epi_year" if "epi_year" in sinave.columns else "year"
        state_cases=sinave[
            pd.to_numeric(sinave[sycol],errors="coerce").eq(year)
            & pd.to_numeric(sinave["epi_week"],errors="coerce").between(1,week)
        ].copy()
        if "sonora_resident" in state_cases.columns:
            state_cases=state_cases[state_cases["sonora_resident"].fillna(False)]
        state_sinave_cases=int(len(state_cases))

        state_profile=demographic_profile(population,year,"Todos") if not population.empty else {}
        state_population=float(state_profile.get("Población",np.nan)) if state_profile else np.nan
        state_sinave_inc=(state_sinave_cases/state_population*100000) if pd.notna(state_population) and state_population>0 else np.nan
        su_state=suive_summary(suive,year,week) if not suive.empty else {"acumulado":np.nan}
        state_suive_cases=su_state.get("acumulado",np.nan)
        state_suive_inc=(float(state_suive_cases)/state_population*100000) if pd.notna(state_suive_cases) and pd.notna(state_population) and state_population>0 else np.nan

        st.markdown("#### Sonora · tasas estatales acumuladas")
        sc=st.columns(4)
        sc[0].metric("Población estatal", "—" if pd.isna(state_population) else f"{int(round(state_population)):,}")
        sc[1].metric("Casos SINAVE residentes Sonora", f"{state_sinave_cases:,}")
        sc[2].metric("Incidencia estatal SINAVE /100 mil", "—" if pd.isna(state_sinave_inc) else f"{state_sinave_inc:,.2f}")
        sc[3].metric("Incidencia estatal SUIVE /100 mil", "—" if pd.isna(state_suive_inc) else f"{state_suive_inc:,.2f}")
        st.caption(f"Corte acumulado SE1–SE{week}. SINAVE y SUIVE son sistemas distintos y sus tasas no deben interpretarse como equivalentes ni sumarse entre sí.")

        state_rates_table=pd.DataFrame([
            {"Ámbito":"Estatal","Sistema":"SINAVE","Año":year,"Corte SE":week,"Casos":state_sinave_cases,"Población":state_population,"Incidencia /100k":state_sinave_inc},
            {"Ámbito":"Estatal","Sistema":"SUIVE","Año":year,"Corte SE":week,"Casos":state_suive_cases,"Población":state_population,"Incidencia /100k":state_suive_inc},
        ])
        export_tables["Incidencia estatal"]=state_rates_table

        st.markdown("#### Tasas territoriales SINAVE")
        level=st.radio("Nivel",["Municipio","Distrito","Región"],horizontal=True)
        table=terr if level=="Municipio" else aggregate_territory(terr,level)
        scope_word={"Municipio":"municipal","Distrito":"distrital","Región":"regional"}[level]
        display_table=table.rename(columns={
            "Incidencia /100k":f"Incidencia {scope_word} /100k",
            "Mortalidad /100k":f"Mortalidad {scope_word} /100k",
        })
        st.dataframe(display_table,hide_index=True,use_container_width=True)
        metrics=[c for c in ["Casos","Positivos","Defunciones","Incidencia /100k","Mortalidad /100k"] if c in table]
        if metrics:
            metric=st.selectbox("Indicador territorial",metrics)
            metric_label={"Incidencia /100k":f"Incidencia {scope_word} /100k","Mortalidad /100k":f"Mortalidad {scope_word} /100k"}.get(metric,metric)
            fig=bar_fig(table.head(25),level,metric,f"{level} · {metric_label}",True)
            st.pyplot(fig,use_container_width=True)
            register_fig("⬇️ PNG",f"Territorio_{level}_{metric}_{year}.png",fig,"terr",images)
            plt.close(fig)
            if level=="Municipio":
                try:
                    geo=fetch_sonora_geojson()
                    fmap=px.choropleth(terr,geojson=geo,locations="Municipio",color=metric,featureidkey="properties.nomgeo",hover_name="Municipio",projection="mercator",title=f"Sonora · {metric_label}")
                    fmap.update_geos(fitbounds="locations",visible=False)
                    fmap.update_layout(height=650,margin=dict(l=0,r=0,t=45,b=0))
                    st.plotly_chart(fmap,use_container_width=True,config={"displaylogo":False,"toImageButtonOptions":{"format":"png","filename":f"Mapa_{metric}_{year}"}})
                except Exception as exc:
                    st.info(f"Mapa INEGI no disponible: {exc}")

        with st.expander("📚 Fórmulas y procedencia de los datos",expanded=False):
            sin_files=bundle.inventory.loc[bundle.inventory["Sistema"].eq("SINAVE"),"Archivo"].astype(str).tolist() if not bundle.inventory.empty else []
            sui_files=bundle.inventory.loc[bundle.inventory["Sistema"].eq("SUIVE"),"Archivo"].astype(str).tolist() if not bundle.inventory.empty else []
            pop_files=bundle.inventory.loc[bundle.inventory["Sistema"].eq("POBLACIÓN"),"Archivo"].astype(str).tolist() if not bundle.inventory.empty else []
            st.markdown(f"**Incidencia municipal SINAVE** = casos SINAVE residentes del municipio acumulados hasta SE{week} / población proyectada de ese municipio × 100,000.")
            st.markdown(f"**Incidencia estatal SINAVE** = todos los casos SINAVE residentes de Sonora acumulados hasta SE{week} / población estatal proyectada × 100,000.")
            st.markdown(f"**Incidencia estatal SUIVE** = casos SUIVE estatales acumulados hasta SE{week} / la misma población estatal proyectada × 100,000.")
            st.markdown("**Numeradores SINAVE:** " + (", ".join(sin_files) if sin_files else "fuente SINAVE local no identificada"))
            st.markdown("**Numerador SUIVE:** " + (", ".join(sui_files) if sui_files else "fuente SUIVE local no identificada"))
            st.markdown("**Denominadores de población:** " + (", ".join(pop_files) if pop_files else "archivo demográfico local no identificado"))
            st.info("Las tasas se calculan con población proyectada del mismo año. La población estatal se obtiene sumando los denominadores municipales/edad/sexo sin duplicar totales.")

        if population.empty:
            st.info("Población municipal no cargada: se muestran conteos, no tasas.")'''

if old_territory not in text:
    raise RuntimeError("No encontré el bloque de Territorio esperado en app_v42.py")
text = text.replace(old_territory,new_territory)

# Edad/sexo: mostrar simultáneamente el ámbito estatal y el municipal.
old_age_rates = '''        st.markdown("#### 🧬 Incidencia EDA específica por edad y sexo")
        if sinave.empty:
            st.info("SINAVE no disponible para calcular tasas específicas.")
        else:
            paths=["Todos los casos"]+sorted(c.replace("path_","") for c in sinave.columns if c.startswith("path_")); pp=st.selectbox("Evento / patógeno",paths,key="pop_pathogen")
            rates=age_sex_rates(sinave,population,year,week,pm,pp); export_tables["Incidencia edad sexo"]=rates
            if rates.empty: st.info("No hay combinación compatible de casos y denominadores para este filtro.")
            else:
                st.dataframe(rates,hide_index=True,use_container_width=True)
                rr=rates.copy(); rr["Estrato"]=rr["Grupo edad"].astype(str)+" · "+rr["Sexo"].astype(str)
                fig=bar_fig(rr.sort_values("Incidencia /100k").tail(30),"Estrato","Incidencia /100k",f"Incidencia específica · {pp} · {pm}",True); st.pyplot(fig,use_container_width=True); register_fig("⬇️ PNG · incidencia edad/sexo",f"Incidencia_Edad_Sexo_{year}_{pm}.png",fig,"pop_rates",images); plt.close(fig)'''

new_age_rates = '''        st.markdown("#### 🧬 Incidencia EDA específica por edad y sexo")
        if sinave.empty:
            st.info("SINAVE no disponible para calcular tasas específicas.")
        else:
            paths=["Todos los casos"]+sorted(c.replace("path_","") for c in sinave.columns if c.startswith("path_"))
            pp=st.selectbox("Evento / patógeno",paths,key="pop_pathogen")
            state_rates=age_sex_rates(sinave,population,year,week,"Todos",pp)
            if not state_rates.empty:
                state_rates=state_rates.copy(); state_rates.insert(0,"Ámbito","Estatal · Sonora")
            export_tables["Incidencia edad sexo estatal"]=state_rates

            if pm=="Todos":
                st.info("Ámbito mostrado: **ESTATAL (Sonora)**. Selecciona un municipio arriba para ver simultáneamente la tasa municipal y la estatal de referencia.")
                rates=state_rates.drop(columns=["Ámbito"],errors="ignore")
                if rates.empty:
                    st.info("No hay combinación compatible de casos y denominadores para este filtro.")
                else:
                    st.dataframe(state_rates,hide_index=True,use_container_width=True)
                    rr=rates.copy(); rr["Estrato"]=rr["Grupo edad"].astype(str)+" · "+rr["Sexo"].astype(str)
                    fig=bar_fig(rr.sort_values("Incidencia /100k").tail(30),"Estrato","Incidencia /100k",f"Incidencia específica ESTATAL · {pp} · Sonora",True)
                    st.pyplot(fig,use_container_width=True); register_fig("⬇️ PNG · incidencia edad/sexo",f"Incidencia_Edad_Sexo_Estatal_{year}.png",fig,"pop_rates_state",images); plt.close(fig)
            else:
                municipal_rates=age_sex_rates(sinave,population,year,week,pm,pp)
                if not municipal_rates.empty:
                    municipal_rates=municipal_rates.copy(); municipal_rates.insert(0,"Ámbito",f"Municipal · {pm}")
                export_tables["Incidencia edad sexo municipal"]=municipal_rates
                tmun,tstate=st.tabs([f"🏘️ Municipal · {pm}","🏛️ Estatal · Sonora"])
                with tmun:
                    st.caption(f"Numerador: casos SINAVE residentes de {pm}; denominador: población proyectada de {pm} para el mismo sexo y grupo de edad.")
                    if municipal_rates.empty: st.info("Sin combinación compatible para el municipio seleccionado.")
                    else:
                        st.dataframe(municipal_rates,hide_index=True,use_container_width=True)
                        rr=municipal_rates.drop(columns=["Ámbito"],errors="ignore").copy(); rr["Estrato"]=rr["Grupo edad"].astype(str)+" · "+rr["Sexo"].astype(str)
                        fig=bar_fig(rr.sort_values("Incidencia /100k").tail(30),"Estrato","Incidencia /100k",f"Incidencia específica MUNICIPAL · {pp} · {pm}",True)
                        st.pyplot(fig,use_container_width=True); register_fig("⬇️ PNG · incidencia municipal",f"Incidencia_Edad_Sexo_Municipal_{year}_{pm}.png",fig,"pop_rates_mun",images); plt.close(fig)
                with tstate:
                    st.caption("Referencia estatal: todos los casos SINAVE residentes de Sonora; denominador: suma de la población municipal proyectada del mismo estrato.")
                    if state_rates.empty: st.info("Sin combinación compatible para Sonora.")
                    else:
                        st.dataframe(state_rates,hide_index=True,use_container_width=True)
                        rr=state_rates.drop(columns=["Ámbito"],errors="ignore").copy(); rr["Estrato"]=rr["Grupo edad"].astype(str)+" · "+rr["Sexo"].astype(str)
                        fig=bar_fig(rr.sort_values("Incidencia /100k").tail(30),"Estrato","Incidencia /100k",f"Incidencia específica ESTATAL · {pp} · Sonora",True)
                        st.pyplot(fig,use_container_width=True); register_fig("⬇️ PNG · incidencia estatal",f"Incidencia_Edad_Sexo_Estatal_{year}.png",fig,"pop_rates_state_compare",images); plt.close(fig)

            st.caption(f"Todas las tasas específicas corresponden al acumulado SE1–SE{week} y se expresan por 100,000 habitantes del mismo año, sexo, grupo etario y ámbito geográfico.")'''

if old_age_rates not in text:
    raise RuntimeError("No encontré el bloque de incidencia edad/sexo esperado en app_v42.py")
text = text.replace(old_age_rates,new_age_rates)

code = compile(text, str(app), "exec")
exec(code, {"__name__": "__main__", "__file__": str(app)})
