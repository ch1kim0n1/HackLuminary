"""Evidence enrichment tests for schema 2.1."""

from hackluminary.pipeline import run_generation


def test_evidence_includes_snippets_and_line_context(tmp_path):
    (tmp_path / "README.md").write_text(
        """
# Demo

## Problem
Teams struggle with demo preparation.

## Solution
Automate evidence-linked storytelling.
""".strip(),
        encoding="utf-8",
    )
    (tmp_path / "main.py").write_text("def run():\n    return 'ok'\n", encoding="utf-8")

    result = run_generation(
        project_dir=tmp_path,
        cli_overrides={"general": {"mode": "deterministic", "format": "json"}},
    )

    payload = result["payload"]
    assert payload["schema_version"] == "2.1"

    evidence = payload["evidence"]
    assert evidence

    first = evidence[0]
    for key in ["source_path", "source_kind", "start_line", "end_line", "snippet", "snippet_hash"]:
        assert key in first

    # At least one README-derived evidence item should carry line context.
    readme_items = [item for item in evidence if item.get("source_kind") == "readme"]
    assert readme_items
    assert any(item.get("start_line") is not None for item in readme_items)
