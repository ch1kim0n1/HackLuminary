"""Git context collection for branch-aware presentation generation."""

from __future__ import annotations

import subprocess
from pathlib import Path


def _run_git(project_path: Path, args: list[str]) -> str:
    completed = subprocess.run(
        ["git", "-C", str(project_path), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


def _ref_exists(project_path: Path, ref: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(project_path), "rev-parse", "--verify", ref],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.returncode == 0


def detect_base_branch(project_path: Path, preferred: str | None = None) -> str | None:
    if preferred:
        if _ref_exists(project_path, preferred):
            return preferred
        return None

    for candidate in ["main", "master", "origin/main", "origin/master"]:
        if _ref_exists(project_path, candidate):
            return candidate
    return None


def collect_git_context(
    project_path: Path,
    include_branch_context: bool = True,
    base_branch: str | None = None,
) -> dict:
    """Collect git metadata required by the v2 JSON schema."""

    payload = {
        "available": False,
        "branch": "",
        "base_branch": "",
        "head_sha": "",
        "base_sha": "",
        "changed_files_count": 0,
        "top_changed_paths": [],
        "change_summary": "Git context disabled.",
        "warnings": [],
    }

    if not include_branch_context:
        payload["change_summary"] = "Branch context disabled by user."
        return payload

    try:
        inside = _run_git(project_path, ["rev-parse", "--is-inside-work-tree"])
    except Exception:
        payload["warnings"].append("Project is not a git repository; delta slide will be skipped.")
        payload["change_summary"] = "Git context unavailable (not a repository)."
        return payload

    if inside != "true":
        payload["warnings"].append("Project is not inside a git working tree.")
        payload["change_summary"] = "Git context unavailable."
        return payload

    payload["available"] = True

    try:
        payload["branch"] = _run_git(project_path, ["rev-parse", "--abbrev-ref", "HEAD"])
        payload["head_sha"] = _run_git(project_path, ["rev-parse", "HEAD"])
    except Exception as exc:
        payload["warnings"].append(f"Failed to read branch metadata: {exc}")
        payload["change_summary"] = "Git metadata partially unavailable."
        return payload

    detected_base = detect_base_branch(project_path, preferred=base_branch)
    if not detected_base:
        payload["warnings"].append("Could not detect base branch (tried main/master).")
        payload["change_summary"] = "Base branch unavailable; showing current branch only."
        return payload

    payload["base_branch"] = detected_base

    try:
        merge_base = _run_git(project_path, ["merge-base", "HEAD", detected_base])
        payload["base_sha"] = merge_base
        diff_paths = _run_git(project_path, ["diff", "--name-only", f"{merge_base}..HEAD"])
    except Exception as exc:
        payload["warnings"].append(f"Failed to compute git diff against {detected_base}: {exc}")
        payload["change_summary"] = "Branch comparison unavailable due to git command failure."
        return payload

    changed_paths = [line.strip() for line in diff_paths.splitlines() if line.strip()]
    changed_paths = sorted(changed_paths)

    payload["changed_files_count"] = len(changed_paths)
    payload["top_changed_paths"] = changed_paths[:10]
    payload["change_summary"] = summarize_changes(changed_paths)

    return payload


def summarize_changes(changed_paths: list[str]) -> str:
    """Create a deterministic summary sentence from changed files."""

    if not changed_paths:
        return "No file changes detected compared to the base branch."

    buckets = {
        "backend": 0,
        "frontend": 0,
        "docs": 0,
        "config": 0,
        "other": 0,
    }

    for path in changed_paths:
        lower = path.lower()
        if lower.endswith((".md", ".rst", ".txt")):
            buckets["docs"] += 1
        elif lower.endswith((".json", ".toml", ".yaml", ".yml", ".ini")):
            buckets["config"] += 1
        elif lower.endswith((".js", ".jsx", ".ts", ".tsx", ".css", ".scss", ".html", ".vue")):
            buckets["frontend"] += 1
        elif lower.endswith((".py", ".go", ".rs", ".java", ".rb", ".php", ".cs")):
            buckets["backend"] += 1
        else:
            buckets["other"] += 1

    non_zero = [f"{name}:{count}" for name, count in buckets.items() if count]
    category_breakdown = ", ".join(non_zero) if non_zero else "other:0"
    return f"{len(changed_paths)} files changed ({category_breakdown})."
