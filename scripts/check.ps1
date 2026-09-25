param([switch]$Browser, [switch]$Build)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'enter-dev.ps1')
$projectRoot = Split-Path -Parent $PSScriptRoot

function Invoke-Checked {
    param([string]$Program, [string[]]$Arguments)
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Program failed with exit code $LASTEXITCODE" }
}

Push-Location (Join-Path $projectRoot 'backend')
try {
    Invoke-Checked 'uv' @('run', 'ruff', 'check', '.')
    Invoke-Checked 'uv' @('run', 'ruff', 'format', '--check', '.')
    Invoke-Checked 'uv' @('run', 'mypy', 'app')
    if (-not $env:EIP_TEST_DATABASE_URL) {
        Write-Warning 'EIP_TEST_DATABASE_URL is unset: PostgreSQL integration tests will be skipped.'
    }
    Invoke-Checked 'uv' @('run', 'pytest')
} finally { Pop-Location }

Push-Location (Join-Path $projectRoot 'frontend')
try {
    Invoke-Checked 'npm.cmd' @('run', 'typecheck')
    Invoke-Checked 'npm.cmd' @('run', 'format:check')
    if ($Build) { Invoke-Checked 'npm.cmd' @('run', 'build') }
    if ($Browser) { Invoke-Checked 'npm.cmd' @('run', 'test:e2e') }
} finally { Pop-Location }
