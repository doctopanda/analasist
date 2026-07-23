@echo off
setlocal EnableExtensions
cd /d "%~dp0"
mkdir "data\sinave\actual" 2>nul
for /f "usebackq delims=" %%F in (`powershell -NoProfile -STA -Command "Add-Type -AssemblyName System.Windows.Forms; $d=New-Object System.Windows.Forms.OpenFileDialog; $d.Title='Selecciona la base SINAVE actualizada'; $d.Filter='Bases SINAVE|*.xls;*.xlsx;*.csv;*.txt|Todos|*.*'; if($d.ShowDialog() -eq 'OK'){$d.FileName}"`) do set "SRC=%%F"
if not defined SRC (
 echo No se selecciono archivo.
 pause
 exit /b 1
)
del /Q "data\sinave\actual\*" 2>nul
copy /Y "%SRC%" "data\sinave\actual\Diarreas_actual%~xSRC" >nul
echo SINAVE actual actualizado correctamente.
echo Archivo: %SRC%
pause
