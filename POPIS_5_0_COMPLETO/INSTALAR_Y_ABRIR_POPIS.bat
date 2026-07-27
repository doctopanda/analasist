@echo off
setlocal
cd /d "%~dp0"
title POPIS 5.0 - Instalacion automatica
echo ===============================================================
echo  POPIS 5.0 TODO EN UNO - INSTALACION AUTOMATICA
echo ===============================================================
where py >nul 2>&1
if %errorlevel%==0 (
  py -3.12 "%~dp0INSTALAR_POPIS.py"
  if %errorlevel%==0 exit /b 0
  py -3 "%~dp0INSTALAR_POPIS.py"
  exit /b %errorlevel%
)
where python >nul 2>&1
if %errorlevel%==0 (
  python "%~dp0INSTALAR_POPIS.py"
  exit /b %errorlevel%
)
echo.
echo ERROR: No se encontro Python 3.10 o posterior.
echo Instala Python y vuelve a ejecutar este archivo.
pause
exit /b 1
