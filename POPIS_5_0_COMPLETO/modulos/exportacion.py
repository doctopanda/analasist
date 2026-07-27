from __future__ import annotations

import io
import zipfile
from typing import Mapping

import matplotlib.pyplot as plt
import pandas as pd


def _png(fig) -> bytes:
    out = io.BytesIO()
    fig.savefig(out, format="png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    return out.getvalue()


def chart_weekly(weekly: pd.DataFrame) -> bytes:
    fig, ax = plt.subplots(figsize=(11, 5.5))
    for year, group in weekly.groupby("Año"):
        ax.plot(group["Semana"], group["Casos"], label=str(int(year)))
    ax.set_title("Casos por semana epidemiológica")
    ax.set_xlabel("Semana epidemiológica")
    ax.set_ylabel("Casos")
    ax.legend(ncol=3, fontsize=8)
    ax.grid(alpha=0.2)
    return _png(fig)


def chart_historical(table: pd.DataFrame, cutoff_week: int) -> bytes:
    col = f"Casos acumulados ≤ SE{cutoff_week}"
    fig, ax = plt.subplots(figsize=(8, 5))
    if col in table.columns:
        ax.bar(table["Año"].astype(str), table[col])
    ax.set_title(f"Casos acumulados al corte SE{cutoff_week}")
    ax.set_xlabel("Año")
    ax.set_ylabel("Casos")
    return _png(fig)


def chart_pathogens(table: pd.DataFrame, title: str = "Patógenos identificados") -> bytes:
    data = table.sort_values("Detecciones", ascending=True)
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.barh(data["Patógeno"], data["Detecciones"])
    ax.set_title(title)
    ax.set_xlabel("Detecciones")
    return _png(fig)


def chart_mortality(table: pd.DataFrame) -> bytes:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(table["Año"].astype(str), table["Defunciones registradas"])
    ax.set_title("Defunciones registradas por año al mismo corte")
    ax.set_xlabel("Año")
    ax.set_ylabel("Defunciones registradas")
    return _png(fig)


def graphics_zip(weekly: pd.DataFrame, historical: pd.DataFrame, pathogens: pd.DataFrame, mortality: pd.DataFrame, cutoff_week: int) -> bytes:
    files = {
        "01_casos_por_semana.png": chart_weekly(weekly),
        "02_acumulado_historico.png": chart_historical(historical, cutoff_week),
        "03_patogenos.png": chart_pathogens(pathogens),
        "04_mortalidad_registrada.png": chart_mortality(mortality),
    }
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, raw in files.items():
            z.writestr(name, raw)
    return out.getvalue()


def excel_report(sheets: Mapping[str, pd.DataFrame]) -> bytes:
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        for name, df in sheets.items():
            safe = str(name)[:31]
            df.to_excel(writer, sheet_name=safe, index=False)
            ws = writer.book[safe]
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions
            for cell in ws[1]:
                cell.font = cell.font.copy(bold=True)
            for col in ws.columns:
                values = [str(c.value or "") for c in col[:1000]]
                width = min(max([len(v) for v in values] + [10]) + 2, 45)
                ws.column_dimensions[col[0].column_letter].width = width
    return out.getvalue()
