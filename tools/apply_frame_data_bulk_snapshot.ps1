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
& $pythonExe "$PSScriptRoot\install_frame_data_bulk_snapshot.py"
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
$licenseDir = Join-Path $packageDir 'licenses'
New-Item -ItemType Directory -Path $licenseDir -Force | Out-Null
Copy-Item '.\licenses\RacingSansOne-OFL.txt' (Join-Path $licenseDir 'RacingSansOne-OFL.txt') -Force
# Refresh runtime dependencies even when reusing an existing package.
foreach ($folder in @($packageDir, "$packageDir\bin")) {
    foreach ($name in @('libc++.dll', 'libunwind.dll')) {
        Copy-Item "$llvmRoot\bin\$name" (Join-Path $folder $name) -Force
    }
}
$enabledFlags = @('TEKKEN6_SNAPSHOT_COMMANDS', 'TEKKEN6_TRACE_SHARED_ACTION', 'TEKKEN6_TEST_FRAME_DATA_HUD', 'TEKKEN6_TEST_OPPONENT_CONTROL', 'TEKKEN6_TEST_RECORD_CYCLE', 'TEKKEN6_TEST_RECORD_SLOTS', 'TEKKEN6_TEST_RECORD_HUD', 'TEKKEN6_TEST_WEIGHTED_PLAYBACK', 'TEKKEN6_TEST_LOOP_PLAYBACK', 'TEKKEN6_TEST_RECORD_MODE')
$traceFlags = @('TEKKEN6_TRACE_STANCE_EXPAND', 'TEKKEN6_TRACE_STANCE_GATE', 'TEKKEN6_TRACE_STANCE_FRAMES', 'TEKKEN6_TRACE_BLOCK_RESPONSE', 'TEKKEN6_TRACE_FRAME_DATA', 'TEKKEN6_TRACE_PRACTICE_WIDGETS', 'TEKKEN6_TRACE_NATIVE_HUD', 'TEKKEN6_TRACE_NATIVE_HUD_NODES', 'TEKKEN6_TRACE_NATIVE_HUD_SCENES')
$probeStamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
foreach ($folder in @($packageDir, "$packageDir\bin")) {
    foreach ($name in @('practice-shared-action.txt', 'practice-command-snapshot.txt')) {
        $oldLog = Join-Path $folder $name
        if (Test-Path $oldLog) { Move-Item $oldLog "$oldLog.before-$probeStamp" }
    }
}
$previous = @{}
try {
    foreach ($flag in ($enabledFlags + $traceFlags)) {
        $previous[$flag] = [Environment]::GetEnvironmentVariable($flag, 'Process')
        $value = if ($flag -in $enabledFlags) { '1' } else { '0' }
        [Environment]::SetEnvironmentVariable($flag, $value, 'Process')
    }
    Start-Process "$packageDir\tekken6.exe" -WorkingDirectory $packageDir -ErrorAction Stop
} finally {
    foreach ($flag in ($enabledFlags + $traceFlags)) {
        [Environment]::SetEnvironmentVariable($flag, $previous[$flag], 'Process')
    }
}
