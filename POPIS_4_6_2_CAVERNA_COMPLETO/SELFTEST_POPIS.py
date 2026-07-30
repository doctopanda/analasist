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
from modulos.redve import death_metrics, link_redve_deaths, load_redve
from modulos.runtime import load_runtime
from modulos.sinave import comparison_at_week, death_comparison_by_year, load_bundle, pathogen_table, summary, weekly_series
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
            "Primer_Apellido": f"APELLIDO{week}", "Segundo_Apellido": "PRUEBA",
            "Nombres": f"PERSONA{week}", "CURP": "", "Sexo": "Masculino",
            "Edad_Años": 30, "Edad_Meses": 0,
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
            "FecDefuncion": "", "MotivoDeEgreso": "",
        })
    return rows


def write_historical_suive_book(path: Path) -> None:
    rows = [["Año"] + list(range(1, 54))]
    for year in range(2018, 2027):
        rows.append([year] + [1000 + (year - 2018) * 10 + week for week in range(1, 54)])
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame(rows).to_excel(writer, sheet_name="SUIVE", index=False, header=False)
        pd.DataFrame({"SINAVE": []}).to_excel(writer, sheet_name="SINAVE", index=False)


def write_population_book(path: Path) -> None:
    rows = []
    for clave, mun, total in [
        ("26030", "HERMOSILLO", 1000000),
        ("26018", "CAJEME", 450000),
        ("26043", "NOGALES", 280000),
    ]:
        parts = [total * 0.24, total * 0.26, total * 0.25, total * 0.25]
        for sexo, edad, pob in [
            ("Hombres", "00-04", parts[0]), ("Hombres", "05-09", parts[1]),
            ("Mujeres", "00-04", parts[2]), ("Mujeres", "05-09", parts[3]),
        ]:
            rows.append({
                "CLAVE": clave, "CLAVE_ENT": 26, "NOM_ENT": "Sonora", "MUN": mun,
                "SEXO": sexo, "AÑO": 2026, "EDAD_QUIN": edad, "POB": pob,
            })
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame({"Portada": ["Proyecciones municipales"]}).to_excel(writer, sheet_name="README", index=False)
        pd.DataFrame(rows).to_excel(writer, sheet_name="Sonora", index=False)


def write_redve(path: Path) -> None:
    rows = [
        {
            "DEFFOLIO": "REDVE-DIRECTA", "DEFFECH_DEF": "10/02/2026",
            "DEFAPEPATER": "DIRECTA", "DEFAPEMATER": "PRUEBA", "DEFNOMBRE": "PERSONA UNO",
            "DEFCURP": "AAAA000101HSRXXX01", "DEFSEXO": "1", "DEFEDAD": "30", "DEFCLV_EDA": "3",
            "DEFCAUSABAS": "A419", "CAUSASUJVIGCVE": "9999", "CAUSASUJVIGDES": "OTRAS CAUSAS",
            "DEFUNCION_DICTAMINADA": "SI", "DEFUNCION_PROCESO_DICTAMINACION": "NO",
            "FECHA_DICTAMINACION": "15/02/2026", "OBSERVACIONES": "Caso con folio SINAVE 26-1",
        },
        {
            "DEFFOLIO": "REDVE-RECUPERADA", "DEFFECH_DEF": "20/03/2026",
            "DEFAPEPATER": "RECUPERADA", "DEFAPEMATER": "PRUEBA", "DEFNOMBRE": "PERSONA DOS",
            "DEFCURP": "BBBB000202MSRXXX02", "DEFSEXO": "2", "DEFEDAD": "30", "DEFCLV_EDA": "3",
            "DEFCAUSABAS": "A099", "CAUSASUJVIGCVE": "A099", "CAUSASUJVIGDES": "GASTROENTERITIS",
            "DEFUNCION_DICTAMINADA": "SI", "DEFUNCION_PROCESO_DICTAMINACION": "NO",
            "FECHA_DICTAMINACION": "25/03/2026", "OBSERVACIONES": "Vinculada por CURP a SINAVE",
        },
    ]
    write_tsv(path, rows)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "POPIS"
        ensure_structure(root)
        (root / "app.py").write_text("# synthetic\n", encoding="utf-8")

        for year in [2022, 2023, 2024, 2025]:
            write_tsv(root / "data/historicos" / f"Diarreas_{year}.xls", make_rows(year, range(1, 11), str(year)[2:]))

        current_rows = make_rows(2026, range(1, 13), "26")
        current_rows[0].update({
            "Primer_Apellido": "DIRECTA", "Segundo_Apellido": "PRUEBA", "Nombres": "PERSONA UNO",
            "CURP": "AAAA000101HSRXXX01", "FecDefuncion": "10/02/2026", "MotivoDeEgreso": "DEFUNCION",
        })
        current_rows[1].update({
            "Primer_Apellido": "RECUPERADA", "Segundo_Apellido": "PRUEBA", "Nombres": "PERSONA DOS",
            "CURP": "BBBB000202MSRXXX02", "Sexo": "Femenino",
        })
        write_tsv(
            root / "data/actual" / "Diarreas_actual.xls",
            current_rows + make_rows(2026, range(53, 54), "26F"),
        )

        suive_path = root / "data/suive" / "Canal endemico EDAs_SUIVE_SINAVE (1)(2).xlsx"
        write_historical_suive_book(suive_path)
        assert classify_file(suive_path) == "suive"

        pop_path = root / "data/poblacion" / "Sonora.ProyeccionesPoblacionMunicipales2015-2030(2).xlsx"
        write_population_book(pop_path)
        assert classify_file(pop_path) == "poblacion"

        redve_path = root / "data/redve" / "REDVE_BASE_ESTATAL_2026-07-15.xls"
        write_redve(redve_path)
        assert classify_file(redve_path) == "redve"

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
        assert assets.suive_file == suive_path and assets.population_file == pop_path
        assert assets.redve_file == redve_path

        base = load_bundle(assets)
        redve = load_redve(assets.redve_file)
        linked, links = link_redve_deaths(base, redve)
        assert len(links) == 2
        metrics = summary(linked, 2026, 12)
        assert metrics["casos_acumulados"] == 12
        assert metrics["defunciones_sinave_con_fecha"] == 1
        assert metrics["defunciones_sinave"] == 1
        assert metrics["defunciones_redve_recuperadas"] == 1
        assert metrics["defunciones_integradas"] == 2
        assert metrics["muertes_eda_dictaminadas_redve"] == 1
        assert death_metrics(linked[linked["Año"].eq(2026)])["defunciones_integradas"] == 2

        comparison = comparison_at_week(linked, 10)
        assert f"Casos SE10" in comparison.columns and f"Acumulado ≤ SE10" in comparison.columns
        assert int(comparison.loc[comparison["Año"].eq(2026), "Casos SE10"].iloc[0]) == 1
        assert int(comparison.loc[comparison["Año"].eq(2026), "Acumulado ≤ SE10"].iloc[0]) == 10
        deaths_by_year = death_comparison_by_year(linked, 12)
        assert int(deaths_by_year.loc[deaths_by_year["Año"].eq(2026), "Integradas"].iloc[0]) == 2

        suive = load_suive(assets.suive_file)
        assert len(suive) == 9 * 53
        sin_series = weekly_series(linked)
        assert int(sin_series[sin_series["Año"].eq(2026)]["Semana"].max()) == 12

        channel, years = build_endemic_channel(
            suive, current_year=2026,
            historical_years=[2018, 2019, 2022, 2023, 2024, 2025],
        )
        assert len(channel) == 53 and len(years) == 6
        attached = attach_current(channel, sin_series, 2026, 12)
        assert attached.loc[attached["Semana"].gt(12), "Casos 2026"].isna().all()
        pseries = pathogen_weekly_series(linked, "Salmonella")
        assert int(pseries[pseries["Año"].eq(2026)]["Semana"].max()) == 12

        weekly_cmp, accum_cmp = compare_systems(linked, suive, 12, 2026)
        assert len(weekly_cmp) == 12 and "Razón de registro SINAVE/SUIVE" in weekly_cmp.columns
        assert "Razón acumulada SINAVE/SUIVE" in accum_cmp.columns

        pop = normalize_population(assets.population_file, 2026)
        assert pop is not None and len(pop) == 3
        totals = dict(zip(pop["Municipio"], pop["Poblacion"]))
        assert round(float(totals["HERMOSILLO"])) == 1000000
        assert round(float(totals["CAJEME"])) == 450000

        current = linked[(linked["Año"].eq(2026)) & pd.to_numeric(linked["SemanaInicio"], errors="coerce").le(12)]
        incidence = incidence_table(current, pop, 100000)
        assert int(incidence["Casos"].sum()) == 12
        assert len(map_html_bytes(build_centroid_map(current, geo))) > 5000

        indicators = calculate_indicators(current, monthly_vibrio_target=50)
        assert len(indicators) >= 8
        qa, _ = audit_base(linked)
        assert int(qa.loc[qa["Indicador"].eq("Registros"), "Valor"].iloc[0]) == len(linked)

        tables = {
            "Resumen": pd.DataFrame([metrics]),
            "Patogenos": pathogen_table(linked, 2026, 12),
            "Comparativo_SE": comparison,
            "Defunciones": deaths_by_year,
            "Incidencia": incidence,
            "Indicadores": indicators,
        }
        assert len(excel_bytes(tables)) > 3000
        assert len(word_bytes("POPIS test", tables)) > 10000
        assert len(html_bytes("POPIS test", tables)) > 1000
        with zipfile.ZipFile(io.BytesIO(graphics_zip(sin_series, suive, tables["Patogenos"]))) as zf:
            assert "SINAVE_series_semanales.png" in zf.namelist()

        # Bandeja: reconoce y respalda tanto SINAVE como REDVE.
        write_tsv(root / "data/entrada" / "Diarreas_2026_actualizada.xls", make_rows(2026, range(1, 14), "26N"))
        write_redve(root / "data/entrada" / "REDVE_BASE_ESTATAL_actualizada.xls")
        inbox_messages = process_inbox(root)
        assert any("Integrado sinave" in message for message in inbox_messages)
        assert any("Integrado redve" in message for message in inbox_messages)
        refreshed = discover_assets(root)
        assert refreshed.cutoff_week == 13 and refreshed.redve_file is not None

        ctx = load_runtime(root, process_updates=False, allow_geo_download=False)
        assert ctx.has_sinave and ctx.has_suive and ctx.has_redve and ctx.geojson and ctx.population is not None
        assert ctx.cutoff_week == 13
        print("POPIS 4.6.2 CAVERNA COMPLETO R4 REDVE: SELFTEST OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
