#!/usr/bin/env python3
"""Build a portable Windows package from a user-provided Tekken 6 ISO."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import zipfile


SUPPORTED_XEX = {
    "ee138a4fe8d32a0edc131451377f4377041a49626153fa992db24f5420a7f15c":
        "Tekken 6 (Europe/USA) Rev 1",
}
def say(message: str) -> None:
    print(message, flush=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(command: list[str], *, cwd: Path, log: Path, label: str,
        progress: int | None = None) -> None:
    say(f"STEP {label}")
    if progress is not None:
        say(f"PROGRESS {progress}")
    with log.open("a", encoding="utf-8", errors="replace") as output:
        output.write(f"\n> {' '.join(command)}\n")
        output.flush()
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        assert process.stdout is not None
        for line in process.stdout:
            output.write(line)
            output.flush()
            say(line.rstrip("\r\n"))
        code = process.wait()
    if code:
        raise RuntimeError(f"{label} failed with exit code {code}. See builder\\build.log.")


def list_iso(xdvdfs: Path, iso: Path, listing: Path, work: Path, log: Path) -> str:
    run([str(xdvdfs), "list", str(iso), str(listing)], cwd=work, log=log,
        label="Inspecting the ISO", progress=8)
    if not listing.is_file():
        raise RuntimeError("The ISO could not be read as an Xbox 360 disc image.")
    names = []
    for row in listing.read_text(encoding="utf-8", errors="replace").splitlines():
        if "\t" in row:
            names.append(row.split("\t", 1)[1].strip().replace("\\", "/"))
    xex = next((name for name in names
                if Path(name).name.lower() == "default.xex" and "/" not in name), None)
    if not xex:
        raise RuntimeError("No Default.xex was found at the root of this ISO.")
    return xex


def prepare_game(xdvdfs: Path, source: Path, project: Path, work: Path,
                 log: Path) -> tuple[Path, str]:
    game = project / "game"
    game.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        xex = next((candidate for candidate in source.iterdir()
                    if candidate.is_file() and candidate.name.lower() == "default.xex"), None)
        if not xex:
            raise RuntimeError("The selected folder must contain Default.xex and the DATA files.")
        identity_path = xex
        source_folder = source
    else:
        listing = work / "iso-files.txt"
        internal_xex = list_iso(xdvdfs, source, listing, work, log)
        identity_path = work / "default-xex-check.bin"
        run([str(xdvdfs), "extract", str(source), internal_xex, str(identity_path)],
            cwd=work, log=log, label="Checking the game version", progress=12)
        source_folder = None

    xex_hash = sha256(identity_path)
    version = SUPPORTED_XEX.get(xex_hash)
    if not version:
        raise RuntimeError(
            "This game image is not the supported Tekken 6 Europe/USA Rev 1 release. "
            f"Default.xex SHA-256: {xex_hash}"
        )
    say(f"Game version: {version}")

    existing_xex = next((candidate for candidate in game.iterdir()
                         if candidate.is_file() and candidate.name.lower() == "default.xex"), None)
    already_ready = existing_xex is not None and sha256(existing_xex) == xex_hash and any(
        candidate.is_file() and candidate.name.lower().startswith("data") and
        candidate.suffix.lower() in (".bin", ".idx")
        for candidate in game.iterdir()
    )
    if not already_ready:
        for child in game.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
        if source_folder is not None:
            say("STEP Copying the game files")
            for item in source_folder.iterdir():
                if item.is_file() and (
                    item.name.lower() == "default.xex" or
                    item.name.upper() == "DINF_300.BIN" or
                    re.fullmatch(r"DATA\d+\.(BIN|IDX)", item.name, re.IGNORECASE)
                ):
                    shutil.copy2(item, game / item.name)
        else:
            assert not any(game.iterdir())
            run([str(xdvdfs), "extract-all", str(source), str(game)], cwd=work,
                log=log, label="Extracting the game data", progress=20)
    if not any(candidate.is_file() and candidate.name.lower().startswith("data") and
               candidate.suffix.lower() == ".bin" for candidate in game.iterdir()):
        raise RuntimeError("The game data files are missing next to Default.xex.")
    return game, version


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--builder-root", required=True, type=Path)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--d3d12-rov", action="store_true")
    parser.add_argument("--vulkan-fsi", action="store_true")
    parser.add_argument("--vulkan-fbo", action="store_true")
    args = parser.parse_args()

    source = args.iso.resolve()
    if not source.is_file() and not source.is_dir():
        parser.error(f"game source does not exist: {source}")
    builder = args.builder_root.resolve()
    project_template = args.project.resolve()
    output = args.output.resolve()
    if not any((args.d3d12_rov, args.vulkan_fsi, args.vulkan_fbo)):
        parser.error("select at least one renderer")

    work = builder / "work"
    work.mkdir(parents=True, exist_ok=True)
    log = builder / "build.log"
    log.write_text(f"Tekken 6 portable build started: {time.ctime()}\n", encoding="utf-8")
    build_info_path = builder / "build-info.json"
    build_info = json.loads(build_info_path.read_text(encoding="utf-8"))
    project = work / "project"
    source_marker = project / ".builder-source-revision"
    marker_value = build_info["recomp_revision"] + "\nsource-bundle-v2"
    source_ready = (
        project.is_dir() and source_marker.is_file() and
        source_marker.read_text(encoding="utf-8").strip() == marker_value
    )
    if project.exists() and not source_ready:
        shutil.rmtree(project)
        shutil.rmtree(work / "windows-build", ignore_errors=True)
    if not source_ready:
        say("STEP Unpacking the build sources")
        say("PROGRESS 3")
        project.mkdir(parents=True)
        if project_template.is_dir():
            shutil.copytree(project_template, project, dirs_exist_ok=True,
                            copy_function=shutil.copy)
        else:
            with zipfile.ZipFile(project_template) as archive:
                for entry in archive.infolist():
                    destination = (project / entry.filename).resolve()
                    if not destination.is_relative_to(project.resolve()):
                        raise RuntimeError("The bundled source archive contains an invalid path.")
                    if entry.is_dir():
                        destination.mkdir(parents=True, exist_ok=True)
                    else:
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        with archive.open(entry) as source_stream, destination.open("wb") as target:
                            shutil.copyfileobj(source_stream, target)
        sdk = project / "third_party" / "rexglue-sdk"
        sdk_markers = (
            "cli11", "libmspack", "FFmpeg", "tomlplusplus", "simde", "xxHash",
            "spdlog", "fmt", "utfcpp", "imgui", "sdl3", "inja", "o1heap",
            "vulkan-headers", "vulkan-memory-allocator", "spirv-headers",
            "spirv-tools", "glslang",
        )
        for directory in (sdk, *(sdk / "thirdparty" / name for name in sdk_markers)):
            (directory / ".git").mkdir(parents=True, exist_ok=True)
        source_marker.write_text(marker_value + "\n", encoding="utf-8")
    xdvdfs = builder / "bin" / "xdvdfs_tool.exe"
    cmake = builder / "cmake" / "bin" / "cmake.exe"
    ninja = builder / "ninja" / "ninja.exe"
    llvm_mingw = builder / "llvm-mingw"
    # The compiler emits build-time Windows tools (including rexglue.exe) that
    # depend on LLVM-MinGW runtime DLLs. Keep those DLLs discoverable for CMake
    # custom commands as well as for the compiler itself.
    runtime_dirs = (
        llvm_mingw / "bin",
        llvm_mingw / "x86_64-w64-mingw32" / "bin",
    )
    os.environ["PATH"] = os.pathsep.join(
        [*(str(path) for path in runtime_dirs), os.environ.get("PATH", "")]
    )

    try:
        game, version = prepare_game(xdvdfs, source, project, work, log)
        build_dir = work / "windows-build"
        use_vulkan = args.vulkan_fsi or args.vulkan_fbo
        configure_command = [
            str(cmake), "-S", str(project), "-B", str(build_dir), "-G", "Ninja",
            f"-DCMAKE_MAKE_PROGRAM={ninja}",
            f"-DPYTHON_EXECUTABLE={builder / 'python' / 'python.exe'}",
            "-DCMAKE_SUPPRESS_REGENERATION=ON",
            f"-DCMAKE_TOOLCHAIN_FILE={project / 'cmake' / 'windows-clang.cmake'}",
            f"-DLLVM_MINGW_ROOT={llvm_mingw}",
            f"-DREXSDK_DIR={project / 'third_party' / 'rexglue-sdk'}",
            "-DCMAKE_BUILD_TYPE=Release",
            "-DTEKKEN6_USE_PREGENERATED_CODE=OFF",
            f"-DREXGLUE_USE_D3D12={'ON' if args.d3d12_rov else 'OFF'}",
            f"-DREXGLUE_USE_VULKAN={'ON' if use_vulkan else 'OFF'}",
            "-DREXGLUE_BUILD_TESTS=OFF",
            "-DREXGLUE_ENABLE_TRACY=OFF",
            "-DREXGLUE_ENABLE_PERF_COUNTERS=OFF",
            "-DREXGLUE_RECOMP_DEBUG_INFO=none",
            "-DTEKKEN6_ENABLE_FMA3=OFF",
        ]
        import_header = project / "generated" / "default" / "tekken6_funcs.h"
        config_marker = build_dir / "portable-builder-config.json"
        config_signature = json.dumps({
            "recomp_revision": build_info["recomp_revision"],
            "sdk_revision": build_info["sdk_revision"],
            "d3d12_rov": args.d3d12_rov,
            "vulkan_fsi": args.vulkan_fsi,
            "vulkan_fbo": args.vulkan_fbo,
        }, sort_keys=True)
        configured = (
            (build_dir / "CMakeCache.txt").is_file() and
            (build_dir / "build.ninja").is_file() and
            config_marker.is_file() and
            config_marker.read_text(encoding="utf-8").strip() == config_signature
        )
        had_import_header = import_header.is_file()
        if not configured:
            run(configure_command, cwd=project, log=log,
                label="Preparing the Windows build", progress=18)

        workers = max(1, min(3, (os.cpu_count() or 2) - 1))
        run([str(cmake), "--build", str(build_dir), "--target", "tekken6_codegen",
             "--parallel", str(workers)], cwd=project, log=log,
            label="Generating game code", progress=22)

        # The Windows runtime exports are derived from codegen's import header.
        # Reconfigure once after first generation so the runtime .def is included.
        if not configured and not had_import_header:
            run(configure_command, cwd=project, log=log,
                label="Finishing Windows build setup", progress=24)
        build_dir.mkdir(parents=True, exist_ok=True)
        config_marker.write_text(config_signature + "\n", encoding="utf-8")

        targets = ["xdvdfs_tool", "tekken6"]
        backends = []
        if args.d3d12_rov:
            targets.append("tekken6_low_overhead")
            backends.append("d3d12-rov")
        if args.vulkan_fsi:
            targets.append("tekken6_vulkan")
            backends.append("vulkan-fsi")
        if args.vulkan_fbo:
            targets.append("tekken6_vulkan_fbo")
            backends.append("vulkan-fbo")
        run([str(cmake), "--build", str(build_dir), "--target", *targets,
             "--parallel", str(workers)], cwd=project, log=log,
            label="Generating and compiling the game", progress=25)

        package_command = [
            str(builder / "python" / "python.exe"), "-I",
            str(project / "tools" / "package_windows.py"),
            "--build-dir", str(build_dir), "--game-root", str(game),
            "--output", str(output), "--llvm-mingw-root", str(llvm_mingw),
            "--source-revision", build_info["recomp_revision"],
            "--sdk-revision", build_info["sdk_revision"],
            "--game-version", version,
        ]
        for backend in backends:
            package_command.extend(("--backend", backend))
        run(package_command, cwd=project, log=log, label="Packaging the Windows game",
            progress=95)
        say("PROGRESS 100")
        say(f"DONE {output}")
        return 0
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        say(f"ERROR {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
