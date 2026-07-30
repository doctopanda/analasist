from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from modulos.calidad import audit_base
from modulos.comparativo import compare_systems
from modulos.exportacion import excel_bytes, html_bytes, word_bytes
from modulos.indicadores import calculate_indicators
from modulos.runtime import load_runtime
from modulos.sinave import comparison_at_week, cutoff_base, observed_cutoff_week, pathogen_table, summary
from modulos.territorio import incidence_table, normalize_population


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera productos POPIS sin abrir Streamlit")
    parser.add_argument("--anio", type=int, default=None)
    parser.add_argument("--semana", type=int, default=None)
    parser.add_argument("--salida", default="salidas")
    args = parser.parse_args()

    ctx = load_runtime(process_updates=True)
    if not ctx.has_sinave:
        raise SystemExit("No hay fuente SINAVE disponible.")

    year = args.anio or ctx.current_year
    if year is None:
        raise SystemExit("No fue posible determinar el año de análisis.")
    detected = observed_cutoff_week(ctx.sinave, year) or 53
    cutoff = args.semana or detected
    if not 1 <= cutoff <= 53:
        raise SystemExit("--semana debe estar entre 1 y 53.")

    work = cutoff_base(ctx.sinave, year, cutoff)
    metrics = summary(ctx.sinave, year, cutoff)
    pathogens = pathogen_table(ctx.sinave, year, cutoff)
    history = comparison_at_week(ctx.sinave, cutoff)
    indicators = calculate_indicators(work)
    audit_summary, audit_issues = audit_base(work)
    pop = normalize_population(ctx.assets.population_file, year) if ctx.assets.population_file else None
    incidence = incidence_table(work, pop, 100000)

    tables = {
        "Resumen": pd.DataFrame([{"Indicador": k, "Valor": v} for k, v in metrics.items()]),
        "Patogenos": pathogens,
        "Comparativo_SE": history,
        "Incidencia_municipal": incidence,
        "Indicadores_normativos": indicators,
        "Calidad": audit_summary,
        "Incidencias_QA": audit_issues,
        "SINAVE_corte": work,
    }
    if ctx.has_suive and year in set(ctx.suive["Año"].astype(int)):
        weekly, accum = compare_systems(ctx.sinave, ctx.suive, cutoff, year)
        tables["SINAVE_vs_SUIVE"] = weekly
        tables["Comparativo_acumulado"] = accum

    output_dir = Path(args.salida)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"POPIS_{year}_SE{cutoff}"
    (output_dir / f"{stem}.xlsx").write_bytes(excel_bytes(tables))
    (output_dir / f"{stem}.docx").write_bytes(word_bytes(
        f"POPIS · Informe epidemiológico EDA · {year} · SE{cutoff}",
        {k: v for k, v in tables.items() if k != "SINAVE_corte"},
    ))
    (output_dir / f"{stem}.html").write_bytes(html_bytes(stem, {k: v for k, v in tables.items() if k != "SINAVE_corte"}))
    print(f"Productos generados en: {output_dir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
