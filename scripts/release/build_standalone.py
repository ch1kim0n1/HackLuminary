#!/usr/bin/env python3
"""Build standalone CLI binaries using PyInstaller for release artifacts."""

from __future__ import annotations

import argparse
import hashlib
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build standalone HackLuminary binary artifact.")
    parser.add_argument("--platform-tag", default=None, help="Override platform tag (e.g., macos-x64).")
    parser.add_argument("--release-version", default=None, help="Release version for metadata.")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    os.chdir(repo_root)

    platform_tag = args.platform_tag or infer_platform_tag()
    binary_name = "hackluminary.exe" if platform.system().lower().startswith("win") else "hackluminary"

    run_pyinstaller(repo_root)

    dist_binary = repo_root / "dist" / binary_name
    if not dist_binary.exists():
        raise RuntimeError(f"Expected binary missing: {dist_binary}")

    release_dir = repo_root / "dist" / "release"
    release_dir.mkdir(parents=True, exist_ok=True)

    artifact_path = package_binary(dist_binary, release_dir, platform_tag)
    sha_path = write_sha256(artifact_path)

    print(f"Built artifact: {artifact_path}")
    print(f"SHA256 file: {sha_path}")


def run_pyinstaller(repo_root: Path) -> None:
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--name",
        "hackluminary",
        "--onefile",
        "--collect-data",
        "hackluminary",
        "hackluminary/cli.py",
    ]
    subprocess.run(cmd, check=True, cwd=repo_root)


def infer_platform_tag() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()

    if machine in {"x86_64", "amd64"}:
        arch = "x64"
    elif machine in {"arm64", "aarch64"}:
        arch = "arm64"
    else:
        arch = machine

    if system.startswith("darwin"):
        return f"macos-{arch}"
    if system.startswith("windows"):
        return f"windows-{arch}"
    if system.startswith("linux"):
        return f"linux-{arch}"
    return f"{system}-{arch}"


def package_binary(dist_binary: Path, release_dir: Path, platform_tag: str) -> Path:
    staging = release_dir / f"staging-{platform_tag}"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True, exist_ok=True)

    target_name = "hackluminary.exe" if dist_binary.suffix.lower() == ".exe" else "hackluminary"
    target = staging / target_name
    shutil.copy2(dist_binary, target)

    license_src = dist_binary.parents[1] / "LICENSE"
    if license_src.exists():
        shutil.copy2(license_src, staging / "LICENSE")

    if platform_tag.startswith("windows-"):
        archive = release_dir / f"hackluminary-{platform_tag}.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for file_path in sorted(staging.iterdir(), key=lambda p: p.name.lower()):
                zf.write(file_path, arcname=file_path.name)
    else:
        archive = release_dir / f"hackluminary-{platform_tag}.tar.gz"
        with tarfile.open(archive, "w:gz") as tf:
            for file_path in sorted(staging.iterdir(), key=lambda p: p.name.lower()):
                tf.add(file_path, arcname=file_path.name)

    shutil.rmtree(staging, ignore_errors=True)
    return archive


def write_sha256(path: Path) -> Path:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    sha_path = path.with_suffix(path.suffix + ".sha256")
    sha_path.write_text(f"{digest}  {path.name}\n", encoding="utf-8")
    return sha_path


if __name__ == "__main__":
    main()
