@echo off
setlocal EnableExtensions

cd /d "%~dp0.."
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

if not exist "shared\collatz_structural_audit.py" (
    echo ERROR: this runner must be inside the repository scripts folder.
    pause
    exit /b 1
)

if not exist "logs" mkdir "logs"

where py >nul 2>nul
if %errorlevel%==0 (
    set "PY=py"
) else (
    where python >nul 2>nul
    if %errorlevel%==0 (
        set "PY=python"
    ) else (
        echo ERROR: Python 3 was not found.
        pause
        exit /b 1
    )
)

echo ============================================================
echo COLLATZ COMPUTATIONAL AUDIT - UTF-8 WINDOWS RUNNER
echo ============================================================
echo.

echo [1/8] Smoke tests
%PY% tests\run_smoke_tests.py > logs\01_smoke_tests.txt 2>&1
type logs\01_smoke_tests.txt
echo.

echo [2/8] Quick structural audit
%PY% shared\collatz_structural_audit.py --suite quick > logs\02_quick_audit.txt 2>&1
type logs\02_quick_audit.txt
echo.

echo [3/8] Target n=35
%PY% shared\collatz_structural_audit.py --suite none --target 35 --max-depth 6 > logs\03_target35.txt 2>&1
type logs\03_target35.txt
echo.

echo [4/8] Target n=27 - direct control only
%PY% shared\collatz_structural_audit.py --suite none --target 27 --max-depth 45 --no-search > logs\04_target27_direct.txt 2>&1
type logs\04_target27_direct.txt
echo.

echo [5/8] Target n=35 below threshold: h=1
%PY% shared\collatz_structural_audit.py --suite none --target 35 --h 1 --max-depth 4 > logs\05_target35_h1.txt 2>&1
type logs\05_target35_h1.txt
echo.

echo [6/8] Target n=35 at threshold: h=4
%PY% shared\collatz_structural_audit.py --suite none --target 35 --h 4 --max-depth 4 > logs\06_target35_h4.txt 2>&1
type logs\06_target35_h4.txt
echo.

echo [7/8] Adversarial examples
%PY% tests\search_counterexamples.py > logs\07_counterexample_search.txt 2>&1
type logs\07_counterexample_search.txt
echo.

echo [8/8] Full structural audit
echo This can take longer.
%PY% shared\collatz_structural_audit.py --suite full > logs\08_full_audit.txt 2>&1
type logs\08_full_audit.txt
echo.

echo ============================================================
echo FINISHED
echo Send me 02_quick_audit.txt and 08_full_audit.txt after rerun.
echo ============================================================
pause
