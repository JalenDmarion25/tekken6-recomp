$ErrorActionPreference = 'Stop'
$packageDir = 'C:\Users\Jalen\Tekken6-Practice-Dev'
$trace = @("$packageDir\practice-command-snapshot.txt", "$packageDir\bin\practice-command-snapshot.txt") |
    Where-Object { Test-Path $_ } |
    ForEach-Object { Get-Item $_ } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
if (!$trace) { throw 'No command snapshot found. Run this build and enter practice first.' }
$output = Join-Path (Split-Path $PSScriptRoot -Parent) ('command-snapshot-results-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.zip')
Compress-Archive -LiteralPath $trace.FullName -DestinationPath $output -ErrorAction Stop
Write-Host "Upload this file: $output"
