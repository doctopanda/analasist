@echo off
setlocal
cd /d "%~dp0"
set "PY=%LOCALAPPDATA%\POPIS5\venv\Scripts\python.exe"
if exist "%PY%" (
  "%PY%" "%~dp0diagnostico.py"
) else (
  python "%~dp0diagnostico.py"
)
echo.
pause
