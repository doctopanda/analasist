"""API estable para la página Focos Espaciales de POPIS 4.6.2.

La primera implementación del motor espacial expuso primitivas como
``spatial_clusters`` y ``grid_counts`` mientras la página multipágina esperaba
``detect_clusters`` y ``grid_concentration``. Este módulo fija ese contrato sin
acoplar la interfaz a detalles internos.
"""
from __future__ import annotations

import math
import unicodedata
import re

import numpy as np
import pandas as pd

from popis_core_patch import canonical_municipality
from popis_spatial import (
    address_table,
    district_for_municipality,
    grid_counts,
    haversine_km,
    merge_coordinates,
    pending_geocoding_export,
    save_exact_geocodes,
)


def _norm(value: object) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", text.strip()).upper()


def coverage(points: pd.DataFrame) -> pd.DataFrame:
    """Resume cobertura y precisión de geolocalización de los casos filtrados."""
    cols = ["Precisión", "Casos", "Porcentaje", "Uso recomendado"]
    if points is None or points.empty:
        return pd.DataFrame(columns=cols)
    precision = points.get("Precisión", pd.Series("Sin coordenada", index=points.index)).fillna("Sin coordenada").astype(str)
    counts = precision.value_counts(dropna=False)
    total = int(counts.sum())
    rows = []
    for name, n in counts.items():
        exact = str(name).lower().startswith("exacta")
        rows.append({
            "Precisión": str(name),
            "Casos": int(n),
            "Porcentaje": round((int(n) / total * 100.0) if total else 0.0, 1),
            "Uso recomendado": "Conglomerados + mapa" if exact else "Contexto territorial; no inferir domicilio",
        })
    return pd.DataFrame(rows, columns=cols)


def _source_column(df: pd.DataFrame, *names: str):
    lookup = {_norm(c): c for c in df.columns}
    for name in names:
        hit = lookup.get(_norm(name))
        if hit is not None:
            return hit
    return None


def _copy_context(points: pd.DataFrame, source: pd.DataFrame) -> pd.DataFrame:
    """Añade variables epidemiológicas al resultado de geocodificación conservando índices."""
    out = points.copy()
    aliases = {
        "onset_date": ("onset_date", "Fecha_Inicio", "Fecha Inicio"),
        "epi_year": ("epi_year", "Año", "Anio"),
        "epi_week": ("epi_week", "SemanaInicio", "Semana"),
    }
    for target, names in aliases.items():
        c = _source_column(source, *names)
        if c is not None:
            out[target] = source.loc[out.index, c]
    out["Distrito"] = out["Municipio"].map(district_for_municipality)
    return out


def spatial_subset(
    sinave: pd.DataFrame,
    year: int,
    week_start: int,
    week_end: int,
    district: str = "Todos",
    municipality: str = "Todos",
    pathogen: str = "Todos los casos",
) -> pd.DataFrame:
    """Filtra SINAVE y devuelve solamente casos con coordenadas utilizables.

    Los centroides INEGI se conservan como contexto. La página decide si un
    análisis debe usar exclusivamente coordenadas exactas.
    """
    if sinave is None or sinave.empty:
        return pd.DataFrame()
    x = sinave.copy()

    ycol = _source_column(x, "epi_year", "year", "Año")
    wcol = _source_column(x, "epi_week", "SemanaInicio", "SE", "Semana")
    if ycol is not None:
        x = x[pd.to_numeric(x[ycol], errors="coerce").eq(int(year))]
    if wcol is not None:
        weeks = pd.to_numeric(x[wcol], errors="coerce")
        x = x[weeks.between(int(week_start), int(week_end))]

    resident = _source_column(x, "sonora_resident")
    if resident is not None:
        r = x[resident]
        if pd.api.types.is_bool_dtype(r):
            x = x[r.fillna(False)]

    mcol = _source_column(x, "municipality", "Mun_Res", "Municipio_Residencia", "Municipio")
    if mcol is not None:
        canon = x[mcol].map(canonical_municipality)
        if municipality and municipality != "Todos":
            target = canonical_municipality(municipality)
            x = x[canon.eq(target)]
            canon = canon.loc[x.index]
        if district and district != "Todos":
            d = canon.map(district_for_municipality)
            x = x[d.eq(district)]

    if pathogen and pathogen != "Todos los casos":
        requested = _norm(pathogen)
        pcols = [c for c in x.columns if str(c).startswith("path_")]
        match = next((c for c in pcols if _norm(str(c).replace("path_", "", 1)) == requested), None)
        if match is not None:
            vals = x[match]
            if pd.api.types.is_bool_dtype(vals):
                x = x[vals.fillna(False)]
            else:
                x = x[pd.to_numeric(vals, errors="coerce").fillna(0).gt(0) | vals.astype(str).str.upper().isin({"TRUE","POSITIVO","SI","SÍ"})]
        else:
            return pd.DataFrame()

    if x.empty:
        return pd.DataFrame()

    points = merge_coordinates(x, use_inegi_fallback=True)
    points = _copy_context(points, x)
    points["Latitud"] = pd.to_numeric(points.get("Latitud"), errors="coerce")
    points["Longitud"] = pd.to_numeric(points.get("Longitud"), errors="coerce")
    return points.dropna(subset=["Latitud", "Longitud"]).copy()


def _signal(n: int, min_cases: int) -> str:
    if n >= max(10, min_cases * 3):
        return "Alta"
    if n >= max(5, min_cases * 2):
        return "Alerta"
    return "Vigilar"


def detect_clusters(
    points: pd.DataFrame,
    radius_km: float = 1.0,
    min_cases: int = 3,
    max_days: int = 7,
    exact_only: bool = True,
):
    """Detecta componentes espacio-temporales y devuelve puntos + resumen.

    Es una señal exploratoria, no una confirmación normativa de brote.
    """
    empty_summary = pd.DataFrame(columns=[
        "Cluster", "Casos", "Inicio", "Fin", "Latitud centro", "Longitud centro",
        "Distrito", "Municipio", "Señal", "Radio usado km",
    ])
    if points is None or points.empty:
        return pd.DataFrame(), empty_summary

    x = points.copy()
    if exact_only and "Precisión" in x:
        x = x[x["Precisión"].astype(str).str.startswith("Exacta", na=False)]
    x["Latitud"] = pd.to_numeric(x.get("Latitud"), errors="coerce")
    x["Longitud"] = pd.to_numeric(x.get("Longitud"), errors="coerce")
    x = x.dropna(subset=["Latitud", "Longitud"]).copy()
    if x.empty:
        return x, empty_summary

    if "onset_date" in x:
        x["_date"] = pd.to_datetime(x["onset_date"], errors="coerce", dayfirst=True)
    else:
        x["_date"] = pd.NaT

    idx = list(x.index)
    adjacency = {i: set() for i in idx}
    for pos, i in enumerate(idx):
        for j in idx[pos + 1:]:
            di, dj = x.at[i, "_date"], x.at[j, "_date"]
            if pd.notna(di) and pd.notna(dj) and abs((di - dj).days) > int(max_days):
                continue
            if haversine_km(
                float(x.at[i, "Latitud"]), float(x.at[i, "Longitud"]),
                float(x.at[j, "Latitud"]), float(x.at[j, "Longitud"]),
            ) <= float(radius_km):
                adjacency[i].add(j)
                adjacency[j].add(i)

    seen, rows, memberships = set(), [], {}
    cid = 0
    for i in idx:
        if i in seen:
            continue
        stack, component = [i], []
        while stack:
            q = stack.pop()
            if q in seen:
                continue
            seen.add(q)
            component.append(q)
            stack.extend(adjacency[q] - seen)
        if len(component) < int(min_cases):
            continue
        cid += 1
        label = f"C{cid:02d}"
        sub = x.loc[component]
        for member in component:
            memberships[member] = label
        dates = sub["_date"].dropna()
        municipality = sub["Municipio"].mode().iloc[0] if "Municipio" in sub and not sub["Municipio"].dropna().empty else ""
        district = sub["Distrito"].mode().iloc[0] if "Distrito" in sub and not sub["Distrito"].dropna().empty else district_for_municipality(municipality)
        n = int(len(sub))
        rows.append({
            "Cluster": label,
            "Casos": n,
            "Inicio": dates.min() if not dates.empty else pd.NaT,
            "Fin": dates.max() if not dates.empty else pd.NaT,
            "Latitud centro": float(sub["Latitud"].mean()),
            "Longitud centro": float(sub["Longitud"].mean()),
            "Distrito": district,
            "Municipio": municipality,
            "Señal": _signal(n, int(min_cases)),
            "Radio usado km": float(radius_km),
        })

    x["Cluster"] = pd.Series(memberships)
    summary = pd.DataFrame(rows, columns=empty_summary.columns)
    if not summary.empty:
        order = pd.Categorical(summary["Señal"], categories=["Alta", "Alerta", "Vigilar"], ordered=True)
        summary = summary.assign(_order=order).sort_values(["_order", "Casos"], ascending=[True, False]).drop(columns="_order")
    return x.drop(columns=["_date"], errors="ignore"), summary


def grid_concentration(points: pd.DataFrame, cell_km: float = 1.0) -> pd.DataFrame:
    """Compatibilidad con la interfaz; agrega tamaño de celda al resumen base."""
    grid = grid_counts(points, cell_km=float(cell_km))
    if grid is None or grid.empty:
        return pd.DataFrame(columns=["Casos", "Latitud", "Longitud", "Celda km"])
    out = grid.copy()
    out["Celda km"] = float(cell_km)
    preferred = [c for c in ["Casos", "Latitud", "Longitud", "Celda km", "gx", "gy"] if c in out.columns]
    return out[preferred]


__all__ = [
    "address_table", "coverage", "detect_clusters", "grid_concentration",
    "pending_geocoding_export", "save_exact_geocodes", "spatial_subset",
]
