from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

PATHOGENS = {
    "Salmonella": "Salmonella",
    "Shigella": "Shigella",
    "E. coli patógena": "EColi",
    "Rotavirus": "Rotavirus",
    "V. cholerae no O1": "VCholeraeNoO1",
    "V. parahaemolyticus": "VParahaemolyticus",
    "Norovirus": "Norovirus",
    "Astrovirus": "Astrovirus",
}


def _decode(raw: bytes) -> str:
    for enc in ("utf-8-sig", "latin-1", "cp1252"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("latin-1", errors="replace")


def read_table(source: str | Path | bytes, filename: str | None = None) -> pd.DataFrame:
    if isinstance(source, (str, Path)):
        p = Path(source)
        raw = p.read_bytes()
        filename = filename or p.name
    else:
        raw = source
    head = _decode(raw[:8192])
    suffix = Path(filename or "archivo.xls").suffix.lower()
    if "\t" in head:
        return pd.read_csv(io.StringIO(_decode(raw)), sep="\t", dtype=str, keep_default_na=False)
    if suffix in {".csv", ".txt"}:
        text = _decode(raw)
        sep = ";" if text[:4096].count(";") > text[:4096].count(",") else ","
        return pd.read_csv(io.StringIO(text), sep=sep, dtype=str, keep_default_na=False)
    engine = "xlrd" if suffix == ".xls" else "openpyxl"
    return pd.read_excel(io.BytesIO(raw), dtype=str, engine=engine).fillna("")


def s(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series([""] * len(df), index=df.index, dtype="object")
    return df[column].fillna("").astype(str).str.strip()


def positive(values: pd.Series) -> pd.Series:
    return values.fillna("").astype(str).str.strip().str.casefold().str.startswith("positivo")


def infer_year(df: pd.DataFrame) -> int:
    for col in ("Fec_captura", "Fecha_Inicio", "Fec_Primer_Contacto"):
        if col in df.columns:
            years = pd.to_datetime(df[col], dayfirst=True, errors="coerce").dt.year.dropna().astype(int)
            if not years.empty:
                return int(years.mode().iloc[0])
    raise ValueError("No fue posible identificar el año de la base SINAVE.")


def normalize_sinave(df: pd.DataFrame, source_name: str = "") -> pd.DataFrame:
    out = df.copy()
    year = infer_year(df)
    out["Año"] = year
    out["Folio_POPIS"] = s(df, "Folio")
    out["Fecha_Inicio_POPIS"] = pd.to_datetime(s(df, "Fecha_Inicio"), dayfirst=True, errors="coerce")
    out["SemanaInicio_POPIS"] = pd.to_numeric(s(df, "SemanaInicio"), errors="coerce").astype("Int64")
    out["SemanaNotif_POPIS"] = pd.to_numeric(s(df, "Sem_Notif"), errors="coerce").astype("Int64")
    out["Municipio_POPIS"] = s(df, "Mun_Res")
    out["Localidad_POPIS"] = s(df, "Loc_Res") if "Loc_Res" in df.columns else s(df, "Residencia_Actual")
    out["DiagFinal_POPIS"] = s(df, "Diag_Final")

    salmonella = positive(s(df, "Salmonella"))
    shigella = positive(s(df, "Shigella"))
    rotavirus = positive(s(df, "Rotavirus")) | positive(s(df, "Rotavirus_InDRE"))
    vpara = positive(s(df, "VibrioParahaemolyticus"))
    vch = positive(s(df, "VibrioCholerae"))
    sero = s(df, "SerogrupoVibrioCholerae").str.casefold()
    vchol_no_o1 = vch & sero.str.contains("no o1", regex=False)
    ecoli_type = s(df, "Patotipo_EColi_InDRE")
    ecoli = ecoli_type.ne("") & ~ecoli_type.str.casefold().str.contains("no pat", regex=False)
    virus = s(df, "OtroVirus_InDRE").str.casefold()
    norovirus = virus.str.contains("norovirus", regex=False)
    astrovirus = virus.str.contains("astrovirus", regex=False)

    flags = {
        "Salmonella": salmonella,
        "Shigella": shigella,
        "E. coli patógena": ecoli,
        "Rotavirus": rotavirus,
        "V. cholerae no O1": vchol_no_o1,
        "V. parahaemolyticus": vpara,
        "Norovirus": norovirus,
        "Astrovirus": astrovirus,
    }
    for label, mask in flags.items():
        out[label] = mask.astype(int)
    out["Patógenos identificados"] = [" | ".join(k for k, mask in flags.items() if bool(mask.loc[i])) for i in out.index]
    any_pos = out[list(flags)].sum(axis=1).gt(0)
    diag = out["DiagFinal_POPIS"].fillna("").astype(str).str.upper()
    status = pd.Series("Otro diagnóstico", index=out.index, dtype="object")
    status[diag.eq("")] = "Pendiente / sin diagnóstico final"
    status[diag.str.startswith("NEGATIVO")] = "Sin patógeno identificado"
    status[diag.str.contains("RECHAZ", regex=False)] = "Muestra rechazada / sin diagnóstico"
    status[any_pos] = "Patógeno identificado"
    out["EstadoResultado_POPIS"] = status
    out["DefuncionRegistrada_POPIS"] = pd.to_datetime(s(df, "FecDefuncion"), dayfirst=True, errors="coerce").notna().astype(int)
    out["ArchivoOrigen_POPIS"] = source_name
    return out.reset_index(drop=True)


def load_sinave(paths: Iterable[str | Path]) -> pd.DataFrame:
    frames = []
    for p in paths:
        path = Path(p)
        frame = read_table(path)
        frames.append(normalize_sinave(frame, path.name))
    if not frames:
        return pd.DataFrame()
    base = pd.concat(frames, ignore_index=True, sort=False)
    # Evita duplicar una misma descarga repetida del mismo año/folio cuando hay varias copias.
    key = base["Año"].astype(str) + "|" + base["Folio_POPIS"].astype(str)
    has_folio = base["Folio_POPIS"].astype(str).str.strip().ne("")
    keep = ~has_folio | ~key.duplicated(keep="last")
    return base.loc[keep].reset_index(drop=True)


def filter_cutoff(base: pd.DataFrame, year: int, cutoff_week: int, exact_week: bool = False) -> pd.DataFrame:
    weeks = pd.to_numeric(base["SemanaInicio_POPIS"], errors="coerce")
    mask = pd.to_numeric(base["Año"], errors="coerce").eq(int(year))
    mask &= weeks.eq(cutoff_week) if exact_week else weeks.between(1, cutoff_week, inclusive="both")
    return base.loc[mask].copy()


def summary(base: pd.DataFrame, year: int, cutoff_week: int) -> dict[str, Any]:
    cum = filter_cutoff(base, year, cutoff_week)
    week = filter_cutoff(base, year, cutoff_week, exact_week=True)
    return {
        "año": year,
        "semana": cutoff_week,
        "casos_acumulados": int(len(cum)),
        "casos_semana": int(len(week)),
        "positivos_acumulados": int(cum["EstadoResultado_POPIS"].eq("Patógeno identificado").sum()),
        "positivos_semana": int(week["EstadoResultado_POPIS"].eq("Patógeno identificado").sum()),
        "defunciones_registradas": int(cum["DefuncionRegistrada_POPIS"].sum()),
    }


def pathogen_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    denom = len(df)
    for p in PATHOGENS:
        n = int(pd.to_numeric(df.get(p, 0), errors="coerce").fillna(0).sum()) if p in df.columns else 0
        rows.append({"Patógeno": p, "Detecciones": n, "% de casos": n / denom if denom else 0.0})
    return pd.DataFrame(rows).sort_values(["Detecciones", "Patógeno"], ascending=[False, True]).reset_index(drop=True)


def weekly_counts(base: pd.DataFrame, years: Iterable[int] | None = None) -> pd.DataFrame:
    work = base.copy()
    work["Año"] = pd.to_numeric(work["Año"], errors="coerce").astype("Int64")
    work["Semana"] = pd.to_numeric(work["SemanaInicio_POPIS"], errors="coerce").astype("Int64")
    work = work[work["Semana"].between(1, 53)]
    if years is not None:
        work = work[work["Año"].isin(list(years))]
    out = work.groupby(["Año", "Semana"], as_index=False).size().rename(columns={"size": "Casos"})
    grid = pd.MultiIndex.from_product([sorted(out["Año"].dropna().astype(int).unique()), range(1, 54)], names=["Año", "Semana"]).to_frame(index=False)
    return grid.merge(out, on=["Año", "Semana"], how="left").fillna({"Casos": 0})


def pathogen_weekly(base: pd.DataFrame, pathogen: str) -> pd.DataFrame:
    if pathogen not in PATHOGENS:
        raise ValueError(f"Patógeno no soportado: {pathogen}")
    work = base.copy()
    work["Año"] = pd.to_numeric(work["Año"], errors="coerce").astype("Int64")
    work["Semana"] = pd.to_numeric(work["SemanaInicio_POPIS"], errors="coerce").astype("Int64")
    work[pathogen] = pd.to_numeric(work[pathogen], errors="coerce").fillna(0)
    work = work[work["Semana"].between(1, 53)]
    return work.groupby(["Año", "Semana"], as_index=False)[pathogen].sum().rename(columns={pathogen: "Casos"})


def endemic_channel(weekly: pd.DataFrame, historical_years: Iterable[int], current_year: int | None = None) -> pd.DataFrame:
    hist = weekly[weekly["Año"].isin([int(y) for y in historical_years])].copy()
    rows = []
    for week in range(1, 54):
        vals = pd.to_numeric(hist.loc[hist["Semana"].eq(week), "Casos"], errors="coerce").dropna().to_numpy(dtype=float)
        if vals.size:
            q1, med, q3 = np.quantile(vals, [0.25, 0.50, 0.75])
            rows.append({"Semana": week, "Q1": q1, "Mediana": med, "Q3": q3, "n_historico": len(vals)})
        else:
            rows.append({"Semana": week, "Q1": np.nan, "Mediana": np.nan, "Q3": np.nan, "n_historico": 0})
    out = pd.DataFrame(rows)
    if current_year is not None:
        cur = weekly[weekly["Año"].eq(int(current_year))][["Semana", "Casos"]].rename(columns={"Casos": "Actual"})
        out = out.merge(cur, on="Semana", how="left")
    return out


def historical_comparison(base: pd.DataFrame, cutoff_week: int) -> pd.DataFrame:
    years = sorted(pd.to_numeric(base["Año"], errors="coerce").dropna().astype(int).unique())
    rows = []
    for y in years:
        c = filter_cutoff(base, y, cutoff_week)
        w = filter_cutoff(base, y, cutoff_week, exact_week=True)
        row = {
            "Año": y,
            f"Casos acumulados ≤ SE{cutoff_week}": len(c),
            f"Casos SE{cutoff_week}": len(w),
            "Positivos acumulados": int(c["EstadoResultado_POPIS"].eq("Patógeno identificado").sum()),
            "Defunciones registradas": int(c["DefuncionRegistrada_POPIS"].sum()),
        }
        for p in PATHOGENS:
            row[p] = int(pd.to_numeric(c[p], errors="coerce").fillna(0).sum())
        rows.append(row)
    return pd.DataFrame(rows)


def mortality_by_year(base: pd.DataFrame, cutoff_week: int) -> pd.DataFrame:
    rows = []
    for y in sorted(pd.to_numeric(base["Año"], errors="coerce").dropna().astype(int).unique()):
        c = filter_cutoff(base, y, cutoff_week)
        cases = len(c)
        deaths = int(c["DefuncionRegistrada_POPIS"].sum())
        rows.append({"Año": y, "Casos": cases, "Defunciones registradas": deaths, "Letalidad cruda": deaths / cases if cases else np.nan})
    return pd.DataFrame(rows)


def municipal_counts(base: pd.DataFrame, year: int, cutoff_week: int) -> pd.DataFrame:
    work = filter_cutoff(base, year, cutoff_week)
    mun = work["Municipio_POPIS"].fillna("").astype(str).str.strip()
    work = work.loc[mun.ne("")].copy()
    work["Municipio"] = mun[mun.ne("")]
    return work.groupby("Municipio", as_index=False).size().rename(columns={"size": "Casos"}).sort_values("Casos", ascending=False)
