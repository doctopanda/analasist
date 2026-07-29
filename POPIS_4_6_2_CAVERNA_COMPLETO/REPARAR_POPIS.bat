@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
set "BASE=%LOCALAPPDATA%\POPIS462"
set "VENV=%BASE%\venv"

echo ===============================================================
echo  POPIS 4.6.2 CAVERNA - REPARACION DEL ENTORNO
echo ===============================================================
echo Este procedimiento SOLO reconstruye el entorno Python.
echo No elimina data, salidas, cartografia ni respaldos del proyecto.
echo.

if exist "%VENV%" (
  echo Eliminando entorno virtual dañado...
  rmdir /s /q "%VENV%"
)

set "PY_CMD="
py -3.12 -c "import sys" >nul 2>&1
if not errorlevel 1 set "PY_CMD=py -3.12"
if not defined PY_CMD (
  py -3 -c "import sys" >nul 2>&1
  if not errorlevel 1 set "PY_CMD=py -3"
)
if not defined PY_CMD (
  python -c "import sys" >nul 2>&1
  if not errorlevel 1 set "PY_CMD=python"
)
if not defined PY_CMD (
  echo ERROR: no se encontro Python 3.
  pause
  exit /b 1
)

if not exist "%BASE%" mkdir "%BASE%"
%PY_CMD% -m venv "%VENV%"
if errorlevel 1 goto :error
"%VENV%\Scripts\python.exe" -m pip install --disable-pip-version-check --upgrade pip
if errorlevel 1 goto :error
"%VENV%\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto :error

echo.
echo Reparacion terminada correctamente.
echo Ejecuta INICIAR_POPIS.bat.
pause
exit /b 0

:error
echo.
echo ERROR: no fue posible reconstruir el entorno POPIS.
pause
exit /b 2
