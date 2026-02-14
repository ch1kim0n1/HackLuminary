"""Quality and pipeline behavior tests."""

from hackluminary.pipeline import run_generation
from hackluminary.quality import evaluate_quality


def test_quality_gate_flags_banned_phrase():
    slides = [
        {
            "id": "problem",
            "type": "content",
            "title": "Problem",
            "content": "This is a revolutionary system.",
            "evidence_refs": ["doc.problem"],
        }
    ]

    report = evaluate_quality(slides)

    assert report["status"] == "fail"
    assert any("banned phrase" in err for err in report["errors"])


def test_pipeline_deterministic_generation_without_git(tmp_path):
    (tmp_path / "README.md").write_text(
        """
# Demo

## Problem
Manual decks take too long.

## Solution
Use local automation.

## Features
- Deterministic slides
""".strip(),
        encoding="utf-8",
    )
    (tmp_path / "main.py").write_text("print('ok')\n", encoding="utf-8")

    result = run_generation(
        project_dir=tmp_path,
        cli_overrides={"general": {"mode": "deterministic", "format": "json"}},
    )

    payload = result["payload"]
    slide_ids = [slide["id"] for slide in payload["slides"]]
    evidence_ids = {entry["id"] for entry in payload["evidence"]}

    assert payload["schema_version"] == "2.1"
    assert "delta" not in slide_ids
    assert payload["quality_report"]["status"] == "pass"
    assert all("claims" in slide for slide in payload["slides"])
    for slide in payload["slides"]:
        for claim in slide.get("claims", []):
            for ref in claim.get("evidence_refs", []):
                assert ref in evidence_ids


def test_pipeline_respects_slide_filter(tmp_path):
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / "main.py").write_text("print('ok')\n", encoding="utf-8")

    result = run_generation(
        project_dir=tmp_path,
        requested_slide_types=["title", "tech", "closing"],
        cli_overrides={"general": {"mode": "deterministic", "format": "json"}},
    )

    slide_ids = [slide["id"] for slide in result["payload"]["slides"]]
    assert slide_ids == ["title", "tech", "closing"]
