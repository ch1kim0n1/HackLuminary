"""Corpus-level benchmarking helpers for visual coverage tuning."""

from __future__ import annotations

import time
from pathlib import Path

from .pipeline import run_generation


def benchmark_visual_coverage(
    corpus_dir: Path,
    confidence_candidates: list[float] | None = None,
    max_projects: int = 12,
) -> dict:
    root = Path(corpus_dir).resolve()
    candidates = confidence_candidates or [0.55, 0.62, 0.72, 0.8]

    projects = _discover_projects(root)
    projects = projects[: max(1, int(max_projects))]

    runs = []
    started = time.perf_counter()
    for min_conf in candidates:
        coverage_values: list[float] = []
        failures = 0
        for project in projects:
            try:
                result = run_generation(
                    project_dir=project,
                    cli_overrides={
                        "general": {
                            "mode": "deterministic",
                            "format": "json",
                            "strict_quality": False,
                        },
                        "images": {
                            "mode": "auto",
                            "min_confidence": float(min_conf),
                            "max_images_per_slide": 1,
                        },
                    },
                )
                metrics = result["payload"].get("quality_report", {}).get("metrics", {})
                coverage_values.append(float(metrics.get("image_coverage", 0.0) or 0.0))
            except Exception:
                failures += 1

        project_count = max(1, len(projects) - failures)
        avg_coverage = sum(coverage_values) / project_count if coverage_values else 0.0
        at_target = sum(1 for value in coverage_values if value >= 0.7)
        runs.append(
            {
                "min_confidence": round(float(min_conf), 3),
                "avg_coverage": round(avg_coverage, 3),
                "coverage_ge_0_7": at_target,
                "coverage_samples": len(coverage_values),
                "failures": failures,
            }
        )

    best = sorted(runs, key=lambda item: (-item["avg_coverage"], item["min_confidence"]))[0] if runs else None
    elapsed = time.perf_counter() - started

    return {
        "corpus_dir": str(root),
        "projects_considered": [str(path) for path in projects],
        "project_count": len(projects),
        "runs": runs,
        "recommended_min_confidence": best["min_confidence"] if best else None,
        "elapsed_sec": round(elapsed, 2),
    }


def _discover_projects(root: Path) -> list[Path]:
    projects: list[Path] = []

    if _looks_like_project(root):
        projects.append(root)

    for path in sorted(root.iterdir(), key=lambda item: item.name.lower()):
        if not path.is_dir():
            continue
        if path.name.startswith("."):
            continue
        if _looks_like_project(path):
            projects.append(path)

    return projects


def _looks_like_project(path: Path) -> bool:
    markers = [
        "README.md",
        "readme.md",
        "main.py",
        "package.json",
        "pyproject.toml",
        "requirements.txt",
    ]
    return any((path / marker).exists() for marker in markers)
