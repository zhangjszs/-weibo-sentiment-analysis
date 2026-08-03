<#
.SYNOPSIS
    Reproducible project quality gate. Runs backend lint, backend fast tests,
    frontend lint, and frontend build in sequence; exits non-zero on first failure.

.DESCRIPTION
    This is the single command that CI and developers use to verify the project
    before pushing. It intentionally does NOT require MySQL, Redis, or a Weibo
    cookie — those are covered by the integration/external test jobs.

    The script preserves each step's exit code and stdout/stderr. Any failure
    short-circuits the rest of the pipeline so the root cause is easy to find.

.PARAMETER BackendOnly
    Skip frontend checks.

.PARAMETER FrontendOnly
    Skip backend checks.

.EXAMPLE
    pwsh -NoProfile -File scripts/verify_project.ps1
    pwsh -NoProfile -File scripts/verify_project.ps1 -BackendOnly
#>
[CmdletBinding()]
param(
    [switch]$BackendOnly,
    [switch]$FrontendOnly
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$FrontendDir = Join-Path $ProjectRoot "frontend"

function Invoke-Step {
    param([string]$Name, [scriptblock]$Script)
    Write-Host "`n===== $Name =====" -ForegroundColor Cyan
    & $Script
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        Write-Host "FAILED: $Name (exit code $code)" -ForegroundColor Red
        exit $code
    }
    Write-Host "OK: $Name" -ForegroundColor Green
}

if (-not $FrontendOnly) {
    Invoke-Step "Backend: ruff check" {
        & python -m ruff check src tests
    }

    Invoke-Step "Backend: pytest (unit + api)" {
        & python -m pytest -m "unit or api" -q --maxfail=1
    }
}

if (-not $BackendOnly) {
    Push-Location $FrontendDir
    try {
        Invoke-Step "Frontend: npm run lint" {
            & npm run lint
        }

        Invoke-Step "Frontend: npm run build" {
            & npm run build
        }
    } finally {
        Pop-Location
    }
}

Write-Host "`nAll quality-gate steps passed." -ForegroundColor Green
exit 0
