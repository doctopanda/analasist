"""POPIS 4.3.1: interfaz 4.2 + focos espaciales + arranque robusto sin años cargados."""
from pathlib import Path

app = Path(__file__).with_name("app_v42.py")
text = app.read_text(encoding="utf-8")
text = text.replace('BUILD = "4.2.0-pop"', 'BUILD = "4.3.1-spatial"')
text = text.replace(
    'SUIVE + SINAVE + demografía + indicadores + territorio · Sonora',
    'SUIVE + SINAVE + demografía + territorio + focos espaciales · Sonora',
)

# Corrección defensiva del selector de año.
# En 4.2/4.3, cuando no había ninguna fuente reconocida, las opciones visibles
# eran [2026] pero el índice se calculaba desde available_years=[] y quedaba -1.
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

code = compile(text, str(app), "exec")
exec(code, {"__name__": "__main__", "__file__": str(app)})
