from __future__ import annotations

import json
import re
import shutil
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

try:
    from .mapa_espacial import load_geojson, read_table
except ImportError:  # permite pruebas directas desde la carpeta
    from mapa_espacial import load_geojson, read_table


TABULAR_EXTENSIONS = {".xls", ".xlsx", ".csv", ".txt"}
GEO_EXTENSIONS = {".geojson", ".json"}
SUPPORTED_EXTENSIONS = TABULAR_EXTENSIONS | GEO_EXTENSIONS

SINAVE_SIGNATURE = {
    "fec_captura",
    "semanainicio",
    "folio",
}
SINAVE_PATHOGEN_COLUMNS = {
    "salmonella",
    "shigella",
    "rotavirus",
    "vibriocholerae",
    "vibrioparahaemolyticus",
    "patotipo_ecoli_indre",
}


@dataclass
class ProjectAssets:
    root: Path
    sinave_by_year: dict[int, Path] = field(default_factory=dict)
    suive_file: Path | None = None
    population_file: Path | None = None
    municipal_geojson: Path | None = None
    district_geojson: Path | None = None
    coordinates_file: Path | None = None
    current_year: int | None = None
    cutoff_week: int | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def sinave_files(self) -> list[Path]:
        return [self.sinave_by_year[y] for y in sorted(self.sinave_by_year)]


@dataclass
class InboxAction:
    source: Path
    kind: str
    destination: Path | None
    status: str
    message: str


# -----------------------------------------------------------------------------
# Normalización y utilidades
# -----------------------------------------------------------------------------


def _ascii(value: Any) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def norm_key(value: Any) -> str:
    text = _ascii(value).upper().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^A-Z0-9 ]+", "", text)
    return text.strip()


def norm_column(value: Any) -> str:
    text = _ascii(value).lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def first_existing(columns: Iterable[str], candidates: Iterable[str]) -> str | None:
    cols = [str(c) for c in columns]
    direct = {c: c for c in cols}
    normalized = {norm_column(c): c for c in cols}
    for candidate in candidates:
        if candidate in direct:
            return direct[candidate]
        key = norm_column(candidate)
        if key in normalized:
            return normalized[key]
    return None


def _safe_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def _decode_head(raw: bytes) -> str:
    for enc in ("utf-8-sig", "latin-1", "cp1252"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1", errors="replace")


def _sniff_columns(path: Path) -> list[str]:
    """Lee solo lo necesario para reconocer el tipo de fuente."""
    suffix = path.suffix.lower()
    try:
        if suffix in {".xls", ".csv", ".txt"}:
            raw = path.read_bytes()[:65536]
            text = _decode_head(raw)
            first_line = text.splitlines()[0] if text.splitlines() else ""
            if "\t" in first_line:
                return [x.strip() for x in first_line.split("\t")]
            if suffix in {".csv", ".txt"}:
                sep = ";" if first_line.count(";") > first_line.count(",") else ","
                return [x.strip() for x in first_line.split(sep)]
        if suffix in {".xlsx", ".xls"}:
            engine = "xlrd" if suffix == ".xls" else "openpyxl"
            sample = pd.read_excel(path, nrows=3, engine=engine)
            return [str(c) for c in sample.columns]
    except Exception:
        return []
    return []


def _extract_year_from_name(path: Path) -> int | None:
    years = [int(x) for x in re.findall(r"(?:19|20)\d{2}", path.name)]
    valid = [y for y in years if 2000 <= y <= 2100]
    return max(valid) if valid else None


def infer_sinave_year(path: Path, frame: pd.DataFrame | None = None) -> int | None:
    year = _extract_year_from_name(path)
    if year:
        return year
    try:
        df = frame if frame is not None else read_table(path)
        date_col = first_existing(df.columns, ["Fec_captura", "Fecha_Inicio", "Fecha de inicio"])
        if date_col:
            years = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce").dt.year.dropna().astype(int)
            if not years.empty:
                return int(years.mode().iloc[0])
    except Exception:
        pass
    return None


def _skip_path(path: Path) -> bool:
    blocked = {
        ".git",
        ".venv",
        "venv",
        "env",
        "node_modules",
        "__pycache__",
        "salidas",
        "output",
        "outputs",
    }
    return any(part.lower() in blocked for part in path.parts)


def find_project_root(anchor: str | Path | None = None) -> Path:
    """Localiza la raíz de POPIS sin exigir una ruta fija."""
    start = Path(anchor).resolve() if anchor else Path(__file__).resolve()
    if start.is_file():
        start = start.parent

    candidates = [start, *start.parents[:6]]
    scored: list[tuple[int, Path]] = []
    for candidate in candidates:
        score = 0
        if (candidate / "data").exists():
            score += 4
        if (candidate / "app.py").exists():
            score += 3
        if (candidate / "popis_core.py").exists():
            score += 3
        if (candidate / "pages").exists():
            score += 1
        if (candidate / "requirements.txt").exists():
            score += 1
        scored.append((score, candidate))

    scored.sort(key=lambda item: (item[0], -len(item[1].parts)), reverse=True)
    best_score, best = scored[0]
    return best if best_score > 0 else start


def _candidate_roots(root: Path) -> list[Path]:
    names = ["data", "assets", "resources", "geografia", "cartografia", "fuentes"]
    roots = [root / name for name in names if (root / name).exists()]
    roots.append(root)
    return roots


def iter_project_files(root: Path) -> list[Path]:
    files: dict[str, Path] = {}
    for base in _candidate_roots(root):
        if base == root:
            iterator = base.glob("*")
        else:
            iterator = base.rglob("*")
        for path in iterator:
            if not path.is_file() or _skip_path(path):
                continue
            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            files[str(path.resolve())] = path
    return list(files.values())


# -----------------------------------------------------------------------------
# Clasificación de archivos
# -----------------------------------------------------------------------------


def classify_file(path: str | Path) -> str:
    path = Path(path)
    suffix = path.suffix.lower()
    name = norm_key(path.stem)

    if suffix in GEO_EXTENSIONS:
        if any(term in name for term in ("DISTRIT", "JURISDIC", "REGION SALUD")):
            return "geo_distritos"
        if any(term in name for term in ("MUNICIP", "MUN SONORA", "SONORA MUN")):
            return "geo_municipios"
        return "geojson"

    if any(term in name for term in ("COORDENAD", "GEOCOD", "LAT LON", "LATITUD LONGITUD")):
        return "coordenadas"
    if any(term in name for term in ("POBLACION", "CONAPO", "PROYECCION")):
        return "poblacion"
    if any(term in name for term in ("SUIVE", "SUAVE", "CANAL ENDEMICO")):
        return "suive"

    if suffix in TABULAR_EXTENSIONS:
        cols = {norm_column(c) for c in _sniff_columns(path)}
        if SINAVE_SIGNATURE.issubset(cols) or (
            {"semanainicio", "folio"}.issubset(cols) and bool(cols & SINAVE_PATHOGEN_COLUMNS)
        ):
            return "sinave"
        if {"latitud", "longitud"}.issubset(cols) and bool(cols & {"folio", "id"}):
            return "coordenadas"

    return "desconocido"


def _source_priority(path: Path) -> int:
    parts = {norm_key(p) for p in path.parts}
    if any("ACTUAL" in p for p in parts):
        return 100
    if any("SINAVE ACTUAL" in p for p in parts):
        return 100
    if any("HISTOR" in p for p in parts):
        return 80
    if any("ENTRADA" in p for p in parts):
        return 60
    return 50


def _pick_latest(paths: list[Path]) -> Path | None:
    if not paths:
        return None
    return max(paths, key=lambda p: (_safe_mtime(p), str(p)))


def discover_project_assets(root: str | Path | None = None) -> ProjectAssets:
    root_path = find_project_root(root)
    assets = ProjectAssets(root=root_path)

    sinave_candidates: dict[int, list[Path]] = {}
    suive: list[Path] = []
    population: list[Path] = []
    muni_geo: list[Path] = []
    dist_geo: list[Path] = []
    coords: list[Path] = []
    generic_geo: list[Path] = []

    for path in iter_project_files(root_path):
        kind = classify_file(path)
        if kind == "sinave":
            year = infer_sinave_year(path)
            if year:
                sinave_candidates.setdefault(year, []).append(path)
        elif kind == "suive":
            suive.append(path)
        elif kind == "poblacion":
            population.append(path)
        elif kind == "geo_municipios":
            muni_geo.append(path)
        elif kind == "geo_distritos":
            dist_geo.append(path)
        elif kind == "coordenadas":
            coords.append(path)
        elif kind == "geojson":
            generic_geo.append(path)

    for year, candidates in sinave_candidates.items():
        assets.sinave_by_year[year] = max(
            candidates,
            key=lambda p: (_source_priority(p), _safe_mtime(p), str(p)),
        )

    assets.suive_file = _pick_latest(suive)
    assets.population_file = _pick_latest(population)
    assets.municipal_geojson = _pick_latest(muni_geo)
    assets.district_geojson = _pick_latest(dist_geo)
    assets.coordinates_file = _pick_latest(coords)

    # Rescate prudente cuando los GeoJSON no tienen nombres descriptivos.
    if generic_geo:
        generic_sorted = sorted(generic_geo, key=_safe_mtime, reverse=True)
        if assets.municipal_geojson is None and generic_sorted:
            assets.municipal_geojson = generic_sorted[0]
        if assets.district_geojson is None and len(generic_sorted) > 1:
            assets.district_geojson = generic_sorted[1]

    if assets.sinave_by_year:
        assets.current_year = max(assets.sinave_by_year)
        try:
            current = read_table(assets.sinave_by_year[assets.current_year])
            week_col = first_existing(current.columns, ["SemanaInicio", "Semana de inicio", "Semana"])
            if week_col:
                weeks = pd.to_numeric(current[week_col], errors="coerce")
                weeks = weeks[weeks.between(1, 53)]
                if not weeks.dropna().empty:
                    assets.cutoff_week = int(weeks.max())
        except Exception as exc:
            assets.warnings.append(f"No se pudo determinar el corte SINAVE: {exc}")

    if not assets.sinave_by_year:
        assets.warnings.append("No se detectaron bases SINAVE en el proyecto.")
    if assets.suive_file is None:
        assets.warnings.append("No se detectó una fuente SUIVE/SUAVE.")
    if assets.population_file is None:
        assets.warnings.append("No se detectó una fuente poblacional.")
    if assets.municipal_geojson is None:
        assets.warnings.append("No se detectó cartografía municipal GeoJSON.")

    return assets


# -----------------------------------------------------------------------------
# Carga automática
# -----------------------------------------------------------------------------


def load_sinave_bundle(assets: ProjectAssets) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for year, path in sorted(assets.sinave_by_year.items()):
        frame = read_table(path)
        frame = frame.copy()
        if "Año" not in frame.columns:
            frame["Año"] = int(year)
        else:
            parsed_year = pd.to_numeric(frame["Año"], errors="coerce")
            frame["Año"] = parsed_year.fillna(year).astype("Int64")
        frame["Archivo de origen"] = path.name
        frames.append(frame)

    if not frames:
        raise ValueError("POPIS no encontró bases SINAVE para cargar automáticamente.")
    return pd.concat(frames, ignore_index=True, sort=False)


def load_optional_geojson(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    try:
        return load_geojson(path)
    except Exception:
        return None


def load_coordinate_table(path: Path | None) -> pd.DataFrame | None:
    if path is None:
        return None
    try:
        return read_table(path)
    except Exception:
        return None


def _read_excel_sheets(path: Path) -> list[pd.DataFrame]:
    try:
        sheets = pd.read_excel(path, sheet_name=None, dtype=str, engine="openpyxl")
        return [df.fillna("") for df in sheets.values()]
    except Exception:
        try:
            return [read_table(path)]
        except Exception:
            return []


def normalize_population_table(path: Path | None, year: int | None = None) -> pd.DataFrame | None:
    """Convierte fuentes poblacionales comunes a Municipio/Poblacion/Año sin inventar denominadores."""
    if path is None:
        return None

    if path.suffix.lower() == ".xlsx":
        frames = _read_excel_sheets(path)
    else:
        try:
            frames = [read_table(path)]
        except Exception:
            frames = []

    for df in frames:
        if df.empty:
            continue
        mun_col = first_existing(
            df.columns,
            ["Municipio", "MUNICIPIO", "NOM_MUN", "NOMGEO", "Municipio residencia", "DES_MPO_RES"],
        )
        pop_col = first_existing(
            df.columns,
            ["Poblacion", "POBLACION", "Población", "POB", "Pob_Total", "TOTAL"],
        )
        year_col = first_existing(df.columns, ["Año", "ANIO", "ANO", "YEAR"])

        if not mun_col or not pop_col:
            continue

        work = df[[mun_col, pop_col] + ([year_col] if year_col else [])].copy()
        work["Municipio"] = work[mun_col].astype(str).str.strip()
        work["Poblacion"] = pd.to_numeric(
            work[pop_col].astype(str).str.replace(",", "", regex=False).str.replace(" ", "", regex=False),
            errors="coerce",
        )
        if year_col:
            work["Año"] = pd.to_numeric(work[year_col], errors="coerce").astype("Int64")
            if year is not None:
                work = work[work["Año"].eq(int(year))]
        elif year is not None:
            work["Año"] = int(year)

        work = work[work["Municipio"].ne("") & work["Poblacion"].notna() & work["Poblacion"].ge(0)]
        if work.empty:
            continue

        group_cols = ["Municipio"] + (["Año"] if "Año" in work.columns else [])
        work = work.groupby(group_cols, as_index=False)["Poblacion"].sum()
        return work

    return None


def status_table(assets: ProjectAssets) -> pd.DataFrame:
    sinave_desc = "No detectado"
    if assets.sinave_by_year:
        years = ", ".join(str(y) for y in sorted(assets.sinave_by_year))
        cut = f" · corte SE{assets.cutoff_week}" if assets.cutoff_week else ""
        sinave_desc = f"{years}{cut}"

    rows = [
        {"Fuente": "SINAVE", "Estado": "🟢" if assets.sinave_by_year else "🔴", "Detalle": sinave_desc},
        {"Fuente": "SUIVE/SUAVE", "Estado": "🟢" if assets.suive_file else "🟠", "Detalle": assets.suive_file.name if assets.suive_file else "No detectado"},
        {"Fuente": "Población", "Estado": "🟢" if assets.population_file else "🟠", "Detalle": assets.population_file.name if assets.population_file else "No detectada"},
        {"Fuente": "Municipios", "Estado": "🟢" if assets.municipal_geojson else "🟠", "Detalle": assets.municipal_geojson.name if assets.municipal_geojson else "No detectado"},
        {"Fuente": "Distritos", "Estado": "🟢" if assets.district_geojson else "🟠", "Detalle": assets.district_geojson.name if assets.district_geojson else "No detectado"},
        {"Fuente": "Coordenadas", "Estado": "🟢" if assets.coordinates_file else "⚪", "Detalle": assets.coordinates_file.name if assets.coordinates_file else "Opcionales"},
    ]
    return pd.DataFrame(rows)


# -----------------------------------------------------------------------------
# Bandeja automática de actualización
# -----------------------------------------------------------------------------


def inbox_dir(root: str | Path) -> Path:
    path = Path(root) / "data" / "entrada"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _backup_existing(destination: Path, root: Path) -> Path | None:
    if not destination.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = root / "data" / "backups" / stamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / destination.name
    shutil.copy2(destination, backup)
    return backup


def _destination_for(path: Path, kind: str, root: Path) -> Path | None:
    suffix = path.suffix.lower()
    if kind == "sinave":
        return root / "data" / "actual" / f"Diarreas_actual{suffix}"
    if kind == "suive":
        return root / "data" / "suive" / path.name
    if kind == "poblacion":
        return root / "data" / "poblacion" / path.name
    if kind in {"geo_municipios", "geo_distritos", "geojson"}:
        return root / "data" / "geografia" / path.name
    if kind == "coordenadas":
        return root / "data" / "coordenadas" / path.name
    return None


def install_source_file(path: str | Path, root: str | Path, move: bool = True) -> InboxAction:
    source = Path(path)
    root_path = Path(root)
    kind = classify_file(source)
    destination = _destination_for(source, kind, root_path)

    if destination is None:
        return InboxAction(source, kind, None, "omitido", "Fuente no reconocida; POPIS no la modificó.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    _backup_existing(destination, root_path)

    try:
        if source.resolve() == destination.resolve():
            return InboxAction(source, kind, destination, "sin_cambios", "La fuente ya está en su ubicación operativa.")
    except OSError:
        pass

    if move:
        shutil.move(str(source), str(destination))
    else:
        shutil.copy2(source, destination)

    return InboxAction(source, kind, destination, "instalado", f"{kind}: {destination.name}")


def process_inbox(root: str | Path) -> list[InboxAction]:
    root_path = Path(root)
    folder = inbox_dir(root_path)
    actions: list[InboxAction] = []
    for path in sorted(folder.iterdir(), key=_safe_mtime):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        action = install_source_file(path, root_path, move=True)
        actions.append(action)
    return actions


def save_uploaded_to_inbox(raw: bytes, filename: str, root: str | Path) -> Path:
    safe_name = Path(filename).name
    destination = inbox_dir(root) / safe_name
    destination.write_bytes(raw)
    return destination
