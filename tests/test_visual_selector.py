"""Visual selector relevance and conservative behavior tests."""

from __future__ import annotations

from hackluminary.visual_selector import attach_visuals_to_slides, score_media_for_slide


SLIDES = [
    {
        "id": "problem",
        "type": "content",
        "title": "Problem",
        "content": "Teams struggle to explain the UI flow in demos.",
        "evidence_refs": ["doc.problem"],
    },
    {
        "id": "demo",
        "type": "list",
        "title": "Demo",
        "list_items": ["Live UI walkthrough", "Feature validation"],
        "evidence_refs": ["doc.features"],
    },
]

MEDIA = [
    {
        "id": "media.a",
        "source_path": "assets/ui-screenshot.png",
        "kind": "repo_image",
        "mime": "image/png",
        "width": 800,
        "height": 450,
        "sha256": "a" * 64,
        "tags": ["ui", "screenshot", "demo"],
        "evidence_refs": ["doc.features"],
        "alt": "UI screenshot",
    },
    {
        "id": "media.b",
        "source_path": "assets/architecture.png",
        "kind": "doc_image",
        "mime": "image/png",
        "width": 1000,
        "height": 700,
        "sha256": "b" * 64,
        "tags": ["architecture", "diagram", "system"],
        "evidence_refs": ["doc.solution"],
        "alt": "Architecture diagram",
    },
]


def test_visual_selector_attaches_max_one_visual_in_conservative_mode():
    updated, summary = attach_visuals_to_slides(
        slides=SLIDES,
        media_catalog=MEDIA,
        mode="auto",
        max_images_per_slide=1,
        min_confidence=0.1,
        visual_style="mixed",
    )

    assert summary["eligible_slides"] == 2
    assert all(len(slide.get("visuals", [])) <= 1 for slide in updated)


def test_visual_selector_respects_confidence_threshold():
    updated, _ = attach_visuals_to_slides(
        slides=SLIDES,
        media_catalog=MEDIA,
        mode="auto",
        max_images_per_slide=1,
        min_confidence=0.95,
        visual_style="mixed",
    )

    assert all(not slide.get("visuals") for slide in updated)


def test_scoring_prefers_demo_screenshot_for_demo_slide():
    score_ui = score_media_for_slide(SLIDES[1], MEDIA[0], visual_style="screenshot")
    score_arch = score_media_for_slide(SLIDES[1], MEDIA[1], visual_style="screenshot")
    assert score_ui > score_arch
