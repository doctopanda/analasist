@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if %errorlevel%==0 (
  py -3.12 "%~dp0INSTALAR_POPIS.py" --repair
  if %errorlevel%==0 exit /b 0
  py -3 "%~dp0INSTALAR_POPIS.py" --repair
  exit /b %errorlevel%
)
python "%~dp0INSTALAR_POPIS.py" --repair
