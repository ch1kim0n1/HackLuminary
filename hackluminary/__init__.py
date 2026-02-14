"""HackLuminary public API."""

from __future__ import annotations

import json
from pathlib import Path

from .pipeline import run_generation
from .studio_server import run_studio_server

__version__ = "2.1.0"


def generate_presentation(
    project_dir,
    output=None,
    fmt="both",
    docs=None,
    theme="default",
    mode="hybrid",
    slides=None,
    max_slides=None,
    base_branch=None,
    include_branch_context=True,
    strict_quality=True,
):
    """Generate a presentation payload and optional rendered outputs.

    This function keeps backward compatibility with the previous API while
    exposing v2 behavior and schema payload.
    """

    overrides = {
        "general": {
            "format": fmt,
            "theme": theme,
            "mode": mode,
            "strict_quality": strict_quality,
        },
        "git": {
            "base_branch": base_branch,
            "include_branch_context": include_branch_context,
        },
    }

    result = run_generation(
        project_dir=project_dir,
        additional_docs=list(docs or []),
        requested_slide_types=slides,
        max_slides=max_slides,
        cli_overrides=overrides,
    )

    payload = result["payload"]
    output_path = Path(output).resolve() if output else None

    if output_path:
        if fmt in ("html", "both") and result.get("html"):
            html_path = output_path if fmt == "html" else output_path.with_suffix(".html")
            html_path.write_text(result["html"], encoding="utf-8")
        if fmt in ("markdown", "both") and result.get("markdown"):
            md_path = output_path if fmt == "markdown" else output_path.with_suffix(".md")
            md_path.write_text(result["markdown"], encoding="utf-8")
        if fmt == "json":
            json_path = output_path if output_path.suffix == ".json" else output_path.with_suffix(".json")
            json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    return {
        "html": result.get("html"),
        "markdown": result.get("markdown"),
        "json": payload,
        "slides": payload.get("slides", []),
        "metadata": payload.get("metadata", {}),
        "quality_report": payload.get("quality_report", {}),
        "warnings": result.get("warnings", []),
    }


def launch_studio(project_dir, base_branch=None, theme=None, port=0, read_only=False, debug=False):
    """Launch local Studio workspace."""

    overrides = {
        "general": {
            "theme": theme,
            "format": "json",
            "mode": "deterministic",
        },
        "git": {
            "base_branch": base_branch,
        },
        "studio": {
            "read_only": read_only,
            "port": port,
        },
    }
    run_studio_server(
        project_path=project_dir,
        cli_overrides=overrides,
        port=port or 0,
        read_only=read_only,
        auto_open=True,
        debug=debug,
    )
