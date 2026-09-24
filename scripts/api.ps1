$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$portableUv = Join-Path $projectRoot '.tools\uv\uv.exe'
$uvCommand = if (Test-Path $portableUv) { $portableUv } else { 'uv' }
Push-Location (Join-Path $projectRoot 'backend')
try { & $uvCommand run uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log } finally { Pop-Location }
