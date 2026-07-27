@echo off
setlocal
cd /d "%~dp0"
set "PY=%LOCALAPPDATA%\POPIS5\venv\Scripts\python.exe"
if not exist "%PY%" (
  echo POPIS 5.0 aun no esta instalado. Iniciando instalador...
  call "%~dp0INSTALAR_Y_ABRIR_POPIS.bat"
  exit /b %errorlevel%
)
"%PY%" "%~dp0launcher.py"
