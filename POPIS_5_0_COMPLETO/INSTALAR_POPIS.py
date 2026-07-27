from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
VENV = LOCALAPPDATA / "POPIS5" / "venv"


def python_in_venv() -> Path:
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def run(cmd: list[str]) -> None:
    print(" ".join(str(x) for x in cmd))
    subprocess.check_call([str(x) for x in cmd])


def ensure_folders() -> None:
    for p in [
        ROOT / "data" / "historicos",
        ROOT / "data" / "actual",
        ROOT / "data" / "entrada",
        ROOT / "data" / "backups",
        ROOT / "data" / "suive",
        ROOT / "data" / "poblacion",
        ROOT / "data" / "geografia",
        ROOT / "data" / "coordenadas",
        ROOT / "salidas",
    ]:
        p.mkdir(parents=True, exist_ok=True)


def candidate_old_roots() -> list[Path]:
    home = Path.home()
    candidates = [
        ROOT.parent,
        Path.cwd(),
        Path("C:/POPIS"),
        Path("C:/POPIS4"),
        home / "POPIS",
        home / "POPIS4",
        home / "Documents" / "POPIS",
        home / "Documents" / "POPIS4",
        home / "Desktop" / "POPIS",
        home / "Desktop" / "POPIS4",
        home / "Downloads" / "POPIS",
        home / "Downloads" / "POPIS4",
    ]
    # También revisa carpetas vecinas cuyo nombre contenga POPIS.
    for parent in [ROOT.parent, home / "Documents", home / "Desktop", home / "Downloads"]:
        try:
            if parent.exists():
                candidates.extend(p for p in parent.iterdir() if p.is_dir() and "popis" in p.name.lower())
        except OSError:
            pass
    unique = []
    seen = set()
    for p in candidates:
        try:
            resolved = p.resolve()
        except OSError:
            continue
        if resolved == ROOT.resolve() or str(resolved) in seen:
            continue
        seen.add(str(resolved))
        unique.append(resolved)
    return unique


def score_old_root(root: Path) -> int:
    if not root.exists() or not root.is_dir():
        return 0
    score = 0
    if (root / "data" / "historicos").exists(): score += 10
    if (root / "data" / "actual").exists(): score += 10
    if (root / "data" / "suive").exists(): score += 6
    if (root / "data" / "poblacion").exists(): score += 5
    if (root / "data" / "geografia").exists(): score += 5
    if (root / "app.py").exists(): score += 3
    try:
        score += min(10, len(list(root.rglob("Diarreas*.xls"))))
    except OSError:
        pass
    return score


def find_old_root() -> Path | None:
    ranked = sorted(((score_old_root(p), p) for p in candidate_old_roots()), reverse=True, key=lambda x: x[0])
    return ranked[0][1] if ranked and ranked[0][0] >= 5 else None


def copy_tree_non_destructive(src: Path, dst: Path) -> int:
    copied = 0
    if not src.exists():
        return copied
    for path in src.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(src)
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            continue
        try:
            shutil.copy2(path, target)
            copied += 1
        except OSError:
            pass
    return copied


def migrate_existing_data() -> None:
    old = find_old_root()
    if old is None:
        print("No se encontró una instalación POPIS anterior. La instalación limpia queda lista para recibir fuentes en data/entrada.")
        return
    print(f"Instalación POPIS anterior detectada: {old}")
    copied = 0
    if (old / "data").exists():
        copied += copy_tree_non_destructive(old / "data", ROOT / "data")
    else:
        # Rescate de diseños antiguos con carpetas separadas.
        for folder in ["historicos", "actual", "suive", "poblacion", "geografia", "coordenadas"]:
            if (old / folder).exists():
                copied += copy_tree_non_destructive(old / folder, ROOT / "data" / folder)
    print(f"Migración no destructiva terminada: {copied} archivo(s) copiado(s).")


def install_environment(repair: bool = False) -> None:
    if sys.version_info < (3, 10):
        raise RuntimeError("POPIS requiere Python 3.10 o posterior.")
    if repair and VENV.exists():
        print(f"Reparación: eliminando entorno aislado {VENV}")
        shutil.rmtree(VENV, ignore_errors=True)
    if not python_in_venv().exists():
        print(f"Creando entorno aislado en {VENV}")
        VENV.parent.mkdir(parents=True, exist_ok=True)
        venv.EnvBuilder(with_pip=True, clear=False).create(VENV)
    py = python_in_venv()
    run([str(py), "-m", "pip", "install", "--upgrade", "pip"])
    run([str(py), "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")])


def create_desktop_launcher() -> None:
    desktop = Path.home() / "Desktop"
    if not desktop.exists():
        return
    cmd = desktop / "POPIS 5.0.cmd"
    text = f'@echo off\r\ncd /d "{ROOT}"\r\ncall "{ROOT / "INICIAR_POPIS.bat"}"\r\n'
    try:
        cmd.write_text(text, encoding="utf-8")
        print(f"Acceso de inicio creado: {cmd}")
    except OSError:
        pass


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repair", action="store_true")
    parser.add_argument("--no-launch", action="store_true")
    args = parser.parse_args()
    print("=" * 66)
    print(" POPIS 5.0 TODO EN UNO · INSTALACIÓN AUTOMÁTICA")
    print(" SUIVE + SINAVE + CANALES + CENTROIDES + INDICADORES + EXPORTACIÓN")
    print("=" * 66)
    ensure_folders()
    migrate_existing_data()
    install_environment(repair=args.repair)
    create_desktop_launcher()
    print("\n✅ POPIS 5.0 quedó instalado.")
    print(f"Entorno: {VENV}")
    print(f"Aplicación: {ROOT}")
    if not args.no_launch:
        run([str(python_in_venv()), str(ROOT / "launcher.py")])


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nERROR DE INSTALACIÓN: {exc}")
        input("Presiona Enter para cerrar...")
        raise
