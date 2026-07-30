@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
set "VENV=%LOCALAPPDATA%\POPIS462\venv"

echo ===============================================================
echo  POPIS 4.6.2 CAVERNA R5 - ARRANQUE SEGURO
echo ===============================================================

if not exist "%VENV%\Scripts\python.exe" (
  echo Entorno POPIS no encontrado. Se ejecutara el instalador completo.
  call INSTALAR_Y_ABRIR_POPIS.bat
  exit /b %errorlevel%
)

"%VENV%\Scripts\python.exe" -c "import streamlit,pandas,plotly,folium; print('Motor POPIS OK')"
if errorlevel 1 (
  echo Dependencias incompletas. Ejecuta REPARAR_POPIS.bat.
  pause
  exit /b 2
)

if exist "MODERNIZAR_STREAMLIT.py" (
  "%VENV%\Scripts\python.exe" MODERNIZAR_STREAMLIT.py >nul
  if errorlevel 1 (
    echo No fue posible modernizar la compatibilidad de Streamlit.
    pause
    exit /b 3
  )
)

if not exist "data\entrada" mkdir "data\entrada"
if not exist "data\redve" mkdir "data\redve"
start "" "http://127.0.0.1:8501"
"%VENV%\Scripts\python.exe" -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
exit /b %errorlevel%
