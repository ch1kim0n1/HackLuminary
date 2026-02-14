"""Environment and project health checks for smooth local usage."""

from __future__ import annotations

import sys
from pathlib import Path

from .config import load_resolved_config
from .git_context import detect_base_branch
from .models import resolve_model_path


def run_doctor(project_path: Path) -> dict:
    """Run local checks and return machine-readable diagnostics."""

    checks: list[dict] = []
    project_path = project_path.resolve()

    checks.append(_check_python_version())
    project_check = _check_project_directory(project_path)
    checks.append(project_check)

    if project_check["status"] == "pass":
        checks.append(_check_project_writable(project_path))
    else:
        checks.append(
            {
                "id": "write_access",
                "status": "warn",
                "message": "Write access check skipped because project directory is missing.",
                "hint": "Create the directory first or pass an existing project path.",
            }
        )

    cfg = _check_config(project_path)
    checks.append(cfg["check"])

    checks.append(_check_git(project_path))
    checks.append(_check_studio_assets())

    if cfg["config"] is not None:
        checks.append(_check_model_availability(cfg["config"]))

    summary = summarize_checks(checks)
    return {"checks": checks, "summary": summary}


def summarize_checks(checks: list[dict]) -> dict:
    passed = sum(1 for c in checks if c["status"] == "pass")
    warns = sum(1 for c in checks if c["status"] == "warn")
    failed = sum(1 for c in checks if c["status"] == "fail")
    status = "pass" if failed == 0 else "fail"
    return {
        "status": status,
        "passed": passed,
        "warnings": warns,
        "failed": failed,
        "total": len(checks),
    }


def _check_python_version() -> dict:
    major, minor = sys.version_info[:2]
    if (major, minor) >= (3, 10):
        return {
            "id": "python_version",
            "status": "pass",
            "message": f"Python {major}.{minor} is supported.",
            "hint": "",
        }
    return {
        "id": "python_version",
        "status": "fail",
        "message": f"Python {major}.{minor} is too old.",
        "hint": "Use Python 3.10+.",
    }


def _check_project_directory(project_path: Path) -> dict:
    if project_path.exists() and project_path.is_dir():
        return {
            "id": "project_dir",
            "status": "pass",
            "message": f"Project directory exists: {project_path}",
            "hint": "",
        }
    return {
        "id": "project_dir",
        "status": "fail",
        "message": f"Project directory is missing: {project_path}",
        "hint": "Run from the repository root or pass --project-dir PATH.",
    }


def _check_project_writable(project_path: Path) -> dict:
    probe_dir = project_path / ".hackluminary"
    probe_file = probe_dir / ".doctor-write-probe"
    try:
        probe_dir.mkdir(parents=True, exist_ok=True)
        probe_file.write_text("ok", encoding="utf-8")
        probe_file.unlink(missing_ok=True)
    except Exception as exc:
        return {
            "id": "write_access",
            "status": "fail",
            "message": f"Project is not writable: {project_path}",
            "hint": str(exc),
        }
    return {
        "id": "write_access",
        "status": "pass",
        "message": "Project write access is available.",
        "hint": "",
    }


def _check_config(project_path: Path) -> dict:
    try:
        cfg = load_resolved_config(project_path)
    except Exception as exc:
        return {
            "config": None,
            "check": {
                "id": "config_load",
                "status": "fail",
                "message": "Configuration failed to load.",
                "hint": str(exc),
            },
        }

    return {
        "config": cfg,
        "check": {
            "id": "config_load",
            "status": "pass",
            "message": "Configuration loaded successfully.",
            "hint": "",
        },
    }


def _check_git(project_path: Path) -> dict:
    git_dir = project_path / ".git"
    if not git_dir.exists():
        return {
            "id": "git_context",
            "status": "warn",
            "message": "No .git directory found; delta slide will be disabled.",
            "hint": "Initialize git or clone with history for branch-aware output.",
        }

    base = detect_base_branch(project_path)
    if not base:
        return {
            "id": "git_context",
            "status": "warn",
            "message": "Could not detect base branch (main/master).",
            "hint": "Set --base-branch explicitly or add main/master reference.",
        }

    return {
        "id": "git_context",
        "status": "pass",
        "message": f"Git repository detected (base branch: {base}).",
        "hint": "",
    }


def _check_model_availability(config: dict) -> dict:
    mode = str(config.get("general", {}).get("mode", "hybrid"))
    ai_enabled = bool(config.get("ai", {}).get("enabled", True))
    alias = str(config.get("ai", {}).get("model_alias", "qwen2.5-3b-instruct-q4_k_m"))

    if mode == "deterministic" or not ai_enabled:
        return {
            "id": "model_ready",
            "status": "pass",
            "message": "Model check skipped (deterministic mode).",
            "hint": "",
        }

    path = resolve_model_path(alias)
    if path and path.exists():
        return {
            "id": "model_ready",
            "status": "pass",
            "message": f"Model is installed: {alias}",
            "hint": str(path),
        }

    return {
        "id": "model_ready",
        "status": "warn",
        "message": f"Model alias is missing: {alias}",
        "hint": f"Run: hackluminary models install {alias}",
    }


def _check_studio_assets() -> dict:
    base = Path(__file__).resolve().parent / "studio"
    assets = [
        base / "index.html",
        base / "studio.css",
        base / "studio.js",
    ]
    missing = [str(path) for path in assets if not path.exists()]
    if missing:
        return {
            "id": "studio_assets",
            "status": "fail",
            "message": "Studio assets are incomplete.",
            "hint": ", ".join(missing),
        }
    return {
        "id": "studio_assets",
        "status": "pass",
        "message": "Studio assets are present.",
        "hint": "",
    }
