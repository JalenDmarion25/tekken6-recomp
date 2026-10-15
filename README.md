# Tekken 6 Recomp

Static recompiler project for the Xbox 360 release of Tekken 6. Game data and
generated code come from a user-provided XEX and are kept out of version control.

## Windows build

For a Linux-hosted Windows build, use an extracted LLVM-MinGW distribution.
Generate guest code from your own game XEX, then configure the Windows build:

```sh
cmake -S third_party/rexglue-sdk -B build/sdk-native -G Ninja \
  -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS=-mssse3 \
  -DREXGLUE_ENABLE_TRACY=OFF -DREXGLUE_ENABLE_PERF_COUNTERS=OFF
cmake --build build/sdk-native --target rexglue --parallel 3
third_party/rexglue-sdk/out/linux-amd64/rexglue codegen tekken6_manifest.toml

cmake -S . -B build/windows-llvm -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE=cmake/windows-clang.cmake \
  -DLLVM_MINGW_ROOT=/path/to/extracted/llvm-mingw \
  -DCMAKE_BUILD_TYPE=Release -DTEKKEN6_USE_PREGENERATED_CODE=ON \
  -DREXGLUE_USE_D3D12=ON -DREXGLUE_USE_VULKAN=ON \
  -DREXGLUE_ENABLE_TRACY=OFF -DREXGLUE_ENABLE_PERF_COUNTERS=OFF \
  -DREXGLUE_RECOMP_DEBUG_INFO=none
cmake --build build/windows-llvm --target tekken6 tekken6_low_overhead \
  tekken6_late_depth tekken6_fused_resolve tekken6_vulkan \
  tekken6_vulkan_fbo --parallel 2

python3 tools/package_windows.py --build-dir build/windows-llvm \
  --game-root /path/to/game --output /path/to/windows-package \
  --llvm-mingw-root /path/to/extracted/llvm-mingw
```

The package tool checks PE imports, stages required compiler runtime DLLs, and
writes a `build-info.json` manifest with source revisions and binary hashes.
CMake defaults to `Release` when no build type is selected. Generated guest
code uses FMA3 by default for faster explicit fused operations; the resulting
executable requires an FMA3-capable CPU. Set `-DTEKKEN6_ENABLE_FMA3=OFF` for a
portable build.

Press **F3** in game to show or hide the FPS and frame-time overlay. It reports
guest frame swaps independently of the host's overlay or presentation rate.
Routine logs are disabled in the Windows launcher. Unhandled crashes write
`crash.txt` and `crash.dmp` under `crashes/<run>/`.

The startup chooser offers internal 3D resolutions from 640x360 through the
original 1024x576. It also enables a 512x512 size for the 1024x1024 offscreen
target by default; this can soften shadows. Uncheck the option to keep the
original offscreen size.

## Rendering paths

`tekken6.exe` selects D3D12 ROV. The runtime includes no-blend shader
specialization and opt-in late-depth and fused RGBA8 resolve paths; unsupported
draws and resolves continue through the general implementation. The optional
late-depth and fused-resolve launchers enable those paths individually.

`tekken6_vulkan.exe` selects Vulkan fragment shader interlock (FSI). It requires
a Vulkan device and driver that expose fragment shader interlock. The explicit
request fails if the extension is unavailable. `tekken6_vulkan_fbo.exe` selects
the experimental framebuffer path, which does not require interlock.

The launcher keeps user saves, shader caches, and per-run logs in the package
directory. Game files and generated recompilation sources are local inputs and
must not be committed.
