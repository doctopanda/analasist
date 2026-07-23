@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

title POPIS 4.0.1 - SUIVE + SINAVE
set "VENV=%LOCALAPPDATA%\POPIS4\venv"
set "PY=%VENV%\Scripts\python.exe"
set "PORT="

echo ===============================================================
echo  POPIS 4.0.1 - SUIVE + SINAVE + INDICADORES + TERRITORIO
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
  echo [1/5] Entorno POPIS 4 localizado.
)

echo [2/5] Verificando dependencias...
"%PY%" -m pip install --disable-pip-version-check --no-cache-dir -r requirements.txt
if errorlevel 1 goto :install_error

echo [3/5] Verificando Streamlit y motor POPIS 4...
"%PY%" -c "import streamlit, pandas, openpyxl; import popis_core, popis_core_patch; print('Streamlit', streamlit.__version__, '- POPIS 4 engine OK')"
if errorlevel 1 goto :install_error

echo [4/5] Buscando puerto libre exclusivo para POPIS 4...
for /f %%P in ('powershell -NoProfile -Command "$u=(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue).LocalPort; (8504..8514 ^| Where-Object {$_ -notin $u} ^| Select-Object -First 1)"') do set "PORT=%%P"
if not defined PORT set "PORT=8504"
echo       Puerto seleccionado: !PORT!

echo [5/5] Iniciando POPIS 4.0.1...
echo.
echo ===============================================================
echo  DIRECCION POPIS 4: http://127.0.0.1:!PORT!
echo  La pantalla debe decir: POPIS 4.0.1
 echo ===============================================================
echo.

start "" cmd /c "timeout /t 3 /nobreak ^>nul & start \"\" http://127.0.0.1:!PORT!"
"%PY%" -m streamlit run app_bootstrap.py --server.address 127.0.0.1 --server.port !PORT! --browser.gatherUsageStats false
exit /b %errorlevel%

:python_error
echo.
echo ERROR: No pude crear el entorno Python.
echo Instala Python 3.12 desde python.org o verifica que el comando py/python funcione.
pause
exit /b 1

:install_error
echo.
echo ERROR: Fallo la instalacion o verificacion de dependencias.
echo Ejecuta REPARAR_POPIS.bat y vuelve a intentar.
pause
exit /b 1
