from __future__ import annotations

from io import BytesIO
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import requests
import streamlit as st

from popis_core import (
    audit_operational_definitions, build_comparison, endemic_channel,
    laboratory_indicators, make_excel_report, nutrave_indicators,
    pathogen_summary, quality_issues, quality_summary, sinave_channel,
    sinave_summary, sinave_weekly, suive_summary, territorial_summary,
    zip_images,
)
from popis_core_patch import aggregate_territory
from popis_data import add_historical, load_preloaded_sources, save_current, save_population
from popis_population import demographic_profile, pyramid, age_sex_rates, population_for_year

BUILD = "4.2.0-pop"
st.set_page_config(page_title=f"POPIS {BUILD}", page_icon="🧪", layout="wide")
st.markdown("""
<style>
.block-container{padding-top:1.1rem;padding-bottom:3rem}
[data-testid="stMetric"]{background:rgba(15,118,110,.07);border:1px solid rgba(15,118,110,.2);padding:12px;border-radius:14px}
.popis-title{font-size:2.3rem;font-weight:850;color:#12353b;margin-bottom:0}.popis-sub{color:#52656a;margin-top:-.2rem}
.note{padding:.8rem 1rem;border-radius:12px;background:#f4f8f8;border-left:4px solid #0f766e}
</style>
""", unsafe_allow_html=True)
st.markdown(f'<p class="popis-title">🧪 POPIS {BUILD}</p>', unsafe_allow_html=True)
st.markdown('<p class="popis-sub">SUIVE + SINAVE + demografía + indicadores + territorio · Sonora</p>', unsafe_allow_html=True)


def fig_to_png(fig, dpi=180):
    bio = BytesIO(); fig.savefig(bio, format="png", dpi=dpi, bbox_inches="tight", facecolor="white"); return bio.getvalue()


def register_fig(label, filename, fig, key, registry):
    payload = fig_to_png(fig); registry[filename] = payload
    st.download_button(label, payload, file_name=filename, mime="image/png", key=key)


def line_fig(data, x, ys, title, ylabel="Casos"):
    fig, ax = plt.subplots(figsize=(10,4.7))
    for y in ys:
        if y in data: ax.plot(data[x], data[y], marker="o" if len(data)<=15 else None, linewidth=2, label=y)
    ax.set(title=title, xlabel="Semana epidemiológica" if x=="SE" else x, ylabel=ylabel); ax.grid(alpha=.2)
    if len(ys)>1: ax.legend(frameon=False)
    fig.tight_layout(); return fig


def bar_fig(data, x, y, title, horizontal=False):
    fig, ax = plt.subplots(figsize=(9,5)); d=data.sort_values(y) if horizontal else data
    (ax.barh(d[x].astype(str),d[y]) if horizontal else ax.bar(d[x].astype(str),d[y]))
    ax.set_title(title,fontweight="bold"); ax.grid(axis="x" if horizontal else "y",alpha=.2); fig.tight_layout(); return fig


def channel_fig(ch,title):
    fig,ax=plt.subplots(figsize=(11,5.2)); x=ch["SE"]
    ax.fill_between(x,0,ch["Q1"],alpha=.12,label="Éxito"); ax.fill_between(x,ch["Q1"],ch["Mediana"],alpha=.13,label="Seguridad")
    ax.fill_between(x,ch["Mediana"],ch["Q3"],alpha=.14,label="Alarma"); ax.plot(x,ch["Actual"],linewidth=2.7,marker="o",markersize=3,label="Actual")
    ax.plot(x,ch["Q1"],linewidth=1); ax.plot(x,ch["Mediana"],linewidth=1.5); ax.plot(x,ch["Q3"],linewidth=1)
    ax.set(title=title,xlabel="Semana epidemiológica",ylabel="Casos",xlim=(1,53)); ax.grid(alpha=.18); ax.legend(frameon=False,ncol=4); fig.tight_layout(); return fig


def pyramid_fig(data, title):
    fig, ax = plt.subplots(figsize=(9,6.8))
    if data.empty: return fig
    y=np.arange(len(data)); men=-pd.to_numeric(data["Hombres"],errors="coerce").fillna(0).to_numpy(); women=pd.to_numeric(data["Mujeres"],errors="coerce").fillna(0).to_numpy()
    ax.barh(y,men,label="Hombres"); ax.barh(y,women,label="Mujeres")
    ax.set_yticks(y); ax.set_yticklabels(data["Grupo edad"]); ax.axvline(0,linewidth=.8); ax.set_xlabel("Población"); ax.set_title(title,fontweight="bold"); ax.legend(frameon=False); ax.grid(axis="x",alpha=.15)
    ticks=ax.get_xticks(); ax.set_xticklabels([f"{abs(int(t)):,}" for t in ticks]); fig.tight_layout(); return fig


@st.cache_data(show_spinner=False, ttl=86400)
def fetch_sonora_geojson():
    r=requests.get("https://gaia.inegi.org.mx/wscatgeo/v2/geo/mgem/26",timeout=30); r.raise_for_status(); return r.json()


bundle = load_preloaded_sources()
suive, sinave, population = bundle.suive, bundle.sinave, bundle.population

with st.sidebar:
    st.success(f"✅ POPIS {BUILD}")
    st.caption("Históricos congelados; SUIVE/SINAVE se reemplazan semanalmente. La población municipal se carga una sola vez.")
    if not bundle.inventory.empty:
        with st.expander("📚 Fuentes precargadas", expanded=True):
            st.dataframe(bundle.inventory[["Sistema","Rol","Archivo","Estado"]],hide_index=True,use_container_width=True)
    for warning in bundle.warnings: st.warning(warning)

    with st.expander("🔄 Actualización semanal", expanded=False):
        new_sinave=st.file_uploader("Nuevo SINAVE actual",type=["xls","xlsx","csv","txt"],key="weekly_sinave")
        if new_sinave and st.button("Guardar como SINAVE actual",use_container_width=True):
            save_current(new_sinave,"SINAVE"); st.success("SINAVE actualizado"); st.cache_data.clear(); st.rerun()
        new_suive=st.file_uploader("Nuevo SUIVE actual",type=["xls","xlsx"],key="weekly_suive")
        if new_suive and st.button("Guardar como SUIVE actual",use_container_width=True):
            save_current(new_suive,"SUIVE"); st.success("SUIVE actualizado"); st.cache_data.clear(); st.rerun()

    with st.expander("🗓️ Mantenimiento anual / inicial", expanded=False):
        hist_sinave=st.file_uploader("Agregar histórico SINAVE",type=["xls","xlsx","csv","txt"],accept_multiple_files=True,key="hist_sinave_add")
        if hist_sinave and st.button("Agregar históricos SINAVE",use_container_width=True):
            done=[]
            for f in hist_sinave:
                try: done.append(add_historical(f,"SINAVE").name)
                except FileExistsError: pass
            st.success(f"Históricos agregados: {len(done)}"); st.rerun()
        hist_suive=st.file_uploader("Agregar histórico SUIVE",type=["xls","xlsx"],key="hist_suive_add")
        if hist_suive and st.button("Agregar histórico SUIVE",use_container_width=True):
            try: add_historical(hist_suive,"SUIVE")
            except FileExistsError as e: st.warning(str(e))
            else: st.success("Histórico SUIVE agregado"); st.rerun()
        new_pop=st.file_uploader("Población municipal por edad y sexo",type=["xls","xlsx","csv"],key="pop_add")
        if new_pop and st.button("Guardar población municipal",use_container_width=True):
            save_population(new_pop); st.success("Población municipal actualizada"); st.cache_data.clear(); st.rerun()

sin_years=set(pd.to_numeric(sinave.get("epi_year",pd.Series(dtype=float)),errors="coerce").dropna().astype(int).tolist()) if not sinave.empty else set()
su_years=set(pd.to_numeric(suive.get("Año",pd.Series(dtype=float)),errors="coerce").dropna().astype(int).tolist()) if not suive.empty else set()
pop_years=set(pd.to_numeric(population.get("Año",pd.Series(dtype=float)),errors="coerce").dropna().astype(int).tolist()) if not population.empty else set()
available_years=sorted(sin_years|su_years|pop_years)
current_year=max(sin_years|su_years) if (sin_years|su_years) else (max(pop_years) if pop_years else 2026)


def max_week_for(yr):
    vals=[]
    if not sinave.empty and "epi_year" in sinave:
        w=pd.to_numeric(sinave.loc[pd.to_numeric(sinave["epi_year"],errors="coerce").eq(yr),"epi_week"],errors="coerce").dropna();
        if len(w): vals.append(int(w[w.between(1,53)].max()))
    if not suive.empty:
        w=pd.to_numeric(suive.loc[suive["Año"].eq(yr),"SE"],errors="coerce").dropna();
        if len(w): vals.append(int(w[w.between(1,53)].max()))
    return max(vals) if vals else 26


def latest_month(yr):
    if not sinave.empty:
        d=sinave.loc[sinave["capture_date"].dt.year.eq(yr),"capture_date"].dropna()
        if len(d): return int(d.max().month)
    return 6

c1,c2,c3=st.columns([1.3,1,1])
with c1: year=st.selectbox("Año epidemiológico",available_years or [2026],index=(available_years.index(current_year) if current_year in available_years else len(available_years)-1))
with c2: week=st.number_input("Semana de corte",1,53,max_week_for(int(year)),1)
with c3: month=st.number_input("Mes para indicadores",1,12,latest_month(int(year)),1)
year,week,month=int(year),int(week),int(month)

if suive.empty and sinave.empty: st.warning("No hay fuentes locales. Usa 'Mantenimiento anual / inicial' para cargarlas una sola vez.")

images={}; export_tables={}
TABS=st.tabs(["🏠 Resumen","📘 SUIVE","🧬 SINAVE","🔄 Comparador","📈 Canal endémico","🗺️ Territorio","👥 Población","☠️ Mortalidad","🧮 Indicadores","🔍 Calidad y auditoría","📦 Exportar"])

with TABS[0]:
    st.subheader(f"Panorama integrado · {year} · corte SE{week}")
    su=suive_summary(suive,year,week) if not suive.empty else {"acumulado":np.nan,"semana":np.nan}
    si=sinave_summary(sinave,year,week) if not sinave.empty else {k:np.nan for k in ["acumulado","semana","positivos_acum","defunciones_acum","letalidad"]}
    cols=st.columns(6); vals=[("SUIVE acumulado",su.get("acumulado")),(f"SUIVE SE{week}",su.get("semana")),("SINAVE acumulado",si.get("acumulado")),(f"SINAVE SE{week}",si.get("semana")),("Patógeno identificado",si.get("positivos_acum")),("Defunciones",si.get("defunciones_acum"))]
    for col,(label,val) in zip(cols,vals): col.metric(label,"—" if pd.isna(val) else f"{int(round(float(val))):,}")
    if not sinave.empty:
        q=quality_issues(sinave,year,week); qs=quality_summary(q); export_tables["Calidad resumen"]=qs; severe=int(q["Severidad"].isin(["Error","Revisar"]).sum()) if not q.empty else 0
        if severe: st.warning(f"🔎 POPIS detectó {severe:,} observaciones que conviene revisar.")
    if not suive.empty:
        cur=suive[(suive["Año"]==year)&(suive["SE"]<=week)]; fig=line_fig(cur,"SE",["Casos"],f"SUIVE · {year}"); st.pyplot(fig,use_container_width=True); register_fig("⬇️ PNG · SUIVE",f"SUIVE_{year}_SE{week}.png",fig,"r_su",images); plt.close(fig)
    if not sinave.empty:
        p=pathogen_summary(sinave,year,week); export_tables["Patógenos"]=p
        if not p.empty:
            fig=bar_fig(p.head(12),"Patógeno","Casos",f"Patógenos SINAVE ≤SE{week}",True); st.pyplot(fig,use_container_width=True); register_fig("⬇️ PNG · patógenos",f"Patogenos_{year}_SE{week}.png",fig,"r_pa",images); plt.close(fig)

with TABS[1]:
    st.subheader("Vigilancia convencional · SUIVE/SUAVE")
    if suive.empty: st.warning("No se detectó SUIVE local.")
    else:
        rows=[]
        for yy in sorted(suive["Año"].unique()):
            sm=suive_summary(suive,int(yy),week); rows.append({"Año":int(yy),f"Acumulado ≤SE{week}":sm["acumulado"],f"SE{week}":sm["semana"]})
        t=pd.DataFrame(rows); st.dataframe(t,hide_index=True,use_container_width=True); export_tables["SUIVE histórico"]=t; export_tables["SUIVE semanal"]=suive
        fig=bar_fig(t,"Año",f"SE{week}",f"Comparativo SUIVE · SE{week}"); st.pyplot(fig,use_container_width=True); register_fig("⬇️ PNG",f"SUIVE_comparativo_SE{week}.png",fig,"su_comp",images); plt.close(fig)

with TABS[2]:
    st.subheader("Vigilancia nominal y etiológica · SINAVE")
    if sinave.empty: st.warning("No se detectó SINAVE local.")
    else:
        sm=sinave_summary(sinave,year,week); m=st.columns(5)
        for col,(lab,val) in zip(m,[("Acumulado",sm["acumulado"]),(f"SE{week}",sm["semana"]),("Positivos",sm["positivos_acum"]),("Defunciones",sm["defunciones_acum"]),("Letalidad %",sm["letalidad"])]): col.metric(lab,f"{val:.2f}" if lab.endswith("%") else f"{int(val):,}")
        p=pathogen_summary(sinave,year,week); st.dataframe(p,hide_index=True,use_container_width=True)
        wk=sinave_weekly(sinave,year); export_tables["SINAVE semanal"]=wk; fig=line_fig(wk[wk.SE<=week],"SE",["Casos"],f"SINAVE · {year}"); st.pyplot(fig,use_container_width=True); register_fig("⬇️ PNG",f"SINAVE_{year}_SE{week}.png",fig,"si_curve",images); plt.close(fig)

with TABS[3]:
    st.subheader("SUIVE ↔ SINAVE"); st.caption("La razón entre sistemas es descriptiva; no equivale automáticamente a subregistro.")
    if suive.empty or sinave.empty: st.warning("Se necesitan ambas fuentes.")
    else:
        comp=build_comparison(suive,sinave,year,week); st.dataframe(comp,hide_index=True,use_container_width=True); export_tables["Comparador"]=comp
        fig=line_fig(comp,"SE",["SUIVE","SINAVE"],f"SUIVE vs SINAVE · {year}"); st.pyplot(fig,use_container_width=True); register_fig("⬇️ PNG",f"SUIVE_vs_SINAVE_{year}.png",fig,"compare",images); plt.close(fig)
        if comp[["SUIVE","SINAVE"]].std().gt(0).all():
            a,b=st.columns(2); a.metric("Pearson",f"{comp[['SUIVE','SINAVE']].corr('pearson').iloc[0,1]:.3f}"); b.metric("Spearman",f"{comp[['SUIVE','SINAVE']].corr('spearman').iloc[0,1]:.3f}")

with TABS[4]:
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
    else: st.warning("Fuente no disponible.")

with TABS[5]:
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
        if population.empty: st.info("Población municipal no cargada: se muestran conteos, no tasas.")

with TABS[6]:
    st.subheader("Población · edad, sexo y denominadores específicos")
    if population.empty:
        st.warning("Carga una vez el archivo Sonora.ProyeccionesPoblacionMunicipales2015-2030.xlsx desde 'Mantenimiento anual / inicial'.")
    elif year not in pop_years:
        st.warning(f"El archivo demográfico no contiene {year}. Años disponibles: {min(pop_years)}–{max(pop_years)}")
    else:
        py=population_for_year(population,year); municipalities=["Todos"]+sorted(py["Municipio"].dropna().astype(str).unique().tolist()); pm=st.selectbox("Municipio para perfil demográfico",municipalities,key="pop_municipality")
        profile=demographic_profile(population,year,pm)
        if profile:
            c=st.columns(6); metrics=[("Población",profile["Población"]),("Hombres",profile["Hombres"]),("Mujeres",profile["Mujeres"]),("% <5",profile["% <5"]),("% 65+",profile["% 65+"]),("Dependencia",profile["Razón dependencia"])]
            for col,(lab,val) in zip(c,metrics): col.metric(lab,f"{int(val):,}" if lab in ["Población","Hombres","Mujeres"] else f"{val:.1f}%")
            c2=st.columns(3); c2[0].metric("Razón H/M",f"{profile['Razón H/M']:.1f} hombres /100 mujeres"); c2[1].metric("Índice de envejecimiento",f"{profile['Índice envejecimiento']:.1f}"); c2[2].metric("% <15",f"{profile['% <15']:.1f}%")
        pyr=pyramid(population,year,pm); export_tables["Pirámide población"]=pyr
        fig=pyramid_fig(pyr,f"Pirámide poblacional · {pm} · {year}"); st.pyplot(fig,use_container_width=True); register_fig("⬇️ PNG · pirámide",f"Piramide_{pm}_{year}.png",fig,"pop_pyr",images); plt.close(fig)

        st.markdown("#### 🧬 Incidencia EDA específica por edad y sexo")
        if sinave.empty:
            st.info("SINAVE no disponible para calcular tasas específicas.")
        else:
            paths=["Todos los casos"]+sorted(c.replace("path_","") for c in sinave.columns if c.startswith("path_")); pp=st.selectbox("Evento / patógeno",paths,key="pop_pathogen")
            rates=age_sex_rates(sinave,population,year,week,pm,pp); export_tables["Incidencia edad sexo"]=rates
            if rates.empty: st.info("No hay combinación compatible de casos y denominadores para este filtro.")
            else:
                st.dataframe(rates,hide_index=True,use_container_width=True)
                rr=rates.copy(); rr["Estrato"]=rr["Grupo edad"].astype(str)+" · "+rr["Sexo"].astype(str)
                fig=bar_fig(rr.sort_values("Incidencia /100k").tail(30),"Estrato","Incidencia /100k",f"Incidencia específica · {pp} · {pm}",True); st.pyplot(fig,use_container_width=True); register_fig("⬇️ PNG · incidencia edad/sexo",f"Incidencia_Edad_Sexo_{year}_{pm}.png",fig,"pop_rates",images); plt.close(fig)
        export_tables["Población normalizada"]=py

with TABS[7]:
    st.subheader("Mortalidad y letalidad")
    if not sinave.empty:
        years=sorted(pd.to_numeric(sinave.epi_year,errors="coerce").dropna().astype(int).unique()); rows=[]
        for yy in years:
            sm=sinave_summary(sinave,int(yy),week); rows.append({"Año":int(yy),"Casos":sm["acumulado"],"Defunciones":sm["defunciones_acum"],"Letalidad %":sm["letalidad"]})
        mort=pd.DataFrame(rows); st.dataframe(mort,hide_index=True,use_container_width=True); export_tables["Mortalidad"]=mort; fig=bar_fig(mort,"Año","Defunciones",f"Defunciones ≤SE{week}"); st.pyplot(fig,use_container_width=True); register_fig("⬇️ PNG",f"Mortalidad_SE{week}.png",fig,"mort",images); plt.close(fig)

with TABS[8]:
    st.subheader("Indicadores normativos EDA"); st.caption("Los indicadores mensuales utilizan fecha de captura; el análisis semanal utiliza año epidemiológico.")
    if not sinave.empty:
        ind=nutrave_indicators(sinave,year,month); lab=laboratory_indicators(sinave,year,month); export_tables["Indicadores NuTraVE"]=ind; export_tables["Indicadores laboratorio"]=lab; st.markdown("#### 🏥 NuTraVE"); st.dataframe(ind,hide_index=True,use_container_width=True); st.markdown("#### 🔬 Laboratorio"); st.dataframe(lab,hide_index=True,use_container_width=True)

with TABS[9]:
    st.subheader("Calidad de datos y auditor normativo")
    if not sinave.empty:
        issues=quality_issues(sinave,year,week); qsum=quality_summary(issues); export_tables["Calidad detalle"]=issues; export_tables["Calidad resumen"]=qsum; st.markdown("#### 🧹 Bitácora de calidad"); st.dataframe(qsum,hide_index=True,use_container_width=True); severities=["Todos"]+sorted(issues.Severidad.unique().tolist()) if not issues.empty else ["Todos"]; sev=st.selectbox("Filtrar severidad",severities); shown=issues if sev=="Todos" else issues[issues.Severidad.eq(sev)]; st.dataframe(shown,hide_index=True,use_container_width=True,height=340); st.info("Cruce de año epidemiológico es informativo: SE52/53 al inicio de enero no se modifica; POPIS ajusta el año epidemiológico asociado."); st.markdown("#### 🔍 Definición operacional EDA"); audit=audit_operational_definitions(sinave,year,week); export_tables["Auditoría EDA"]=audit; review=audit[audit.Concordante.eq("Revisar")]; a,b=st.columns(2); a.metric("Evaluados",f"{len(audit):,}"); b.metric("Revisar clasificación",f"{len(review):,}"); st.dataframe(review if len(review) else audit.head(50),hide_index=True,use_container_width=True)

with TABS[10]:
    st.subheader("Centro de exportación")
    if not bundle.inventory.empty: export_tables["Fuentes"] = bundle.inventory
    if export_tables:
        excel=make_excel_report(export_tables); st.download_button("📊 Descargar reporte Excel",excel,file_name=f"POPIS_{BUILD}_{year}_SE{week}.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if images:
        st.download_button("🖼️ Descargar TODAS las gráficas (ZIP)",zip_images(images),file_name=f"POPIS_graficas_{year}_SE{week}.zip",mime="application/zip")
        for name,payload in images.items(): st.download_button(f"⬇️ {name}",payload,file_name=name,mime="image/png",key=f"all_{name}")

st.divider(); st.caption(f"POPIS {BUILD} · datos nominales locales · población por municipio/edad/sexo · no publicar bases SINAVE con identificadores personales")
