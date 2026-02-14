"""AI post-processing pipeline with schema and quality gate enforcement."""

from __future__ import annotations

import json

from .errors import ErrorCode, HackLuminaryError
from .inference.llamacpp_backend import LlamaCppBackend
from .models import resolve_model_path
from .quality import enforce_quality, evaluate_quality


def enhance_slides_with_ai(slides: list[dict], evidence: list[dict], config: dict) -> tuple[list[dict], dict]:
    """Optionally enhance deterministic slides using local llama.cpp model output."""

    mode = config["general"]["mode"]
    strict_quality = bool(config["general"].get("strict_quality", True))
    ai_enabled = bool(config["ai"].get("enabled", True))

    if mode == "deterministic" or not ai_enabled:
        report = evaluate_quality(slides)
        enforce_quality(report, strict_quality)
        return slides, report

    backend = _load_backend(config)

    try:
        payload = backend.generate_json(
            _build_prompt(slides, evidence),
            max_tokens=int(config["ai"].get("max_tokens", 700)),
            temperature=float(config["ai"].get("temperature", 0.2)),
            top_p=float(config["ai"].get("top_p", 0.9)),
        )
        merged = _merge_ai_payload(slides, payload)
    except HackLuminaryError:
        if mode == "hybrid" and not strict_quality:
            report = evaluate_quality(slides)
            report.setdefault("warnings", []).append(
                "AI enhancement was skipped due to backend or schema issues."
            )
            return slides, report
        raise
    except Exception as exc:
        if mode == "hybrid" and not strict_quality:
            report = evaluate_quality(slides)
            report.setdefault("warnings", []).append(f"AI enhancement skipped: {exc}")
            return slides, report
        raise HackLuminaryError(
            ErrorCode.RUNTIME_ERROR,
            "AI enhancement failed.",
            hint=str(exc),
        ) from exc

    report = evaluate_quality(merged)
    enforce_quality(report, strict_quality)
    return merged, report


def _load_backend(config: dict) -> LlamaCppBackend:
    backend_name = config["ai"].get("backend", "llama.cpp")
    if backend_name != "llama.cpp":
        raise HackLuminaryError(
            ErrorCode.MODEL_NOT_AVAILABLE,
            f"Unsupported AI backend '{backend_name}'.",
        )

    alias = config["ai"].get("model_alias", "qwen2.5-3b-instruct-q4_k_m")
    model_path = resolve_model_path(alias)
    if not model_path:
        raise HackLuminaryError(
            ErrorCode.MODEL_NOT_AVAILABLE,
            f"Local model alias '{alias}' is not installed.",
            hint=f"Run: hackluminary models install {alias}",
        )

    return LlamaCppBackend(model_path)


def _build_prompt(slides: list[dict], evidence: list[dict]) -> str:
    spec = {
        "task": "Improve slide wording while staying faithful to evidence.",
        "rules": [
            "Return JSON only.",
            "Do not add new unsupported claims.",
            "Keep the same slide ids.",
            "Preserve factual meaning.",
            "Avoid fluff and hype terms.",
        ],
        "output_schema": {
            "slides": [
                {
                    "id": "string",
                    "title": "optional string",
                    "subtitle": "optional string",
                    "content": "optional string",
                    "list_items": ["optional list of strings"],
                }
            ]
        },
        "slides": slides,
        "evidence": evidence,
    }
    return json.dumps(spec, ensure_ascii=False)


def _merge_ai_payload(slides: list[dict], payload: dict) -> list[dict]:
    updates = payload.get("slides")
    if not isinstance(updates, list):
        raise HackLuminaryError(
            ErrorCode.PARSE_ERROR,
            "AI response does not include a valid 'slides' list.",
        )

    slide_map = {slide["id"]: dict(slide) for slide in slides}

    for update in updates:
        if not isinstance(update, dict):
            continue
        slide_id = update.get("id")
        if slide_id not in slide_map:
            continue

        target = slide_map[slide_id]

        for key in ("title", "subtitle", "content"):
            value = update.get(key)
            if isinstance(value, str) and value.strip():
                target[key] = value.strip()

        list_items = update.get("list_items")
        if isinstance(list_items, list):
            cleaned = [str(item).strip() for item in list_items if str(item).strip()]
            if cleaned:
                target["list_items"] = cleaned[:8]

        claims = update.get("claims")
        if isinstance(claims, list):
            cleaned_claims = []
            for claim in claims[:10]:
                if not isinstance(claim, dict):
                    continue
                text = str(claim.get("text", "")).strip()
                if not text:
                    continue
                cleaned_claims.append(
                    {
                        "text": text,
                        "evidence_refs": [
                            str(ref).strip()
                            for ref in claim.get("evidence_refs", target.get("evidence_refs", []))
                            if str(ref).strip()
                        ],
                        "confidence": float(claim.get("confidence", 0.8)),
                    }
                )
            if cleaned_claims:
                target["claims"] = cleaned_claims

        notes = update.get("notes")
        if isinstance(notes, str):
            target["notes"] = notes.strip()[:600]

        slide_map[slide_id] = target

    merged = [slide_map[slide["id"]] for slide in slides]
    return merged
