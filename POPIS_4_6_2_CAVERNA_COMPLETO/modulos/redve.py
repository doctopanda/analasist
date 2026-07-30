from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .io_utils import first_existing, norm_key, read_table

EDA_CIE_PATTERN = re.compile(r"^A0[0-9]", re.IGNORECASE)
PLACEHOLDER_CURPS = {"", "XXXX999999XXXXXX99", "XEXX010101HNEXXXA4", "XAXX010101000"}


def _text(df: pd.DataFrame, column: str | None) -> pd.Series:
    if not column or column not in df.columns:
        return pd.Series([""] * len(df), index=df.index, dtype="object")
    return df[column].fillna("").astype(str).str.strip()


def _normalized_identifier(value: object) -> str:
    return re.sub(r"[^A-Z0-9]", "", norm_key(value))


def _valid_curp(value: object) -> str:
    curp = _normalized_identifier(value)
    if curp in PLACEHOLDER_CURPS or len(curp) != 18:
        return ""
    return curp


def _name_key(apellido1: object, apellido2: object, nombres: object) -> str:
    parts = [norm_key(apellido1), norm_key(apellido2), norm_key(nombres)]
    return " ".join(part for part in parts if part).strip()


def _sex_key(value: object) -> str:
    text = norm_key(value)
    if text in {"1", "H", "HOMBRE", "MASCULINO"}:
        return "H"
    if text in {"2", "M", "MUJER", "FEMENINO"}:
        return "M"
    return text[:1]


def _numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _sinave_age_months(df: pd.DataFrame) -> pd.Series:
    years = _numeric(_text(df, first_existing(df.columns, ["Edad_Años", "Edad_Anios", "Edad"]))).fillna(0)
    months = _numeric(_text(df, first_existing(df.columns, ["Edad_Meses", "MesesEdad"]))).fillna(0)
    result = years * 12 + months
    return result.where(result.gt(0))


def _redve_age_months(df: pd.DataFrame) -> pd.Series:
    age = _numeric(_text(df, first_existing(df.columns, ["DEFEDAD", "EDAD"])))
    unit_code = _text(df, first_existing(df.columns, ["DEFCLV_EDA", "CLAVE_EDAD"])).str.strip()
    unit_desc = _text(df, first_existing(df.columns, ["DES_TIEMPO", "UNIDAD_EDAD"])).map(norm_key)
    result = pd.Series(pd.NA, index=df.index, dtype="Float64")
    years_mask = unit_code.eq("3") | unit_desc.str.contains("ANO", regex=False)
    months_mask = unit_code.eq("2") | unit_desc.str.contains("MES", regex=False)
    days_mask = unit_code.eq("1") | unit_desc.str.contains("DIA", regex=False)
    result.loc[years_mask] = age.loc[years_mask] * 12
    result.loc[months_mask] = age.loc[months_mask]
    result.loc[days_mask] = age.loc[days_mask] / 30.4375
    return result


def _extract_sinave_folios_from_text(value: object) -> set[str]:
    text = "" if value is None else str(value).upper()
    if not text:
        return set()
    found: set[str] = set()
    patterns = [
        r"FOLIO(?:\s+EN)?(?:\s+PLATAFORMA)?(?:\s+(?:SINAVE|SIVAVE))?\s*[:#-]?\s*([A-Z]{2,6}\d{2}-?\d{4,12}|\d{5,12})",
        r"(?:SINAVE|SIVAVE)\s*(?:FOLIO)?\s*[:#\-(]?\s*([A-Z]{2,6}\d{2}-?\d{4,12}|\d{5,12})",
        r"CON\s+FOLIO\s+([A-Z]{2,6}\d{2}-?\d{4,12}|\d{5,12})\s+EN\s+PLATAFORMA\s+(?:SINAVE|SIVAVE)",
    ]
    for pattern in patterns:
        for match in re.findall(pattern, text, flags=re.IGNORECASE):
            normalized = _normalized_identifier(match)
            if len(normalized) >= 5:
                found.add(normalized)
    for marker in re.finditer(r"SINAVE|SIVAVE", text, flags=re.IGNORECASE):
        start = max(0, marker.start() - 70)
        end = min(len(text), marker.end() + 90)
        for token in re.findall(r"\b\d{5,12}\b", text[start:end]):
            found.add(token)
    return found


def load_redve(path: str | Path) -> pd.DataFrame:
    """Lee y normaliza REDVE/SEED sin asumir que sea una base exclusiva de EDA."""
    raw = read_table(path)
    out = raw.copy()
    out.columns = [str(column).strip() for column in out.columns]

    death_date = first_existing(out.columns, ["DEFFECH_DEF", "FECHA_DEFUNCION", "FEC_DEFUNCION"])
    dictum_date = first_existing(out.columns, ["FECHA_DICTAMINACION", "FEC_DICTAM", "FEC_DICTAMINACION"])
    out["REDVE_Fecha_defuncion_dt"] = pd.to_datetime(_text(out, death_date), dayfirst=True, errors="coerce")
    out["REDVE_Fecha_dictaminacion_dt"] = pd.to_datetime(_text(out, dictum_date), dayfirst=True, errors="coerce")

    out["_redve_curp"] = _text(out, first_existing(out.columns, ["DEFCURP", "CURP"])).map(_valid_curp)
    out["_redve_name"] = [
        _name_key(a, b, n)
        for a, b, n in zip(
            _text(out, first_existing(out.columns, ["DEFAPEPATER", "PRIMER_APELLIDO"])),
            _text(out, first_existing(out.columns, ["DEFAPEMATER", "SEGUNDO_APELLIDO"])),
            _text(out, first_existing(out.columns, ["DEFNOMBRE", "NOMBRES"])),
        )
    ]
    out["_redve_sex"] = _text(out, first_existing(out.columns, ["DEFSEXO", "DESSEXO", "SEXO"])).map(_sex_key)
    out["_redve_age_months"] = _redve_age_months(out)

    text_columns = [
        first_existing(out.columns, ["OBSERVACIONES"]),
        first_existing(out.columns, ["COMENTARIOS"]),
        first_existing(out.columns, ["FOLIOCONFIRMADO"]),
    ]
    text_columns = [column for column in text_columns if column]
    out["REDVE_Folios_SINAVE"] = [
        sorted(set().union(*(_extract_sinave_folios_from_text(row[column]) for column in text_columns)))
        if text_columns else []
        for _, row in out.iterrows()
    ]

    out["REDVE_DEFFOLIO"] = _text(out, first_existing(out.columns, ["DEFFOLIO", "FOLIO_REDVE"]))
    out["REDVE_CAUSASUJVIGCVE"] = _text(out, first_existing(out.columns, ["CAUSASUJVIGCVE", "CAUSA_SUJETA_CVE"]))
    out["REDVE_CAUSASUJVIGDES"] = _text(out, first_existing(out.columns, ["CAUSASUJVIGDES", "CAUSA_SUJETA_DES"]))
    out["REDVE_DEFUNCION_DICTAMINADA"] = _text(out, first_existing(out.columns, ["DEFUNCION_DICTAMINADA"]))
    out["REDVE_DEFUNCION_PROCESO_DICTAMINACION"] = _text(out, first_existing(out.columns, ["DEFUNCION_PROCESO_DICTAMINACION"]))
    out["REDVE_AII"] = _text(out, first_existing(out.columns, ["AII", "ESTATUS"])).map(norm_key)

    code = out["REDVE_CAUSASUJVIGCVE"].map(_normalized_identifier)
    dictaminated = out["REDVE_DEFUNCION_DICTAMINADA"].map(norm_key).eq("SI")
    in_process = out["REDVE_DEFUNCION_PROCESO_DICTAMINACION"].map(norm_key).eq("SI")
    is_eda = code.str.match(EDA_CIE_PATTERN, na=False)
    out["Muerte atribuida a EDA REDVE"] = is_eda & dictaminated
    out["Muerte EDA pendiente REDVE"] = is_eda & (~dictaminated | in_process)
    out["Archivo REDVE"] = Path(path).name
    return out


def _candidate_rows_by_folio(sinave: pd.DataFrame, redve: pd.DataFrame) -> list[tuple[int, int, str, str]]:
    candidates: list[tuple[int, int, str, str]] = []
    folio_col = first_existing(sinave.columns, ["Folio", "FOLIO", "Folio_SINAVE"])
    if not folio_col:
        return candidates
    sin_folios = _text(sinave, folio_col).map(_normalized_identifier)
    lookup: dict[str, list[int]] = {}
    for idx, folio in sin_folios.items():
        if folio:
            lookup.setdefault(folio, []).append(idx)
    for ridx, folios in redve["REDVE_Folios_SINAVE"].items():
        for folio in folios:
            for sidx in lookup.get(folio, []):
                candidates.append((sidx, ridx, "Folio SINAVE explícito en REDVE", "Muy alta"))
    return candidates


def _candidate_rows_by_curp(sinave: pd.DataFrame, redve: pd.DataFrame) -> list[tuple[int, int, str, str]]:
    candidates: list[tuple[int, int, str, str]] = []
    curp_col = first_existing(sinave.columns, ["CURP", "Curp"])
    if not curp_col:
        return candidates
    sin_curps = _text(sinave, curp_col).map(_valid_curp)
    sin_lookup: dict[str, list[int]] = {}
    red_lookup: dict[str, list[int]] = {}
    for idx, curp in sin_curps.items():
        if curp:
            sin_lookup.setdefault(curp, []).append(idx)
    for idx, curp in redve["_redve_curp"].items():
        if curp:
            red_lookup.setdefault(curp, []).append(idx)
    for curp in set(sin_lookup).intersection(red_lookup):
        if len(sin_lookup[curp]) == 1 and len(red_lookup[curp]) == 1:
            candidates.append((sin_lookup[curp][0], red_lookup[curp][0], "CURP exacta y única", "Alta"))
    return candidates


def _candidate_rows_by_identity(sinave: pd.DataFrame, redve: pd.DataFrame) -> list[tuple[int, int, str, str]]:
    candidates: list[tuple[int, int, str, str]] = []
    a1 = first_existing(sinave.columns, ["Primer_Apellido", "Apellido_Paterno"])
    a2 = first_existing(sinave.columns, ["Segundo_Apellido", "Apellido_Materno"])
    names = first_existing(sinave.columns, ["Nombres", "Nombre"])
    if not (a1 and names):
        return candidates
    sin_names = pd.Series([
        _name_key(x, y, z)
        for x, y, z in zip(_text(sinave, a1), _text(sinave, a2), _text(sinave, names))
    ], index=sinave.index)
    sin_sex = _text(sinave, first_existing(sinave.columns, ["Sexo", "SEXO"])).map(_sex_key)
    sin_age = _sinave_age_months(sinave)
    sin_lookup: dict[str, list[int]] = {}
    red_lookup: dict[str, list[int]] = {}
    for idx, key in sin_names.items():
        if key:
            sin_lookup.setdefault(key, []).append(idx)
    for idx, key in redve["_redve_name"].items():
        if key:
            red_lookup.setdefault(key, []).append(idx)
    for key in set(sin_lookup).intersection(red_lookup):
        if len(sin_lookup[key]) != 1 or len(red_lookup[key]) != 1:
            continue
        sidx, ridx = sin_lookup[key][0], red_lookup[key][0]
        if sin_sex.loc[sidx] and redve.at[ridx, "_redve_sex"] and sin_sex.loc[sidx] != redve.at[ridx, "_redve_sex"]:
            continue
        s_age = sin_age.loc[sidx]
        r_age = redve.at[ridx, "_redve_age_months"]
        if pd.notna(s_age) and pd.notna(r_age):
            tolerance = 1.5 if max(float(s_age), float(r_age)) < 24 else 12.5
            if abs(float(s_age) - float(r_age)) > tolerance:
                continue
        candidates.append((sidx, ridx, "Nombre completo único + sexo + edad compatible", "Media"))
    return candidates


def link_redve_deaths(sinave: pd.DataFrame, redve: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Enriquece SINAVE con evidencia REDVE sin agregar defunciones no vinculadas."""
    out = sinave.copy()
    direct_date = pd.to_datetime(out.get("FecDefuncion_dt", pd.Series(pd.NaT, index=out.index)), errors="coerce")
    motive = _text(out, first_existing(out.columns, ["MotivoDeEgreso", "Motivo_Egreso"]))
    direct_motive = motive.map(norm_key).str.contains(r"DEFUN|FALLEC", regex=True, na=False)
    out["Defunción SINAVE con fecha"] = direct_date.notna()
    out["Defunción SINAVE"] = direct_date.notna() | direct_motive
    out["Defunción REDVE"] = False
    out["Defunción integrada"] = out["Defunción SINAVE"]
    out["Fuente defunción"] = out["Defunción SINAVE"].map({True: "SINAVE", False: "Sin evidencia"})
    out["Fecha defunción integrada"] = direct_date
    out["Criterio cruce REDVE"] = ""
    out["Confianza cruce REDVE"] = ""
    for column in [
        "REDVE_DEFFOLIO", "REDVE_CAUSASUJVIGCVE", "REDVE_CAUSASUJVIGDES",
        "REDVE_DEFUNCION_DICTAMINADA", "REDVE_DEFUNCION_PROCESO_DICTAMINACION",
        "REDVE_FECHA_DICTAMINACION", "Muerte atribuida a EDA REDVE",
        "Muerte EDA pendiente REDVE", "Archivo REDVE",
    ]:
        out[column] = False if column.startswith("Muerte ") else ""

    if redve is None or redve.empty or out.empty:
        return out, pd.DataFrame(columns=["Índice SINAVE", "Índice REDVE", "Criterio", "Confianza"])

    priority = {"Muy alta": 0, "Alta": 1, "Media": 2}
    candidates = (
        _candidate_rows_by_folio(out, redve)
        + _candidate_rows_by_curp(out, redve)
        + _candidate_rows_by_identity(out, redve)
    )
    candidates.sort(key=lambda row: (priority.get(row[3], 9), row[0], row[1]))
    used_sinave: set[int] = set()
    used_redve: set[int] = set()
    accepted: list[dict[str, object]] = []

    for sidx, ridx, criterion, confidence in candidates:
        if sidx in used_sinave or ridx in used_redve:
            continue
        used_sinave.add(sidx)
        used_redve.add(ridx)
        accepted.append({"Índice SINAVE": sidx, "Índice REDVE": ridx, "Criterio": criterion, "Confianza": confidence})

        redve_date = redve.at[ridx, "REDVE_Fecha_defuncion_dt"]
        out.at[sidx, "Defunción REDVE"] = pd.notna(redve_date)
        out.at[sidx, "Defunción integrada"] = bool(out.at[sidx, "Defunción SINAVE"]) or pd.notna(redve_date)
        if bool(out.at[sidx, "Defunción SINAVE"]) and pd.notna(redve_date):
            out.at[sidx, "Fuente defunción"] = "SINAVE + REDVE"
        elif pd.notna(redve_date):
            out.at[sidx, "Fuente defunción"] = "REDVE"
        if pd.isna(out.at[sidx, "Fecha defunción integrada"]) and pd.notna(redve_date):
            out.at[sidx, "Fecha defunción integrada"] = redve_date
        out.at[sidx, "Criterio cruce REDVE"] = criterion
        out.at[sidx, "Confianza cruce REDVE"] = confidence
        out.at[sidx, "REDVE_DEFFOLIO"] = redve.at[ridx, "REDVE_DEFFOLIO"]
        out.at[sidx, "REDVE_CAUSASUJVIGCVE"] = redve.at[ridx, "REDVE_CAUSASUJVIGCVE"]
        out.at[sidx, "REDVE_CAUSASUJVIGDES"] = redve.at[ridx, "REDVE_CAUSASUJVIGDES"]
        out.at[sidx, "REDVE_DEFUNCION_DICTAMINADA"] = redve.at[ridx, "REDVE_DEFUNCION_DICTAMINADA"]
        out.at[sidx, "REDVE_DEFUNCION_PROCESO_DICTAMINACION"] = redve.at[ridx, "REDVE_DEFUNCION_PROCESO_DICTAMINACION"]
        date_dictum = redve.at[ridx, "REDVE_Fecha_dictaminacion_dt"]
        out.at[sidx, "REDVE_FECHA_DICTAMINACION"] = "" if pd.isna(date_dictum) else date_dictum.strftime("%Y-%m-%d")
        out.at[sidx, "Muerte atribuida a EDA REDVE"] = bool(redve.at[ridx, "Muerte atribuida a EDA REDVE"])
        out.at[sidx, "Muerte EDA pendiente REDVE"] = bool(redve.at[ridx, "Muerte EDA pendiente REDVE"])
        out.at[sidx, "Archivo REDVE"] = redve.at[ridx, "Archivo REDVE"]

    out["Defunción integrada"] = out["Defunción integrada"].fillna(False).astype(bool)
    out["Defunción REDVE"] = out["Defunción REDVE"].fillna(False).astype(bool)
    out["Muerte atribuida a EDA REDVE"] = out["Muerte atribuida a EDA REDVE"].fillna(False).astype(bool)
    out["Muerte EDA pendiente REDVE"] = out["Muerte EDA pendiente REDVE"].fillna(False).astype(bool)
    return out, pd.DataFrame(accepted)


def death_metrics(frame: pd.DataFrame) -> dict[str, int]:
    if frame is None or frame.empty:
        return {
            "defunciones_sinave": 0,
            "defunciones_sinave_con_fecha": 0,
            "defunciones_redve_recuperadas": 0,
            "defunciones_integradas": 0,
            "muertes_eda_dictaminadas_redve": 0,
            "muertes_eda_pendientes_redve": 0,
        }
    direct = frame.get("Defunción SINAVE", pd.Series(False, index=frame.index)).fillna(False).astype(bool)
    direct_date = frame.get("Defunción SINAVE con fecha", pd.Series(False, index=frame.index)).fillna(False).astype(bool)
    redve = frame.get("Defunción REDVE", pd.Series(False, index=frame.index)).fillna(False).astype(bool)
    integrated = frame.get("Defunción integrada", direct | redve).fillna(False).astype(bool)
    return {
        "defunciones_sinave": int(direct.sum()),
        "defunciones_sinave_con_fecha": int(direct_date.sum()),
        "defunciones_redve_recuperadas": int((redve & ~direct).sum()),
        "defunciones_integradas": int(integrated.sum()),
        "muertes_eda_dictaminadas_redve": int(frame.get("Muerte atribuida a EDA REDVE", pd.Series(False, index=frame.index)).fillna(False).astype(bool).sum()),
        "muertes_eda_pendientes_redve": int(frame.get("Muerte EDA pendiente REDVE", pd.Series(False, index=frame.index)).fillna(False).astype(bool).sum()),
    }
