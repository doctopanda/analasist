@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ============================================================
echo  POPIS 4.8 - VISUAL CAVERNA
echo  Integracion automatica + identidad visual epidemiologica
echo ============================================================
echo.

set "PYEXE="
if exist "%LOCALAPPDATA%\POPIS4\venv\Scripts\python.exe" set "PYEXE=%LOCALAPPDATA%\POPIS4\venv\Scripts\python.exe"
if not defined PYEXE if exist "%LOCALAPPDATA%\POPIS\venv\Scripts\python.exe" set "PYEXE=%LOCALAPPDATA%\POPIS\venv\Scripts\python.exe"

if defined PYEXE goto runvenv
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 goto runpy
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 goto runpython

echo ERROR: no encontre Python ni el entorno virtual de POPIS.
pause
exit /b 1

:runvenv
"%PYEXE%" INSTALAR_POPIS_4_7.py %*
goto done

:runpy
py -3 INSTALAR_POPIS_4_7.py %*
goto done

:runpython
python INSTALAR_POPIS_4_7.py %*

:done
if %ERRORLEVEL% NEQ 0 (
  echo.
  echo La actualizacion no se completo. Revisa el mensaje anterior.
) else (
  echo.
  echo Listo. POPIS ya tiene el visual CAVERNA.
  echo Abre POPIS con tu INICIAR_POPIS.bat habitual.
)
echo.
pause
