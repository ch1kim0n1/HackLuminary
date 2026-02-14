"""Studio server API contract tests."""

import json
import threading
import urllib.request

from hackluminary.studio_server import create_studio_server


def _request_json(url, method="GET", payload=None):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, method=method, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=4) as res:
        raw = res.read().decode("utf-8")
    return json.loads(raw)


def test_studio_api_endpoints(tmp_path):
    (tmp_path / "README.md").write_text(
        """
# Studio Demo

## Problem
Deck quality varies across teams.

## Solution
Ground claims in repository evidence.
""".strip(),
        encoding="utf-8",
    )
    (tmp_path / "main.py").write_text("print('studio')\n", encoding="utf-8")

    httpd, state = create_studio_server(tmp_path, port=0)
    host, port = httpd.server_address
    base = f"http://{host}:{port}"

    thread = threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
    thread.start()

    try:
        context = _request_json(f"{base}/api/context")
        assert context["ok"] is True
        assert context["data"]["schema_version"] == "2.2"
        assert context["data"]["read_only"] is False
        assert "studio" in context["data"]["config"]

        slides = _request_json(f"{base}/api/slides")
        assert slides["ok"] is True
        assert slides["data"]["slides"]

        evidence = _request_json(f"{base}/api/evidence")
        assert evidence["ok"] is True
        assert evidence["data"]["evidence"]

        media = _request_json(f"{base}/api/media")
        assert media["ok"] is True
        assert "media_catalog" in media["data"]

        update_payload = {
            "slides": [
                {
                    "id": slides["data"]["slides"][0]["id"],
                    "title": "Updated Title",
                    "claims": [
                        {
                            "text": "Updated claim",
                            "evidence_refs": ["doc.title"],
                            "confidence": 0.9,
                        }
                    ],
                }
            ]
        }
        updated = _request_json(f"{base}/api/slides", method="POST", payload=update_payload)
        assert updated["ok"] is True
        assert updated["data"]["slides"][0]["title"] == "Updated Title"

        validated = _request_json(f"{base}/api/validate", method="POST", payload={})
        assert validated["ok"] is True
        assert "quality_report" in validated["data"]

        exported = _request_json(f"{base}/api/export", method="POST", payload={"format": "html"})
        assert exported["ok"] is True
        assert "<!DOCTYPE html>" in exported["data"]["outputs"]["html"]

        visual_fix = _request_json(f"{base}/api/visuals/auto-fix", method="POST", payload={})
        assert visual_fix["ok"] is True
        assert "quality_report" in visual_fix["data"]

        saved = _request_json(
            f"{base}/api/session",
            method="PUT",
            payload={"slide_order": [slide["id"] for slide in state.context.slides]},
        )
        assert saved["ok"] is True
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=2)
