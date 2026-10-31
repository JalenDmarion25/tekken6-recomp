$ErrorActionPreference = 'Stop'
$packageDir = 'C:\Users\Jalen\Tekken6-Practice-Dev'
$trace = @("$packageDir\practice-stance-frames.txt", "$packageDir\bin\practice-stance-frames.txt") |
    Where-Object { Test-Path $_ } |
    ForEach-Object { Get-Item $_ } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
if (!$trace) { throw 'No practice-stance-frames.txt found. Run the capture and perform an attack first.' }
$root = Split-Path $PSScriptRoot -Parent
$output = Join-Path $root ('stance-frame-results-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.zip')
Compress-Archive -LiteralPath $trace.FullName -DestinationPath $output -ErrorAction Stop
Write-Host "Upload this file: $output"
