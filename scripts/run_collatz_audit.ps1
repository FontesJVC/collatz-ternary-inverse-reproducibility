$ErrorActionPreference = "Continue"
Set-Location (Split-Path $PSScriptRoot -Parent)

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

New-Item -ItemType Directory -Force -Path "logs" | Out-Null

if (Get-Command py -ErrorAction SilentlyContinue) {
    $Python = "py"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $Python = "python"
} else {
    Write-Host "Python 3 was not found." -ForegroundColor Red
    exit 1
}

function Run-Step {
    param([int]$N, [string]$Title, [string]$Log, [string[]]$Args)
    Write-Host ""
    Write-Host "[$N/8] $Title" -ForegroundColor Cyan
    & $Python @Args 2>&1 | Tee-Object -FilePath $Log
}

Run-Step 1 "Smoke tests" "logs\01_smoke_tests.txt" @("tests\run_smoke_tests.py")
Run-Step 2 "Quick structural audit" "logs\02_quick_audit.txt" @("shared\collatz_structural_audit.py","--suite","quick")
Run-Step 3 "Target n=35" "logs\03_target35.txt" @("shared\collatz_structural_audit.py","--suite","none","--target","35","--max-depth","6")
Run-Step 4 "Target n=27 direct control" "logs\04_target27_direct.txt" @("shared\collatz_structural_audit.py","--suite","none","--target","27","--max-depth","45","--no-search")
Run-Step 5 "Target n=35, h=1" "logs\05_target35_h1.txt" @("shared\collatz_structural_audit.py","--suite","none","--target","35","--h","1","--max-depth","4")
Run-Step 6 "Target n=35, h=4" "logs\06_target35_h4.txt" @("shared\collatz_structural_audit.py","--suite","none","--target","35","--h","4","--max-depth","4")
Run-Step 7 "Adversarial examples" "logs\07_counterexample_search.txt" @("tests\search_counterexamples.py")
Run-Step 8 "Full structural audit" "logs\08_full_audit.txt" @("shared\collatz_structural_audit.py","--suite","full")

Write-Host ""
Write-Host "FINISHED. Send me 02_quick_audit.txt and 08_full_audit.txt after rerun." -ForegroundColor Green
