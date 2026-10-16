#!/usr/bin/env python3
"""Assemble the Windows one-click ISO builder release folder."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
SDK_SUBMODULES = (
    "cli11", "libmspack", "FFmpeg", "tomlplusplus", "simde", "xxHash",
    "spdlog", "fmt", "utfcpp", "imgui", "sdl3", "inja", "o1heap",
    "vulkan-headers", "vulkan-memory-allocator", "spirv-headers",
    "spirv-tools", "glslang",
)


def git_revision(path: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(path), "rev-parse", "HEAD"], text=True
    ).strip()


def ignore_project(path: str, names: list[str]) -> set[str]:
    excluded = {
        ".git", ".local-tests", "build", "out", "logs", "cache", "crashes",
        "user", "game", "CMakeFiles", "__pycache__",
    }
    if path == str(ROOT / "generated" / "default"):
        excluded.update(name for name in names if name != ".gitkeep")
    return {name for name in names if name in excluded}


def apply_sdk_patch(sdk: Path) -> None:
    patch = ROOT / "patches/rexglue/0001-tekken6-runtime.patch"
    already_applied = subprocess.run(
        ["git", "apply", "--reverse", "--check", str(patch)], cwd=sdk,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0
    if already_applied:
        return
    subprocess.run(["git", "apply", "--check", str(patch)], cwd=sdk, check=True)
    subprocess.run(["git", "apply", str(patch)], cwd=sdk, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--builder-exe", required=True, type=Path)
    parser.add_argument("--llvm-mingw-root", required=True, type=Path)
    parser.add_argument("--cmake-root", required=True, type=Path,
                        help="Extracted portable CMake directory containing bin/cmake.exe")
    parser.add_argument("--ninja", required=True, type=Path)
    parser.add_argument("--python-root", required=True, type=Path,
                        help="Extracted Python embeddable package directory")
    parser.add_argument("--xdvdfs-tool", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise SystemExit(f"Output folder must be empty: {output}")
    builder = output / "builder"
    project = builder / "project"
    builder.mkdir(parents=True, exist_ok=True)

    if not args.builder_exe.is_file():
        raise SystemExit(f"Builder executable not found: {args.builder_exe}")
    if not (args.cmake_root / "bin" / "cmake.exe").is_file():
        raise SystemExit(f"Portable CMake is missing: {args.cmake_root / 'bin' / 'cmake.exe'}")
    if not (args.python_root / "python.exe").is_file():
        raise SystemExit(f"Python embeddable package is missing: {args.python_root}")
    if not args.ninja.is_file() or not args.xdvdfs_tool.is_file():
        raise SystemExit("Ninja or xdvdfs_tool.exe is missing")
    if not (args.llvm_mingw_root / "bin" / "x86_64-w64-mingw32-clang++.exe").is_file():
        raise SystemExit("LLVM-MinGW does not contain the x64 Windows Clang driver")

    shutil.copy2(args.builder_exe, output / "Tekken 6 Builder.exe")
    for runtime_name in ("libc++.dll", "libunwind.dll"):
        runtime = args.llvm_mingw_root / "bin" / runtime_name
        if not runtime.is_file():
            raise SystemExit(f"LLVM-MinGW runtime DLL is missing: {runtime}")
        shutil.copy2(runtime, output / runtime_name)
    shutil.copytree(ROOT, project, ignore=ignore_project)
    apply_sdk_patch(project / "third_party" / "rexglue-sdk")

    sdk = project / "third_party" / "rexglue-sdk"
    for marker in (sdk, *(sdk / "thirdparty" / name for name in SDK_SUBMODULES)):
        if not marker.is_dir():
            raise SystemExit(f"Required SDK source is missing: {marker}")
        (marker / ".git").mkdir(exist_ok=True)

    shutil.copytree(args.llvm_mingw_root, builder / "llvm-mingw")
    shutil.copytree(args.cmake_root, builder / "cmake")
    shutil.copytree(args.python_root, builder / "python")
    shutil.copy2(ROOT / "tools" / "build_from_iso.py", builder / "build_from_iso.py")
    (builder / "ninja").mkdir()
    shutil.copy2(args.ninja, builder / "ninja" / "ninja.exe")
    (builder / "bin").mkdir()
    shutil.copy2(args.xdvdfs_tool, builder / "bin" / "xdvdfs_tool.exe")

    metadata = {
        "recomp_revision": git_revision(ROOT),
        "sdk_revision": git_revision(ROOT / "third_party" / "rexglue-sdk"),
    }
    (builder / "build-info.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    (output / "README.txt").write_text(
        "TEKKEN 6 BUILDER\n\n"
        "1. Extract the complete release folder.\n"
        "2. Open Tekken 6 Builder.exe.\n"
        "3. Select your own Xbox 360 ISO.\n"
        "4. Choose one or more renderer versions and press Build.\n\n"
        "The builder checks the game version, extracts the game on this PC, and "
        "creates a Windows package in the folder you choose. It includes no game "
        "ISO or game data. Keep the builder folder beside the executable.\n\n"
        "The first build needs several gigabytes of free disk space and can take "
        "a while. Internet access is not needed after downloading the release.\n",
        encoding="utf-8",
    )
    print(f"Portable builder package created at {output}")


if __name__ == "__main__":
    main()
