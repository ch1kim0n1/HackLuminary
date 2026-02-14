#!/usr/bin/env python3
"""Render Winget manifests from release metadata."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from hackluminary.release_assets import render_winget_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Render Winget manifests for release.")
    parser.add_argument("--version", required=True)
    parser.add_argument("--repo", required=True, help="GitHub repository slug, e.g. owner/repo.")
    parser.add_argument("--installer-sha256", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    manifests = render_winget_manifest(
        version=args.version,
        repo=args.repo,
        installer_sha256=args.installer_sha256,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, content in manifests.items():
        path = args.output_dir / name
        path.write_text(content, encoding="utf-8")
        print(f"Wrote manifest: {path}")


if __name__ == "__main__":
    main()
