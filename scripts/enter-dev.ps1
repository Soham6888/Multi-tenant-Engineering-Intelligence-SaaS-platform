# Dot-source this script to expose project runtimes in the current terminal only.
$projectRoot = Split-Path -Parent $PSScriptRoot
$runtimePaths = @(
    (Join-Path $projectRoot '.tools\node-v22.23.2-win-x64'),
    (Join-Path $projectRoot '.tools\uv'),
    (Join-Path $projectRoot '.tools\postgres17\pgsql\bin'),
    (Join-Path $projectRoot 'backend\.venv\Scripts')
)
foreach ($runtimePath in $runtimePaths) {
    if ((Test-Path -LiteralPath $runtimePath) -and ($env:PATH -split ';' -notcontains $runtimePath)) {
        $env:PATH = $runtimePath + ';' + $env:PATH
    }
}
Write-Output 'Project runtimes are available in this terminal. No system PATH changes were made.'
