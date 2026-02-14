"""Tests for generated auxiliary artifacts."""

from hackluminary.artifacts import build_notes_markdown, build_talk_track_markdown


def _slides():
    return [
        {
            "id": "title",
            "title": "Demo",
            "subtitle": "Evidence-grounded deck",
            "evidence_refs": ["doc.title"],
        },
        {
            "id": "problem",
            "title": "Problem",
            "content": "Teams waste time assembling slides manually.",
            "evidence_refs": ["doc.problem"],
            "notes": "Keep this short and concrete.",
        },
    ]


def test_build_notes_markdown_includes_refs():
    text = build_notes_markdown(_slides())
    assert "Speaker Notes" in text
    assert "Evidence refs: doc.problem" in text


def test_build_talk_track_contains_common_durations():
    text = build_talk_track_markdown(_slides())
    assert "30 Second Pitch" in text
    assert "60 Second Pitch" in text
    assert "3 Minute Pitch" in text
