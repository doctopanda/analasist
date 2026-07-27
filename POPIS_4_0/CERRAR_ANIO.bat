@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ===============================================================
echo  POPIS 4.1 - CIERRE ANUAL
 echo ===============================================================
echo.
set /p YEAR=Escribe el anio que vas a cerrar (ej. 2026): 
if "%YEAR%"=="" exit /b 1

mkdir "data\sinave\historico" 2>nul
mkdir "data\suive\historico" 2>nul

for %%F in ("data\sinave\actual\*") do (
  if exist "%%~fF" copy /Y "%%~fF" "data\sinave\historico\Diarreas_%YEAR%%%~xF" >nul
)
for %%F in ("data\suive\actual\*") do (
  if exist "%%~fF" copy /Y "%%~fF" "data\suive\historico\SUIVE_cierre_%YEAR%%%~xF" >nul
)

echo.
echo Los archivos actuales fueron COPIADOS al historico.
echo No se borraron los actuales para evitar perdida accidental.
echo Cuando tengas la primera base del nuevo anio, reemplazala desde POPIS.
pause
