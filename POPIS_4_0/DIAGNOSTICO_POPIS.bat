@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "VENV=%LOCALAPPDATA%\POPIS4\venv"
set "PY=%VENV%\Scripts\python.exe"
echo ===============================================================
echo  DIAGNOSTICO POPIS 4.0
echo ===============================================================
echo Proyecto: %CD%
echo Entorno:  %VENV%
echo.
where py 2>nul
where python 2>nul
if exist "%PY%" (
  echo.
  "%PY%" --version
  "%PY%" -c "import sys; print('Ejecutable:', sys.executable)"
  "%PY%" -c "import streamlit,pandas,numpy,openpyxl; print('Streamlit',streamlit.__version__); print('Pandas',pandas.__version__); print('Numpy',numpy.__version__); print('Openpyxl',openpyxl.__version__)"
) else (
  echo.
  echo El entorno POPIS todavia no existe.
)
echo.
for %%F in (app.py popis_core.py requirements.txt INICIAR_POPIS.bat) do (
  if exist "%%F" (echo [OK] %%F) else (echo [FALTA] %%F)
)
pause
