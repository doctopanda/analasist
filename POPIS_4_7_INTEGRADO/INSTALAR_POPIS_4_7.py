from __future__ import annotations

import shutil
import sys
from datetime import datetime
from pathlib import Path

SOURCE = Path(__file__).resolve().parent


def looks_like_popis(path: Path) -> bool:
    return path.is_dir() and any(
        (path / name).exists()
        for name in ("app.py", "popis_core.py", "INICIAR_POPIS.bat", "data")
    )


def resolve_target() -> Path:
    if len(sys.argv) > 1:
        target = Path(sys.argv[1].strip('"')).expanduser().resolve()
        if not looks_like_popis(target):
            raise SystemExit(f"La ruta no parece ser POPIS: {target}")
        return target

    for candidate in (Path.cwd().resolve(), SOURCE, SOURCE.parent):
        if looks_like_popis(candidate):
            return candidate

    typed = input("Ruta de la carpeta POPIS: ").strip().strip('"')
    target = Path(typed).expanduser().resolve()
    if not looks_like_popis(target):
        raise SystemExit(f"La ruta no parece ser POPIS: {target}")
    return target


def copy_with_backup(source: Path, destination: Path, backup_root: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        backup_dir = backup_root / destination.parent.name
        backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(destination, backup_dir / destination.name)
    shutil.copy2(source, destination)


def append_requirements(target: Path) -> None:
    path = target / "requirements.txt"
    text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
    additions = []
    if "folium" not in text.lower():
        additions.append("folium>=0.17,<1")
    if "streamlit-folium" not in text.lower():
        additions.append("streamlit-folium>=0.23,<1")
    if additions:
        with path.open("a", encoding="utf-8") as fh:
            fh.write("\n# POPIS 4.7 territorio integrado\n")
            for line in additions:
                fh.write(line + "\n")


def main() -> None:
    target = resolve_target()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = target / f"backup_POPIS_4_7_{stamp}"
    backup_root.mkdir(parents=True, exist_ok=True)

    files = [
        (SOURCE / "pages" / "00_Centro_de_Datos.py", target / "pages" / "00_Centro_de_Datos.py"),
        (SOURCE / "pages" / "08_Mapa_Territorial.py", target / "pages" / "08_Mapa_Territorial.py"),
        (SOURCE / "modulos" / "autocarga.py", target / "modulos" / "autocarga.py"),
        (SOURCE / "modulos" / "mapa_integrado.py", target / "modulos" / "mapa_integrado.py"),
        (SOURCE / "modulos" / "mapa_espacial.py", target / "modulos" / "mapa_espacial.py"),
    ]

    missing = [source.name for source, _ in files if not source.exists()]
    if missing:
        raise SystemExit("Paquete incompleto: " + ", ".join(missing))

    for relative in (
        "pages", "modulos", "data/entrada", "data/backups", "data/geografia",
        "data/poblacion", "data/coordenadas", "data/suive",
    ):
        (target / relative).mkdir(parents=True, exist_ok=True)

    init_file = target / "modulos" / "__init__.py"
    if not init_file.exists():
        init_file.write_text("# Modulos POPIS\n", encoding="utf-8")

    for source, destination in files:
        copy_with_backup(source, destination, backup_root)

    append_requirements(target)
    (target / "POPIS_4_7_INTEGRADO.txt").write_text(
        "POPIS 4.7 INTEGRADO\nCentro de Datos automatico + mapa territorial integrado\n",
        encoding="utf-8",
    )

    print("POPIS 4.7 integrado correctamente.")
    print(f"Destino: {target}")
    print(f"Respaldo: {backup_root}")
    print("Abre POPIS con tu INICIAR_POPIS.bat habitual.")


if __name__ == "__main__":
    main()
