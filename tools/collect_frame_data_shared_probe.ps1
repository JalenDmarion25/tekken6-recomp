$ErrorActionPreference = 'Stop'
$packageDir = 'C:\Users\Jalen\Tekken6-Practice-Dev'
$trace = @("$packageDir\practice-shared-action.txt", "$packageDir\bin\practice-shared-action.txt") |
    Where-Object { Test-Path $_ } |
    ForEach-Object { Get-Item $_ } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
if (!$trace) { throw 'No shared native action log found. Run this build and enter practice first.' }
$output = Join-Path (Split-Path $PSScriptRoot -Parent) ('shared-action-results-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.zip')
Compress-Archive -LiteralPath $trace.FullName -DestinationPath $output -ErrorAction Stop
Write-Host "Upload this file: $output"
