"""Tests for documentation parsing and safety behavior."""

from pathlib import Path

from hackluminary.document_parser import DocumentParser


def test_parser_extracts_key_sections(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text(
        """
# Sample App

A local-first app.

## Problem
Hackathon teams run out of time preparing decks.

## Solution
Generate evidence-linked slides from the repo.

## Features
- Offline runtime
- Branch context
- JSON output

## Impact
- Faster prep
- Better consistency
""".strip(),
        encoding="utf-8",
    )

    parsed = DocumentParser(tmp_path).parse()

    assert parsed["title"] == "Sample App"
    assert "Hackathon teams" in parsed["problem"]
    assert "Generate evidence-linked" in parsed["solution"]
    assert "Offline runtime" in parsed["features"]
    assert parsed["impact_points"]


def test_parser_skips_additional_docs_outside_project(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text("# Demo\n", encoding="utf-8")

    outside = Path(tmp_path.parent) / "outside.md"
    outside.write_text("secret", encoding="utf-8")

    parser = DocumentParser(tmp_path, additional_docs=[str(outside)])
    parsed = parser.parse()

    assert any("outside project" in warning for warning in parsed["warnings"])


def test_parser_fallback_when_readme_missing(tmp_path):
    parsed = DocumentParser(tmp_path).parse()

    assert parsed["title"] == tmp_path.name
    assert any("README file not found" in warning for warning in parsed["warnings"])
