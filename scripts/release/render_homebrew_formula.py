#!/usr/bin/env python3
"""Render Homebrew formula from release checksums."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from hackluminary.release_assets import render_homebrew_formula


def main() -> None:
    parser = argparse.ArgumentParser(description="Render Homebrew formula for release.")
    parser.add_argument("--version", required=True)
    parser.add_argument("--repo", required=True, help="GitHub repository slug, e.g. owner/repo.")
    parser.add_argument("--arm64-sha256", required=True)
    parser.add_argument("--x64-sha256", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    formula = render_homebrew_formula(
        version=args.version,
        repo=args.repo,
        arm64_sha256=args.arm64_sha256,
        x64_sha256=args.x64_sha256,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(formula, encoding="utf-8")
    print(f"Wrote Homebrew formula: {args.output}")


if __name__ == "__main__":
    main()
