"""Telemetry module tests (opt-in local + explicit flush)."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from hackluminary.telemetry import (
    disable_telemetry_in_project_config,
    enable_telemetry_in_project_config,
    flush_telemetry_events,
    telemetry_status,
    write_telemetry_event,
)


class _Handler(BaseHTTPRequestHandler):
    received = []

    def do_POST(self):  # noqa: N802
        size = int(self.headers.get("Content-Length", "0") or 0)
        body = self.rfile.read(size).decode("utf-8") if size else "{}"
        self.__class__.received.append(json.loads(body))
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, format, *args):  # noqa: A003
        return


def test_enable_disable_telemetry_config(tmp_path):
    path = enable_telemetry_in_project_config(tmp_path, endpoint="https://example.invalid/ingest")
    text = path.read_text(encoding="utf-8")
    assert "[telemetry]" in text
    assert "enabled = true" in text

    path = disable_telemetry_in_project_config(tmp_path)
    text = path.read_text(encoding="utf-8")
    assert "enabled = false" in text


def test_write_status_and_flush_dry_run(tmp_path):
    config = {"telemetry": {"enabled": True, "anonymous": True, "endpoint": "https://example.invalid/ingest"}}
    write_telemetry_event(tmp_path, config, "generate", {"command": "generate", "status": "success"})
    write_telemetry_event(tmp_path, config, "validate", {"command": "validate", "status": "success"})

    status = telemetry_status(tmp_path, config)
    assert status["queued_events"] == 2

    dry = flush_telemetry_events(tmp_path, config, dry_run=True)
    assert dry["status"] == "dry-run"
    assert dry["would_send"] == 2


def test_flush_sends_and_removes_events(tmp_path):
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    _Handler.received = []
    thread = threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
    thread.start()

    try:
        endpoint = f"http://{httpd.server_address[0]}:{httpd.server_address[1]}/ingest"
        config = {"telemetry": {"enabled": True, "anonymous": True, "endpoint": endpoint}}
        write_telemetry_event(tmp_path, config, "generate", {"command": "generate", "status": "success"})

        result = flush_telemetry_events(tmp_path, config)
        assert result["status"] == "ok"
        assert result["sent"] == 1

        status = telemetry_status(tmp_path, config)
        assert status["queued_events"] == 0
        assert _Handler.received
        assert _Handler.received[0]["events"][0]["event"] == "generate"
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=2)
