"""Evidence normalization layer for claim traceability."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def build_evidence(
    code_analysis: dict,
    doc_data: dict,
    git_context: dict,
    project_path: Path | None = None,
    media_catalog: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Build evidence records with schema v2.1 enrichment fields.

    The function keeps backward compatibility by preserving `id`, `type`, `title`,
    and `value` while adding richer source metadata.
    """

    project_root = Path(project_path).resolve() if project_path else None
    evidence: list[dict[str, Any]] = []

    readme_path = _find_readme(project_root) if project_root else None
    readme_text = ""
    if readme_path and readme_path.exists():
        readme_text = readme_path.read_text(encoding="utf-8", errors="ignore")

    def add(
        item_id: str,
        item_type: str,
        title: str,
        value: Any,
        source_kind: str,
        source_path: str = "",
        source_text: str = "",
    ) -> None:
        if value in (None, "", [], {}):
            return

        snippet = _value_to_snippet(value)
        start_line, end_line = _line_span(source_text, snippet)

        entry = {
            "id": item_id,
            "type": item_type,
            "title": title,
            "value": value,
            "source_path": source_path,
            "source_kind": source_kind,
            "start_line": start_line,
            "end_line": end_line,
            "snippet": snippet,
            "snippet_hash": hashlib.sha1(snippet.encode("utf-8")).hexdigest(),
        }
        evidence.append(entry)

    add(
        "repo.project",
        "repo",
        "Project Name",
        code_analysis.get("project_name"),
        source_kind="code",
        source_path="",
        source_text="",
    )
    add("repo.files", "repo", "Source File Count", code_analysis.get("file_count"), "code")
    add("repo.lines", "repo", "Total Source Lines", code_analysis.get("total_lines"), "code")
    add("repo.languages", "repo", "Languages", code_analysis.get("languages"), "code")
    add("repo.frameworks", "repo", "Frameworks", code_analysis.get("frameworks"), "code")
    add("repo.dependencies", "repo", "Dependencies", code_analysis.get("dependencies"), "code")
    add("repo.features", "repo", "Detected Features", code_analysis.get("features"), "code")

    readme_rel = _rel_path(readme_path, project_root)

    add(
        "doc.title",
        "documentation",
        "README Title",
        doc_data.get("title"),
        source_kind="readme",
        source_path=readme_rel,
        source_text=readme_text,
    )
    add(
        "doc.description",
        "documentation",
        "Project Description",
        doc_data.get("description"),
        source_kind="readme",
        source_path=readme_rel,
        source_text=readme_text,
    )
    add(
        "doc.problem",
        "documentation",
        "Problem Statement",
        doc_data.get("problem"),
        source_kind="readme",
        source_path=readme_rel,
        source_text=readme_text,
    )
    add(
        "doc.solution",
        "documentation",
        "Solution Statement",
        doc_data.get("solution"),
        source_kind="readme",
        source_path=readme_rel,
        source_text=readme_text,
    )
    add(
        "doc.features",
        "documentation",
        "Documented Features",
        doc_data.get("features"),
        source_kind="readme",
        source_path=readme_rel,
        source_text=readme_text,
    )

    # Add representative code snippets from key files for Studio citation cards.
    if project_root:
        for idx, relative in enumerate(code_analysis.get("key_files", [])[:3], start=1):
            code_path = (project_root / relative).resolve()
            if not code_path.exists() or not code_path.is_file():
                continue
            text = code_path.read_text(encoding="utf-8", errors="ignore")
            lines = text.splitlines()
            snippet = "\n".join(lines[: min(12, len(lines))]).strip()
            if not snippet:
                continue
            add(
                f"code.key.{idx}",
                "code",
                f"Key File Snippet: {relative}",
                snippet,
                source_kind="code",
                source_path=relative,
                source_text=text,
            )

    add("git.branch", "git", "Current Branch", git_context.get("branch"), "git", source_path=".git")
    add("git.base_branch", "git", "Base Branch", git_context.get("base_branch"), "git", source_path=".git")
    add("git.head_sha", "git", "Head Commit", git_context.get("head_sha"), "git", source_path=".git")
    add("git.base_sha", "git", "Base Commit", git_context.get("base_sha"), "git", source_path=".git")
    add(
        "git.changed_files",
        "git",
        "Changed Files",
        git_context.get("top_changed_paths"),
        "git",
        source_path=".git",
    )
    add(
        "git.change_summary",
        "git",
        "Change Summary",
        git_context.get("change_summary"),
        "git",
        source_path=".git",
    )

    for media in media_catalog or []:
        source_path = str(media.get("source_path", "")).strip()
        media_id = str(media.get("id", "")).strip()
        sha = str(media.get("sha256", "")).strip()
        if not source_path or not media_id:
            continue

        title = source_path.rsplit("/", 1)[-1]
        add(
            f"media.{sha[:12] or media_id}",
            "image",
            f"Image Asset: {title}",
            {
                "source_path": source_path,
                "sha256": sha,
                "width": media.get("width"),
                "height": media.get("height"),
                "tags": media.get("tags", []),
            },
            source_kind=str(media.get("kind", "repo_image")),
            source_path=source_path,
            source_text=str(media.get("alt", "")),
        )

    return evidence


def evidence_index(evidence: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {entry["id"]: entry for entry in evidence}


def _value_to_snippet(value: Any, limit: int = 320) -> str:
    if isinstance(value, str):
        text = value.strip()
    elif isinstance(value, (list, tuple)):
        text = "\n".join(str(item) for item in value)
    elif isinstance(value, dict):
        text = json.dumps(value, indent=2, ensure_ascii=False)
    else:
        text = str(value)
    return text[:limit]


def _line_span(source_text: str, snippet: str) -> tuple[int | None, int | None]:
    if not source_text or not snippet:
        return (None, None)

    clean_snippet = snippet.strip()
    if not clean_snippet:
        return (None, None)

    idx = source_text.find(clean_snippet)
    if idx < 0:
        return (None, None)

    start_line = source_text.count("\n", 0, idx) + 1
    end_line = start_line + clean_snippet.count("\n")
    return (start_line, end_line)


def _find_readme(project_root: Path | None) -> Path | None:
    if not project_root:
        return None
    for name in ["README.md", "readme.md", "README.txt", "README"]:
        path = project_root / name
        if path.exists() and path.is_file():
            return path
    return None


def _rel_path(path: Path | None, root: Path | None) -> str:
    if not path or not root:
        return ""
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)
