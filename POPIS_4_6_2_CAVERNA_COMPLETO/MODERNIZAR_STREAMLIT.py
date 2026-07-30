from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent
LEGACY_KEY = "use_" + "container_width"
REPLACEMENTS = {
    f"{LEGACY_KEY}=True": 'width="stretch"',
    f"{LEGACY_KEY} = True": 'width="stretch"',
    f"{LEGACY_KEY}=False": 'width="content"',
    f"{LEGACY_KEY} = False": 'width="content"',
}


def modernize_file(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    updated = text
    for old, new in REPLACEMENTS.items():
        updated = updated.replace(old, new)
    if updated == text:
        return 0
    path.write_text(updated, encoding="utf-8", newline="\n")
    return 1


def main() -> int:
    targets = [ROOT / "app.py", *sorted((ROOT / "pages").glob("*.py"))]
    changed = sum(modernize_file(path) for path in targets if path.exists())
    remaining = []
    for path in targets:
        if path.exists() and LEGACY_KEY in path.read_text(encoding="utf-8"):
            remaining.append(str(path.relative_to(ROOT)))
    if remaining:
        print("API heredada aún presente en:")
        for item in remaining:
            print(" -", item)
        return 2
    print(f"Compatibilidad Streamlit modernizada: {changed} archivo(s) actualizado(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
