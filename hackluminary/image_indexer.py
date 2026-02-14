"""Offline local image discovery and metadata indexing."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from .image_processor import inspect_image, normalize_allowed_extensions, safe_relative_path, to_data_uri

MARKDOWN_IMAGE_PATTERN = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


def index_project_images(
    project_root: Path,
    image_dirs: list[str] | None,
    allowed_extensions: list[str],
    max_image_bytes: int,
) -> dict:
    """Index local project images and markdown references."""

    root = Path(project_root).resolve()
    warnings: list[str] = []
    allowed = normalize_allowed_extensions(allowed_extensions)

    refs = _collect_markdown_image_refs(root)

    media_catalog: list[dict] = []
    seen_paths: set[str] = set()

    for path in _iter_image_candidates(root, image_dirs, allowed, warnings):
        try:
            rel = safe_relative_path(root, path)
        except ValueError:
            warnings.append(f"Skipped image outside project root: {path}")
            continue

        if rel in seen_paths:
            continue

        try:
            meta = inspect_image(path, root, allowed, max_image_bytes=max_image_bytes)
        except Exception as exc:
            warnings.append(f"Skipped image {rel}: {exc}")
            continue

        seen_paths.add(rel)

        ref_meta = refs.get(rel, {})
        alt_candidates = ref_meta.get("alts", [])
        alt_text = str(alt_candidates[0]).strip() if alt_candidates else ""

        tags = _collect_tags(rel, alt_candidates)
        media_id = f"media.{meta['sha256'][:16]}"

        entry = {
            "id": media_id,
            "source_path": rel,
            "kind": "doc_image" if rel in refs else "repo_image",
            "mime": meta["mime"],
            "width": meta.get("width"),
            "height": meta.get("height"),
            "sha256": meta["sha256"],
            "tags": tags,
            "evidence_refs": ["doc.features", "doc.solution"] if rel in refs else ["repo.features"],
            "alt": alt_text,
        }

        # Keep Studio thumbnails responsive without shipping a separate file server route.
        if meta.get("bytes", 0) <= 450_000:
            try:
                entry["preview_data_uri"] = to_data_uri(path, meta["mime"])
            except Exception:
                pass

        media_catalog.append(entry)

    media_catalog.sort(key=lambda item: item["source_path"].lower())

    by_kind = {
        "repo_image": sum(1 for item in media_catalog if item.get("kind") == "repo_image"),
        "doc_image": sum(1 for item in media_catalog if item.get("kind") == "doc_image"),
        "generated_screenshot": sum(1 for item in media_catalog if item.get("kind") == "generated_screenshot"),
    }

    return {
        "media_catalog": media_catalog,
        "warnings": warnings,
        "summary": {
            "count": len(media_catalog),
            "by_kind": by_kind,
            "configured_image_dirs": list(image_dirs or []),
        },
    }


def _iter_image_candidates(root: Path, image_dirs: list[str] | None, allowed: set[str], warnings: list[str]) -> Iterable[Path]:
    requested = ["."]
    if image_dirs:
        requested.extend(image_dirs)

    seen_roots: set[Path] = set()

    for raw in requested:
        candidate = Path(raw)
        directory = (root / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()

        try:
            directory.relative_to(root)
        except ValueError:
            warnings.append(f"Skipped image dir outside project root: {raw}")
            continue

        if not directory.exists() or not directory.is_dir():
            warnings.append(f"Image dir not found: {raw}")
            continue

        if directory in seen_roots:
            continue
        seen_roots.add(directory)

        for path in sorted(directory.rglob("*"), key=lambda item: str(item).lower()):
            if not path.is_file():
                continue
            if any(part.startswith(".") and part not in {".", ".."} for part in path.parts if part not in {str(root)}):
                # Ignore hidden files/directories for deterministic behavior.
                continue
            if path.suffix.lower() in allowed:
                yield path


def _collect_markdown_image_refs(root: Path) -> dict[str, dict]:
    refs: dict[str, dict] = {}
    for doc in sorted(root.rglob("*.md"), key=lambda item: str(item).lower()):
        if not doc.is_file():
            continue
        if ".git" in doc.parts:
            continue

        text = doc.read_text(encoding="utf-8", errors="ignore")
        for match in MARKDOWN_IMAGE_PATTERN.finditer(text):
            alt = match.group(1).strip()
            raw_target = match.group(2).strip().split()[0]

            if raw_target.startswith("http://") or raw_target.startswith("https://"):
                continue
            if raw_target.startswith("data:"):
                continue

            target = (doc.parent / raw_target).resolve()
            try:
                rel = safe_relative_path(root, target)
            except ValueError:
                continue

            entry = refs.setdefault(rel, {"alts": []})
            if alt:
                entry["alts"].append(alt)

    return refs


def _collect_tags(source_path: str, alts: list[str]) -> list[str]:
    raw_parts = [source_path]
    raw_parts.extend(alts)

    tokens: list[str] = []
    for chunk in raw_parts:
        for token in re.split(r"[^a-zA-Z0-9]+", chunk.lower()):
            if len(token) < 2:
                continue
            tokens.append(token)

    unique: list[str] = []
    seen = set()
    for token in tokens:
        if token in seen:
            continue
        seen.add(token)
        unique.append(token)

    return unique[:24]
