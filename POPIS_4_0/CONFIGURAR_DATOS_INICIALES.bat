@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ===============================================================
echo  POPIS 4.1 - CONFIGURACION INICIAL DE DATOS LOCALES
echo ===============================================================
echo.
echo Este proceso NO sube datos a Internet. Solo copia archivos dentro
echo de esta carpeta POPIS.
echo.

mkdir "data\sinave\historico" 2>nul
mkdir "data\sinave\actual" 2>nul
mkdir "data\suive\historico" 2>nul
mkdir "data\suive\actual" 2>nul
mkdir "data\poblacion" 2>nul

set "SRC=%~dp0IMPORTAR"
if not exist "%SRC%" mkdir "%SRC%"

echo Coloca dentro de la carpeta IMPORTAR los 7 archivos y vuelve a ejecutar.
echo POPIS buscara tambien archivos colocados junto a este BAT.
echo.

call :copy_hist "Diarreas_2022(1).xls"
call :copy_hist "Diarreas_2023(1).xls"
call :copy_hist "Diarreas_2024(1).xls"
call :copy_hist "Diarreas_2025(1).xls"
call :copy_current "Diarreas_actual.xls"
call :copy_pop "Sonora_CONAPO.xlsx"
call :copy_suive "Canal endemico EDAs_SUIVE_SINAVE (1)(1).xlsx"

echo.
echo ===============================================================
echo Configuracion terminada.
echo Si algun archivo aparece como FALTA, copialo a IMPORTAR y repite.
echo ===============================================================
pause
exit /b 0

:locate
set "FOUND="
if exist "%SRC%\%~1" set "FOUND=%SRC%\%~1"
if not defined FOUND if exist "%~dp0%~1" set "FOUND=%~dp0%~1"
exit /b 0

:copy_hist
call :locate "%~1"
if defined FOUND (
  copy /Y "%FOUND%" "data\sinave\historico\%~1" >nul
  echo [OK] SINAVE historico: %~1
) else echo [FALTA] %~1
exit /b 0

:copy_current
call :locate "%~1"
if defined FOUND (
  del /Q "data\sinave\actual\*" 2>nul
  copy /Y "%FOUND%" "data\sinave\actual\Diarreas_actual.xls" >nul
  echo [OK] SINAVE actual
) else echo [FALTA] %~1
exit /b 0

:copy_pop
call :locate "%~1"
if defined FOUND (
  del /Q "data\poblacion\*" 2>nul
  copy /Y "%FOUND%" "data\poblacion\Sonora_CONAPO.xlsx" >nul
  echo [OK] CONAPO Sonora
) else echo [FALTA] %~1
exit /b 0

:copy_suive
call :locate "%~1"
if defined FOUND (
  rem La primera copia se conserva como base historica; la segunda es la semanal reemplazable.
  if not exist "data\suive\historico\SUIVE_HISTORICO_BASE.xlsx" copy /Y "%FOUND%" "data\suive\historico\SUIVE_HISTORICO_BASE.xlsx" >nul
  del /Q "data\suive\actual\*" 2>nul
  copy /Y "%FOUND%" "data\suive\actual\SUIVE_actual.xlsx" >nul
  echo [OK] SUIVE historico + actual
) else echo [FALTA] %~1
exit /b 0
