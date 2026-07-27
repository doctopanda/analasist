@echo off
setlocal EnableExtensions
cd /d "%~dp0"
mkdir "data\suive\actual" 2>nul
for /f "usebackq delims=" %%F in (`powershell -NoProfile -STA -Command "Add-Type -AssemblyName System.Windows.Forms; $d=New-Object System.Windows.Forms.OpenFileDialog; $d.Title='Selecciona el SUIVE actualizado'; $d.Filter='Excel SUIVE|*.xls;*.xlsx;*.xlsm|Todos|*.*'; if($d.ShowDialog() -eq 'OK'){$d.FileName}"`) do set "SRC=%%F"
if not defined SRC (
 echo No se selecciono archivo.
 pause
 exit /b 1
)
for %%G in ("%SRC%") do set "EXT=%%~xG"
del /Q "data\suive\actual\*" 2>nul
copy /Y "%SRC%" "data\suive\actual\SUIVE_actual%EXT%" >nul
echo SUIVE actual actualizado correctamente.
echo Archivo: %SRC%
pause
