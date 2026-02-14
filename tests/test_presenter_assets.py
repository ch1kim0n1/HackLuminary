"""Static presenter asset sanity tests."""

from pathlib import Path


def test_presenter_js_has_timer_controls():
    path = Path("hackluminary/studio/presenter.js")
    text = path.read_text(encoding="utf-8")

    assert "startTimer" in text
    assert "pauseTimer" in text
    assert "resetTimer" in text
    assert "setTargetMinutes" in text
    assert "setTitles" in text


def test_studio_js_has_quality_fix_controls():
    path = Path("hackluminary/studio/studio.js")
    text = path.read_text(encoding="utf-8")

    assert "autoFixIssues" in text
    assert "fixAllBtn" in text
