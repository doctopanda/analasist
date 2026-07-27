@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

title POPIS 4.6.1 - SUIVE AUTOMATICO + ESPACIAL
set "VENV=%LOCALAPPDATA%\POPIS4\venv"
set "PY=%VENV%\Scripts\python.exe"
set "STATE=%LOCALAPPDATA%\POPIS4"
set "LOGOUT=%STATE%\POPIS_streamlit_out.log"
set "LOGERR=%STATE%\POPIS_streamlit_error.log"
set "PIDFILE=%STATE%\POPIS.pid"
set "PORTFILE=%STATE%\POPIS.port"

if not exist "%STATE%" mkdir "%STATE%"

echo ===============================================================
echo  POPIS 4.6.1 - SUIVE AUTOMATICO + ESPACIAL CORREGIDO
echo  Cubo + Refresh All + mapas + reportes Excel / Word
echo ===============================================================
echo.

echo [0/7] Cerrando instancia POPIS anterior si sigue activa...
if exist "%PIDFILE%" (
  set /p OLDPID=<"%PIDFILE%"
  if defined OLDPID (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$p=Get-CimInstance Win32_Process -Filter 'ProcessId=!OLDPID!' -ErrorAction SilentlyContinue; if($p -and $p.CommandLine -match 'streamlit' -and $p.CommandLine -match 'app_bootstrap.py'){Stop-Process -Id !OLDPID! -Force -ErrorAction SilentlyContinue; Start-Sleep -Milliseconds 500}"
  )
)
if exist "%PIDFILE%" del /q "%PIDFILE%" >nul 2>&1
if exist "%PORTFILE%" del /q "%PORTFILE%" >nul 2>&1
if exist "%LOGOUT%" del /q "%LOGOUT%" >nul 2>&1
if exist "%LOGERR%" del /q "%LOGERR%" >nul 2>&1

if not exist "%PY%" (
  echo [1/7] Creando entorno virtual aislado...
  py -3.12 -m venv "%VENV%" 2>nul
  if errorlevel 1 python -m venv "%VENV%"
  if errorlevel 1 goto :python_error
) else (
  echo [1/7] Entorno POPIS localizado.
)

echo [2/7] Verificando dependencias...
"%PY%" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto :install_error

echo [3/7] Verificando motor POPIS, cubo SUIVE, espacial y reportes...
"%PY%" -c "import streamlit,pandas,openpyxl,docx,PIL; import popis_core,popis_data,popis_runtime,popis_reports,popis_suive_cube,popis_excel_refresh,popis_spatial; print('Motor POPIS 4.6.1 OK')"
if errorlevel 1 goto :install_error

echo [4/7] Verificando interfaz POPIS 4.6.1...
if not exist "app_bootstrap.py" goto :app_error
if not exist "app_v46.py" goto :app_error
findstr /c:"4.6.1-spatialfix" "app_v46.py" >nul
if errorlevel 1 goto :version_error
echo       Interfaz 4.6.1-spatialfix localizada.

echo [5/7] Seleccionando puerto libre...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$l=New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Loopback,0); $l.Start(); $p=$l.LocalEndpoint.Port; $l.Stop(); Set-Content -LiteralPath '%PORTFILE%' -Value $p"
if errorlevel 1 goto :port_error
if not exist "%PORTFILE%" goto :port_error
set /p PORT=<"%PORTFILE%"
if not defined PORT goto :port_error
echo       Puerto nuevo: !PORT!

echo [6/7] Iniciando servidor POPIS 4.6.1...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$args=@('-m','streamlit','run','app_bootstrap.py','--server.address','127.0.0.1','--server.port','!PORT!','--browser.gatherUsageStats','false'); $p=Start-Process -FilePath '%PY%' -ArgumentList $args -WorkingDirectory '%CD%' -RedirectStandardOutput '%LOGOUT%' -RedirectStandardError '%LOGERR%' -PassThru; Set-Content -LiteralPath '%PIDFILE%' -Value $p.Id"
if errorlevel 1 goto :server_error

echo [7/7] Esperando confirmacion HTTP de Streamlit...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$url='http://127.0.0.1:!PORT!/_stcore/health'; $ok=$false; for($i=0;$i -lt 90;$i++){ try { $r=Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 2; if($r.StatusCode -eq 200){$ok=$true;break} } catch {}; Start-Sleep -Seconds 1 }; if(-not $ok){exit 1}"
if errorlevel 1 goto :health_error

echo.
echo ===============================================================
echo  POPIS 4.6.1 ESTA ACTIVO
echo  http://127.0.0.1:!PORT!
echo.
echo  EN LA BARRA LATERAL DEBE DECIR:
echo  POPIS 4.6.1-spatialfix
echo ===============================================================
echo.
powershell.exe -NoProfile -Command "Start-Process 'http://127.0.0.1:!PORT!'"

echo No cierres esta ventana mientras uses POPIS.
set /p POPISPID=<"%PIDFILE%"
powershell.exe -NoProfile -Command "if (Get-Process -Id !POPISPID! -ErrorAction SilentlyContinue) { Wait-Process -Id !POPISPID! }"
exit /b 0

:health_error
echo ERROR: Streamlit no respondio despues de 90 segundos.
if exist "%LOGERR%" type "%LOGERR%"
if exist "%LOGOUT%" type "%LOGOUT%"
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
echo ERROR: faltan app_bootstrap.py o app_v46.py en %CD%
pause
exit /b 1

:version_error
echo ERROR: app_v46.py no corresponde a POPIS 4.6.1-spatialfix.
echo Reemplaza los archivos del programa con el ZIP completo mas reciente.
pause
exit /b 1

:port_error
echo ERROR: no pude obtener un puerto libre.
pause
exit /b 1
