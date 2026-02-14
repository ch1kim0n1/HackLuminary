"""Conservative visual selection for slide enrichment."""

from __future__ import annotations

import math
import re
from copy import deepcopy


def attach_visuals_to_slides(
    slides: list[dict],
    media_catalog: list[dict],
    mode: str = "auto",
    max_images_per_slide: int = 1,
    min_confidence: float = 0.72,
    visual_style: str = "mixed",
) -> tuple[list[dict], dict]:
    """Attach at most N relevant visuals per slide using deterministic scoring."""

    normalized_mode = str(mode or "off").lower()
    max_images = max(0, min(int(max_images_per_slide or 1), 2))

    copied = [deepcopy(slide) for slide in slides]
    for slide in copied:
        slide.setdefault("visuals", [])

    if normalized_mode == "off" or max_images == 0:
        return copied, {"attached": 0, "eligible_slides": 0}

    if not media_catalog:
        for slide in copied:
            slide["visuals"] = []
        return copied, {"attached": 0, "eligible_slides": _eligible_slide_count(copied)}

    attached = 0

    for slide in copied:
        if not _is_visual_eligible_slide(slide):
            slide["visuals"] = []
            continue

        scores = []
        for media in media_catalog:
            score = score_media_for_slide(slide, media, visual_style=visual_style)
            scores.append((score, media))

        scores.sort(key=lambda item: (-item[0], item[1].get("id", "")))

        chosen: list[dict] = []
        for score, media in scores:
            if score < min_confidence:
                continue
            chosen.append(_to_slide_visual(slide, media, score))
            if len(chosen) >= max_images:
                break

        # If strict mode is active and unique allocation prevented selection,
        # allow reuse of the best high-confidence visual.
        if not chosen and normalized_mode == "strict":
            for score, media in scores:
                if score >= min_confidence:
                    chosen.append(_to_slide_visual(slide, media, score))
                    break

        slide["visuals"] = chosen
        attached += len(chosen)

    return copied, {
        "attached": attached,
        "eligible_slides": _eligible_slide_count(copied),
    }


def score_media_for_slide(slide: dict, media: dict, visual_style: str = "mixed") -> float:
    slide_tokens = _slide_tokens(slide)
    media_tokens = set(str(token).lower() for token in media.get("tags", []) if str(token).strip())

    if not slide_tokens or not media_tokens:
        base = 0.0
    else:
        overlap = len(slide_tokens & media_tokens)
        norm = max(1.0, math.sqrt(len(slide_tokens) * len(media_tokens)))
        base = overlap / norm

    refs = set(str(ref) for ref in slide.get("evidence_refs", []) if str(ref).strip())
    media_refs = set(str(ref) for ref in media.get("evidence_refs", []) if str(ref).strip())
    if refs and media_refs and refs & media_refs:
        base += 0.45

    kind = str(media.get("kind", "repo_image"))
    style = str(visual_style or "mixed").lower()

    if style == "evidence" and kind == "doc_image":
        base += 0.2
    elif style == "screenshot" and kind == "repo_image":
        base += 0.2
    elif style == "mixed":
        base += 0.08

    if kind == "doc_image" and any(ref.startswith("doc.") for ref in refs):
        base += 0.22

    title = str(slide.get("title", "")).lower()
    slide_id = str(slide.get("id", "")).lower()
    if ("demo" in title or slide_id == "demo") and _looks_like_demo_image(media):
        base += 0.2
    if "tech" in title and _looks_like_architecture_image(media):
        base += 0.2
    if "impact" in title and _looks_like_chart_image(media):
        base += 0.2

    return round(min(1.0, max(0.0, base)), 3)


def _to_slide_visual(slide: dict, media: dict, confidence: float) -> dict:
    source_path = str(media.get("source_path", ""))
    alt = str(media.get("alt", "")).strip()
    if not alt:
        alt = f"Visual for {str(slide.get('title', 'slide')).strip() or 'slide'}"

    caption = alt
    if caption == alt and source_path:
        stem = source_path.rsplit("/", 1)[-1].rsplit(".", 1)[0].replace("-", " ").replace("_", " ")
        if stem and stem.lower() != alt.lower():
            caption = f"{alt} ({stem})"

    refs = list(slide.get("evidence_refs", []))[:3]
    return {
        "id": str(media.get("id", "")),
        "type": "image",
        "source_path": source_path,
        "alt": alt,
        "caption": caption[:160],
        "evidence_refs": refs,
        "confidence": confidence,
        "width": media.get("width"),
        "height": media.get("height"),
        "sha256": media.get("sha256"),
    }


def _slide_tokens(slide: dict) -> set[str]:
    parts: list[str] = []
    for key in ["title", "subtitle", "content"]:
        value = slide.get(key)
        if value:
            parts.append(str(value))

    items = slide.get("list_items", [])
    if isinstance(items, list):
        parts.extend(str(item) for item in items)

    claims = slide.get("claims", [])
    if isinstance(claims, list):
        parts.extend(str(claim.get("text", "")) for claim in claims if isinstance(claim, dict))

    refs = slide.get("evidence_refs", [])
    if isinstance(refs, list):
        parts.extend(str(ref) for ref in refs)

    tokens: set[str] = set()
    for chunk in parts:
        for token in re.split(r"[^a-zA-Z0-9]+", chunk.lower()):
            if len(token) < 3:
                continue
            tokens.add(token)

    return tokens


def _looks_like_demo_image(media: dict) -> bool:
    tags = set(str(tag).lower() for tag in media.get("tags", []))
    markers = {"demo", "screenshot", "screen", "ui", "interface", "app"}
    return bool(tags & markers)


def _looks_like_architecture_image(media: dict) -> bool:
    tags = set(str(tag).lower() for tag in media.get("tags", []))
    markers = {"arch", "architecture", "diagram", "flow", "system", "design"}
    return bool(tags & markers)


def _looks_like_chart_image(media: dict) -> bool:
    tags = set(str(tag).lower() for tag in media.get("tags", []))
    markers = {"chart", "graph", "metrics", "impact", "results", "stats"}
    return bool(tags & markers)


def _is_visual_eligible_slide(slide: dict) -> bool:
    slide_type = str(slide.get("type", "")).lower()
    if slide_type in {"title", "closing"}:
        return False
    return True


def _eligible_slide_count(slides: list[dict]) -> int:
    return sum(1 for slide in slides if _is_visual_eligible_slide(slide))
