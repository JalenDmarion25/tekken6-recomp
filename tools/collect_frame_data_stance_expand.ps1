$ErrorActionPreference = 'Stop'
$packageDir = 'C:\Users\Jalen\Tekken6-Practice-Dev'
$files = @('practice-stance-expanded-trace.txt', 'practice-frame-stance-expanded.txt') | ForEach-Object {
    $name = $_
    @("$packageDir\$name", "$packageDir\bin\$name") |
        Where-Object { Test-Path $_ } |
        ForEach-Object { Get-Item $_ } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
}
if (!($files | Where-Object { $_.Name -eq 'practice-stance-expanded-trace.txt' })) {
    throw 'No stance expansion capture found. Launch with -Capture and land an attack first.'
}
$output = Join-Path (Split-Path $PSScriptRoot -Parent) ('stance-expanded-results-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.zip')
Compress-Archive -LiteralPath @($files.FullName) -DestinationPath $output -ErrorAction Stop
Write-Host "Upload this file: $output"
