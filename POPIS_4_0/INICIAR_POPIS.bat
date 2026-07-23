@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

title POPIS 4.1.2 - ARRANQUE SEGURO
set "VENV=%LOCALAPPDATA%\POPIS4\venv"
set "PY=%VENV%\Scripts\python.exe"
set "STATE=%LOCALAPPDATA%\POPIS4"
set "LOGOUT=%STATE%\POPIS_streamlit_out.log"
set "LOGERR=%STATE%\POPIS_streamlit_error.log"
set "PIDFILE=%STATE%\POPIS.pid"
set "PORTFILE=%STATE%\POPIS.port"

if not exist "%STATE%" mkdir "%STATE%"
if exist "%LOGOUT%" del /q "%LOGOUT%" >nul 2>&1
if exist "%LOGERR%" del /q "%LOGERR%" >nul 2>&1
if exist "%PIDFILE%" del /q "%PIDFILE%" >nul 2>&1
if exist "%PORTFILE%" del /q "%PORTFILE%" >nul 2>&1

echo ===============================================================
echo  POPIS 4.1.2 - ARRANQUE SEGURO
echo  SUIVE + SINAVE + INDICADORES + TERRITORIO
echo ===============================================================
echo.

if not exist "%PY%" (
  echo [1/6] Creando entorno virtual aislado...
  py -3.12 -m venv "%VENV%" 2>nul
  if errorlevel 1 python -m venv "%VENV%"
  if errorlevel 1 goto :python_error
) else (
  echo [1/6] Entorno POPIS localizado.
)

echo [2/6] Verificando dependencias...
"%PY%" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto :install_error

echo [3/6] Verificando motor POPIS...
"%PY%" -c "import streamlit,pandas,openpyxl; import popis_core,popis_core_patch,popis_data,popis_runtime; print('Motor POPIS OK')"
if errorlevel 1 goto :install_error

if not exist "app_bootstrap.py" goto :app_error

echo [4/6] Seleccionando puerto libre...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$l=New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Loopback,0); $l.Start(); $p=$l.LocalEndpoint.Port; $l.Stop(); Set-Content -LiteralPath '%PORTFILE%' -Value $p"
if errorlevel 1 goto :port_error
if not exist "%PORTFILE%" goto :port_error
set /p PORT=<"%PORTFILE%"
if not defined PORT goto :port_error
echo       Puerto: !PORT!

echo [5/6] Iniciando servidor Streamlit...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$args=@('-m','streamlit','run','app_bootstrap.py','--server.address','127.0.0.1','--server.port','!PORT!','--browser.gatherUsageStats','false'); $p=Start-Process -FilePath '%PY%' -ArgumentList $args -WorkingDirectory '%CD%' -RedirectStandardOutput '%LOGOUT%' -RedirectStandardError '%LOGERR%' -PassThru; Set-Content -LiteralPath '%PIDFILE%' -Value $p.Id"
if errorlevel 1 goto :server_error

echo [6/6] Esperando a que POPIS responda...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$url='http://127.0.0.1:!PORT!/_stcore/health'; $ok=$false; for($i=0;$i -lt 90;$i++){ try { $r=Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 2; if($r.StatusCode -eq 200){$ok=$true;break} } catch {}; Start-Sleep -Seconds 1 }; if(-not $ok){exit 1}"
if errorlevel 1 goto :health_error

echo.
echo ===============================================================
echo  POPIS ESTA ACTIVO
echo  http://127.0.0.1:!PORT!
echo ===============================================================
echo.
powershell.exe -NoProfile -Command "Start-Process 'http://127.0.0.1:!PORT!'"

echo El navegador ya debe mostrar POPIS.
echo No cierres esta ventana mientras lo uses.
echo.
set /p POPISPID=<"%PIDFILE%"
powershell.exe -NoProfile -Command "if (Get-Process -Id !POPISPID! -ErrorAction SilentlyContinue) { Wait-Process -Id !POPISPID! }"
exit /b 0

:health_error
echo.
echo ===============================================================
echo ERROR: Streamlit no respondio despues de 90 segundos.
echo ===============================================================
echo.
echo --- ERROR DE STREAMLIT ---
if exist "%LOGERR%" type "%LOGERR%"
echo.
echo --- SALIDA DE STREAMLIT ---
if exist "%LOGOUT%" type "%LOGOUT%"
echo.
echo Los logs tambien quedaron en:
echo   %LOGERR%
echo   %LOGOUT%
pause
exit /b 1

:server_error
echo ERROR: no pude iniciar el proceso de Streamlit.
if exist "%LOGERR%" type "%LOGERR%"
pause
exit /b 1

:python_error
echo ERROR: no pude crear el entorno Python.
pause
exit /b 1

:install_error
echo ERROR: fallo la instalacion o verificacion de dependencias.
pause
exit /b 1

:app_error
echo ERROR: no encuentro app_bootstrap.py en %CD%
pause
exit /b 1

:port_error
echo ERROR: no pude obtener un puerto libre.
echo Archivo esperado: %PORTFILE%
pause
exit /b 1
