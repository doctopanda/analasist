from __future__ import annotations

import pandas as pd

from .io_utils import first_existing


def audit_base(base: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Genera resumen de calidad y detalle de incidencias sin alterar la base."""
    if base.empty:
        return pd.DataFrame([{"Indicador": "Registros", "Valor": 0}]), pd.DataFrame()

    issues: list[dict] = []
    n = len(base)
    folio_col = first_existing(base.columns, ["Folio", "FOLIO", "folio"])
    week_col = first_existing(base.columns, ["SemanaInicio", "Semana de inicio", "Semana"])
    mun_col = first_existing(base.columns, ["Mun_Res", "Municipio", "Municipio residencia"])
    final_col = first_existing(base.columns, ["Diag_Final", "Diagnóstico final", "Diagnostico final"])

    if folio_col:
        folio = base[folio_col].fillna("").astype(str).str.strip()
        missing = folio.eq("")
        duplicates = folio.ne("") & folio.duplicated(keep=False)
        for idx in base.index[missing]:
            issues.append({"Fila": int(idx) + 2, "Tipo": "Folio faltante", "Campo": folio_col, "Valor": ""})
        for idx in base.index[duplicates]:
            issues.append({"Fila": int(idx) + 2, "Tipo": "Folio duplicado", "Campo": folio_col, "Valor": folio.loc[idx]})
    else:
        missing = pd.Series(True, index=base.index)
        duplicates = pd.Series(False, index=base.index)

    invalid_week = pd.Series(False, index=base.index)
    if week_col:
        week = pd.to_numeric(base[week_col], errors="coerce")
        invalid_week = week.notna() & ~week.between(1, 53)
        for idx in base.index[invalid_week]:
            issues.append({"Fila": int(idx) + 2, "Tipo": "Semana fuera de rango", "Campo": week_col, "Valor": base.at[idx, week_col]})

    missing_mun = pd.Series(False, index=base.index)
    if mun_col:
        missing_mun = base[mun_col].fillna("").astype(str).str.strip().eq("")

    pending = pd.Series(False, index=base.index)
    if final_col:
        pending = base[final_col].fillna("").astype(str).str.strip().eq("")

    summary = pd.DataFrame([
        {"Indicador": "Registros", "Valor": n},
        {"Indicador": "Columnas", "Valor": len(base.columns)},
        {"Indicador": "Folio faltante", "Valor": int(missing.sum()) if folio_col else n},
        {"Indicador": "Registros en folios duplicados", "Valor": int(duplicates.sum())},
        {"Indicador": "Semana fuera de rango", "Valor": int(invalid_week.sum())},
        {"Indicador": "Municipio de residencia faltante", "Valor": int(missing_mun.sum())},
        {"Indicador": "Diagnóstico final pendiente", "Valor": int(pending.sum())},
    ])
    return summary, pd.DataFrame(issues)


def completeness_table(base: pd.DataFrame, max_columns: int = 80) -> pd.DataFrame:
    if base.empty:
        return pd.DataFrame(columns=["Campo", "Completitud %", "N completos", "N total"])
    rows = []
    for col in list(base.columns)[:max_columns]:
        s = base[col]
        complete = s.notna()
        if s.dtype == "object":
            complete &= s.astype(str).str.strip().ne("")
        n_complete = int(complete.sum())
        rows.append({
            "Campo": str(col),
            "Completitud %": n_complete / len(base) * 100,
            "N completos": n_complete,
            "N total": len(base),
        })
    return pd.DataFrame(rows).sort_values("Completitud %").reset_index(drop=True)
