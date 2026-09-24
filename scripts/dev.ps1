$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$portableNode = Join-Path $projectRoot '.tools\node-v22.23.2-win-x64'
if (Test-Path (Join-Path $portableNode 'node.exe')) {
    $env:PATH = $portableNode + ';' + $env:PATH
}
Push-Location (Join-Path $projectRoot 'frontend')
try { npm.cmd run dev } finally { Pop-Location }
