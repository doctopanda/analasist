"""POPIS 4.3: interfaz 4.2 + módulo multipágina de focos espaciales."""
from pathlib import Path

app = Path(__file__).with_name("app_v42.py")
text = app.read_text(encoding="utf-8")
text = text.replace('BUILD = "4.2.0-pop"', 'BUILD = "4.3.0-spatial"')
text = text.replace('SUIVE + SINAVE + demografía + indicadores + territorio · Sonora', 'SUIVE + SINAVE + demografía + territorio + focos espaciales · Sonora')
code = compile(text, str(app), "exec")
exec(code, {"__name__":"__main__","__file__":str(app)})
