from __future__ import annotations

import io
import json
import tempfile
import zipfile
from pathlib import Path

import pandas as pd

from modulos.calidad import audit_base
from modulos.canal_endemico import attach_current, build_endemic_channel, pathogen_weekly_series
from modulos.comparativo import compare_systems
from modulos.exportacion import excel_bytes, graphics_zip, html_bytes, word_bytes
from modulos.indicadores import calculate_indicators
from modulos.io_utils import classify_file, discover_assets, ensure_structure, process_inbox
from modulos.runtime import load_runtime
from modulos.sinave import load_bundle, pathogen_table, summary, weekly_series
from modulos.suive import load_suive
from modulos.territorio import build_centroid_map, incidence_table, map_html_bytes, normalize_population


def write_tsv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, sep="\t", index=False, encoding="latin-1")


def make_rows(year: int, weeks: range, prefix: str) -> list[dict]:
    rows = []
    first_week = min(weeks)
    for week in weeks:
        municipality = "HERMOSILLO" if week % 2 else "CAJEME"
        rows.append({
            "Fec_captura": f"15/06/{year}", "Fec_Prim_Contacto": f"14/06/{year}",
            "Fec_Dx_Final": f"20/06/{year}", "Fecha_Inicio": f"12/06/{year}",
            "SemanaInicio": week, "Sem_Notif": week, "Folio": f"{prefix}-{week}",
            "Mun_Res": municipality, "CVE_EDO_RES": 26,
            "CVE_MPO_RES": 30 if municipality == "HERMOSILLO" else 18,
            "Diag_Prob": "COLERA" if week == first_week else "SINDROME DIARREICO",
            "Diag_Final": "POSITIVO" if week % 3 == 0 else "NEGATIVO A ENTEROPATOGENOS",
            "Salmonella": "Positivo" if week % 3 == 0 else "",
            "Shigella": "Positivo" if week % 5 == 0 else "", "Rotavirus": "",
            "VibrioCholerae": "Positivo" if week == first_week else "",
            "SerogrupoVibrioCholerae": "NO O1" if week == first_week else "",
            "VibrioParahaemolyticus": "", "Patotipo_EColi_InDRE": "",
            "Rotavirus_InDRE": "", "OtroVirus_InDRE": "",
            "MuestraVibrio": "Hisopo rectal" if week == first_week else "",
            "FecRecepLab": f"15/06/{year}" if week == first_week else "",
            "Monitoreo": "Si" if week % 10 == 0 else "No",
        })
    return rows


def write_historical_suive_book(path: Path) -> None:
    rows = [["Año"] + list(range(1, 54))]
    for year in range(2018, 2027):
        rows.append([year] + [1000 + (year - 2018) * 10 + week for week in range(1, 54)])
    raw = pd.DataFrame(rows)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        raw.to_excel(writer, sheet_name="SUIVE", index=False, header=False)
        pd.DataFrame({"SINAVE": []}).to_excel(writer, sheet_name="SINAVE", index=False)


def write_population_book(path: Path) -> None:
    rows = []
    specs = [("26030", "HERMOSILLO", 1000000), ("26018", "CAJEME", 450000), ("26043", "NOGALES", 280000)]
    for clave, mun, total in specs:
        parts = [total * 0.24, total * 0.26, total * 0.25, total * 0.25]
        for sexo, edad, pob in [("Hombres", "00-04", parts[0]), ("Hombres", "05-09", parts[1]), ("Mujeres", "00-04", parts[2]), ("Mujeres", "05-09", parts[3])]:
            rows.append({"CLAVE": clave, "CLAVE_ENT": 26, "NOM_ENT": "Sonora", "MUN": mun, "SEXO": sexo, "AÑO": 2026, "EDAD_QUIN": edad, "POB": pob})
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame({"Portada": ["Proyecciones municipales"]}).to_excel(writer, sheet_name="README", index=False)
        pd.DataFrame(rows).to_excel(writer, sheet_name="Sonora", index=False)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "POPIS"
        ensure_structure(root)
        (root / "app.py").write_text("# synthetic\n", encoding="utf-8")
        for year in [2022, 2023, 2024, 2025]:
            write_tsv(root / "data/historicos" / f"Diarreas_{year}.xls", make_rows(year, range(1, 11), str(year)[2:]))
        current_rows = make_rows(2026, range(1, 13), "26") + make_rows(2026, range(53, 54), "26F")
        write_tsv(root / "data/actual" / "Diarreas_actual.xls", current_rows)

        suive_path = root / "data/suive" / "Canal endemico EDAs_SUIVE_SINAVE (1)(2).xlsx"
        write_historical_suive_book(suive_path)
        assert classify_file(suive_path) == "suive"

        pop_path = root / "data/poblacion" / "Sonora.ProyeccionesPoblacionMunicipales2015-2030(2).xlsx"
        write_population_book(pop_path)
        assert classify_file(pop_path) == "poblacion"

        geo = {"type": "FeatureCollection", "features": [
            {"type": "Feature", "properties": {"NOMGEO": "HERMOSILLO"}, "geometry": {"type": "Polygon", "coordinates": [[[-111.2, 28.8], [-110.7, 28.8], [-110.7, 29.3], [-111.2, 29.3], [-111.2, 28.8]]]}},
            {"type": "Feature", "properties": {"NOMGEO": "CAJEME"}, "geometry": {"type": "Polygon", "coordinates": [[[-110.2, 27.2], [-109.6, 27.2], [-109.6, 27.8], [-110.2, 27.8], [-110.2, 27.2]]]}},
            {"type": "Feature", "properties": {"NOMGEO": "NOGALES"}, "geometry": {"type": "Polygon", "coordinates": [[[-111.2, 31.1], [-110.7, 31.1], [-110.7, 31.5], [-111.2, 31.5], [-111.2, 31.1]]]}},
        ]}
        (root / "data/geografia/municipios_sonora.geojson").write_text(json.dumps(geo), encoding="utf-8")

        assets = discover_assets(root)
        assert sorted(assets.sinave_by_year) == [2022, 2023, 2024, 2025, 2026]
        assert assets.current_year == 2026 and assets.cutoff_week == 12
        assert any("SE53" in warning for warning in assets.warnings)
        assert assets.suive_file.name.startswith("Canal endemico")
        assert assets.population_file.name.startswith("Sonora.Proyecciones")

        base = load_bundle(assets)
        assert len(base) == 53 and base["Patógeno identificado"].any()
        s = summary(base, 2026, 12)
        assert s["casos_acumulados"] == 12
        assert not pathogen_table(base, 2026, 12).empty

        suive = load_suive(assets.suive_file)
        assert len(suive) == 9 * 53
        sin_series = weekly_series(base)
        current_series = sin_series[sin_series["Año"].eq(2026)]
        assert int(current_series["Semana"].max()) == 12
        assert not current_series["Semana"].gt(12).any()

        channel, years = build_endemic_channel(suive, current_year=2026, historical_years=[2018, 2019, 2022, 2023, 2024, 2025])
        assert len(channel) == 53 and len(years) == 6
        attached = attach_current(channel, sin_series, 2026, 12)
        assert "Casos 2026" in attached.columns
        assert attached.loc[attached["Semana"].gt(12), "Casos 2026"].isna().all()
        pseries = pathogen_weekly_series(base, "Salmonella")
        current_pathogen = pseries[pseries["Año"].eq(2026)]
        assert int(current_pathogen["Semana"].max()) == 12

        weekly_cmp, accum_cmp = compare_systems(base, suive, 12, 2026)
        assert len(weekly_cmp) == 12 and "Razón de registro SINAVE/SUIVE" in weekly_cmp.columns
        assert "Razón acumulada SINAVE/SUIVE" in accum_cmp.columns

        pop = normalize_population(assets.population_file, 2026)
        print("DEBUG_POP=", repr(pop))
        assert pop is not None and len(pop) == 3
        totals = dict(zip(pop["Municipio"], pop["Poblacion"]))
        assert round(float(totals["HERMOSILLO"])) == 1000000
        assert round(float(totals["CAJEME"])) == 450000
        assert round(float(totals["NOGALES"])) == 280000

        incidence = incidence_table(base[(base["Año"].eq(2026)) & pd.to_numeric(base["SemanaInicio"], errors="coerce").le(12)], pop, 100000)
        assert set(incidence["Municipio"]) == {"HERMOSILLO", "CAJEME", "NOGALES"}
        assert int(incidence["Casos"].sum()) == 12
        map_obj = build_centroid_map(base[(base["Año"].eq(2026)) & pd.to_numeric(base["SemanaInicio"], errors="coerce").le(12)], geo)
        assert len(map_html_bytes(map_obj)) > 5000

        ind = calculate_indicators(base[(base["Año"].eq(2026)) & pd.to_numeric(base["SemanaInicio"], errors="coerce").le(12)], monthly_vibrio_target=50)
        assert len(ind) >= 8 and {"Numerador", "Denominador", "Resultado %", "Meta %"}.issubset(ind.columns)
        qa, issues = audit_base(base)
        assert int(qa.loc[qa["Indicador"].eq("Registros"), "Valor"].iloc[0]) == len(base)
        tables = {"Resumen": pd.DataFrame([s]), "Patogenos": pathogen_table(base, 2026, 12), "Incidencia": incidence, "Indicadores": ind}
        assert len(excel_bytes(tables)) > 3000
        assert len(word_bytes("POPIS test", tables)) > 10000
        assert len(html_bytes("POPIS test", tables)) > 1000
        graph_zip = graphics_zip(sin_series, suive, tables["Patogenos"])
        assert len(graph_zip) > 1000
        with zipfile.ZipFile(io.BytesIO(graph_zip)) as zf:
            assert "SINAVE_series_semanales.png" in zf.namelist()

        write_tsv(root / "data/entrada" / "Diarreas_2026_actualizada.xls", make_rows(2026, range(1, 14), "26N"))
        messages = process_inbox(root)
        assert any("Integrado sinave" in m for m in messages)
        refreshed = discover_assets(root)
        assert refreshed.cutoff_week == 13
        assert any((root / "data/backups").rglob("Diarreas_actual.xls"))
        ctx = load_runtime(root, process_updates=False, allow_geo_download=False)
        assert ctx.has_sinave and ctx.has_suive and ctx.geojson and ctx.population is not None
        assert ctx.cutoff_week == 13
        print("POPIS 4.6.2 CAVERNA COMPLETO R3: SELFTEST OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
