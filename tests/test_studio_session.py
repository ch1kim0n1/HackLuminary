"""Studio session persistence tests."""

import json

from hackluminary.studio_session import (
    default_session,
    get_studio_session_path,
    load_session,
    save_session,
)


def test_session_default_when_missing(tmp_path):
    session = load_session(tmp_path)
    assert session["studio_schema_version"] == "1.0"
    assert session["slide_order"] == []


def test_session_save_and_load(tmp_path):
    payload = default_session()
    payload["slide_order"] = ["title", "problem"]
    payload["note_blocks"] = {"title": "Opening note"}

    path = save_session(tmp_path, payload)
    assert path == get_studio_session_path(tmp_path)
    assert path.exists()

    loaded = load_session(tmp_path)
    assert loaded["slide_order"] == ["title", "problem"]
    assert loaded["note_blocks"]["title"] == "Opening note"

    # Ensure valid JSON persisted.
    parsed = json.loads(path.read_text(encoding="utf-8"))
    assert parsed["studio_schema_version"] == "1.0"
