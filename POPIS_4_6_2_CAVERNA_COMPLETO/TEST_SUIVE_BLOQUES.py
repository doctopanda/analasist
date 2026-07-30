from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd

from modulos.suive import current_cutoff, load_suive


def make_multiblock_book(path: Path) -> None:
    rows: list[list[object]] = []
    rows.append(["", "", "Año \\ SE", *range(1, 54), "POBLACIÓN"])
    for year in range(2018, 2026):
        rows.append(["", "", year, *[1000 + (year - 2018) * 10 + week for week in range(1, 54)], 3_000_000 + year])
    rows.append(["", "", 2026, 1335, 1300, 1400, 1160, *([None] * 49), 3_168_624])
    rows.append([])
    rows.append(["", "", "Incidencia acumulada:"])
    rows.append(["", "", "Año \\ SE", *range(1, 54)])
    for year in range(2018, 2027):
        rows.append(["", "", year, *([0.0] * 53)])
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame(rows).to_excel(writer, sheet_name="SUIVE", index=False, header=False)
        pd.DataFrame({"SINAVE": []}).to_excel(writer, sheet_name="SINAVE", index=False)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "Canal endemico EDAs_SUIVE_SINAVE.xlsx"
        make_multiblock_book(path)
        suive = load_suive(path)
        current = suive[suive["Año"].eq(2026)].sort_values("Semana")
        assert current["Semana"].tolist() == [1, 2, 3, 4]
        assert current["Casos"].tolist() == [1335.0, 1300.0, 1400.0, 1160.0]
        assert current_cutoff(suive, 2026) == 4
        assert float(suive.loc[suive["Año"].eq(2018) & suive["Semana"].eq(1), "Casos"].iloc[0]) == 1001.0
        assert not ((suive["Año"].eq(2026)) & suive["Semana"].gt(4)).any()
        print("SUIVE multibloque: bloque bruto seleccionado y corte 2026 preservado")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
