@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

title POPIS 4.1 - DATOS PRECARGADOS
set "VENV=%LOCALAPPDATA%\POPIS4\venv"
set "PY=%VENV%\Scripts\python.exe"
set "PORT="

echo ===============================================================
echo  POPIS 4.1 - SUIVE + SINAVE + DATOS LOCALES PRECARGADOS
echo ===============================================================
echo.

if not exist "%PY%" (
  echo [1/5] Creando entorno virtual aislado en:
  echo       %VENV%
  if not exist "%LOCALAPPDATA%\POPIS4" mkdir "%LOCALAPPDATA%\POPIS4"
  py -3.12 -m venv "%VENV%" 2>nul
  if errorlevel 1 python -m venv "%VENV%"
  if errorlevel 1 goto :python_error
) else (
  echo [1/5] Entorno POPIS localizado.
)

echo [2/5] Verificando dependencias...
"%PY%" -m pip install --disable-pip-version-check --no-cache-dir -r requirements.txt
if errorlevel 1 goto :install_error

echo [3/5] Verificando motor POPIS 4.1...
"%PY%" -c "import streamlit,pandas,openpyxl; import popis_core,popis_core_patch,popis_data; print('Motor POPIS 4.1 OK')"
if errorlevel 1 goto :install_error

echo [4/5] Buscando puerto libre...
for /f %%P in ('powershell -NoProfile -Command "$u=(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue).LocalPort; (8504..8514 ^| Where-Object {$_ -notin $u} ^| Select-Object -First 1)"') do set "PORT=%%P"
if not defined PORT set "PORT=8504"
echo       Puerto: !PORT!

echo [5/5] Iniciando POPIS 4.1...
echo.
echo ===============================================================
echo  http://127.0.0.1:!PORT!
echo  Debes ver: POPIS 4.1.0-data
echo ===============================================================
echo.

REM Abrir navegador sin usar comillas escapadas con barra invertida.
start "" powershell.exe -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 3; Start-Process 'http://127.0.0.1:!PORT!'"

REM Mantener Streamlit en primer plano mientras POPIS este abierto.
"%PY%" -m streamlit run app_bootstrap.py --server.address 127.0.0.1 --server.port !PORT! --browser.gatherUsageStats false
exit /b %errorlevel%

:python_error
echo.
echo ERROR: no pude crear el entorno Python.
pause
exit /b 1

:install_error
echo.
echo ERROR: fallo la instalacion o verificacion. Ejecuta REPARAR_POPIS.bat.
pause
exit /b 1
