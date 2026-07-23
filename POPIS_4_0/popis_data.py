"""Gestor local de fuentes para POPIS 4.x.

Los datos nominales SINAVE se mantienen SOLO en la computadora del usuario.
Este módulo busca históricos congelados y archivos actuales en data/ y permite
reemplazar el archivo semanal sin volver a cargar todo desde la interfaz.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import shutil

import pandas as pd

import popis_core as core

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
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


def ensure_tree() -> None:
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


def load_preloaded_sources() -> SourceBundle:
    """Carga los datos locales. Los archivos actuales prevalecen sobre históricos SUIVE."""
    ensure_tree()
    warnings: list[str] = []
    inventory: list[dict] = []

    # SINAVE nominal: históricos + archivo semanal actual. El actual se coloca al final
    # para que el combinador pueda preferir la versión más reciente de un folio repetido.
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

    # SUIVE puede tener un workbook histórico y otro actual. Si ambos incluyen la misma
    # combinación Año-SE, el archivo actual reemplaza el valor histórico.
    suive_frames: list[pd.DataFrame] = []
    for role, folder in [("Histórico", SUIVE_HIST), ("Actual semanal", SUIVE_CURRENT)]:
        for p in _files(folder, EXCEL_EXTS):
            try:
                frame = core.parse_suive_history(p, p.name)
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

    # Población: se utiliza el archivo más reciente por fecha de modificación.
    pop_files = _files(POPULATION_DIR, TABLE_EXTS)
    population = pd.DataFrame()
    if pop_files:
        p = max(pop_files, key=lambda x: x.stat().st_mtime)
        try:
            population = core.read_any_table(p, p.name)
            inventory.append(_inventory_row("CONAPO", "Denominadores", p))
        except Exception as exc:
            warnings.append(f"Población {p.name}: {exc}")
            inventory.append(_inventory_row("CONAPO", "Denominadores", p, "Error", str(exc)))

    return SourceBundle(
        suive=suive,
        sinave=sinave,
        population=population,
        inventory=pd.DataFrame(inventory),
        warnings=warnings,
    )


def save_current(uploaded, system: str) -> Path:
    """Guarda/reemplaza una fuente semanal desde un UploadedFile de Streamlit."""
    ensure_tree()
    system = system.upper().strip()
    if system == "SINAVE":
        destination = SINAVE_CURRENT / f"Diarreas_actual{Path(uploaded.name).suffix.lower()}"
        # Un solo archivo actual: elimina versiones previas para evitar duplicidad.
        for old in _files(SINAVE_CURRENT, TABLE_EXTS):
            old.unlink(missing_ok=True)
    elif system == "SUIVE":
        destination = SUIVE_CURRENT / f"SUIVE_actual{Path(uploaded.name).suffix.lower()}"
        for old in _files(SUIVE_CURRENT, TABLE_EXTS):
            old.unlink(missing_ok=True)
    else:
        raise ValueError("system debe ser SINAVE o SUIVE")
    payload = uploaded.getvalue() if hasattr(uploaded, "getvalue") else uploaded.read()
    destination.write_bytes(payload)
    return destination


def add_historical(uploaded, system: str) -> Path:
    """Agrega un histórico anual. No sobreescribe silenciosamente otro histórico."""
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
    destination = POPULATION_DIR / f"Sonora_CONAPO{Path(uploaded.name).suffix.lower()}"
    for old in _files(POPULATION_DIR, TABLE_EXTS):
        old.unlink(missing_ok=True)
    payload = uploaded.getvalue() if hasattr(uploaded, "getvalue") else uploaded.read()
    destination.write_bytes(payload)
    return destination
