"""Local Studio server for NotebookLM-style workflow."""

from __future__ import annotations

import json
import mimetypes
import threading
import webbrowser
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .errors import ErrorCode, HackLuminaryError
from .presentation_generator import PresentationGenerator
from .pipeline import run_generation
from .quality import evaluate_quality
from .studio_session import load_session, save_session
from .visual_selector import attach_visuals_to_slides


STATIC_DIR = Path(__file__).resolve().parent / "studio"


@dataclass
class StudioContext:
    project_path: Path
    config: dict
    payload: dict
    slides: list[dict]
    evidence: list[dict]
    media_catalog: list[dict]
    metadata: dict
    warnings: list[str]


class StudioState:
    """In-memory state for Studio API and workspace session."""

    def __init__(
        self,
        project_path: Path,
        cli_overrides: dict | None = None,
        read_only: bool = False,
    ) -> None:
        self.project_path = Path(project_path).resolve()
        self.read_only = read_only
        self._cli_overrides = cli_overrides or {}
        self._lock = threading.RLock()

        self.context = self._load_context()
        self.session = load_session(self.project_path)
        self._apply_session()

    def _load_context(self) -> StudioContext:
        overrides = {
            "general": {
                "format": "json",
                "mode": "deterministic",
            }
        }
        _deep_merge(overrides, self._cli_overrides)

        result = run_generation(
            project_dir=self.project_path,
            cli_overrides=overrides,
        )

        if not result["config"].get("features", {}).get("studio_enabled", True):
            raise HackLuminaryError(
                ErrorCode.INVALID_INPUT,
                "Studio is disabled by configuration (features.studio_enabled=false).",
            )

        payload = result["payload"]
        return StudioContext(
            project_path=self.project_path,
            config=result["config"],
            payload=payload,
            slides=[dict(slide) for slide in payload.get("slides", [])],
            evidence=[dict(item) for item in payload.get("evidence", [])],
            media_catalog=[dict(item) for item in payload.get("media_catalog", [])],
            metadata=dict(payload.get("metadata", {})),
            warnings=list(result.get("warnings", [])),
        )

    def _apply_session(self) -> None:
        slide_by_id = {slide["id"]: slide for slide in self.context.slides}

        ordered_ids = [sid for sid in self.session.get("slide_order", []) if sid in slide_by_id]
        remainder = [sid for sid in slide_by_id if sid not in ordered_ids]
        full_order = ordered_ids + remainder

        reordered = [slide_by_id[sid] for sid in full_order]

        draft_overrides = self.session.get("draft_overrides", {})
        if isinstance(draft_overrides, dict):
            for slide in reordered:
                override = draft_overrides.get(slide["id"], {})
                if not isinstance(override, dict):
                    continue
                for key in ["title", "subtitle", "content", "list_items", "claims", "evidence_refs", "notes", "visuals"]:
                    if key in override:
                        slide[key] = override[key]

        note_blocks = self.session.get("note_blocks", {})
        if isinstance(note_blocks, dict):
            for slide in reordered:
                if slide["id"] in note_blocks and isinstance(note_blocks[slide["id"]], str):
                    slide["notes"] = note_blocks[slide["id"]][:800]

        self.context.slides = reordered
        self._refresh_quality()

    def _refresh_quality(self) -> None:
        images_cfg = self.context.config.get("images", {})
        report = evaluate_quality(
            self.context.slides,
            image_mode=str(images_cfg.get("mode", "off")),
            min_visual_confidence=float(images_cfg.get("min_confidence", 0.72)),
        )
        self.context.payload["quality_report"] = report
        self.session["last_validation"] = report

    def get_context_payload(self) -> dict:
        with self._lock:
            payload = {
                "schema_version": self.context.payload.get("schema_version", "2.2"),
                "metadata": self.context.metadata,
                "git_context": self.context.payload.get("git_context", {}),
                "quality_report": self.context.payload.get("quality_report", {}),
                "config": {
                    "theme": self.context.config.get("general", {}).get("theme"),
                    "features": self.context.config.get("features", {}),
                    "ui": self.context.config.get("ui", {}),
                    "studio": self.context.config.get("studio", {}),
                    "images": self.context.config.get("images", {}),
                },
                "read_only": self.read_only,
                "warnings": self.context.warnings,
            }
            return payload

    def get_slides_payload(self) -> dict:
        with self._lock:
            return {"slides": self.context.slides}

    def get_evidence_payload(self) -> dict:
        with self._lock:
            return {"evidence": self.context.evidence}

    def get_media_payload(self) -> dict:
        with self._lock:
            return {"media_catalog": self.context.media_catalog}

    def get_session_payload(self) -> dict:
        with self._lock:
            return {"session": self.session}

    def update_slides(self, incoming_slides: list[dict]) -> dict:
        with self._lock:
            if self.read_only:
                raise HackLuminaryError(ErrorCode.INVALID_INPUT, "Studio is in read-only mode.")

            slide_by_id = {slide["id"]: dict(slide) for slide in self.context.slides}

            for patch in incoming_slides:
                if not isinstance(patch, dict):
                    continue
                sid = patch.get("id")
                if sid not in slide_by_id:
                    continue

                current = slide_by_id[sid]
                for key in ["title", "subtitle", "content", "list_items", "claims", "evidence_refs", "notes", "visuals"]:
                    if key not in patch:
                        continue

                    value = patch[key]
                    if key == "list_items":
                        if isinstance(value, list):
                            current[key] = [str(item).strip() for item in value if str(item).strip()][:10]
                    elif key == "claims":
                        current[key] = _sanitize_claims(value, fallback_refs=current.get("evidence_refs", []))
                    elif key == "evidence_refs":
                        if isinstance(value, list):
                            current[key] = [str(item).strip() for item in value if str(item).strip()][:12]
                    elif key == "visuals":
                        current[key] = _sanitize_visuals(value, self.project_path)
                    elif key == "notes":
                        current[key] = str(value)[:800]
                    else:
                        current[key] = str(value)[:5000]

                slide_by_id[sid] = current

            ordered = []
            for slide in self.context.slides:
                ordered.append(slide_by_id[slide["id"]])

            self.context.slides = ordered
            self._refresh_quality()
            self._sync_session_from_slides()
            return {
                "slides": self.context.slides,
                "quality_report": self.context.payload.get("quality_report", {}),
            }

    def _sync_session_from_slides(self) -> None:
        self.session["slide_order"] = [slide["id"] for slide in self.context.slides]
        draft_overrides = {}
        notes = {}
        for slide in self.context.slides:
            draft_overrides[slide["id"]] = {
                key: slide.get(key)
                for key in ["title", "subtitle", "content", "list_items", "claims", "evidence_refs", "notes", "visuals"]
                if key in slide
            }
            if slide.get("notes"):
                notes[slide["id"]] = slide.get("notes")
        self.session["draft_overrides"] = draft_overrides
        self.session["note_blocks"] = notes

    def save_session(self, payload: dict) -> dict:
        with self._lock:
            if self.read_only:
                raise HackLuminaryError(ErrorCode.INVALID_INPUT, "Studio is in read-only mode.")

            if not isinstance(payload, dict):
                raise HackLuminaryError(ErrorCode.INVALID_INPUT, "Session payload must be an object.")

            for key in [
                "selected_slides",
                "slide_order",
                "draft_overrides",
                "note_blocks",
                "pinned_evidence",
                "presenter",
                "last_validation",
            ]:
                if key in payload:
                    self.session[key] = payload[key]

            saved = save_session(self.project_path, self.session)
            return {"session": self.session, "path": str(saved)}

    def validate(self, slides: list[dict] | None = None) -> dict:
        with self._lock:
            target = slides if slides is not None else self.context.slides
            images_cfg = self.context.config.get("images", {})
            report = evaluate_quality(
                target,
                image_mode=str(images_cfg.get("mode", "off")),
                min_visual_confidence=float(images_cfg.get("min_confidence", 0.72)),
            )
            return {"quality_report": report}

    def export(self, fmt: str, slides: list[dict] | None = None, output_path: str | None = None) -> dict:
        with self._lock:
            target_slides = slides if slides is not None else self.context.slides
            renderer = PresentationGenerator(
                target_slides,
                metadata=self.context.metadata,
                theme=self.context.config.get("general", {}).get("theme", "default"),
                project_root=self.project_path,
            )

            outputs = {}
            if fmt in {"html", "both"}:
                outputs["html"] = renderer.generate_html()
            if fmt in {"markdown", "both"}:
                outputs["markdown"] = renderer.generate_markdown()
            if fmt == "json":
                outputs["json"] = json.dumps(
                    {
                        "schema_version": "2.2",
                        "metadata": self.context.metadata,
                        "git_context": self.context.payload.get("git_context", {}),
                        "slides": target_slides,
                        "evidence": self.context.evidence,
                        "media_catalog": self.context.media_catalog,
                        "quality_report": self.validate(target_slides)["quality_report"],
                    },
                    indent=2,
                )

            paths = []
            if output_path:
                safe = _safe_project_path(self.project_path, output_path)
                safe.parent.mkdir(parents=True, exist_ok=True)
                if "html" in outputs:
                    path = safe if fmt == "html" else safe.with_suffix(".html")
                    path.write_text(outputs["html"], encoding="utf-8")
                    paths.append(str(path))
                if "markdown" in outputs:
                    path = safe if fmt == "markdown" else safe.with_suffix(".md")
                    path.write_text(outputs["markdown"], encoding="utf-8")
                    paths.append(str(path))
                if "json" in outputs:
                    path = safe if safe.suffix == ".json" else safe.with_suffix(".json")
                    path.write_text(outputs["json"], encoding="utf-8")
                    paths.append(str(path))

            return {"format": fmt, "outputs": outputs, "paths": paths}

    def auto_fix_visuals(self, slide_ids: list[str] | None = None) -> dict:
        with self._lock:
            if self.read_only:
                raise HackLuminaryError(ErrorCode.INVALID_INPUT, "Studio is in read-only mode.")

            images_cfg = self.context.config.get("images", {})
            updated, _summary = attach_visuals_to_slides(
                slides=self.context.slides,
                media_catalog=self.context.media_catalog,
                mode=str(images_cfg.get("mode", "auto")),
                max_images_per_slide=int(images_cfg.get("max_images_per_slide", 1)),
                min_confidence=float(images_cfg.get("min_confidence", 0.72)),
                visual_style=str(images_cfg.get("visual_style", "mixed")),
            )

            selected = set(str(item) for item in slide_ids or [])
            if selected:
                current_by_id = {slide["id"]: slide for slide in self.context.slides}
                for patched in updated:
                    sid = patched.get("id")
                    if sid in selected:
                        current_by_id[sid] = patched
                self.context.slides = [current_by_id[slide["id"]] for slide in self.context.slides]
            else:
                self.context.slides = updated

            self._refresh_quality()
            self._sync_session_from_slides()
            return {"slides": self.context.slides, "quality_report": self.context.payload.get("quality_report", {})}


class StudioHTTPHandler(BaseHTTPRequestHandler):
    """Request handler bound dynamically to a `StudioState` instance."""

    state: StudioState

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path

        try:
            if path in {"/", "/index.html"}:
                return self._serve_static("index.html")
            if path == "/studio.css":
                return self._serve_static("studio.css")
            if path == "/studio.js":
                return self._serve_static("studio.js")
            if path == "/presenter.css":
                return self._serve_static("presenter.css")
            if path == "/presenter.js":
                return self._serve_static("presenter.js")

            if path == "/api/context":
                return self._json_ok(self.state.get_context_payload())
            if path == "/api/slides":
                return self._json_ok(self.state.get_slides_payload())
            if path == "/api/evidence":
                return self._json_ok(self.state.get_evidence_payload())
            if path == "/api/media":
                return self._json_ok(self.state.get_media_payload())
            if path == "/api/session":
                return self._json_ok(self.state.get_session_payload())

            return self._json_error(404, ErrorCode.INVALID_INPUT, f"Unknown route: {path}")
        except HackLuminaryError as exc:
            return self._json_error(400, exc.code, exc.message, exc.hint)
        except Exception as exc:  # pragma: no cover - defensive
            return self._json_error(500, ErrorCode.RUNTIME_ERROR, f"Internal error: {exc}")

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path

        try:
            data = self._read_json_body()

            if path == "/api/slides":
                slides = data.get("slides", [])
                if not isinstance(slides, list):
                    raise HackLuminaryError(ErrorCode.INVALID_INPUT, "'slides' must be an array.")
                payload = self.state.update_slides(slides)
                return self._json_ok(payload)

            if path == "/api/validate":
                incoming = data.get("slides")
                payload = self.state.validate(incoming if isinstance(incoming, list) else None)
                return self._json_ok(payload)

            if path == "/api/export":
                fmt = str(data.get("format", "html"))
                if fmt not in {"html", "markdown", "json", "both"}:
                    raise HackLuminaryError(ErrorCode.INVALID_INPUT, f"Invalid export format: {fmt}")
                incoming = data.get("slides")
                output_path = data.get("output_path")
                payload = self.state.export(fmt, incoming if isinstance(incoming, list) else None, output_path)
                return self._json_ok(payload)

            if path == "/api/visuals/auto-fix":
                slide_ids = data.get("slide_ids")
                if slide_ids is not None and not isinstance(slide_ids, list):
                    raise HackLuminaryError(ErrorCode.INVALID_INPUT, "'slide_ids' must be an array when provided.")
                payload = self.state.auto_fix_visuals(slide_ids if isinstance(slide_ids, list) else None)
                return self._json_ok(payload)

            return self._json_error(404, ErrorCode.INVALID_INPUT, f"Unknown route: {path}")
        except HackLuminaryError as exc:
            return self._json_error(400, exc.code, exc.message, exc.hint)
        except Exception as exc:  # pragma: no cover - defensive
            return self._json_error(500, ErrorCode.RUNTIME_ERROR, f"Internal error: {exc}")

    def do_PUT(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path

        try:
            data = self._read_json_body()

            if path == "/api/session":
                payload = self.state.save_session(data)
                return self._json_ok(payload)

            return self._json_error(404, ErrorCode.INVALID_INPUT, f"Unknown route: {path}")
        except HackLuminaryError as exc:
            return self._json_error(400, exc.code, exc.message, exc.hint)
        except Exception as exc:  # pragma: no cover - defensive
            return self._json_error(500, ErrorCode.RUNTIME_ERROR, f"Internal error: {exc}")

    def _serve_static(self, filename: str) -> None:
        path = (STATIC_DIR / filename).resolve()
        if not path.exists() or not path.is_file():
            self._json_error(404, ErrorCode.INVALID_INPUT, f"Static file not found: {filename}")
            return

        content_type, _ = mimetypes.guess_type(str(path))
        self.send_response(200)
        self.send_header("Content-Type", content_type or "text/plain; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(path.read_bytes())

    def _read_json_body(self) -> dict:
        raw = self.rfile.read(int(self.headers.get("Content-Length", "0") or 0))
        if not raw:
            return {}
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise HackLuminaryError(ErrorCode.PARSE_ERROR, "Invalid JSON body.", hint=str(exc)) from exc
        if not isinstance(payload, dict):
            raise HackLuminaryError(ErrorCode.INVALID_INPUT, "Request body must be a JSON object.")
        return payload

    def _json_ok(self, payload: dict) -> None:
        body = json.dumps({"ok": True, "data": payload}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1")
        self.end_headers()
        self.wfile.write(body)

    def _json_error(self, status: int, code: ErrorCode | str, message: str, hint: str | None = None) -> None:
        body = {"ok": False, "error": {"code": str(code), "message": message}}
        if hint:
            body["error"]["hint"] = hint
        raw = json.dumps(body).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        # Silence request logs by default.
        return


def create_studio_server(
    project_path: Path | str,
    cli_overrides: dict | None = None,
    port: int = 0,
    read_only: bool = False,
) -> tuple[ThreadingHTTPServer, StudioState]:
    state = StudioState(Path(project_path), cli_overrides=cli_overrides, read_only=read_only)

    handler_cls = type("BoundStudioHandler", (StudioHTTPHandler,), {})
    handler_cls.state = state

    httpd = ThreadingHTTPServer(("127.0.0.1", port), handler_cls)
    httpd.daemon_threads = True

    return httpd, state


def run_studio_server(
    project_path: Path | str,
    cli_overrides: dict | None = None,
    port: int = 0,
    read_only: bool = False,
    auto_open: bool = True,
    debug: bool = False,
) -> None:
    """Run the Studio server and block until interrupted."""

    httpd, _state = create_studio_server(
        project_path=project_path,
        cli_overrides=cli_overrides,
        port=port,
        read_only=read_only,
    )

    host, bound_port = httpd.server_address
    url = f"http://{host}:{bound_port}/"

    if auto_open:
        webbrowser.open(url)

    if debug:
        print(f"Studio server listening on {url}")

    try:
        httpd.serve_forever(poll_interval=0.3)
    except KeyboardInterrupt:
        pass
    finally:
        httpd.shutdown()
        httpd.server_close()


def _safe_project_path(project_root: Path, candidate: str) -> Path:
    root = project_root.resolve()
    path = Path(candidate)
    if not path.is_absolute():
        path = (root / path).resolve()
    else:
        path = path.resolve()

    try:
        path.relative_to(root)
    except ValueError as exc:
        raise HackLuminaryError(
            ErrorCode.INVALID_INPUT,
            "Output path must stay within the project directory.",
            hint=str(path),
        ) from exc

    return path


def _sanitize_claims(value: Any, fallback_refs: list[str]) -> list[dict]:
    claims = []
    if not isinstance(value, list):
        return claims

    for item in value[:12]:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text", "")).strip()
        if not text:
            continue
        refs = item.get("evidence_refs", fallback_refs)
        if not isinstance(refs, list):
            refs = fallback_refs
        claims.append(
            {
                "text": text[:600],
                "evidence_refs": [str(ref).strip() for ref in refs if str(ref).strip()][:12],
                "confidence": float(item.get("confidence", 0.8)),
            }
        )

    return claims


def _sanitize_visuals(value: Any, project_root: Path) -> list[dict]:
    visuals: list[dict] = []
    if not isinstance(value, list):
        return visuals

    for item in value[:2]:
        if not isinstance(item, dict):
            continue
        source_path = str(item.get("source_path", "")).strip()
        if not source_path:
            continue
        if source_path.startswith("http://") or source_path.startswith("https://"):
            continue
        try:
            safe_path = _safe_project_path(project_root, source_path)
            source_path = str(safe_path.relative_to(project_root.resolve()))
        except HackLuminaryError:
            continue

        refs = item.get("evidence_refs", [])
        if not isinstance(refs, list):
            refs = []

        try:
            confidence = float(item.get("confidence", 0.0))
        except (TypeError, ValueError):
            confidence = 0.0

        visuals.append(
            {
                "id": str(item.get("id", ""))[:128],
                "type": "image",
                "source_path": source_path,
                "alt": str(item.get("alt", "")).strip()[:240],
                "caption": str(item.get("caption", "")).strip()[:240],
                "evidence_refs": [str(ref).strip() for ref in refs if str(ref).strip()][:8],
                "confidence": confidence,
                "width": item.get("width"),
                "height": item.get("height"),
                "sha256": str(item.get("sha256", ""))[:128],
            }
        )

    return visuals


def _deep_merge(base: dict, override: dict) -> None:
    for key, value in override.items():
        if value is None:
            continue
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
