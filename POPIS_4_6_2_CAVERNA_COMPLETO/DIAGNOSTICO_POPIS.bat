@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
set "VENV=%LOCALAPPDATA%\POPIS462\venv"

echo ===============================================================
echo  POPIS 4.6.2 CAVERNA - DIAGNOSTICO
echo ===============================================================
echo Proyecto: %CD%
echo Entorno:  %VENV%
echo.

echo [Archivos principales]
for %%F in (app.py requirements.txt VERSION.txt) do (
  if exist "%%F" (echo OK  %%F) else (echo FALTA %%F)
)
echo.

if exist "%VENV%\Scripts\python.exe" (
  echo [Python POPIS]
  "%VENV%\Scripts\python.exe" --version
  "%VENV%\Scripts\python.exe" -c "import sys; print(sys.executable)"
  echo.
  echo [Paquetes]
  "%VENV%\Scripts\python.exe" -c "import streamlit,pandas,numpy,plotly,folium,openpyxl; print('streamlit',streamlit.__version__); print('pandas',pandas.__version__); print('numpy',numpy.__version__)"
  echo.
  echo [Compilacion]
  "%VENV%\Scripts\python.exe" -m compileall -q app.py modulos pages
  if errorlevel 1 (echo ERROR DE COMPILACION) else (echo Codigo Python OK)
  echo.
  echo [Fuentes detectadas]
  "%VENV%\Scripts\python.exe" -c "from modulos.runtime import load_runtime,system_status; c=load_runtime(process_updates=False,allow_geo_download=False); print(system_status(c).to_string(index=False)); print('Corte:',c.cutoff_label); print('SINAVE filas:',len(c.sinave)); print('SUIVE filas:',len(c.suive)); print('Avisos:',c.warnings)"
) else (
  echo No existe el entorno virtual POPIS.
  echo Ejecuta INSTALAR_Y_ABRIR_POPIS.bat.
)

echo.
echo [Carpetas]
for %%D in (data\historicos data\actual data\suive data\poblacion data\geografia data\entrada data\backups salidas cache logs) do (
  if exist "%%D" (echo OK  %%D) else (echo FALTA %%D)
)
echo.
pause
