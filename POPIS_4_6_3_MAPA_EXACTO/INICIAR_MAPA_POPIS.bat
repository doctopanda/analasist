@echo off
setlocal EnableExtensions
title POPIS 4.6.3 - MAPA EXACTO

echo ===============================================================
echo  POPIS 4.6.3 - MAPA EXACTO
echo  PUNTOS EXACTOS + CONCENTRACION + LIMITES TERRITORIALES
echo ===============================================================
echo.

set "ROOT=%~dp0"
set "VENV=%LOCALAPPDATA%\POPIS4\venv"
set "PY=%VENV%\Scripts\python.exe"

if not exist "%PY%" (
    echo No encontre el entorno POPIS en:
    echo %VENV%
    echo.
    echo Crea primero el entorno del POPIS principal o ejecuta:
    echo   py -3.12 -m venv "%VENV%"
    pause
    exit /b 1
)

echo [1/3] Verificando dependencias del mapa...
"%PY%" -m pip install -r "%ROOT%requirements_mapa.txt"
if errorlevel 1 (
    echo ERROR: no fue posible instalar/verificar dependencias.
    pause
    exit /b 1
)

echo [2/3] Verificando modulo espacial...
"%PY%" -c "from modulos.mapa_espacial import build_folium_map; print('Motor espacial POPIS OK')"
if errorlevel 1 (
    echo ERROR: el modulo espacial no pudo importarse.
    pause
    exit /b 1
)

echo [3/3] Iniciando Streamlit...
cd /d "%ROOT%"
"%PY%" -m streamlit run app_mapa.py

endlocal
