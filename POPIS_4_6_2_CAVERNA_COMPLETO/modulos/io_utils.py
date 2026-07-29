from __future__ import annotations

import hashlib
import io
import json
import re
import shutil
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, BinaryIO, Iterable

import pandas as pd

DATA_EXTENSIONS = {".xls", ".xlsx", ".csv", ".txt"}


def project_root(start: str | Path | None = None) -> Path:
    if start is not None:
        return Path(start).resolve()
    return Path(__file__).resolve().parents[1]


def ensure_structure(root: str | Path | None = None) -> Path:
    root = project_root(root)
    for rel in (
        "data/historicos", "data/actual", "data/suive", "data/poblacion",
        "data/geografia", "data/entrada", "data/backups", "salidas", "cache", "logs",
    ):
        (root / rel).mkdir(parents=True, exist_ok=True)
    return root


def ascii_text(value: Any) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def norm_key(value: Any) -> str:
    text = ascii_text(value).upper().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^A-Z0-9 ]+", "", text)
    return text.strip()


def first_existing(columns: Iterable[str], candidates: Iterable[str]) -> str | None:
    cols = [str(c) for c in columns]
    exact = {c: c for c in cols}
    normalized = {norm_key(c): c for c in cols}
    for candidate in candidates:
        if candidate in exact:
            return candidate
        key = norm_key(candidate)
        if key in normalized:
            return normalized[key]
    return None


def decode_bytes(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "latin-1", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            pass
    return raw.decode("latin-1", errors="replace")


def read_table(source: str | Path | bytes | BinaryIO, filename: str | None = None,
               sheet_name: str | int | None = 0, dtype: Any = str) -> pd.DataFrame:
    """Lee CSV, TSV, XLSX y los .xls SINAVE que realmente son texto tabulado."""
    if isinstance(source, (str, Path)):
        path = Path(source)
        raw = path.read_bytes()
        filename = filename or path.name
    elif isinstance(source, bytes):
        raw = source
    else:
        raw = source.read()

    suffix = Path(filename or "archivo").suffix.lower()
    head = decode_bytes(raw[:16384])

    if "\t" in head and ("SemanaInicio" in head or "Fec_captura" in head or head.count("\t") >= 5):
        return pd.read_csv(io.StringIO(decode_bytes(raw)), sep="\t", dtype=dtype, keep_default_na=False)

    if suffix in {".csv", ".txt"}:
        text = decode_bytes(raw)
        sample = text[:8192]
        separators = {";": sample.count(";"), ",": sample.count(","), "\t": sample.count("\t")}
        sep = max(separators, key=separators.get)
        return pd.read_csv(io.StringIO(text), sep=sep, dtype=dtype, keep_default_na=False)

    engine = "xlrd" if suffix == ".xls" else "openpyxl"
    return pd.read_excel(io.BytesIO(raw), sheet_name=sheet_name, dtype=dtype, engine=engine).fillna("")


def read_excel_raw(path: str | Path, sheet_name: str | int | None = 0) -> pd.DataFrame:
    path = Path(path)
    engine = "xlrd" if path.suffix.lower() == ".xls" else "openpyxl"
    return pd.read_excel(path, sheet_name=sheet_name, header=None, engine=engine)


def file_sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def infer_year(df: pd.DataFrame, fallback_name: str = "") -> int | None:
    for column in ("Año", "ANIO", "ANO", "Anio"):
        if column in df.columns:
            s = pd.to_numeric(df[column], errors="coerce").dropna().astype(int)
            s = s[s.between(2000, 2100)]
            if not s.empty:
                return int(s.mode().iloc[0])
    for column in ("Fec_captura", "Fecha_Inicio", "Fecha de inicio", "FECHA_INICIO"):
        if column in df.columns:
            s = pd.to_datetime(df[column], dayfirst=True, errors="coerce").dt.year.dropna().astype(int)
            if not s.empty:
                return int(s.mode().iloc[0])
    match = re.search(r"(20\d{2})", fallback_name)
    return int(match.group(1)) if match else None


def infer_cutoff_week(df: pd.DataFrame, year: int | None = None, today: date | None = None) -> int | None:
    """Obtiene la última semana observada sin convertir semanas futuras en cero.

    En el año calendario vigente se ignoran semanas posteriores a la semana actual.
    Esto evita que valores aislados como SE53 en una descarga de mitad de año eleven
    artificialmente el corte epidemiológico. Los huecos posteriores al último dato
    observado quedan como ausencia de dato, no como cero.
    """
    column = first_existing(df.columns, ["SemanaInicio", "Semana de inicio", "SEMANA_INICIO", "Semana"])
    if not column:
        return None
    weeks = pd.to_numeric(df[column], errors="coerce")
    weeks = weeks[weeks.between(1, 53)]
    if weeks.empty:
        return None

    today = today or date.today()
    if year is None:
        year = infer_year(df)
    if year == today.year:
        calendar_cap = max(1, min(53, int(today.isocalendar().week)))
        plausible = weeks[weeks.le(calendar_cap)]
        if not plausible.empty:
            weeks = plausible
    return int(weeks.max()) if not weeks.empty else None


def classify_file(path: str | Path) -> str:
    path = Path(path)
    if path.suffix.lower() in {".json", ".geojson"}:
        try:
            obj = json.loads(path.read_text(encoding="utf-8-sig"))
            if isinstance(obj, dict) and obj.get("type") == "FeatureCollection":
                return "geografia"
        except Exception:
            return "desconocido"
    if path.suffix.lower() not in DATA_EXTENSIONS:
        return "desconocido"
    try:
        df = read_table(path)
    except Exception:
        return "desconocido"
    keys = {norm_key(c) for c in df.columns}
    sinave_signals = sum(k in keys for k in map(norm_key, ["Folio", "SemanaInicio", "Fec_captura", "Diag_Final"]))
    pathogen_signals = sum(k in keys for k in map(norm_key, ["Salmonella", "Shigella", "Rotavirus", "VibrioCholerae"]))
    if sinave_signals >= 2 and (sinave_signals + pathogen_signals) >= 3:
        return "sinave"
    if {norm_key("Año"), norm_key("Semana"), norm_key("Casos")}.issubset(keys):
        return "suive"
    if first_existing(df.columns, ["Municipio", "NOM_MUN", "NOMGEO"]) and first_existing(df.columns, ["Poblacion", "POBLACION", "Población", "POB", "Total"]):
        return "poblacion"
    name = norm_key(path.name)
    if "SUIVE" in name or "SUAVE" in name or "CANAL ENDEMICO" in name:
        return "suive"
    return "desconocido"


@dataclass
class Assets:
    root: Path
    sinave_by_year: dict[int, Path] = field(default_factory=dict)
    current_sinave: Path | None = None
    suive_file: Path | None = None
    population_file: Path | None = None
    municipal_geojson: Path | None = None
    current_year: int | None = None
    cutoff_week: int | None = None
    warnings: list[str] = field(default_factory=list)


def _latest(paths: list[Path]) -> Path | None:
    return max(paths, key=lambda p: p.stat().st_mtime) if paths else None


def discover_assets(root: str | Path | None = None) -> Assets:
    root = ensure_structure(root)
    assets = Assets(root=root)

    historical = [p for p in (root / "data/historicos").iterdir() if p.is_file() and p.suffix.lower() in DATA_EXTENSIONS]
    current = [p for p in (root / "data/actual").iterdir() if p.is_file() and p.suffix.lower() in DATA_EXTENSIONS]

    candidates: list[tuple[int, Path, int]] = []
    for priority, collection in ((1, historical), (2, current)):
        for path in collection:
            try:
                df = read_table(path)
                year = infer_year(df, path.name)
                if year:
                    candidates.append((year, path, priority))
            except Exception as exc:
                assets.warnings.append(f"No se pudo leer {path.name}: {exc}")

    for year in sorted({x[0] for x in candidates}):
        matches = [x for x in candidates if x[0] == year]
        matches.sort(key=lambda x: (x[2], x[1].stat().st_mtime), reverse=True)
        assets.sinave_by_year[year] = matches[0][1]

    if assets.sinave_by_year:
        assets.current_year = max(assets.sinave_by_year)
        assets.current_sinave = assets.sinave_by_year[assets.current_year]
        try:
            current_df = read_table(assets.current_sinave)
            assets.cutoff_week = infer_cutoff_week(current_df, year=assets.current_year)
            week_col = first_existing(current_df.columns, ["SemanaInicio", "Semana de inicio", "SEMANA_INICIO", "Semana"])
            if week_col and assets.cutoff_week:
                raw_weeks = pd.to_numeric(current_df[week_col], errors="coerce")
                later = sorted(set(raw_weeks[raw_weeks.between(assets.cutoff_week + 1, 53)].dropna().astype(int)))
                if later:
                    assets.warnings.append(
                        "Se detectaron semanas posteriores al corte observado "
                        f"({', '.join('SE'+str(w) for w in later)}). No se usan como ceros ni amplían la serie actual."
                    )
        except Exception:
            pass

    suive = [p for p in (root / "data/suive").iterdir() if p.is_file() and p.suffix.lower() in DATA_EXTENSIONS]
    assets.suive_file = _latest(suive)
    population = [p for p in (root / "data/poblacion").iterdir() if p.is_file() and p.suffix.lower() in DATA_EXTENSIONS]
    assets.population_file = _latest(population)
    geo = [p for p in (root / "data/geografia").iterdir() if p.is_file() and p.suffix.lower() in {".json", ".geojson"}]
    assets.municipal_geojson = _latest(geo)
    return assets


def backup_and_replace(source: Path, destination: Path, root: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = root / "data/backups" / stamp
    backup_root.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        shutil.copy2(destination, backup_root / destination.name)
    shutil.copy2(source, destination)
    return destination


def process_inbox(root: str | Path | None = None) -> list[str]:
    root = ensure_structure(root)
    messages: list[str] = []
    inbox = root / "data/entrada"
    for path in sorted(inbox.iterdir()):
        if not path.is_file():
            continue
        kind = classify_file(path)
        if kind == "desconocido":
            messages.append(f"Sin clasificar: {path.name}")
            continue
        if kind == "sinave":
            try:
                df = read_table(path)
                year = infer_year(df, path.name)
            except Exception as exc:
                messages.append(f"Error {path.name}: {exc}")
                continue
            if year is None:
                messages.append(f"SINAVE sin año identificable: {path.name}")
                continue
            current_year = datetime.now().year
            if year >= current_year:
                destination = root / "data/actual" / "Diarreas_actual.xls"
            else:
                destination = root / "data/historicos" / f"Diarreas_{year}{path.suffix.lower()}"
        elif kind == "suive":
            destination = root / "data/suive" / path.name
        elif kind == "poblacion":
            destination = root / "data/poblacion" / path.name
        elif kind == "geografia":
            destination = root / "data/geografia" / "municipios_sonora.geojson"
        else:
            continue
        backup_and_replace(path, destination, root)
        path.unlink(missing_ok=True)
        messages.append(f"Integrado {kind}: {destination.name}")
    return messages
