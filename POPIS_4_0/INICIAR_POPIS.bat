@echo off
setlocal EnableExtensions
cd /d "%~dp0"

title POPIS 4.0
set "VENV=%LOCALAPPDATA%\POPIS4\venv"
set "PY=%VENV%\Scripts\python.exe"

echo ===============================================================
echo  POPIS 4.0 - Procesador Operativo de Patogenos e Indicadores
echo ===============================================================
echo.

if not exist "%PY%" (
  echo [1/4] Creando entorno virtual aislado en:
  echo       %VENV%
  if not exist "%LOCALAPPDATA%\POPIS4" mkdir "%LOCALAPPDATA%\POPIS4"
  py -3.12 -m venv "%VENV%" 2>nul
  if errorlevel 1 python -m venv "%VENV%"
  if errorlevel 1 goto :python_error
) else (
  echo [1/4] Entorno POPIS localizado.
)

echo [2/4] Verificando dependencias...
"%PY%" -m pip install --disable-pip-version-check --no-cache-dir -r requirements.txt
if errorlevel 1 goto :install_error

echo [3/4] Verificando Streamlit...
"%PY%" -c "import streamlit, pandas, openpyxl; print('Streamlit', streamlit.__version__, '- OK')"
if errorlevel 1 goto :install_error

echo [4/4] Iniciando POPIS 4.0...
echo.
echo Abre: http://127.0.0.1:8501
echo Para detener POPIS, cierra esta ventana o presiona Ctrl+C.
echo.
start "" "http://127.0.0.1:8501"
"%PY%" -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
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
