"""Deterministic slide construction."""

from __future__ import annotations

from typing import Callable


ALL_SLIDE_TYPES = [
    "title",
    "problem",
    "solution",
    "demo",
    "impact",
    "tech",
    "future",
    "delta",
    "closing",
]

PRIORITY_ORDER = [
    "title",
    "problem",
    "solution",
    "demo",
    "tech",
    "impact",
    "delta",
    "future",
    "closing",
]


def resolve_slide_types(
    requested: list[str] | None,
    max_slides: int | None,
    has_git_context: bool,
) -> list[str]:
    """Resolve slide type set while enforcing deterministic ordering."""

    if requested:
        requested_clean = [item.strip() for item in requested if item.strip()]
        selected = [item for item in requested_clean if item in ALL_SLIDE_TYPES]
    else:
        selected = [item for item in ALL_SLIDE_TYPES if has_git_context or item != "delta"]

    if not has_git_context and "delta" in selected:
        selected = [item for item in selected if item != "delta"]

    if max_slides and max_slides > 0 and max_slides < len(selected):
        priority_subset = [item for item in PRIORITY_ORDER if item in selected][:max_slides]
        selected = [item for item in ALL_SLIDE_TYPES if item in priority_subset]

    return selected


def build_deterministic_slides(
    code_analysis: dict,
    doc_data: dict,
    git_context: dict,
    evidence_ids: set[str],
    slide_types: list[str],
) -> list[dict]:
    """Build deterministic slides with explicit evidence references."""

    creators: dict[str, Callable[[], dict]] = {
        "title": lambda: _title_slide(code_analysis, doc_data, git_context, evidence_ids),
        "problem": lambda: _problem_slide(doc_data, evidence_ids),
        "solution": lambda: _solution_slide(code_analysis, doc_data, evidence_ids),
        "demo": lambda: _demo_slide(code_analysis, doc_data, evidence_ids),
        "impact": lambda: _impact_slide(doc_data, evidence_ids),
        "tech": lambda: _tech_slide(code_analysis, evidence_ids),
        "future": lambda: _future_slide(code_analysis, doc_data, evidence_ids),
        "delta": lambda: _delta_slide(git_context, evidence_ids),
        "closing": lambda: _closing_slide(code_analysis, doc_data, git_context, evidence_ids),
    }

    slides = [creators[slide_type]() for slide_type in slide_types if slide_type in creators]
    for slide in slides:
        slide.setdefault("id", slide["type"])
        slide.setdefault("evidence_refs", [])
        slide.setdefault("claims", _derive_claims(slide))
        slide.setdefault("notes", "")
    return slides


def _refs(candidates: list[str], evidence_ids: set[str]) -> list[str]:
    return [item for item in candidates if item in evidence_ids]


def _title_slide(code_analysis: dict, doc_data: dict, git_context: dict, evidence_ids: set[str]) -> dict:
    subtitle = doc_data.get("description") or "Hackathon-ready presentation generated from local project evidence."
    subtitle = subtitle.strip()[:220]

    if git_context.get("available") and git_context.get("branch"):
        subtitle = f"{subtitle} Current branch: {git_context['branch']}."

    evidence_refs = _refs(["doc.title", "doc.description", "git.branch"], evidence_ids)
    return {
        "id": "title",
        "type": "title",
        "title": doc_data.get("title") or code_analysis.get("project_name") or "Project",
        "subtitle": subtitle,
        "evidence_refs": evidence_refs,
        "claims": [_claim_from_text(subtitle, evidence_refs, confidence=0.93)],
    }


def _problem_slide(doc_data: dict, evidence_ids: set[str]) -> dict:
    content = doc_data.get("problem")
    if not content:
        content = (
            "Teams lose demo time because project context is scattered across code, docs, and commits. "
            "The goal is to turn repository evidence into a concise story quickly."
        )

    evidence_refs = _refs(["doc.problem", "doc.description", "repo.project"], evidence_ids)
    return {
        "id": "problem",
        "type": "content",
        "title": "The Problem",
        "content": content,
        "evidence_refs": evidence_refs,
        "claims": [_claim_from_text(content, evidence_refs, confidence=0.9)],
    }


def _solution_slide(code_analysis: dict, doc_data: dict, evidence_ids: set[str]) -> dict:
    solution = doc_data.get("solution")
    primary = code_analysis.get("primary_language") or "modern tooling"
    if not solution:
        solution = (
            "This workflow produces deterministic slides from repository facts and optional local AI refinement, "
            f"keeping outputs reproducible while adapting narrative quality for {primary} projects."
        )

    evidence_refs = _refs(["doc.solution", "repo.languages", "repo.frameworks", "repo.project"], evidence_ids)
    return {
        "id": "solution",
        "type": "content",
        "title": "Our Solution",
        "content": solution,
        "evidence_refs": evidence_refs,
        "claims": [_claim_from_text(solution, evidence_refs, confidence=0.9)],
    }


def _demo_slide(code_analysis: dict, doc_data: dict, evidence_ids: set[str]) -> dict:
    features = [item.strip() for item in doc_data.get("features", []) if item.strip()]
    detected = code_analysis.get("features", [])

    for item in detected:
        if item not in features:
            features.append(item)

    if not features:
        features = [
            "Deterministic parsing of project source and documentation",
            "Branch-aware context from local git history",
            "Offline-first rendering with no runtime CDN dependencies",
            "JSON schema output suitable for automation",
        ]

    evidence_refs = _refs(["doc.features", "repo.features", "repo.dependencies", "repo.project"], evidence_ids)
    claims = [_claim_from_text(item, evidence_refs, confidence=0.88) for item in features[:7]]
    return {
        "id": "demo",
        "type": "list",
        "title": "Key Features",
        "list_items": features[:7],
        "evidence_refs": evidence_refs,
        "claims": claims,
    }


def _impact_slide(doc_data: dict, evidence_ids: set[str]) -> dict:
    points = [item.strip() for item in doc_data.get("impact_points", []) if item.strip()]
    if not points:
        points = [
            "Cuts presentation prep time from hours to minutes",
            "Improves narrative consistency across team members",
            "Keeps technical claims traceable to repository evidence",
            "Works reliably in low-connectivity hackathon environments",
        ]

    evidence_refs = _refs(["doc.description", "repo.files", "repo.lines"], evidence_ids)
    claims = [_claim_from_text(item, evidence_refs, confidence=0.86) for item in points[:6]]
    return {
        "id": "impact",
        "type": "list",
        "title": "Impact & Benefits",
        "list_items": points[:6],
        "evidence_refs": evidence_refs,
        "claims": claims,
    }


def _tech_slide(code_analysis: dict, evidence_ids: set[str]) -> dict:
    langs = code_analysis.get("languages", {})
    frameworks = code_analysis.get("frameworks", [])
    deps = code_analysis.get("dependencies", [])

    items = []
    primary = code_analysis.get("primary_language", "Unknown")
    if primary and primary != "Unknown":
        items.append(f"Primary language: {primary}")
    if langs:
        lang_summary = ", ".join(f"{name} ({count})" for name, count in list(langs.items())[:5])
        items.append(f"Language distribution: {lang_summary}")
    if frameworks:
        items.append("Frameworks: " + ", ".join(frameworks[:6]))
    if deps:
        items.append("Dependencies: " + ", ".join(deps[:8]))

    files = code_analysis.get("file_count", 0)
    lines = code_analysis.get("total_lines", 0)
    items.append(f"Scale: {files} source files, {lines:,} lines")

    evidence_refs = _refs(["repo.languages", "repo.frameworks", "repo.dependencies", "repo.files", "repo.lines"], evidence_ids)
    claims = [_claim_from_text(item, evidence_refs, confidence=0.92) for item in items]
    return {
        "id": "tech",
        "type": "list",
        "title": "Technology Stack",
        "list_items": items,
        "evidence_refs": evidence_refs,
        "claims": claims,
    }


def _future_slide(code_analysis: dict, doc_data: dict, evidence_ids: set[str]) -> dict:
    items = [item.strip() for item in doc_data.get("future_items", []) if item.strip()]
    if not items:
        items = [
            "Add richer repository analysis for architecture-level insights",
            "Expand local model catalog and speed profiles for laptops",
            "Improve quality gates with domain-specific heuristics",
            "Ship stronger team templates for common hackathon judging tracks",
        ]

    if code_analysis.get("frameworks"):
        items.append("Harden framework-specific storytelling templates")

    evidence_refs = _refs(["repo.frameworks", "repo.features", "doc.solution", "repo.files"], evidence_ids)
    claims = [_claim_from_text(item, evidence_refs, confidence=0.8) for item in items[:6]]
    return {
        "id": "future",
        "type": "list",
        "title": "Future Plans",
        "list_items": items[:6],
        "evidence_refs": evidence_refs,
        "claims": claims,
    }


def _delta_slide(git_context: dict, evidence_ids: set[str]) -> dict:
    changed = git_context.get("changed_files_count", 0)
    branch = git_context.get("branch") or "unknown"
    base = git_context.get("base_branch") or "unknown"

    items = [
        f"Branch: {branch}",
        f"Base branch: {base}",
        git_context.get("change_summary") or "No change summary available.",
    ]

    top_paths = git_context.get("top_changed_paths", [])
    if top_paths:
        items.append("Top changed paths: " + ", ".join(top_paths[:5]))
    elif changed == 0:
        items.append("No changed files detected relative to base branch.")

    evidence_refs = _refs(
        ["git.branch", "git.base_branch", "git.changed_files", "git.change_summary"],
        evidence_ids,
    )

    claims = [_claim_from_text(item, evidence_refs, confidence=0.95) for item in items]
    return {
        "id": "delta",
        "type": "list",
        "title": "Branch Delta",
        "list_items": items,
        "evidence_refs": evidence_refs,
        "claims": claims,
    }


def _closing_slide(code_analysis: dict, doc_data: dict, git_context: dict, evidence_ids: set[str]) -> dict:
    language = code_analysis.get("primary_language", "software")
    branch = git_context.get("branch")
    subtitle = f"{doc_data.get('title', 'Project')} · Built with {language}"
    if branch:
        subtitle += f" · Branch {branch}"

    evidence_refs = _refs(["repo.languages", "git.branch", "doc.title"], evidence_ids)
    return {
        "id": "closing",
        "type": "closing",
        "title": "Thank You",
        "subtitle": subtitle,
        "evidence_refs": evidence_refs,
        "claims": [_claim_from_text(subtitle, evidence_refs, confidence=0.85)],
    }


def _claim_from_text(text: str, evidence_refs: list[str], confidence: float = 0.85) -> dict:
    return {
        "text": str(text).strip(),
        "evidence_refs": list(evidence_refs),
        "confidence": round(float(confidence), 2),
    }


def _derive_claims(slide: dict) -> list[dict]:
    refs = list(slide.get("evidence_refs", []))

    if slide.get("type") in {"content", "problem", "solution"}:
        content = slide.get("content") or ""
        return [_claim_from_text(content, refs, confidence=0.84)] if str(content).strip() else []

    if slide.get("type") in {"list", "tech", "delta", "demo", "impact", "future"}:
        claims = []
        for item in slide.get("list_items", [])[:8]:
            if str(item).strip():
                claims.append(_claim_from_text(str(item), refs, confidence=0.82))
        return claims

    subtitle = slide.get("subtitle") or ""
    return [_claim_from_text(subtitle, refs, confidence=0.8)] if str(subtitle).strip() else []
