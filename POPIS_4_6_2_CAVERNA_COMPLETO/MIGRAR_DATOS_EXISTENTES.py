from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

DATA_DIRS = ["historicos", "actual", "suive", "poblacion", "geografia"]


def has_popis_data(path: Path) -> bool:
    data = path / "data"
    if not data.is_dir():
        return False
    return any((data / name).is_dir() and any((data / name).iterdir()) for name in DATA_DIRS)


def candidates(current: Path) -> list[Path]:
    found: list[Path] = []
    roots = [current.parent, Path.home(), Path.home() / "Documents", Path.home() / "Documentos"]
    seen: set[Path] = set()
    for base in roots:
        if not base.exists():
            continue
        try:
            children = list(base.glob("POPIS*")) + list(base.glob("popis*"))
        except Exception:
            continue
        for child in children:
            try:
                resolved = child.resolve()
            except Exception:
                continue
            if resolved == current.resolve() or resolved in seen or not resolved.is_dir():
                continue
            seen.add(resolved)
            if has_popis_data(resolved):
                found.append(resolved)
    return sorted(found, key=lambda p: p.stat().st_mtime, reverse=True)


def copy_missing(source: Path, destination: Path) -> tuple[int, int]:
    copied = skipped = 0
    if not source.exists():
        return copied, skipped
    destination.mkdir(parents=True, exist_ok=True)
    for item in source.rglob("*"):
        if not item.is_file():
            continue
        relative = item.relative_to(source)
        target = destination / relative
        if target.exists():
            skipped += 1
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
        copied += 1
    return copied, skipped


def migrate(source: Path, current: Path) -> None:
    print(f"Origen detectado: {source}")
    total_copied = total_skipped = 0
    for name in DATA_DIRS:
        copied, skipped = copy_missing(source / "data" / name, current / "data" / name)
        total_copied += copied
        total_skipped += skipped
        print(f"  data/{name}: {copied} copiado(s), {skipped} existente(s) conservado(s)")
    print(f"Migración terminada: {total_copied} archivo(s) copiado(s). No se eliminó nada del origen.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Migración no destructiva de datos POPIS")
    parser.add_argument("source", nargs="?", help="Ruta a POPIS anterior")
    parser.add_argument("--auto", action="store_true", help="Detectar automáticamente una instalación vecina")
    args = parser.parse_args()
    current = Path(__file__).resolve().parent
    source = Path(args.source).expanduser().resolve() if args.source else None
    if source is None and args.auto:
        options = candidates(current)
        if options:
            source = options[0]
    if source is None:
        print("No se encontró una instalación POPIS anterior con datos. Se continúa con instalación limpia.")
        return 0
    if not source.exists() or not has_popis_data(source):
        print(f"La ruta no contiene datos POPIS reconocibles: {source}")
        return 0
    migrate(source, current)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
