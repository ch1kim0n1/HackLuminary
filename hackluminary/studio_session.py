"""Studio session persistence helpers."""

from __future__ import annotations

import json
from pathlib import Path

SESSION_SCHEMA_VERSION = "1.0"


def get_studio_session_path(project_path: Path | str) -> Path:
    root = Path(project_path).resolve()
    return root / ".hackluminary" / "studio" / "session.json"


def default_session() -> dict:
    return {
        "studio_schema_version": SESSION_SCHEMA_VERSION,
        "selected_slides": [],
        "slide_order": [],
        "draft_overrides": {},
        "note_blocks": {},
        "pinned_evidence": {},
        "presenter": {
            "timer_minutes": 7,
            "last_slide_index": 0,
        },
        "last_validation": {},
    }


def load_session(project_path: Path | str) -> dict:
    path = get_studio_session_path(project_path)
    if not path.exists():
        return default_session()

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default_session()

    return migrate_session(payload)


def save_session(project_path: Path | str, payload: dict) -> Path:
    path = get_studio_session_path(project_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    merged = default_session()
    merged.update({k: v for k, v in payload.items() if k in merged})
    merged["studio_schema_version"] = SESSION_SCHEMA_VERSION

    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    tmp.replace(path)
    return path


def migrate_session(payload: dict) -> dict:
    session = default_session()

    if isinstance(payload, dict):
        for key in session.keys():
            if key in payload:
                session[key] = payload[key]

    if not isinstance(session.get("draft_overrides"), dict):
        session["draft_overrides"] = {}
    if not isinstance(session.get("note_blocks"), dict):
        session["note_blocks"] = {}
    if not isinstance(session.get("pinned_evidence"), dict):
        session["pinned_evidence"] = {}
    if not isinstance(session.get("presenter"), dict):
        session["presenter"] = {"timer_minutes": 7, "last_slide_index": 0}

    session["studio_schema_version"] = SESSION_SCHEMA_VERSION
    return session
