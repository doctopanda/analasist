"""POPIS 4.3.4: interfaz 4.2 + focos espaciales + tasas explícitas + gráficas ordenables + canal dual."""
from pathlib import Path

app = Path(__file__).with_name("app_v42.py")
text = app.read_text(encoding="utf-8")
text = text.replace('BUILD = "4.2.0-pop"', 'BUILD = "4.3.4-charts"')
text = text.replace(
    'SUIVE + SINAVE + demografía + indicadores + territorio · Sonora',
    'SUIVE + SINAVE + demografía + territorio + focos espaciales · Sonora',
)

# ---------------------------------------------------------------------------
# Selector de año defensivo
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Gráficas de barras ordenables
# ---------------------------------------------------------------------------
old_bar = '''def bar_fig(data, x, y, title, horizontal=False):
    fig, ax = plt.subplots(figsize=(9,5)); d=data.sort_values(y) if horizontal else data
    (ax.barh(d[x].astype(str),d[y]) if horizontal else ax.bar(d[x].astype(str),d[y]))
    ax.set_title(title,fontweight="bold"); ax.grid(axis="x" if horizontal else "y",alpha=.2); fig.tight_layout(); return fig'''
new_bar = '''def bar_fig(data, x, y, title, horizontal=False, order="Automático", order_col=None):
    fig, ax = plt.subplots(figsize=(9,5))
    d=data.copy()
    invert_y=False
    if not d.empty:
        if order=="Mayor → menor":
            d=d.sort_values(y,ascending=True if horizontal else False,na_position="last")
        elif order=="Menor → mayor":
            d=d.sort_values(y,ascending=False if horizontal else True,na_position="last")
        elif order=="Edad ascendente":
            key=order_col if order_col in d.columns else x
            d["_orden_grafica"]=pd.to_numeric(d[key].astype(str).str.extract(r"(\\d+)",expand=False),errors="coerce").fillna(9999)
            extras=["Sexo"] if "Sexo" in d.columns else []
            d=d.sort_values(["_orden_grafica"]+extras,ascending=True).drop(columns="_orden_grafica")
            invert_y=horizontal
        elif order=="Año ascendente":
            d=d.sort_values(x,ascending=True)
            invert_y=horizontal
        elif order=="Alfabético A-Z":
            d=d.assign(_orden_grafica=d[x].astype(str)).sort_values("_orden_grafica").drop(columns="_orden_grafica")
            invert_y=horizontal
        elif order=="Automático" and horizontal:
            d=d.sort_values(y,ascending=True,na_position="last")
    (ax.barh(d[x].astype(str),d[y]) if horizontal else ax.bar(d[x].astype(str),d[y]))
    if invert_y:
        ax.invert_yaxis()
    ax.set_title(title,fontweight="bold"); ax.grid(axis="x" if horizontal else "y",alpha=.2); fig.tight_layout(); return fig'''
if old_bar not in text:
    raise RuntimeError("No encontré la función bar_fig esperada")
text = text.replace(old_bar,new_bar)

# ---------------------------------------------------------------------------
# Canal endémico individual + vista dual en paneles coordinados
# ---------------------------------------------------------------------------
old_channel_func = '''def channel_fig(ch,title):
    fig,ax=plt.subplots(figsize=(11,5.2)); x=ch["SE"]
    ax.fill_between(x,0,ch["Q1"],alpha=.12,label="Éxito"); ax.fill_between(x,ch["Q1"],ch["Mediana"],alpha=.13,label="Seguridad")
    ax.fill_between(x,ch["Mediana"],ch["Q3"],alpha=.14,label="Alarma"); ax.plot(x,ch["Actual"],linewidth=2.7,marker="o",markersize=3,label="Actual")
    ax.plot(x,ch["Q1"],linewidth=1); ax.plot(x,ch["Mediana"],linewidth=1.5); ax.plot(x,ch["Q3"],linewidth=1)
    ax.set(title=title,xlabel="Semana epidemiológica",ylabel="Casos",xlim=(1,53)); ax.grid(alpha=.18); ax.legend(frameon=False,ncol=4); fig.tight_layout(); return fig'''
new_channel_func = '''def _draw_channel(ax,ch,title):
    x=ch["SE"]
    ax.fill_between(x,0,ch["Q1"],alpha=.12,label="Éxito")
    ax.fill_between(x,ch["Q1"],ch["Mediana"],alpha=.13,label="Seguridad")
    ax.fill_between(x,ch["Mediana"],ch["Q3"],alpha=.14,label="Alarma")
    ax.plot(x,ch["Actual"],linewidth=2.7,marker="o",markersize=3,label="Actual")
    ax.plot(x,ch["Q1"],linewidth=1)
    ax.plot(x,ch["Mediana"],linewidth=1.5)
    ax.plot(x,ch["Q3"],linewidth=1)
    ax.set(title=title,ylabel="Casos",xlim=(1,53))
    ax.grid(alpha=.18)
    ax.legend(frameon=False,ncol=4)


def channel_fig(ch,title):
    fig,ax=plt.subplots(figsize=(11,5.2))
    _draw_channel(ax,ch,title)
    ax.set_xlabel("Semana epidemiológica")
    fig.tight_layout()
    return fig


def dual_channel_fig(ch_suive,ch_sinave,title_suive,title_sinave):
    fig,axes=plt.subplots(2,1,figsize=(11,9.2),sharex=True)
    _draw_channel(axes[0],ch_suive,title_suive)
    _draw_channel(axes[1],ch_sinave,title_sinave)
    axes[1].set_xlabel("Semana epidemiológica")
    fig.suptitle("Canales endémicos simultáneos · escalas independientes",fontweight="bold")
    fig.tight_layout(rect=(0,0,1,.97))
    return fig'''
if old_channel_func not in text:
    raise RuntimeError("No encontré la función channel_fig esperada")
text = text.replace(old_channel_func,new_channel_func)

# ---------------------------------------------------------------------------
# Canal endémico: SUIVE, SINAVE o ambos simultáneamente
# ---------------------------------------------------------------------------
old_channel_tab = '''with TABS[4]:
    st.subheader("Canal endémico dinámico"); source=st.radio("Fuente",["SUIVE","SINAVE"],horizontal=True,key="ch_src")
    if source=="SUIVE" and not suive.empty:
        hist=[int(y) for y in sorted(suive.Año.unique()) if int(y)<year]; default=[y for y in hist if y not in (2020,2021)] or hist; selected=st.multiselect("Años históricos",hist,default=default)
        if selected:
            ch=endemic_channel(suive,year,selected,week); export_tables["Canal SUIVE"]=ch; fig=channel_fig(ch,f"Canal endémico SUIVE · {year}"); st.pyplot(fig,use_container_width=True); register_fig("⬇️ PNG",f"Canal_SUIVE_{year}.png",fig,"ch_su",images); plt.close(fig); row=ch[ch.SE.eq(week)]
            if not row.empty: st.metric(f"Zona SE{week}",row.iloc[0]["Zona"])
    elif source=="SINAVE" and not sinave.empty:
        paths=["Todos los casos"]+sorted(c.replace("path_","") for c in sinave.columns if c.startswith("path_")); pathogen=st.selectbox("Patógeno",paths); hist=[int(y) for y in sorted(pd.to_numeric(sinave.epi_year,errors="coerce").dropna().unique()) if int(y)<year]; selected=st.multiselect("Años históricos SINAVE",hist,default=hist); muni=["Todos"]+sorted(sinave.loc[sinave.sonora_resident,"municipality"].dropna().astype(str).unique()); mun=st.selectbox("Municipio",muni)
        if selected:
            ch=sinave_channel(sinave,year,selected,pathogen,week,mun); export_tables["Canal SINAVE"]=ch; fig=channel_fig(ch,f"SINAVE · {pathogen} · {mun}"); st.pyplot(fig,use_container_width=True); register_fig("⬇️ PNG",f"Canal_SINAVE_{year}.png",fig,"ch_si",images); plt.close(fig)
    else: st.warning("Fuente no disponible.")'''
new_channel_tab = '''with TABS[4]:
    st.subheader("Canal endémico dinámico")
    source=st.radio("Vista",["SUIVE","SINAVE","Ambos"],horizontal=True,key="ch_src")

    if source=="SUIVE":
        if suive.empty:
            st.warning("SUIVE no disponible.")
        else:
            hist=[int(y) for y in sorted(suive.Año.unique()) if int(y)<year]
            default=[y for y in hist if y not in (2020,2021)] or hist
            selected=st.multiselect("Años históricos SUIVE",hist,default=default,key="ch_su_hist")
            if selected:
                ch=endemic_channel(suive,year,selected,week)
                export_tables["Canal SUIVE"]=ch
                fig=channel_fig(ch,f"Canal endémico SUIVE · {year}")
                st.pyplot(fig,use_container_width=True); register_fig("⬇️ PNG",f"Canal_SUIVE_{year}.png",fig,"ch_su",images); plt.close(fig)
                row=ch[ch.SE.eq(week)]
                if not row.empty: st.metric(f"Zona SUIVE · SE{week}",row.iloc[0]["Zona"])

    elif source=="SINAVE":
        if sinave.empty:
            st.warning("SINAVE no disponible.")
        else:
            paths=["Todos los casos"]+sorted(c.replace("path_","") for c in sinave.columns if c.startswith("path_"))
            pathogen=st.selectbox("Patógeno",paths,key="ch_si_path")
            hist=[int(y) for y in sorted(pd.to_numeric(sinave.epi_year,errors="coerce").dropna().unique()) if int(y)<year]
            selected=st.multiselect("Años históricos SINAVE",hist,default=hist,key="ch_si_hist")
            muni=["Todos"]+sorted(sinave.loc[sinave.sonora_resident,"municipality"].dropna().astype(str).unique())
            mun=st.selectbox("Municipio",muni,key="ch_si_mun")
            if selected:
                ch=sinave_channel(sinave,year,selected,pathogen,week,mun)
                export_tables["Canal SINAVE"]=ch
                fig=channel_fig(ch,f"SINAVE · {pathogen} · {mun}")
                st.pyplot(fig,use_container_width=True); register_fig("⬇️ PNG",f"Canal_SINAVE_{year}.png",fig,"ch_si",images); plt.close(fig)
                row=ch[ch.SE.eq(week)]
                if not row.empty: st.metric(f"Zona SINAVE · SE{week}",row.iloc[0]["Zona"])

    else:
        if suive.empty or sinave.empty:
            st.warning("La vista simultánea necesita SUIVE y SINAVE disponibles.")
        else:
            st.info("Los canales se muestran juntos pero en paneles y escalas independientes para evitar que la magnitud de SUIVE aplaste visualmente a SINAVE.")
            ca,cb=st.columns(2)
            with ca:
                hist_su=[int(y) for y in sorted(suive.Año.unique()) if int(y)<year]
                default_su=[y for y in hist_su if y not in (2020,2021)] or hist_su
                sel_su=st.multiselect("Históricos SUIVE",hist_su,default=default_su,key="ch_both_su_hist")
            with cb:
                paths=["Todos los casos"]+sorted(c.replace("path_","") for c in sinave.columns if c.startswith("path_"))
                pathogen=st.selectbox("Evento / patógeno SINAVE",paths,key="ch_both_path")
                hist_si=[int(y) for y in sorted(pd.to_numeric(sinave.epi_year,errors="coerce").dropna().unique()) if int(y)<year]
                sel_si=st.multiselect("Históricos SINAVE",hist_si,default=hist_si,key="ch_both_si_hist")
                muni=["Todos"]+sorted(sinave.loc[sinave.sonora_resident,"municipality"].dropna().astype(str).unique())
                mun=st.selectbox("Municipio SINAVE",muni,key="ch_both_mun")
            if sel_su and sel_si:
                ch_su=endemic_channel(suive,year,sel_su,week)
                ch_si=sinave_channel(sinave,year,sel_si,pathogen,week,mun)
                export_tables["Canal SUIVE"]=ch_su; export_tables["Canal SINAVE"]=ch_si
                fig=dual_channel_fig(ch_su,ch_si,f"SUIVE · {year}",f"SINAVE · {pathogen} · {mun}")
                st.pyplot(fig,use_container_width=True); register_fig("⬇️ PNG · ambos canales",f"Canales_SUIVE_SINAVE_{year}.png",fig,"ch_both",images); plt.close(fig)
                za=ch_su[ch_su.SE.eq(week)]; zb=ch_si[ch_si.SE.eq(week)]; mc=st.columns(2)
                mc[0].metric(f"Zona SUIVE · SE{week}",za.iloc[0]["Zona"] if not za.empty else "—")
                mc[1].metric(f"Zona SINAVE · SE{week}",zb.iloc[0]["Zona"] if not zb.empty else "—")'''
if old_channel_tab not in text:
    raise RuntimeError("No encontré el bloque de Canal endémico esperado")
text = text.replace(old_channel_tab,new_channel_tab)

# ---------------------------------------------------------------------------
# Territorio: tasas explícitas + orden configurable
# ---------------------------------------------------------------------------
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
        if population.empty: st.info("Población municipal no cargada: se muestran conteos, no tasas.")'''
if old_territory not in text:
    raise RuntimeError("No encontré el bloque de Territorio esperado en app_v42.py")
text = text.replace(old_territory,new_territory)

# ---------------------------------------------------------------------------
# Edad/sexo: ámbitos estatal y municipal + orden ascendente de edad
# ---------------------------------------------------------------------------
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
            ac1,ac2=st.columns([1.5,1])
            paths=["Todos los casos"]+sorted(c.replace("path_","") for c in sinave.columns if c.startswith("path_"))
            with ac1: pp=st.selectbox("Evento / patógeno",paths,key="pop_pathogen")
            with ac2: age_graph_order=st.selectbox("Orden de las gráficas",["Edad ascendente","Mayor → menor","Menor → mayor"],key="age_graph_order")
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
                    fig=bar_fig(rr,"Estrato","Incidencia /100k",f"Incidencia específica ESTATAL · {pp} · Sonora",True,order=age_graph_order,order_col="Grupo edad")
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
                        fig=bar_fig(rr,"Estrato","Incidencia /100k",f"Incidencia específica MUNICIPAL · {pp} · {pm}",True,order=age_graph_order,order_col="Grupo edad")
                        st.pyplot(fig,use_container_width=True); register_fig("⬇️ PNG · incidencia municipal",f"Incidencia_Edad_Sexo_Municipal_{year}_{pm}.png",fig,"pop_rates_mun",images); plt.close(fig)
                with tstate:
                    st.caption("Referencia estatal: todos los casos SINAVE residentes de Sonora; denominador: suma de la población municipal proyectada del mismo estrato.")
                    if state_rates.empty: st.info("Sin combinación compatible para Sonora.")
                    else:
                        st.dataframe(state_rates,hide_index=True,use_container_width=True)
                        rr=state_rates.drop(columns=["Ámbito"],errors="ignore").copy(); rr["Estrato"]=rr["Grupo edad"].astype(str)+" · "+rr["Sexo"].astype(str)
                        fig=bar_fig(rr,"Estrato","Incidencia /100k",f"Incidencia específica ESTATAL · {pp} · Sonora",True,order=age_graph_order,order_col="Grupo edad")
                        st.pyplot(fig,use_container_width=True); register_fig("⬇️ PNG · incidencia estatal",f"Incidencia_Edad_Sexo_Estatal_{year}.png",fig,"pop_rates_state_compare",images); plt.close(fig)
            st.caption(f"Todas las tasas específicas corresponden al acumulado SE1–SE{week} y se expresan por 100,000 habitantes del mismo año, sexo, grupo etario y ámbito geográfico.")'''
if old_age_rates not in text:
    raise RuntimeError("No encontré el bloque de incidencia edad/sexo esperado en app_v42.py")
text = text.replace(old_age_rates,new_age_rates)

# ---------------------------------------------------------------------------
# Orden configurable en otros comparativos de barras
# ---------------------------------------------------------------------------
old_path_chart='''            fig=bar_fig(p.head(12),"Patógeno","Casos",f"Patógenos SINAVE ≤SE{week}",True); st.pyplot(fig,use_container_width=True); register_fig("⬇️ PNG · patógenos",f"Patogenos_{year}_SE{week}.png",fig,"r_pa",images); plt.close(fig)'''
new_path_chart='''            path_order=st.selectbox("Orden gráfica de patógenos",["Mayor → menor","Menor → mayor","Alfabético A-Z"],key="path_graph_order")
            ppchart=p.nlargest(min(12,len(p)),"Casos") if path_order=="Mayor → menor" else (p.nsmallest(min(12,len(p)),"Casos") if path_order=="Menor → mayor" else p.sort_values("Patógeno").head(12))
            fig=bar_fig(ppchart,"Patógeno","Casos",f"Patógenos SINAVE ≤SE{week}",True,order=path_order); st.pyplot(fig,use_container_width=True); register_fig("⬇️ PNG · patógenos",f"Patogenos_{year}_SE{week}.png",fig,"r_pa",images); plt.close(fig)'''
if old_path_chart in text:
    text=text.replace(old_path_chart,new_path_chart)

old_suive_chart='''        fig=bar_fig(t,"Año",f"SE{week}",f"Comparativo SUIVE · SE{week}"); st.pyplot(fig,use_container_width=True); register_fig("⬇️ PNG",f"SUIVE_comparativo_SE{week}.png",fig,"su_comp",images); plt.close(fig)'''
new_suive_chart='''        su_order=st.selectbox("Orden gráfica SUIVE",["Año ascendente","Mayor → menor","Menor → mayor"],key="suive_graph_order")
        fig=bar_fig(t,"Año",f"SE{week}",f"Comparativo SUIVE · SE{week}",order=su_order); st.pyplot(fig,use_container_width=True); register_fig("⬇️ PNG",f"SUIVE_comparativo_SE{week}.png",fig,"su_comp",images); plt.close(fig)'''
if old_suive_chart in text:
    text=text.replace(old_suive_chart,new_suive_chart)

old_mort_chart='''        mort=pd.DataFrame(rows); st.dataframe(mort,hide_index=True,use_container_width=True); export_tables["Mortalidad"]=mort; fig=bar_fig(mort,"Año","Defunciones",f"Defunciones ≤SE{week}"); st.pyplot(fig,use_container_width=True); register_fig("⬇️ PNG",f"Mortalidad_SE{week}.png",fig,"mort",images); plt.close(fig)'''
new_mort_chart='''        mort=pd.DataFrame(rows); st.dataframe(mort,hide_index=True,use_container_width=True); export_tables["Mortalidad"]=mort
        mort_order=st.selectbox("Orden gráfica de defunciones",["Año ascendente","Mayor → menor","Menor → mayor"],key="mort_graph_order")
        fig=bar_fig(mort,"Año","Defunciones",f"Defunciones ≤SE{week}",order=mort_order); st.pyplot(fig,use_container_width=True); register_fig("⬇️ PNG",f"Mortalidad_SE{week}.png",fig,"mort",images); plt.close(fig)'''
if old_mort_chart in text:
    text=text.replace(old_mort_chart,new_mort_chart)

code = compile(text, str(app), "exec")
exec(code, {"__name__": "__main__", "__file__": str(app)})
