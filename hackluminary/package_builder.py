"""Bundle manifests and hackathon package artifacts."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path
from typing import Iterable


def build_manifest_payload(
    artifact_paths: Iterable[Path],
    payload: dict,
) -> dict:
    artifacts = []
    for path in artifact_paths:
        file_path = Path(path)
        if not file_path.exists() or not file_path.is_file():
            continue
        artifacts.append(
            {
                "path": file_path.name,
                "bytes": file_path.stat().st_size,
                "sha256": _sha256(file_path),
            }
        )

    artifacts.sort(key=lambda item: item["path"].lower())

    return {
        "schema_version": "2.2",
        "payload_schema_version": payload.get("schema_version", "2.2"),
        "slide_count": len(payload.get("slides", [])),
        "evidence_count": len(payload.get("evidence", [])),
        "media_count": len(payload.get("media_catalog", [])),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }


def write_manifest(bundle_dir: Path, artifact_paths: Iterable[Path], payload: dict) -> Path:
    manifest = build_manifest_payload(artifact_paths, payload)
    target = Path(bundle_dir).resolve() / "manifest.json"
    target.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return target


def build_devpost_package(
    project_root: Path,
    output_zip: Path,
    payload: dict,
    artifact_paths: Iterable[Path],
) -> Path:
    root = Path(project_root).resolve()
    target = Path(output_zip).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    artifacts = [Path(path).resolve() for path in artifact_paths if Path(path).exists()]
    media_candidates = _top_media_files(payload.get("media_catalog", []), root, limit=4)

    with zipfile.ZipFile(target, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in artifacts:
            archive.write(file_path, arcname=file_path.name)

        for media_path in media_candidates:
            archive.write(media_path, arcname=f"screenshots/{media_path.name}")

        archive.writestr("project-summary.md", _devpost_summary(payload))

    return target


def _top_media_files(media_catalog: list[dict], project_root: Path, limit: int = 4) -> list[Path]:
    ranked: list[tuple[int, str, Path]] = []

    for media in media_catalog:
        source = str(media.get("source_path", "")).strip()
        if not source:
            continue
        candidate = (project_root / source).resolve()
        try:
            candidate.relative_to(project_root)
        except ValueError:
            continue
        if not candidate.exists() or not candidate.is_file():
            continue

        tags = set(str(tag).lower() for tag in media.get("tags", []))
        score = 0
        if {"screenshot", "screen", "demo", "ui", "interface"} & tags:
            score += 3
        if str(media.get("kind", "")) == "doc_image":
            score += 1
        score += 1 if media.get("width") and media.get("height") else 0

        ranked.append((score, source.lower(), candidate))

    ranked.sort(key=lambda item: (-item[0], item[1]))

    seen: set[Path] = set()
    selected: list[Path] = []
    for _, _, path in ranked:
        if path in seen:
            continue
        seen.add(path)
        selected.append(path)
        if len(selected) >= limit:
            break

    return selected


def _devpost_summary(payload: dict) -> str:
    metadata = payload.get("metadata", {})
    project = metadata.get("project", "HackLuminary Project")

    first_problem = ""
    first_solution = ""
    for slide in payload.get("slides", []):
        sid = str(slide.get("id", ""))
        if sid == "problem" and not first_problem:
            first_problem = str(slide.get("content", "") or " ".join(slide.get("list_items", [])[:2])).strip()
        if sid == "solution" and not first_solution:
            first_solution = str(slide.get("content", "") or " ".join(slide.get("list_items", [])[:2])).strip()

    languages = metadata.get("languages", {})
    lang_line = ", ".join(f"{k} ({v})" for k, v in list(languages.items())[:5])

    lines = [
        f"# {project}",
        "",
        "## Problem",
        first_problem or "Problem statement derived from repository evidence.",
        "",
        "## Solution",
        first_solution or "Solution summary derived from repository evidence.",
        "",
        "## Tech",
        lang_line or "See deck for technical details.",
        "",
        "## What is Included",
        "- Presentation deck",
        "- Speaker notes",
        "- Talk track",
        "- Screenshots",
        "",
    ]
    return "\n".join(lines)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(1024 * 256)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()
