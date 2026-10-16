#!/usr/bin/env python3
"""Stage a Windows build and user-provided game data into a portable directory."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

SYSTEM_DLLS = {
    "advapi32.dll", "avrt.dll", "bcrypt.dll", "cfgmgr32.dll", "comctl32.dll",
    "comdlg32.dll", "crypt32.dll", "d3d12.dll", "dbghelp.dll", "dnsapi.dll",
    "dwmapi.dll", "dxgi.dll", "gdi32.dll", "hid.dll", "imm32.dll", "iphlpapi.dll",
    "kernel32.dll", "kernelbase.dll", "mf.dll", "mfplat.dll", "mfreadwrite.dll",
    "mfuuid.dll", "msvcrt.dll", "ntdll.dll", "ole32.dll", "oleaut32.dll",
    "powrprof.dll", "propsys.dll", "psapi.dll", "rpcrt4.dll", "secur32.dll",
    "setupapi.dll", "shell32.dll", "shlwapi.dll", "user32.dll", "userenv.dll",
    "usp10.dll", "ucrtbase.dll", "uuid.dll", "version.dll", "winhttp.dll",
    "wininet.dll", "winmm.dll", "winspool.drv", "ws2_32.dll", "wtsapi32.dll",
}


def copy_if_changed(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size == source.stat().st_size:
        with destination.open("rb") as old, source.open("rb") as new:
            if hashlib.file_digest(old, "sha256").digest() == hashlib.file_digest(new, "sha256").digest():
                return
    shutil.copyfile(source, destination)


def main() -> None:
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--build-dir", required=True, type=Path)
    parser.add_argument("--game-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--llvm-mingw-root", required=True, type=Path)
    parser.add_argument("--reuse-game", action="store_true",
                        help="Reuse staged game data after size and XEX identity checks")
    parser.add_argument("--source-revision")
    parser.add_argument("--sdk-revision")
    parser.add_argument("--game-version", default="user-provided Tekken 6 XEX")
    parser.add_argument("--backend", action="append", choices=(
        "d3d12-rov", "vulkan-fsi", "vulkan-fbo"),
        help="Backend to include (repeat for multiple; default includes all available)")
    args = parser.parse_args()
    build = args.build_dir.resolve()
    output = args.output.resolve()

    if args.backend:
        required_launchers = {
            "d3d12-rov": "tekken6_low_overhead.exe",
            "vulkan-fsi": "tekken6_vulkan.exe",
            "vulkan-fbo": "tekken6_vulkan_fbo.exe",
        }
        missing = [required_launchers[backend] for backend in args.backend
                   if not (build / required_launchers[backend]).is_file()]
        if missing:
            raise SystemExit("Missing selected renderer executable(s): " + ", ".join(missing))

    # A rebuild into an existing destination should reflect the current
    # checklist, rather than leave launchers from an earlier selection behind.
    for stale_name in (
        "tekken6.exe", "tekken6_vulkan.exe", "tekken6_vulkan_fbo.exe",
        "tekken6_late_depth.exe", "tekken6_fused_resolve.exe",
    ):
        (output / stale_name).unlink(missing_ok=True)

    gpu_plugin = build / "rexgpu-xenos.dll"
    if not gpu_plugin.is_file():
        raise SystemExit(f"Missing Windows GPU plugin: {gpu_plugin}")
    binary_dir = output / "bin"
    binary_dir.mkdir(parents=True, exist_ok=True)
    package_executables = [binary_dir / "tekken6.exe"]
    for name in ("tekken6.exe", "librexruntime.dll", "rexgpu-xenos.dll"):
        copy_if_changed(build / name, binary_dir / name)
    launchers = {
        "tekken6_low_overhead.exe": ("tekken6.exe", "d3d12-rov"),
        "tekken6_vulkan.exe": ("tekken6_vulkan.exe", "vulkan-fsi"),
        "tekken6_vulkan_fbo.exe": ("tekken6_vulkan_fbo.exe", "vulkan-fbo"),
        "tekken6_late_depth.exe": ("tekken6_late_depth.exe", "d3d12-rov"),
        "tekken6_fused_resolve.exe": ("tekken6_fused_resolve.exe", "d3d12-rov"),
    }
    for source, (destination, backend) in launchers.items():
        if args.backend and backend not in args.backend:
            continue
        built = build / source
        if built.is_file():
            copy_if_changed(built, output / destination)
            package_executables.append(output / destination)

    search_dirs = [build, args.llvm_mingw_root / "x86_64-w64-mingw32/bin"]
    objdump_candidates = (
        args.llvm_mingw_root / "bin" / "llvm-objdump.exe",
        args.llvm_mingw_root / "bin" / "x86_64-w64-mingw32-objdump.exe",
        args.llvm_mingw_root / "bin" / "x86_64-w64-mingw32-objdump",
        args.llvm_mingw_root / "bin" / "llvm-objdump",
        shutil.which("x86_64-w64-mingw32-objdump"),
    )
    objdump = next((str(candidate) for candidate in objdump_candidates
                    if candidate and Path(candidate).is_file()), None)
    if not objdump:
        raise SystemExit("x86_64-w64-mingw32-objdump is required to check DLL dependencies")
    pending = list(binary_dir.glob("*.dll")) + package_executables
    checked = set()
    while pending:
        executable = pending.pop()
        if executable in checked:
            continue
        checked.add(executable)
        imports = subprocess.check_output([objdump, "-p", str(executable)], text=True)
        for name in re.findall(r"DLL Name: (\S+)", imports):
            if name.lower() in SYSTEM_DLLS or name.lower().startswith(("api-ms-", "ext-ms-")):
                continue
            staged = binary_dir / name
            if not staged.exists():
                source = next((directory / name for directory in search_dirs
                               if (directory / name).is_file()), None)
                if source is None:
                    raise SystemExit(f"Unresolved DLL dependency: {name} (needed by {executable.name})")
                copy_if_changed(source, staged)
            pending.append(staged)
            if executable.parent == output:
                copy_if_changed(staged, output / name)
                pending.append(output / name)

    game_root = args.game_root.resolve()
    xex = game_root / "default.xex"
    if not xex.is_file():
        xex = game_root / "Default.xex"
    if not xex.is_file():
        raise SystemExit("The supplied game directory has no default.xex")
    for source in sorted(game_root.iterdir()):
        if source.is_file() and (re.fullmatch(r"DATA\d+\.(BIN|IDX)", source.name, re.I)
                                 or source.name.upper() == "DINF_300.BIN"):
            destination = output / "game" / source.name
            if args.reuse_game:
                if not destination.is_file() or destination.stat().st_size != source.stat().st_size:
                    raise SystemExit(f"Staged game file missing or size differs: {destination}")
                if source.suffix.upper() == ".IDX" and source.read_bytes() != destination.read_bytes():
                    raise SystemExit(f"Staged game index differs: {destination}")
            else:
                copy_if_changed(source, destination)
    staged_xex = output / "game/default.xex"
    if args.reuse_game:
        if not staged_xex.is_file() or xex.read_bytes() != staged_xex.read_bytes():
            raise SystemExit("Existing staged XEX differs from the supplied reference")
    else:
        copy_if_changed(xex, staged_xex)

    for directory in ("cache", "crashes", "user"):
        (output / directory).mkdir(exist_ok=True)
    selected_backends = args.backend or [
        backend for backend, executable in (
            ("d3d12-rov", output / "tekken6_low_overhead.exe"),
            ("vulkan-fsi", output / "tekken6_vulkan.exe"),
            ("vulkan-fbo", output / "tekken6_vulkan_fbo.exe"),
        ) if executable.is_file()
    ]
    readme_lines = [
        "TEKKEN 6 RECOMPILED WINDOWS BUILD\n\n"
        "Copy this folder to Windows. Keep bin and game beside the launchers.\n"
        "Each launcher offers internal 3D resolutions from lightest to heaviest GPU workload: "
        "640x360, 768x432, and original 1024x576.\n"
        "The chooser also enables a 512x512 size for the 1024x1024 offscreen target by default; "
        "this can soften shadows. Uncheck it to keep the original size.\n"
        "Unsupported render cases fall back to the standard implementation.\n"
        "Press F3 in game to show or hide the FPS and frame-time overlay.\n"
        "Only unhandled crashes write reports under crashes/<run>/.\n"
        "The launchers share user saves and persistent caches under this folder.\n"
    ]
    if "d3d12-rov" in selected_backends:
        readme_lines.append("tekken6.exe starts the D3D12 ROV build (widest compatibility).\n")
    if "vulkan-fsi" in selected_backends:
        readme_lines.append("tekken6_vulkan.exe selects Vulkan FSI and requires fragment shader interlock.\n")
    if "vulkan-fbo" in selected_backends:
        readme_lines.append("tekken6_vulkan_fbo.exe selects the experimental Vulkan framebuffer path.\n")
    (output / "READ ME.txt").write_text(
        "".join(readme_lines),
        encoding="utf-8",
    )

    repo = Path(__file__).resolve().parents[1]
    revision = args.source_revision or subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    sdk_revision = args.sdk_revision or subprocess.check_output(
        ["git", "-C", str(repo / "third_party/rexglue-sdk"), "rev-parse", "HEAD"],
        text=True,
    ).strip()
    hashes = {}
    for source in sorted(checked):
        with source.open("rb") as stream:
            hashes[str(source.relative_to(output))] = hashlib.file_digest(stream, "sha256").hexdigest()
    manifest = {
        "recomp_commit": revision,
        "sdk_commit": sdk_revision,
        "configuration": "Release",
        "backends": selected_backends,
        "game_version": args.game_version,
        "sha256": hashes,
    }
    (output / "build-info.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Staged Windows package at {output}")
    print(f"Checked {len(checked)} PE files and packaged {len(hashes)} executables/DLLs")


if __name__ == "__main__":
    main()
