"""Manifest and Devpost package tests."""

from __future__ import annotations

import json
import zipfile

from hackluminary.package_builder import build_devpost_package, write_manifest


def test_manifest_contains_hashes(tmp_path):
    html = tmp_path / "deck.html"
    notes = tmp_path / "notes.md"
    html.write_text("<html></html>", encoding="utf-8")
    notes.write_text("# Notes", encoding="utf-8")

    payload = {
        "schema_version": "2.2",
        "slides": [{"id": "title"}],
        "evidence": [{"id": "doc.title"}],
        "media_catalog": [],
    }
    manifest_path = write_manifest(tmp_path, [html, notes], payload)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "2.2"
    assert manifest["artifact_count"] == 2
    assert all(len(item["sha256"]) == 64 for item in manifest["artifacts"])


def test_devpost_package_contains_expected_files(tmp_path):
    (tmp_path / "README.md").write_text("# Demo", encoding="utf-8")
    deck = tmp_path / "deck.html"
    notes = tmp_path / "notes.md"
    deck.write_text("<html>deck</html>", encoding="utf-8")
    notes.write_text("notes", encoding="utf-8")

    payload = {
        "metadata": {"project": "Demo", "languages": {"Python": 3}},
        "slides": [
            {"id": "problem", "content": "Problem text"},
            {"id": "solution", "content": "Solution text"},
        ],
        "media_catalog": [],
    }

    zip_path = build_devpost_package(
        project_root=tmp_path,
        output_zip=tmp_path / "devpost.zip",
        payload=payload,
        artifact_paths=[deck, notes],
    )

    with zipfile.ZipFile(zip_path, "r") as archive:
        names = set(archive.namelist())

    assert "deck.html" in names
    assert "notes.md" in names
    assert "project-summary.md" in names
