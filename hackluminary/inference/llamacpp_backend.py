"""llama.cpp GGUF inference backend for local-only generation."""

from __future__ import annotations

import json
from pathlib import Path

from ..errors import ErrorCode, HackLuminaryError


class LlamaCppBackend:
    """Thin adapter around llama-cpp-python with JSON-focused generation."""

    def __init__(self, model_path: Path, n_ctx: int = 4096, n_threads: int | None = None) -> None:
        model_path = Path(model_path)
        if not model_path.exists():
            raise HackLuminaryError(
                ErrorCode.MODEL_NOT_AVAILABLE,
                f"Model file not found: {model_path}",
                hint="Run: hackluminary models install qwen2.5-3b-instruct-q4_k_m",
            )

        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise HackLuminaryError(
                ErrorCode.MODEL_NOT_AVAILABLE,
                "llama-cpp-python is not installed.",
                hint="Install with: pip install 'hackluminary[ml]'",
            ) from exc

        self._client = Llama(
            model_path=str(model_path),
            n_ctx=n_ctx,
            n_threads=n_threads,
            verbose=False,
        )

    def generate_json(
        self,
        prompt: str,
        max_tokens: int = 700,
        temperature: float = 0.2,
        top_p: float = 0.9,
    ) -> dict:
        result = self._client.create_completion(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )

        try:
            raw_text = result["choices"][0]["text"]
        except Exception as exc:  # pragma: no cover - defensive
            raise HackLuminaryError(
                ErrorCode.RUNTIME_ERROR,
                "Model response format was invalid.",
                hint=str(exc),
            ) from exc

        return self._parse_json(raw_text)

    def _parse_json(self, text: str) -> dict:
        cleaned = text.strip()
        if not cleaned:
            raise HackLuminaryError(
                ErrorCode.RUNTIME_ERROR,
                "Model returned an empty response.",
            )

        try:
            payload = json.loads(cleaned)
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError:
            pass

        left = cleaned.find("{")
        right = cleaned.rfind("}")
        if left >= 0 and right > left:
            candidate = cleaned[left : right + 1]
            try:
                payload = json.loads(candidate)
            except json.JSONDecodeError as exc:
                raise HackLuminaryError(
                    ErrorCode.RUNTIME_ERROR,
                    "Model output was not valid JSON.",
                    hint=str(exc),
                ) from exc
            if isinstance(payload, dict):
                return payload

        raise HackLuminaryError(
            ErrorCode.RUNTIME_ERROR,
            "Model output did not contain a valid JSON object.",
            hint="Enable --debug to inspect raw model output.",
        )
