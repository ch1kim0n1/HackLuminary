"""Corpus benchmark tests for image coverage tuning."""

from __future__ import annotations

import base64

from hackluminary.benchmark import benchmark_visual_coverage


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="
)


def _make_project(path, with_image):
    path.mkdir(parents=True, exist_ok=True)
    readme = "# Demo\n\n## Problem\nSlow demos\n\n## Solution\nFast decks\n"
    if with_image:
        (path / "assets").mkdir(exist_ok=True)
        (path / "assets" / "ui.png").write_bytes(PNG_1X1)
        readme += "\n![UI screenshot](assets/ui.png)\n"
    (path / "README.md").write_text(readme, encoding="utf-8")
    (path / "main.py").write_text("print('ok')\n", encoding="utf-8")


def test_benchmark_returns_recommendation(tmp_path):
    _make_project(tmp_path / "proj-a", with_image=True)
    _make_project(tmp_path / "proj-b", with_image=False)

    result = benchmark_visual_coverage(tmp_path, max_projects=5)

    assert result["project_count"] >= 2
    assert result["runs"]
    assert result["recommended_min_confidence"] is not None
