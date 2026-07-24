"""Gestor local y persistente de fuentes para POPIS 4.x.

Los datos nominales SINAVE permanecen SOLO en la computadora del usuario.
Las fuentes se almacenan fuera de la carpeta de cada versión, en
%LOCALAPPDATA%/POPIS4/data (Windows), para que actualizar el programa no deje
las bases atrás.

Desde POPIS 4.4, una actualización semanal SUIVE se valida ANTES de reemplazar
el corte anterior. Un archivo que no contenga una serie positiva del año actual
no puede borrar silenciosamente los datos válidos ya existentes.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from io import BytesIO
from pathlib import Path
import os
import shutil

import pandas as pd

import popis_core as core
from popis_population import read_population_projection

ROOT = Path(__file__).resolve().parent
LEGACY_DATA = ROOT / "data"

if os.environ.get("POPIS_DATA_DIR"):
    DATA = Path(os.environ["POPIS_DATA_DIR"]).expanduser()
else:
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        DATA = Path(local_appdata) / "POPIS4" / "data"
    else:
        DATA = Path.home() / ".popis4" / "data"

SINAVE_HIST = DATA / "sinave" / "historico"
SINAVE_CURRENT = DATA / "sinave" / "actual"
SUIVE_HIST = DATA / "suive" / "historico"
SUIVE_CURRENT = DATA / "suive" / "actual"
POPULATION_DIR = DATA / "poblacion"

TABLE_EXTS = {".xls", ".xlsx", ".xlsm", ".csv", ".txt"}
EXCEL_EXTS = {".xls", ".xlsx", ".xlsm"}


@dataclass
class SourceBundle:
    suive: pd.DataFrame
    sinave: pd.DataFrame
    population: pd.DataFrame
    inventory: pd.DataFrame
    warnings: list[str]


def _copy_missing_tree(source: Path, destination: Path) -> int:
    if not source.exists() or source.resolve() == destination.resolve():
        return 0
    copied = 0
    for src in source.rglob("*"):
        if not src.is_file():
            continue
        rel = src.relative_to(source)
        dst = destination / rel
        if dst.exists():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(src, dst)
            copied += 1
        except OSError:
            pass
    return copied


def ensure_tree() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    _copy_missing_tree(LEGACY_DATA, DATA)
    for folder in [SINAVE_HIST, SINAVE_CURRENT, SUIVE_HIST, SUIVE_CURRENT, POPULATION_DIR]:
        folder.mkdir(parents=True, exist_ok=True)


def _files(folder: Path, extensions: set[str]) -> list[Path]:
    if not folder.exists():
        return []
    return sorted([p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in extensions])


def _inventory_row(system: str, role: str, path: Path, status: str = "Disponible", detail: str = "") -> dict:
    return {
        "Sistema": system,
        "Rol": role,
        "Archivo": path.name,
        "Tamaño MB": round(path.stat().st_size / 1024 / 1024, 2) if path.exists() else None,
        "Estado": status,
        "Detalle": detail,
    }


def inspect_suive_payload(payload: bytes, filename: str) -> dict:
    """Lee un posible corte SUIVE y devuelve un diagnóstico antes de guardarlo."""
    frame = core.parse_suive_history(BytesIO(payload), filename)
    if frame.empty:
        raise ValueError("El archivo SUIVE no produjo ninguna serie semanal.")
    frame = frame.copy()
    frame["Año"] = pd.to_numeric(frame["Año"], errors="coerce")
    frame["SE"] = pd.to_numeric(frame["SE"], errors="coerce")
    frame["Casos"] = pd.to_numeric(frame["Casos"], errors="coerce")
    frame = frame.dropna(subset=["Año", "SE", "Casos"])
    if frame.empty:
        raise ValueError("El archivo SUIVE no contiene año, semana y casos numéricos reconocibles.")

    years = sorted(frame["Año"].astype(int).unique().tolist())
    latest_year = max(years)
    latest = frame[frame["Año"].eq(latest_year)].sort_values("SE")
    positive = latest[latest["Casos"].gt(0)]
    last_se = int(positive["SE"].max()) if not positive.empty else 0
    accumulated = float(latest.loc[latest["SE"].le(last_se), "Casos"].sum()) if last_se else 0.0
    last_week_cases = float(latest.loc[latest["SE"].eq(last_se), "Casos"].sum()) if last_se else 0.0

    return {
        "frame": frame,
        "years": years,
        "latest_year": latest_year,
        "last_se": last_se,
        "accumulated": accumulated,
        "last_week_cases": last_week_cases,
        "positive_weeks": int(len(positive)),
    }


def inspect_suive_upload(uploaded) -> dict:
    payload = uploaded.getvalue() if hasattr(uploaded, "getvalue") else uploaded.read()
    return inspect_suive_payload(payload, getattr(uploaded, "name", "SUIVE.xlsx"))


def _validate_weekly_suive(payload: bytes, filename: str) -> dict:
    info = inspect_suive_payload(payload, filename)
    current_year = date.today().year
    if info["latest_year"] < current_year:
        raise ValueError(
            f"El archivo semanal SUIVE termina en {info['latest_year']} y no contiene el año actual {current_year}. "
            "No se reemplazó el corte anterior."
        )
    if info["positive_weeks"] == 0 or info["accumulated"] <= 0:
        raise ValueError(
            f"La serie SUIVE {info['latest_year']} fue interpretada con 0 casos. "
            "Esto suele ocurrir cuando el libro trae fórmulas sin valores calculados o se seleccionó una tabla incorrecta. "
            "No se reemplazó el corte anterior."
        )
    return info


def load_preloaded_sources() -> SourceBundle:
    ensure_tree()
    warnings: list[str] = []
    inventory: list[dict] = []

    sinave_paths = _files(SINAVE_HIST, TABLE_EXTS) + _files(SINAVE_CURRENT, TABLE_EXTS)
    sinave = pd.DataFrame()
    if sinave_paths:
        try:
            sinave = core.combine_sinave([(p, p.name) for p in sinave_paths])
            for p in sinave_paths:
                role = "Actual semanal" if p.parent == SINAVE_CURRENT else "Histórico"
                inventory.append(_inventory_row("SINAVE", role, p))
        except Exception as exc:
            warnings.append(f"SINAVE precargado: {exc}")
            for p in sinave_paths:
                inventory.append(_inventory_row("SINAVE", "Local", p, "Error", str(exc)))

    # SUIVE: histórico y actual. El actual reemplaza solamente Año-SE coincidente.
    suive_frames: list[pd.DataFrame] = []
    for role, folder in [("Histórico", SUIVE_HIST), ("Actual semanal", SUIVE_CURRENT)]:
        for p in _files(folder, EXCEL_EXTS):
            try:
                frame = core.parse_suive_history(p, p.name)
                # Protección adicional: un corte semanal completamente cero no debe
                # anular una serie histórica positiva del mismo año.
                if role == "Actual semanal":
                    latest_year = int(pd.to_numeric(frame["Año"], errors="coerce").max())
                    latest = frame[pd.to_numeric(frame["Año"], errors="coerce").eq(latest_year)]
                    if latest.empty or pd.to_numeric(latest["Casos"], errors="coerce").fillna(0).gt(0).sum() == 0:
                        raise ValueError(f"corte semanal {latest_year} interpretado con 0 casos; se conserva el histórico")
                frame["_role"] = role
                frame["_source"] = p.name
                suive_frames.append(frame)
                inventory.append(_inventory_row("SUIVE", role, p))
            except Exception as exc:
                warnings.append(f"SUIVE {p.name}: {exc}")
                inventory.append(_inventory_row("SUIVE", role, p, "Error", str(exc)))
    if suive_frames:
        suive = pd.concat(suive_frames, ignore_index=True)
        order = pd.Categorical(suive["_role"], categories=["Histórico", "Actual semanal"], ordered=True)
        suive = suive.assign(_order=order).sort_values(["Año", "SE", "_order"])
        suive = suive.drop_duplicates(["Año", "SE"], keep="last").drop(columns=["_order"])
    else:
        suive = pd.DataFrame()

    pop_files = _files(POPULATION_DIR, TABLE_EXTS)
    population = pd.DataFrame()
    if pop_files:
        p = max(pop_files, key=lambda x: x.stat().st_mtime)
        try:
            population = read_population_projection(p, p.name)
            years = pd.to_numeric(population.get("Año", pd.Series(dtype=float)), errors="coerce").dropna()
            detail = f"{len(population):,} filas; {int(years.min())}-{int(years.max())}" if len(years) else f"{len(population):,} filas"
            inventory.append(_inventory_row("POBLACIÓN", "Municipio × edad × sexo", p, detail=detail))
        except Exception as exc:
            warnings.append(f"Población {p.name}: {exc}")
            inventory.append(_inventory_row("POBLACIÓN", "Denominadores", p, "Error", str(exc)))

    if not inventory:
        warnings.append(f"No se encontraron fuentes locales en: {DATA}")

    return SourceBundle(
        suive=suive,
        sinave=sinave,
        population=population,
        inventory=pd.DataFrame(inventory),
        warnings=warnings,
    )


def save_current(uploaded, system: str) -> Path:
    """Valida y reemplaza atómicamente una fuente semanal."""
    ensure_tree()
    system = system.upper().strip()
    payload = uploaded.getvalue() if hasattr(uploaded, "getvalue") else uploaded.read()
    suffix = Path(uploaded.name).suffix.lower()

    if system == "SINAVE":
        folder = SINAVE_CURRENT
        destination = folder / f"Diarreas_actual{suffix}"
    elif system == "SUIVE":
        folder = SUIVE_CURRENT
        destination = folder / f"SUIVE_actual{suffix}"
        _validate_weekly_suive(payload, uploaded.name)
    else:
        raise ValueError("system debe ser SINAVE o SUIVE")

    # Primero escribir temporalmente. Solo después borrar el corte anterior.
    temp = folder / f".__popis_tmp__{suffix}"
    temp.write_bytes(payload)
    for old in _files(folder, TABLE_EXTS):
        if old != temp:
            old.unlink(missing_ok=True)
    temp.replace(destination)
    return destination


def add_historical(uploaded, system: str) -> Path:
    ensure_tree()
    system = system.upper().strip()
    folder = SINAVE_HIST if system == "SINAVE" else SUIVE_HIST if system == "SUIVE" else None
    if folder is None:
        raise ValueError("system debe ser SINAVE o SUIVE")
    destination = folder / Path(uploaded.name).name
    if destination.exists():
        raise FileExistsError(f"Ya existe {destination.name} en históricos")
    payload = uploaded.getvalue() if hasattr(uploaded, "getvalue") else uploaded.read()
    destination.write_bytes(payload)
    return destination


def save_population(uploaded) -> Path:
    ensure_tree()
    destination = POPULATION_DIR / f"Sonora_Poblacion_Municipal_Edad_Sexo{Path(uploaded.name).suffix.lower()}"
    for old in _files(POPULATION_DIR, TABLE_EXTS):
        old.unlink(missing_ok=True)
    payload = uploaded.getvalue() if hasattr(uploaded, "getvalue") else uploaded.read()
    destination.write_bytes(payload)
    return destination
