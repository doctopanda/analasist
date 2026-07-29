from __future__ import annotations

import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
THEME_MARKER = "# POPIS_CAVERNA_THEME"


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
        try:
            relative = destination.relative_to(destination.parents[2])
        except Exception:
            relative = Path(destination.parent.name) / destination.name
        backup_path = backup_root / relative
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(destination, backup_path)
    shutil.copy2(source, destination)


def backup_file(path: Path, target: Path, backup_root: Path) -> None:
    if not path.exists():
        return
    try:
        relative = path.relative_to(target)
    except ValueError:
        relative = Path(path.name)
    backup_path = backup_root / relative
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, backup_path)


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
            fh.write("\n# POPIS territorio integrado\n")
            for line in additions:
                fh.write(line + "\n")


def _set_page_config_end_line(tree: ast.AST) -> int | None:
    candidates: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "set_page_config":
            candidates.append(int(getattr(node, "end_lineno", node.lineno)))
    return min(candidates) if candidates else None


def _imports_end_line(tree: ast.Module) -> int:
    end_line = 0
    for i, node in enumerate(tree.body):
        if i == 0 and isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant):
            if isinstance(node.value.value, str):
                end_line = int(getattr(node, "end_lineno", node.lineno))
                continue
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            end_line = int(getattr(node, "end_lineno", node.lineno))
            continue
        break
    return end_line


def apply_theme_to_script(path: Path, target: Path, backup_root: Path) -> bool:
    """Inyecta el tema después de set_page_config, sin alterar la lógica de la página."""
    if not path.exists() or path.name == "tema_caverna.py":
        return False

    text = path.read_text(encoding="utf-8", errors="ignore")
    if THEME_MARKER in text or "aplicar_tema_caverna()" in text:
        return False

    try:
        tree = ast.parse(text)
    except SyntaxError:
        print(f"AVISO: no se pudo aplicar tema automáticamente a {path.name}; sintaxis no interpretable.")
        return False

    insert_after = _set_page_config_end_line(tree)
    if insert_after is None:
        insert_after = _imports_end_line(tree)

    lines = text.splitlines(keepends=True)
    injection = (
        "\n"
        f"{THEME_MARKER}\n"
        "from modulos.tema_caverna import aplicar_tema_caverna\n"
        "aplicar_tema_caverna()\n"
        "\n"
    )

    backup_file(path, target, backup_root)
    lines.insert(max(0, insert_after), injection)
    path.write_text("".join(lines), encoding="utf-8")
    return True


def patch_existing_pages(target: Path, backup_root: Path) -> list[str]:
    candidates: list[Path] = []
    app = target / "app.py"
    if app.exists():
        candidates.append(app)
    pages = target / "pages"
    if pages.exists():
        candidates.extend(sorted(p for p in pages.glob("*.py") if p.is_file()))

    patched: list[str] = []
    for path in candidates:
        if apply_theme_to_script(path, target, backup_root):
            patched.append(str(path.relative_to(target)))
    return patched


def main() -> None:
    target = resolve_target()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = target / f"backup_POPIS_CAVERNA_{stamp}"
    backup_root.mkdir(parents=True, exist_ok=True)

    files = [
        (SOURCE / "pages" / "00_Centro_de_Datos.py", target / "pages" / "00_Centro_de_Datos.py"),
        (SOURCE / "pages" / "08_Mapa_Territorial.py", target / "pages" / "08_Mapa_Territorial.py"),
        (SOURCE / "modulos" / "autocarga.py", target / "modulos" / "autocarga.py"),
        (SOURCE / "modulos" / "mapa_integrado.py", target / "modulos" / "mapa_integrado.py"),
        (SOURCE / "modulos" / "mapa_espacial.py", target / "modulos" / "mapa_espacial.py"),
        (SOURCE / "modulos" / "tema_caverna.py", target / "modulos" / "tema_caverna.py"),
        (SOURCE / ".streamlit" / "config.toml", target / ".streamlit" / "config.toml"),
    ]

    missing = [str(source.relative_to(SOURCE)) for source, _ in files if not source.exists()]
    if missing:
        raise SystemExit("Paquete incompleto: " + ", ".join(missing))

    for relative in (
        "pages", "modulos", ".streamlit", "data/entrada", "data/backups", "data/geografia",
        "data/poblacion", "data/coordenadas", "data/suive",
    ):
        (target / relative).mkdir(parents=True, exist_ok=True)

    init_file = target / "modulos" / "__init__.py"
    if not init_file.exists():
        init_file.write_text("# Modulos POPIS\n", encoding="utf-8")

    for source, destination in files:
        copy_with_backup(source, destination, backup_root)

    append_requirements(target)
    patched = patch_existing_pages(target, backup_root)

    (target / "POPIS_VISUAL_CAVERNA.txt").write_text(
        "POPIS 4.8 - VISUAL CAVERNA\n"
        "Tema: azul marino + coral/rosa + tarjetas clínicas + sidebar CAVERNA\n"
        f"Scripts tematizados automaticamente: {len(patched)}\n",
        encoding="utf-8",
    )

    print("POPIS actualizado con visual CAVERNA correctamente.")
    print(f"Destino: {target}")
    print(f"Respaldo: {backup_root}")
    print(f"Paginas tematizadas: {len(patched)}")
    for item in patched:
        print(f"  - {item}")
    print("Abre POPIS con tu INICIAR_POPIS.bat habitual.")


if __name__ == "__main__":
    main()
