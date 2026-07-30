@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

echo ===============================================================
echo  POPIS 4.6.2 CAVERNA R5 - INSTALACION AUTOMATICA COMPLETA
echo  SUIVE + SINAVE + REDVE + CANALES + INDICADORES + TERRITORIO
echo ===============================================================
echo.

set "VENV=%LOCALAPPDATA%\POPIS462\venv"
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
  echo ERROR: No se encontro Python 3.
  echo Instala Python 3.12 desde python.org y vuelve a ejecutar este archivo.
  pause
  exit /b 1
)

echo [1/7] Python localizado: %PY_CMD%

if not exist "%VENV%\Scripts\python.exe" (
  echo [2/7] Creando entorno virtual aislado en:
  echo       %VENV%
  if not exist "%LOCALAPPDATA%\POPIS462" mkdir "%LOCALAPPDATA%\POPIS462"
  %PY_CMD% -m venv "%VENV%"
  if errorlevel 1 goto :error_venv
) else (
  echo [2/7] Entorno virtual POPIS ya existe.
)

echo [3/7] Instalando/verificando dependencias...
"%VENV%\Scripts\python.exe" -m pip install --disable-pip-version-check --upgrade pip
if errorlevel 1 goto :error_pip
"%VENV%\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto :error_pip

echo [4/7] Preparando estructura y buscando datos POPIS existentes...
"%VENV%\Scripts\python.exe" MIGRAR_DATOS_EXISTENTES.py --auto
if not exist "data\historicos" mkdir "data\historicos"
if not exist "data\actual" mkdir "data\actual"
if not exist "data\suive" mkdir "data\suive"
if not exist "data\poblacion" mkdir "data\poblacion"
if not exist "data\geografia" mkdir "data\geografia"
if not exist "data\redve" mkdir "data\redve"
if not exist "data\entrada" mkdir "data\entrada"
if not exist "data\backups" mkdir "data\backups"
if not exist "salidas" mkdir "salidas"
if not exist "cache" mkdir "cache"
if not exist "logs" mkdir "logs"

echo [5/7] Modernizando compatibilidad de Streamlit...
"%VENV%\Scripts\python.exe" MODERNIZAR_STREAMLIT.py
if errorlevel 1 goto :error_codigo

echo [6/7] Verificando codigo POPIS...
"%VENV%\Scripts\python.exe" -m compileall -q app.py modulos pages MODERNIZAR_STREAMLIT.py
if errorlevel 1 goto :error_codigo

echo [7/7] Abriendo POPIS 4.6.2 R5...
echo URL: http://127.0.0.1:8501
echo.
start "" "http://127.0.0.1:8501"
"%VENV%\Scripts\python.exe" -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
exit /b %errorlevel%

:error_venv
echo.
echo ERROR: no fue posible crear el entorno virtual POPIS.
pause
exit /b 2

:error_pip
echo.
echo ERROR: no fue posible instalar las dependencias.
echo Ejecuta REPARAR_POPIS.bat y vuelve a intentar.
pause
exit /b 3

:error_codigo
echo.
echo ERROR: la verificacion o modernizacion del codigo fallo.
echo Ejecuta DIAGNOSTICO_POPIS.bat para obtener detalle.
pause
exit /b 4
