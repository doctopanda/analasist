from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path


def refresh_excel_workbook(path: str | Path, backup_root: str | Path | None = None,
                           timeout: int = 300) -> tuple[bool, str]:
    """Ejecuta RefreshAll + recálculo + guardado mediante Excel COM en Windows.

    No modifica el libro si Excel no está instalado o si la actualización falla.
    Antes de abrir el libro guarda una copia de respaldo cuando backup_root se proporciona.
    """
    workbook = Path(path).resolve()
    if not workbook.exists():
        return False, f"No existe el libro: {workbook}"
    if os.name != "nt":
        return False, "La actualización automática RefreshAll requiere Windows con Microsoft Excel instalado."
    if workbook.suffix.lower() not in {".xlsx", ".xlsm", ".xlsb", ".xls"}:
        return False, "La fuente SUIVE no es un libro Excel compatible con RefreshAll."

    if backup_root is not None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(backup_root) / stamp / "suive_refresh"
        backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(workbook, backup_dir / workbook.name)

    safe_path = str(workbook).replace("'", "''")
    script = f"""
$ErrorActionPreference = 'Stop'
$excel = $null
$book = $null
try {{
  $excel = New-Object -ComObject Excel.Application
  $excel.Visible = $false
  $excel.DisplayAlerts = $false
  $book = $excel.Workbooks.Open('{safe_path}', 0, $false)
  $book.RefreshAll()
  try {{ $excel.CalculateUntilAsyncQueriesDone() }} catch {{ }}
  $excel.CalculateFullRebuild()
  Start-Sleep -Seconds 2
  $book.Save()
  $book.Close($true)
  $book = $null
  $excel.Quit()
  $excel = $null
  Write-Output 'POPIS_SUIVE_REFRESH_OK'
}} finally {{
  if ($book -ne $null) {{ try {{ $book.Close($false) }} catch {{ }} }}
  if ($excel -ne $null) {{ try {{ $excel.Quit() }} catch {{ }} }}
  [GC]::Collect()
  [GC]::WaitForPendingFinalizers()
}}
"""
    ps1 = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".ps1", encoding="utf-8-sig", delete=False) as fh:
            fh.write(script)
            ps1 = Path(fh.name)
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps1)],
            capture_output=True, text=True, timeout=timeout, check=False,
        )
        if result.returncode == 0 and "POPIS_SUIVE_REFRESH_OK" in result.stdout:
            return True, "Excel ejecutó RefreshAll, recálculo completo y guardado correctamente."
        detail = (result.stderr or result.stdout or "Error desconocido").strip()
        return False, f"Excel no pudo completar la actualización: {detail[-1000:]}"
    except subprocess.TimeoutExpired:
        return False, f"La actualización excedió {timeout} segundos. El libro original tiene respaldo previo."
    except Exception as exc:
        return False, f"Error al ejecutar Excel: {exc}"
    finally:
        if ps1:
            ps1.unlink(missing_ok=True)
