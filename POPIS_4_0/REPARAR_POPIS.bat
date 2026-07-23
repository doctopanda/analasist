@echo off
setlocal EnableExtensions
set "VENV=%LOCALAPPDATA%\POPIS4\venv"
echo ===============================================================
echo  REPARAR POPIS 4.0
echo ===============================================================
echo.
echo Se eliminara SOLO el entorno virtual de POPIS:
echo %VENV%
echo.
if exist "%VENV%" rmdir /s /q "%VENV%"
if exist "%VENV%" (
  echo No fue posible eliminar el entorno. Cierra POPIS y vuelve a intentar.
  pause
  exit /b 1
)
echo Entorno eliminado correctamente.
echo Ejecuta INICIAR_POPIS.bat para reconstruirlo.
pause
