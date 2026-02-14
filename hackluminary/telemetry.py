"""Opt-in local telemetry support."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path


def is_telemetry_enabled(config: dict) -> bool:
    telemetry = config.get("telemetry", {})
    return bool(telemetry.get("enabled", False))


def write_telemetry_event(project_root: Path, config: dict, event: str, payload: dict | None = None) -> Path | None:
    telemetry = config.get("telemetry", {})
    if not bool(telemetry.get("enabled", False)):
        return None

    root = Path(project_root).resolve()
    metrics_dir = root / ".hackluminary" / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    target = metrics_dir / "events.jsonl"

    data = {
        "event": str(event),
        "ts": int(time.time()),
        "anonymous": bool(telemetry.get("anonymous", True)),
    }

    safe_payload = _sanitize_payload(payload or {})
    if safe_payload:
        data["payload"] = safe_payload

    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, ensure_ascii=True) + "\n")

    return target


def duration_bucket(seconds: float) -> str:
    value = max(0.0, float(seconds))
    if value < 10:
        return "lt10s"
    if value < 30:
        return "10-30s"
    if value < 60:
        return "30-60s"
    if value < 120:
        return "60-120s"
    return "gte120s"


def enable_telemetry_in_project_config(project_root: Path, endpoint: str) -> Path:
    return _upsert_telemetry_section(project_root, enabled=True, endpoint=endpoint, anonymous=True)


def disable_telemetry_in_project_config(project_root: Path) -> Path:
    return _upsert_telemetry_section(project_root, enabled=False, endpoint="", anonymous=True)


def telemetry_status(project_root: Path, config: dict) -> dict:
    root = Path(project_root).resolve()
    telemetry = config.get("telemetry", {})
    events_path = _events_path(root)
    queued = 0
    if events_path.exists():
        queued = sum(1 for line in events_path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip())
    return {
        "enabled": bool(telemetry.get("enabled", False)),
        "anonymous": bool(telemetry.get("anonymous", True)),
        "endpoint": str(telemetry.get("endpoint", "")),
        "events_file": str(events_path),
        "queued_events": queued,
    }


def flush_telemetry_events(
    project_root: Path,
    config: dict,
    max_events: int = 200,
    timeout_sec: float = 4.0,
    dry_run: bool = False,
) -> dict:
    root = Path(project_root).resolve()
    telemetry = config.get("telemetry", {})
    endpoint = str(telemetry.get("endpoint", "")).strip()
    enabled = bool(telemetry.get("enabled", False))

    if not enabled:
        return {"status": "disabled", "sent": 0, "remaining": 0, "endpoint": endpoint}
    if not endpoint:
        return {"status": "no-endpoint", "sent": 0, "remaining": _queued_count(root), "endpoint": endpoint}

    events_path = _events_path(root)
    if not events_path.exists():
        return {"status": "empty", "sent": 0, "remaining": 0, "endpoint": endpoint}

    raw_lines = [line for line in events_path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip()]
    if not raw_lines:
        return {"status": "empty", "sent": 0, "remaining": 0, "endpoint": endpoint}

    limit = max(1, int(max_events))
    send_lines = raw_lines[:limit]
    remaining_lines = raw_lines[limit:]

    events = []
    dropped = 0
    for raw in send_lines:
        try:
            item = json.loads(raw)
        except json.JSONDecodeError:
            dropped += 1
            continue
        if isinstance(item, dict):
            events.append(item)
        else:
            dropped += 1

    if dry_run:
        return {
            "status": "dry-run",
            "sent": 0,
            "would_send": len(events),
            "dropped": dropped,
            "remaining": len(remaining_lines) + len(events) + dropped,
            "endpoint": endpoint,
        }

    if not events:
        events_path.write_text("\n".join(remaining_lines) + ("\n" if remaining_lines else ""), encoding="utf-8")
        return {"status": "empty-batch", "sent": 0, "remaining": len(remaining_lines), "dropped": dropped, "endpoint": endpoint}

    body = json.dumps(
        {
            "events": events,
            "client": "hackluminary",
            "sent_at": int(time.time()),
            "anonymous": bool(telemetry.get("anonymous", True)),
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": "hackluminary/2.2",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=float(timeout_sec)) as resp:
            code = int(resp.getcode())
        if code < 200 or code >= 300:
            return {
                "status": "http-error",
                "sent": 0,
                "remaining": len(raw_lines),
                "endpoint": endpoint,
                "http_status": code,
            }
    except urllib.error.URLError as exc:
        return {
            "status": "network-error",
            "sent": 0,
            "remaining": len(raw_lines),
            "endpoint": endpoint,
            "error": str(exc),
        }

    events_path.write_text("\n".join(remaining_lines) + ("\n" if remaining_lines else ""), encoding="utf-8")
    return {
        "status": "ok",
        "sent": len(events),
        "dropped": dropped,
        "remaining": len(remaining_lines),
        "endpoint": endpoint,
    }


def _upsert_telemetry_section(project_root: Path, enabled: bool, endpoint: str, anonymous: bool) -> Path:
    path = Path(project_root).resolve() / "hackluminary.toml"
    endpoint_escaped = str(endpoint).replace("\\", "\\\\").replace('"', '\\"')

    section_lines = [
        "[telemetry]",
        f"enabled = {str(bool(enabled)).lower()}",
        f"anonymous = {str(bool(anonymous)).lower()}",
        f'endpoint = "{endpoint_escaped}"',
    ]

    if not path.exists():
        path.write_text("\n".join(section_lines) + "\n", encoding="utf-8")
        return path

    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()

    start = None
    end = None
    for idx, line in enumerate(lines):
        if line.strip() == "[telemetry]":
            start = idx
            break

    if start is not None:
        end = len(lines)
        for idx in range(start + 1, len(lines)):
            if lines[idx].strip().startswith("[") and lines[idx].strip().endswith("]"):
                end = idx
                break
        new_lines = lines[:start] + section_lines + lines[end:]
    else:
        new_lines = lines[:]
        if new_lines and new_lines[-1].strip():
            new_lines.append("")
        new_lines.extend(section_lines)

    path.write_text("\n".join(new_lines).rstrip() + "\n", encoding="utf-8")
    return path


def _events_path(project_root: Path) -> Path:
    return Path(project_root).resolve() / ".hackluminary" / "metrics" / "events.jsonl"


def _queued_count(project_root: Path) -> int:
    events_path = _events_path(project_root)
    if not events_path.exists():
        return 0
    return sum(1 for line in events_path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip())


def _sanitize_payload(payload: dict) -> dict:
    allowed = {
        "command",
        "status",
        "duration_bucket",
        "preset",
        "image_mode",
        "image_coverage_bucket",
        "error_code",
    }

    sanitized = {}
    for key, value in payload.items():
        if key not in allowed:
            continue
        if isinstance(value, (str, int, float, bool)):
            sanitized[key] = value
    return sanitized
