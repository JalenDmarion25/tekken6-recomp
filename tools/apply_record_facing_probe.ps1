$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$builderRoot = 'C:\Users\Jalen\Emulators\Tekken6NativeOnline\builder'
$pythonExe = "$builderRoot\python\python.exe"
$cmakeExe = 'C:\Program Files\CMake\bin\cmake.exe'
$llvmRoot = "$builderRoot\llvm-mingw"
$buildDir = "$PWD\build\practice"
$packageDir = 'C:\Users\Jalen\Tekken6-Practice-Dev'
foreach ($tool in @($pythonExe, $cmakeExe, "$llvmRoot\bin\libc++.dll", "$llvmRoot\bin\libunwind.dll")) {
    if (!(Test-Path $tool)) { throw "Required tool or runtime missing: $tool" }
}
$objdump = Get-ChildItem "$builderRoot\packaging-tools" -Recurse -File -Filter llvm-objdump.exe |
    Select-Object -First 1 -ExpandProperty FullName
if (!$objdump) { throw 'Windows objdump not found in packaging-tools' }
$env:LLVM_MINGW_ROOT = $llvmRoot
$env:PATH = "C:\Program Files\Git\cmd;$llvmRoot\bin;$llvmRoot\x86_64-w64-mingw32\bin;$env:PATH"
& $pythonExe "$PSScriptRoot\install_record_facing_probe.py"
if ($LASTEXITCODE -ne 0) { throw 'Installation failed' }
& $cmakeExe --build $buildDir --target tekken6 tekken6_low_overhead --parallel 2
if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
$previousObjdump = $env:TEKKEN6_OBJDUMP
try {
    $env:TEKKEN6_OBJDUMP = $objdump
    & $pythonExe '.\tools\package_windows.py' --build-dir $buildDir --game-root "$PWD\game" --output $packageDir --llvm-mingw-root $llvmRoot --backend d3d12-rov --reuse-game
    if ($LASTEXITCODE -ne 0) { throw 'Packaging failed' }
} finally {
    $env:TEKKEN6_OBJDUMP = $previousObjdump
}
# Refresh runtime dependencies even when reusing an existing package.
foreach ($folder in @($packageDir, "$packageDir\bin")) {
    foreach ($name in @('libc++.dll', 'libunwind.dll')) {
        Copy-Item "$llvmRoot\bin\$name" (Join-Path $folder $name) -Force
    }
}
$flags = @('TEKKEN6_TEST_OPPONENT_CONTROL', 'TEKKEN6_TEST_RECORD_CYCLE', 'TEKKEN6_TEST_RECORD_SLOTS', 'TEKKEN6_TEST_RECORD_HUD', 'TEKKEN6_TEST_WEIGHTED_PLAYBACK', 'TEKKEN6_TEST_LOOP_PLAYBACK', 'TEKKEN6_TEST_RECORD_MODE', 'TEKKEN6_TRACE_RECORD_FACING')
$previous = @{}
try {
    foreach ($flag in $flags) {
        $previous[$flag] = [Environment]::GetEnvironmentVariable($flag, 'Process')
        [Environment]::SetEnvironmentVariable($flag, '1', 'Process')
    }
    Start-Process "$packageDir\tekken6.exe" -WorkingDirectory $packageDir
} finally {
    foreach ($flag in $flags) {
        [Environment]::SetEnvironmentVariable($flag, $previous[$flag], 'Process')
    }
}
