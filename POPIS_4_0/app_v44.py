"""POPIS 4.3.5: mapa completo de Sonora + tasas territoriales con base seleccionable."""
from pathlib import Path

wrapper = Path(__file__).with_name("app_v43.py")
source = wrapper.read_text(encoding="utf-8")
source = source.replace("4.3.4-charts", "4.3.5-territory")
source = source.replace(
    '"""POPIS 4.3.4: interfaz 4.2 + focos espaciales + tasas explícitas + gráficas ordenables + canal dual."""',
    '"""POPIS 4.3.5: interfaz 4.2 + mapa completo + tasas configurables + gráficas ordenables + canal dual."""',
)

old = '''new_territory = \'\'\'with TABS[5]:
    st.subheader("Territorio · residencia habitual")
    if sinave.empty:
        st.warning("SINAVE no disponible.")
    else:
        terr=territorial_summary(sinave,year,week,population if not population.empty else None)
        export_tables["Territorio municipal"]=terr

        sycol="epi_year" if "epi_year" in sinave.columns else "year"
        state_cases=sinave[pd.to_numeric(sinave[sycol],errors="coerce").eq(year) & pd.to_numeric(sinave["epi_week"],errors="coerce").between(1,week)].copy()
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
        export_tables["Incidencia estatal"]=pd.DataFrame([
            {"Ámbito":"Estatal","Sistema":"SINAVE","Año":year,"Corte SE":week,"Casos":state_sinave_cases,"Población":state_population,"Incidencia /100k":state_sinave_inc},
            {"Ámbito":"Estatal","Sistema":"SUIVE","Año":year,"Corte SE":week,"Casos":state_suive_cases,"Población":state_population,"Incidencia /100k":state_suive_inc},
        ])

        st.markdown("#### Tasas territoriales SINAVE")
        level=st.radio("Nivel",["Municipio","Distrito","Región"],horizontal=True)
        table=terr if level=="Municipio" else aggregate_territory(terr,level)
        scope_word={"Municipio":"municipal","Distrito":"distrital","Región":"regional"}[level]
        display_table=table.rename(columns={"Incidencia /100k":f"Incidencia {scope_word} /100k","Mortalidad /100k":f"Mortalidad {scope_word} /100k"})
        st.dataframe(display_table,hide_index=True,use_container_width=True)
        metrics=[c for c in ["Casos","Positivos","Defunciones","Incidencia /100k","Mortalidad /100k"] if c in table]
        if metrics:
            oc1,oc2=st.columns([1.4,1])
            with oc1: metric=st.selectbox("Indicador territorial",metrics)
            with oc2: graph_order=st.selectbox("Orden de la gráfica",["Mayor → menor","Menor → mayor","Alfabético A-Z"],key="terr_graph_order")
            metric_label={"Incidencia /100k":f"Incidencia {scope_word} /100k","Mortalidad /100k":f"Mortalidad {scope_word} /100k"}.get(metric,metric)
            if graph_order=="Mayor → menor": plot_table=table.nlargest(min(25,len(table)),metric)
            elif graph_order=="Menor → mayor": plot_table=table.nsmallest(min(25,len(table)),metric)
            else: plot_table=table.sort_values(level).head(25)
            fig=bar_fig(plot_table,level,metric,f"{level} · {metric_label}",True,order=graph_order)
            st.pyplot(fig,use_container_width=True); register_fig("⬇️ PNG",f"Territorio_{level}_{metric}_{year}.png",fig,"terr",images); plt.close(fig)
            if level=="Municipio":
                try:
                    geo=fetch_sonora_geojson(); fmap=px.choropleth(terr,geojson=geo,locations="Municipio",color=metric,featureidkey="properties.nomgeo",hover_name="Municipio",projection="mercator",title=f"Sonora · {metric_label}")
                    fmap.update_geos(fitbounds="locations",visible=False); fmap.update_layout(height=650,margin=dict(l=0,r=0,t=45,b=0)); st.plotly_chart(fmap,use_container_width=True,config={"displaylogo":False,"toImageButtonOptions":{"format":"png","filename":f"Mapa_{metric}_{year}"}})
                except Exception as exc: st.info(f"Mapa INEGI no disponible: {exc}")

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
        if population.empty: st.info("Población municipal no cargada: se muestran conteos, no tasas.")\'\'\''''

new = '''new_territory = \'\'\'with TABS[5]:
    st.subheader("Territorio · residencia habitual")
    if sinave.empty:
        st.warning("SINAVE no disponible.")
    else:
        from popis_core import _norm_text
        from popis_core_patch import _DISTRICT_BY_MUN, _REGION_BY_MUN

        terr=territorial_summary(sinave,year,week,population if not population.empty else None)

        st.markdown("#### Escala de las tasas")
        rate_base=st.selectbox(
            "Expresar tasas por",
            [1000,10000,100000],
            index=2,
            format_func=lambda x: f"{x:,} habitantes".replace(","," "),
            key="territory_rate_base",
        )
        rate_label=f"{rate_base:,}".replace(","," ")

        sycol="epi_year" if "epi_year" in sinave.columns else "year"
        state_cases=sinave[pd.to_numeric(sinave[sycol],errors="coerce").eq(year) & pd.to_numeric(sinave["epi_week"],errors="coerce").between(1,week)].copy()
        if "sonora_resident" in state_cases.columns:
            state_cases=state_cases[state_cases["sonora_resident"].fillna(False)]
        state_sinave_cases=int(len(state_cases))
        state_profile=demographic_profile(population,year,"Todos") if not population.empty else {}
        state_population=float(state_profile.get("Población",np.nan)) if state_profile else np.nan
        state_sinave_rate=(state_sinave_cases/state_population*rate_base) if pd.notna(state_population) and state_population>0 else np.nan
        su_state=suive_summary(suive,year,week) if not suive.empty else {"acumulado":np.nan}
        state_suive_cases=su_state.get("acumulado",np.nan)
        state_suive_rate=(float(state_suive_cases)/state_population*rate_base) if pd.notna(state_suive_cases) and pd.notna(state_population) and state_population>0 else np.nan

        st.markdown("#### Sonora · tasas estatales acumuladas")
        sc=st.columns(4)
        sc[0].metric("Población estatal", "—" if pd.isna(state_population) else f"{int(round(state_population)):,}")
        sc[1].metric("Casos SINAVE residentes Sonora", f"{state_sinave_cases:,}")
        sc[2].metric(f"Incidencia estatal SINAVE /{rate_label}", "—" if pd.isna(state_sinave_rate) else f"{state_sinave_rate:,.2f}")
        sc[3].metric(f"Incidencia estatal SUIVE /{rate_label}", "—" if pd.isna(state_suive_rate) else f"{state_suive_rate:,.2f}")
        st.caption(f"Corte acumulado SE1–SE{week}. Cambiar la base modifica la escala, no el patrón relativo. SINAVE y SUIVE son sistemas distintos y no se suman entre sí.")
        export_tables["Incidencia estatal"]=pd.DataFrame([
            {"Ámbito":"Estatal","Sistema":"SINAVE","Año":year,"Corte SE":week,"Casos":state_sinave_cases,"Población":state_population,f"Incidencia /{rate_label}":state_sinave_rate},
            {"Ámbito":"Estatal","Sistema":"SUIVE","Año":year,"Corte SE":week,"Casos":state_suive_cases,"Población":state_population,f"Incidencia /{rate_label}":state_suive_rate},
        ])

        # Construir una tabla municipal completa usando el denominador demográfico.
        # Así aparecen municipios con cero casos y el mapa conserva los 72 polígonos.
        terr_full=terr.copy()
        if not population.empty:
            pop_y=population_for_year(population,year).copy()
            if not pop_y.empty:
                if pop_y["Sexo"].isin(["Hombres","Mujeres"]).any():
                    pop_y=pop_y[pop_y["Sexo"].isin(["Hombres","Mujeres"])]
                pop_y=pop_y[pop_y["Grupo edad"].ne("Total")]
                pop_mun=pop_y.groupby("Municipio",as_index=False)["Población"].sum()
                pop_mun["_key"]=pop_mun["Municipio"].map(_norm_text)
                tj=terr.copy(); tj["_key"]=tj["Municipio"].map(_norm_text)
                tj=tj.drop(columns=["Municipio","Población"],errors="ignore")
                terr_full=pop_mun.merge(tj,on="_key",how="left")
                terr_full["Distrito"]=terr_full.get("Distrito",pd.Series(index=terr_full.index,dtype=object)).fillna(terr_full["_key"].map(_DISTRICT_BY_MUN))
                terr_full["Región"]=terr_full.get("Región",pd.Series(index=terr_full.index,dtype=object)).fillna(terr_full["_key"].map(_REGION_BY_MUN))
                for c in ["Casos","Positivos","Defunciones"]:
                    terr_full[c]=pd.to_numeric(terr_full.get(c,0),errors="coerce").fillna(0)
                terr_full["Positividad %"]=np.where(terr_full["Casos"]>0,terr_full["Positivos"]/terr_full["Casos"]*100,np.nan)
                terr_full["Letalidad %"]=np.where(terr_full["Casos"]>0,terr_full["Defunciones"]/terr_full["Casos"]*100,np.nan)
                terr_full=terr_full.drop(columns="_key",errors="ignore")

        export_tables["Territorio municipal completo"]=terr_full

        st.markdown("#### Tasas territoriales SINAVE")
        level=st.radio("Nivel",["Municipio","Distrito","Región"],horizontal=True)
        table=terr_full.copy() if level=="Municipio" else aggregate_territory(terr_full,level)
        scope_word={"Municipio":"municipal","Distrito":"distrital","Región":"regional"}[level]
        scope_noun={"Municipio":"municipio","Distrito":"distrito","Región":"región"}[level]
        inc_col=f"Incidencia {scope_word} /{rate_label}"
        state_den_col=f"Tasa casos del {scope_noun} / población estatal · por {rate_label}"
        ratio_col=f"Razón incidencia {scope_word} / incidencia estatal SINAVE"
        mort_col=f"Mortalidad {scope_word} /{rate_label}"

        if "Población" in table.columns:
            table[inc_col]=np.where(table["Población"]>0,table["Casos"]/table["Población"]*rate_base,np.nan)
            table[mort_col]=np.where(table["Población"]>0,table["Defunciones"]/table["Población"]*rate_base,np.nan)
        else:
            table[inc_col]=np.nan; table[mort_col]=np.nan
        table[state_den_col]=(table["Casos"]/state_population*rate_base) if pd.notna(state_population) and state_population>0 else np.nan
        table[ratio_col]=(table[inc_col]/state_sinave_rate) if pd.notna(state_sinave_rate) and state_sinave_rate>0 else np.nan

        display_table=table.drop(columns=["Incidencia /100k","Mortalidad /100k"],errors="ignore")
        st.dataframe(display_table,hide_index=True,use_container_width=True)
        export_tables[f"Tasas {scope_word}"]=display_table
        st.caption("La razón de incidencias compara la incidencia del territorio con la incidencia estatal SINAVE. >1 significa incidencia superior al promedio estatal; <1, inferior. No depende de elegir 1 000, 10 000 o 100 000 como escala.")

        metrics=[c for c in ["Casos","Positivos","Defunciones",inc_col,state_den_col,ratio_col,mort_col] if c in table]
        if metrics:
            oc1,oc2=st.columns([1.4,1])
            with oc1: metric=st.selectbox("Indicador territorial",metrics)
            with oc2: graph_order=st.selectbox("Orden de la gráfica",["Mayor → menor","Menor → mayor","Alfabético A-Z"],key="terr_graph_order")
            if graph_order=="Mayor → menor": plot_table=table.nlargest(min(25,len(table)),metric)
            elif graph_order=="Menor → mayor": plot_table=table.nsmallest(min(25,len(table)),metric)
            else: plot_table=table.sort_values(level).head(25)
            fig=bar_fig(plot_table,level,metric,f"{level} · {metric}",True,order=graph_order)
            st.pyplot(fig,use_container_width=True); register_fig("⬇️ PNG",f"Territorio_{level}_{year}_{rate_base}.png",fig,"terr",images); plt.close(fig)

            if level=="Municipio":
                try:
                    geo=fetch_sonora_geojson()
                    geo_names=[f.get("properties",{}).get("nomgeo","") for f in geo.get("features",[])]
                    map_base=pd.DataFrame({"Municipio":geo_names})
                    map_base=map_base[map_base["Municipio"].astype(str).str.strip().ne("")].drop_duplicates()
                    map_base["_key"]=map_base["Municipio"].map(_norm_text)
                    map_values=table.copy(); map_values["_key"]=map_values["Municipio"].map(_norm_text)
                    map_values=map_values.drop(columns=["Municipio"],errors="ignore")
                    map_data=map_base.merge(map_values,on="_key",how="left").drop(columns="_key",errors="ignore")
                    for c in ["Casos","Positivos","Defunciones",inc_col,state_den_col,ratio_col,mort_col]:
                        if c in map_data.columns:
                            map_data[c]=pd.to_numeric(map_data[c],errors="coerce").fillna(0)
                    fmap=px.choropleth(
                        map_data,geojson=geo,locations="Municipio",color=metric,
                        featureidkey="properties.nomgeo",hover_name="Municipio",
                        hover_data={"Casos":True,"Población":True,inc_col:True,ratio_col:True},
                        projection="mercator",title=f"Sonora completo · {metric}"
                    )
                    fmap.update_geos(fitbounds="locations",visible=False)
                    fmap.update_layout(height=720,margin=dict(l=0,r=0,t=45,b=0))
                    st.plotly_chart(fmap,use_container_width=True,config={"displaylogo":False,"toImageButtonOptions":{"format":"png","filename":f"Mapa_{metric}_{year}"}})
                    st.caption(f"Mapa construido con {len(map_base)} polígonos municipales del GeoJSON INEGI; los municipios sin casos permanecen visibles con valor 0.")
                except Exception as exc: st.info(f"Mapa INEGI no disponible: {exc}")

        with st.expander("📚 Fórmulas y procedencia de los datos",expanded=False):
            sin_files=bundle.inventory.loc[bundle.inventory["Sistema"].eq("SINAVE"),"Archivo"].astype(str).tolist() if not bundle.inventory.empty else []
            sui_files=bundle.inventory.loc[bundle.inventory["Sistema"].eq("SUIVE"),"Archivo"].astype(str).tolist() if not bundle.inventory.empty else []
            pop_files=bundle.inventory.loc[bundle.inventory["Sistema"].eq("POBLACIÓN"),"Archivo"].astype(str).tolist() if not bundle.inventory.empty else []
            st.markdown(f"**Incidencia municipal SINAVE** = casos SINAVE residentes del municipio acumulados hasta SE{week} / población proyectada de ese municipio × {rate_label}.")
            st.markdown(f"**Tasa de casos del municipio con denominador estatal** = casos del municipio / población total proyectada de Sonora × {rate_label}. Se muestra como contribución estandarizada, no como sustituto de la incidencia municipal.")
            st.markdown(f"**Incidencia estatal SINAVE** = todos los casos SINAVE residentes de Sonora acumulados hasta SE{week} / población estatal proyectada × {rate_label}.")
            st.markdown("**Razón de incidencias municipio/estado** = incidencia municipal / incidencia estatal SINAVE. Es una comparación de riesgo relativo descriptiva; 1 equivale al promedio estatal.")
            st.markdown(f"**Incidencia estatal SUIVE** = casos SUIVE estatales acumulados hasta SE{week} / la misma población estatal proyectada × {rate_label}.")
            st.markdown("**Numeradores SINAVE:** " + (", ".join(sin_files) if sin_files else "fuente SINAVE local no identificada"))
            st.markdown("**Numerador SUIVE:** " + (", ".join(sui_files) if sui_files else "fuente SUIVE local no identificada"))
            st.markdown("**Denominadores de población:** " + (", ".join(pop_files) if pop_files else "archivo demográfico local no identificado"))
            st.info("La base 1 000 / 10 000 / 100 000 solo reescala la tasa. La razón municipio/estado permanece igual porque numerador y referencia cambian por el mismo factor.")
        if population.empty: st.info("Población municipal no cargada: se muestran conteos, no tasas.")\'\'\''''

if old not in source:
    raise RuntimeError("No encontré el bloque territorial 4.3.4 esperado en app_v43.py")
source = source.replace(old, new)

code = compile(source, str(wrapper), "exec")
exec(code, {"__name__": "__main__", "__file__": str(wrapper)})
