from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from .io_utils import Assets, discover_assets, ensure_structure, process_inbox
from .sinave import load_bundle
from .suive import load_suive
from .territorio import ensure_sonora_geojson, load_geojson, normalize_population


@dataclass
class RuntimeContext:
    root: Path
    assets: Assets
    sinave: pd.DataFrame = field(default_factory=pd.DataFrame)
    suive: pd.DataFrame = field(default_factory=pd.DataFrame)
    population: pd.DataFrame | None = None
    geojson: dict | None = None
    current_year: int | None = None
    cutoff_week: int | None = None
    inbox_messages: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def has_sinave(self) -> bool:
        return not self.sinave.empty

    @property
    def has_suive(self) -> bool:
        return not self.suive.empty

    @property
    def cutoff_label(self) -> str:
        if self.current_year and self.cutoff_week:
            return f"SE {self.cutoff_week} · {self.current_year}"
        if self.current_year:
            return str(self.current_year)
        return "Sin corte"


def load_runtime(root: str | Path | None = None, process_updates: bool = True,
                 allow_geo_download: bool = True) -> RuntimeContext:
    root = ensure_structure(root)
    inbox_messages: list[str] = []
    if process_updates:
        try:
            inbox_messages = process_inbox(root)
        except Exception as exc:
            inbox_messages = [f"No fue posible procesar data/entrada: {exc}"]

    assets = discover_assets(root)
    warnings = list(assets.warnings)

    sinave = pd.DataFrame()
    if assets.sinave_by_year:
        try:
            sinave = load_bundle(assets)
        except Exception as exc:
            warnings.append(f"SINAVE: {exc}")

    suive = pd.DataFrame()
    if assets.suive_file:
        try:
            suive = load_suive(assets.suive_file)
        except Exception as exc:
            warnings.append(f"SUIVE/SUAVE: {exc}")

    current_year = assets.current_year
    if current_year is None:
        years = []
        if not sinave.empty and "Año" in sinave:
            years.extend(pd.to_numeric(sinave["Año"], errors="coerce").dropna().astype(int).tolist())
        if not suive.empty:
            years.extend(pd.to_numeric(suive["Año"], errors="coerce").dropna().astype(int).tolist())
        current_year = max(years) if years else None

    cutoff_week = assets.cutoff_week
    if cutoff_week is None and current_year and not suive.empty:
        weeks = suive.loc[suive["Año"].eq(current_year), "Semana"]
        cutoff_week = int(weeks.max()) if not weeks.empty else None

    population = None
    if assets.population_file:
        population = normalize_population(assets.population_file, current_year)
        if population is None:
            warnings.append(f"No fue posible normalizar población desde {assets.population_file.name}.")

    geo_path = assets.municipal_geojson
    if geo_path is None and allow_geo_download:
        geo_path = ensure_sonora_geojson(root)
        if geo_path:
            assets.municipal_geojson = geo_path
    geojson = load_geojson(geo_path)
    if geojson is None and geo_path:
        warnings.append(f"No fue posible leer la cartografía {Path(geo_path).name}.")

    return RuntimeContext(
        root=root,
        assets=assets,
        sinave=sinave,
        suive=suive,
        population=population,
        geojson=geojson,
        current_year=current_year,
        cutoff_week=cutoff_week,
        inbox_messages=inbox_messages,
        warnings=warnings,
    )


def system_status(ctx: RuntimeContext) -> pd.DataFrame:
    return pd.DataFrame([
        {"Componente": "SINAVE", "Estado": "Listo" if ctx.has_sinave else "Sin fuente", "Fuente": ctx.assets.current_sinave.name if ctx.assets.current_sinave else ""},
        {"Componente": "SUIVE/SUAVE", "Estado": "Listo" if ctx.has_suive else "Sin fuente", "Fuente": ctx.assets.suive_file.name if ctx.assets.suive_file else ""},
        {"Componente": "Población", "Estado": "Listo" if ctx.population is not None and not ctx.population.empty else "Sin fuente compatible", "Fuente": ctx.assets.population_file.name if ctx.assets.population_file else ""},
        {"Componente": "Cartografía municipal", "Estado": "Listo" if ctx.geojson else "No disponible", "Fuente": ctx.assets.municipal_geojson.name if ctx.assets.municipal_geojson else ""},
        {"Componente": "Bandeja de actualización", "Estado": "Activa", "Fuente": "data/entrada"},
    ])
