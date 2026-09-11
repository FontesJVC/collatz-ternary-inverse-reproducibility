@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

if not exist "logs" mkdir "logs"
if not exist "results" mkdir "results"

where py >nul 2>nul
if %errorlevel%==0 (
  set "PY=py"
) else (
  set "PY=python"
)

echo ============================================================
echo DEEP COLLATZ COMPUTATIONAL AUDIT
echo ============================================================
echo.
echo Choose a preset:
echo   1 = validation  ^(short test^)
echo   2 = deep        ^(recommended substantial audit^)
echo   3 = overnight   ^(very heavy^)
echo.
set /p choice=Enter 1, 2, or 3: 

if "%choice%"=="1" set PRESET=validation
if "%choice%"=="2" set PRESET=deep
if "%choice%"=="3" set PRESET=overnight

if "%PRESET%"=="" (
  echo Invalid choice.
  pause
  exit /b 1
)

echo.
echo Running preset: %PRESET%
echo.

%PY% deep_audit\deep_audit.py --preset %PRESET% 2>&1 | powershell -NoProfile -Command "$input | Tee-Object -FilePath 'deep_audit\logs\deep_audit_%PRESET%.txt'"

echo.
echo Converting the tabular results to Excel...
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\convert_results_to_xlsx.ps1" ^
  -CsvPath ".\deep_audit\results\deep_audit_%PRESET%.csv" ^
  -XlsxPath ".\deep_audit\deep_audit\results\deep_audit_%PRESET%.xlsx"

echo.
echo Finished.
echo Main spreadsheet:
echo   deep_audit\results\deep_audit_%PRESET%.xlsx
echo.
pause
