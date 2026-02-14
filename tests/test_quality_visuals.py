"""Visual quality metrics and strict mode checks."""

from __future__ import annotations

from hackluminary.quality import evaluate_quality


def _slide(slide_id: str, with_visual: bool, confidence: float = 0.9):
    slide = {
        "id": slide_id,
        "type": "content",
        "title": slide_id.title(),
        "content": "Evidence-backed point",
        "evidence_refs": ["doc.problem"],
    }
    if with_visual:
        slide["visuals"] = [
            {
                "id": f"media.{slide_id}",
                "type": "image",
                "source_path": f"assets/{slide_id}.png",
                "alt": f"{slide_id} image",
                "caption": "caption",
                "confidence": confidence,
            }
        ]
    else:
        slide["visuals"] = []
    return slide


def test_quality_reports_visual_metrics():
    slides = [_slide("problem", True), _slide("solution", False)]
    report = evaluate_quality(slides, image_mode="auto", min_visual_confidence=0.72)

    assert report["metrics"]["image_coverage"] == 0.5
    assert "solution" in report["metrics"]["slides_without_visual"]
    assert report["metrics"]["visual_confidence_mean"] == 0.9


def test_strict_mode_fails_low_coverage():
    slides = [_slide("problem", True), _slide("solution", False), _slide("demo", False)]
    report = evaluate_quality(slides, image_mode="strict", min_visual_confidence=0.72)

    assert report["status"] == "fail"
    assert any("Image coverage" in err for err in report["errors"])


def test_strict_mode_flags_missing_alt_text():
    slide = _slide("demo", True)
    slide["visuals"][0]["alt"] = ""
    report = evaluate_quality([slide], image_mode="strict", min_visual_confidence=0.72)

    assert report["status"] == "fail"
    assert any("missing alt" in err.lower() for err in report["errors"])
