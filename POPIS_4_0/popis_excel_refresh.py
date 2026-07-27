"""Automatización local del Cubo SUIVE mediante Microsoft Excel.

POPIS no envía el archivo a Internet. En Windows, usa PowerShell + COM para:
abrir el libro registrado, ejecutar RefreshAll, esperar consultas asíncronas,
recalcular, guardar y cerrar. Después valida el resultado con el lector SUIVE
multiformato y promueve el libro actualizado al corte semanal vigente.
"""
from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import pandas as pd

import popis_data as data

CUBE_DIR = data.DATA / "suive" / "cubo"
PATH_FILE = CUBE_DIR / "source_path.txt"
SUPPORTED = {".xlsx", ".xlsm"}


@dataclass
class _UploadProxy:
    payload: bytes
    name: str

    def getvalue(self) -> bytes:
        return self.payload


def ensure_cube_dir() -> None:
    CUBE_DIR.mkdir(parents=True, exist_ok=True)


def register_cube_path(path: str | Path) -> Path:
    """Registra un libro existente SIN copiarlo, preservando rutas/conexiones."""
    ensure_cube_dir()
    p = Path(str(path).strip().strip('"')).expanduser()
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"No encuentro el archivo: {p}")
    if p.suffix.lower() not in SUPPORTED:
        raise ValueError("El cubo automático debe ser .xlsx o .xlsm")
    PATH_FILE.write_text(str(p.resolve()), encoding="utf-8")
    return p.resolve()


def save_cube_copy(uploaded) -> Path:
    """Copia un cubo cargado desde el navegador al almacén persistente local."""
    ensure_cube_dir()
    suffix = Path(uploaded.name).suffix.lower()
    if suffix not in SUPPORTED:
        raise ValueError("El cubo automático debe ser .xlsx o .xlsm")
    destination = CUBE_DIR / f"Cubo_SUIVE{suffix}"
    payload = uploaded.getvalue() if hasattr(uploaded, "getvalue") else uploaded.read()
    temp = CUBE_DIR / f".__cube_tmp__{suffix}"
    temp.write_bytes(payload)
    temp.replace(destination)
    PATH_FILE.write_text(str(destination.resolve()), encoding="utf-8")
    return destination.resolve()


def get_cube_source() -> Path | None:
    ensure_cube_dir()
    if PATH_FILE.exists():
        raw = PATH_FILE.read_text(encoding="utf-8").strip()
        if raw:
            p = Path(raw)
            if p.exists() and p.is_file():
                return p
    candidates = [p for p in CUBE_DIR.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED]
    return max(candidates, key=lambda p: p.stat().st_mtime) if candidates else None


def inspect_cube(path: str | Path | None = None) -> dict:
    p = Path(path) if path else get_cube_source()
    if p is None:
        raise FileNotFoundError("No hay un Cubo SUIVE registrado.")
    info = data.inspect_suive_payload(p.read_bytes(), p.name)
    info["path"] = str(p)
    info["modified"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(p.stat().st_mtime))
    return info


def _powershell_refresh_script() -> str:
    # Las variables sensibles/rutas se pasan en ENV para evitar problemas de comillas.
    return r'''
$ErrorActionPreference = 'Stop'
$excel = $null
$wb = $null
$path = [System.IO.Path]::GetFullPath($env:POPIS_CUBE_PATH)
$visible = ($env:POPIS_EXCEL_VISIBLE -eq '1')
$timeoutSec = [int]$env:POPIS_EXCEL_TIMEOUT
$started = Get-Date
try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $visible
    $excel.DisplayAlerts = $visible
    $excel.AskToUpdateLinks = $false
    $wb = $excel.Workbooks.Open($path, 0, $false)

    # Fuerza modo sin background cuando Excel lo permita.
    foreach ($conn in @($wb.Connections)) {
        try { $conn.OLEDBConnection.BackgroundQuery = $false } catch {}
        try { $conn.ODBCConnection.BackgroundQuery = $false } catch {}
    }

    $wb.RefreshAll()
    try { $excel.CalculateUntilAsyncQueriesDone() } catch {}

    $deadline = (Get-Date).AddSeconds($timeoutSec)
    do {
        $refreshing = $false
        foreach ($conn in @($wb.Connections)) {
            try { if ($conn.OLEDBConnection.Refreshing) { $refreshing = $true } } catch {}
            try { if ($conn.ODBCConnection.Refreshing) { $refreshing = $true } } catch {}
        }
        if (-not $refreshing) { break }
        if ((Get-Date) -gt $deadline) { throw "Tiempo de espera agotado actualizando conexiones de Excel." }
        Start-Sleep -Milliseconds 750
    } while ($true)

    # Refresca cachés de tablas dinámicas cuando existan.
    try {
        for ($i=1; $i -le $wb.PivotCaches().Count; $i++) {
            try { $wb.PivotCaches().Item($i).Refresh() } catch {}
        }
    } catch {}

    try { $excel.CalculateFullRebuild() } catch { $excel.CalculateFull() }
    $wb.Save()

    [pscustomobject]@{
        ok = $true
        workbook = $path
        connections = $wb.Connections.Count
        elapsed_seconds = [math]::Round(((Get-Date)-$started).TotalSeconds,1)
        saved_at = (Get-Date).ToString('s')
    } | ConvertTo-Json -Compress
}
catch {
    [pscustomobject]@{
        ok = $false
        workbook = $path
        error = $_.Exception.Message
    } | ConvertTo-Json -Compress
    exit 2
}
finally {
    if ($wb -ne $null) { try { $wb.Close($true) } catch {} }
    if ($excel -ne $null) { try { $excel.Quit() } catch {} }
    if ($wb -ne $null) { try { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($wb) } catch {} }
    if ($excel -ne $null) { try { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($excel) } catch {} }
    [GC]::Collect(); [GC]::WaitForPendingFinalizers()
}
'''


def refresh_excel(path: str | Path, visible: bool = False, timeout: int = 300) -> dict:
    """Ejecuta Refresh All usando Excel de escritorio instalado en Windows."""
    if os.name != "nt":
        raise RuntimeError("La actualización automática del cubo requiere Windows + Microsoft Excel de escritorio.")
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    timeout = int(max(30, min(timeout, 1800)))
    env = os.environ.copy()
    env["POPIS_CUBE_PATH"] = str(p.resolve())
    env["POPIS_EXCEL_VISIBLE"] = "1" if visible else "0"
    env["POPIS_EXCEL_TIMEOUT"] = str(timeout)
    try:
        proc = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", _powershell_refresh_script()],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=timeout + 90,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"Excel no terminó la actualización en {timeout + 90} segundos.") from exc

    lines = [ln.strip() for ln in (proc.stdout or "").splitlines() if ln.strip().startswith("{")]
    result = None
    for line in reversed(lines):
        try:
            result = json.loads(line)
            break
        except Exception:
            pass
    if proc.returncode != 0 or not result or not result.get("ok"):
        detail = (result or {}).get("error") if isinstance(result, dict) else None
        detail = detail or (proc.stderr or proc.stdout or "Error desconocido de Excel").strip()
        if "ActiveX" in detail or "COM" in detail or "80040154" in detail:
            detail += " Verifica que Microsoft Excel de escritorio esté instalado."
        raise RuntimeError(detail)
    return result


def refresh_and_promote(visible: bool = False, timeout: int = 300) -> dict:
    """Refresh Excel → valida → promueve a SUIVE actual → devuelve diagnóstico."""
    p = get_cube_source()
    if p is None:
        raise FileNotFoundError("Primero registra la ruta del Cubo SUIVE o copia un cubo a POPIS.")

    try:
        before = inspect_cube(p)
    except Exception:
        before = None

    excel_result = refresh_excel(p, visible=visible, timeout=timeout)
    after = inspect_cube(p)
    if after["positive_weeks"] <= 0 or after["accumulated"] <= 0:
        raise RuntimeError("Excel terminó, pero POPIS interpretó el cubo actualizado con cero casos. No se reemplazó SUIVE.")

    # Evitar regresión accidental frente al corte previo almacenado.
    bundle = data.load_preloaded_sources()
    current = bundle.suive
    previous_latest = None
    if current is not None and not current.empty:
        yr = int(after["latest_year"])
        y = current[pd.to_numeric(current["Año"], errors="coerce").eq(yr)].copy()
        if not y.empty:
            y["SE"] = pd.to_numeric(y["SE"], errors="coerce")
            y["Casos"] = pd.to_numeric(y["Casos"], errors="coerce")
            positive = y[y["Casos"].gt(0)]
            if not positive.empty:
                se = int(positive["SE"].max())
                accum = float(y[y["SE"].le(se)]["Casos"].sum())
                previous_latest = {"last_se": se, "accumulated": accum}

    if previous_latest:
        if after["last_se"] < previous_latest["last_se"]:
            raise RuntimeError(
                f"El cubo actualizado termina en SE{after['last_se']}, anterior a la SE{previous_latest['last_se']} vigente. "
                "No se reemplazó SUIVE."
            )
        if after["last_se"] == previous_latest["last_se"] and after["accumulated"] < previous_latest["accumulated"] * 0.8:
            raise RuntimeError(
                "El acumulado del cubo cayó más de 20% respecto al corte vigente en la misma semana. "
                "POPIS lo bloqueó para revisión."
            )

    proxy = _UploadProxy(p.read_bytes(), p.name)
    destination = data.save_current(proxy, "SUIVE")
    result = {
        "path": str(p),
        "destination": str(destination),
        "excel": excel_result,
        "before": before,
        "after": after,
        "previous_latest": previous_latest,
    }
    if before and before.get("latest_year") == after.get("latest_year"):
        result["delta_accumulated"] = after["accumulated"] - before["accumulated"]
        result["delta_week"] = after["last_se"] - before["last_se"]
    return result
