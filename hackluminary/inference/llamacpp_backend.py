
from __future__ import annotations

import concurrent.futures
import json
import re
from pathlib import Path

from ..errors import ErrorCode, HackLuminaryError


def _write_debug_output(raw_text: str, candidate: str | None = None) -> Path | str:
    """Persist raw model output for debugging JSON issues."""
    try:
        debug_dir = Path.home() / ".local" / "share" / "hackluminary"
        debug_dir.mkdir(parents=True, exist_ok=True)
        debug_file = debug_dir / "last_model_output.json.txt"

        parts: list[str] = ["=== RAW MODEL OUTPUT ===\n", raw_text]
        if candidate is not None and candidate != raw_text:
            parts.append("\n\n=== CANDIDATE JSON SLICE ===\n")
            parts.append(candidate)

        debug_file.write_text("".join(parts), encoding="utf-8", errors="replace")
        return debug_file
    except Exception:
        # Best-effort only; never block on debug logging.
        return "unknown"


def _looks_truncated_json(text: str) -> bool:
    """Heuristic for obviously truncated JSON (unbalanced braces/brackets)."""
    brace_delta = text.count("{") - text.count("}")
    bracket_delta = text.count("[") - text.count("]")
    return brace_delta != 0 or bracket_delta != 0


class LlamaCppBackend:
    """Thin adapter around llama-cpp-python with JSON-focused generation."""

    def __init__(
        self, model_path: Path, n_ctx: int = 4096, n_threads: int | None = None, request_timeout: int = 60
    ) -> None:
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
        self._request_timeout = request_timeout

    def generate_json(
        self,
        prompt: str,
        max_tokens: int = 700,
        temperature: float = 0.2,
        top_p: float = 0.9,
        max_retries: int = 3,
    ) -> dict:
        # Use explicit shutdown(wait=False) so that a timed-out llama.cpp thread
        # (which cannot be interrupted) does not block the whole process.
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        try:
            for i in range(max_retries):
                try:
                    future = executor.submit(
                        self._client.create_completion,
                        prompt=prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        top_p=top_p,
                    )
                    result = future.result(timeout=self._request_timeout)
                except concurrent.futures.TimeoutError as exc:
                    raise HackLuminaryError(
                        ErrorCode.RUNTIME_ERROR,
                        "Model generation timed out.",
                        hint=f"Timeout was {self._request_timeout}s. Increase ai.request_timeout in config.",
                    ) from exc

                try:
                    raw_text = result["choices"][0]["text"]
                except Exception as exc:  # pragma: no cover - defensive
                    raise HackLuminaryError(
                        ErrorCode.RUNTIME_ERROR,
                        "Model response format was invalid.",
                        hint=str(exc),
                    ) from exc

                try:
                    return self._parse_json(raw_text)
                except HackLuminaryError as e:
                    if i == max_retries - 1:
                        raise e
        finally:
            executor.shutdown(wait=False)

    def generate_json_zero_shot(self, prompt: str, max_tokens: int = 700) -> dict:
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        try:
            future = executor.submit(
                self._client.create_completion,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=0.0,  # Set temperature to 0 for deterministic output
                top_p=1.0,
            )
            result = future.result(timeout=self._request_timeout)
        except concurrent.futures.TimeoutError as exc:
            raise HackLuminaryError(
                ErrorCode.RUNTIME_ERROR,
                "Model generation timed out.",
                hint=f"Timeout was {self._request_timeout}s. Increase ai.request_timeout in config.",
            ) from exc
        finally:
            executor.shutdown(wait=False)

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

        # Strategy 1: Look for a fenced block of ```json ... ```
        match = re.search(r"```json\n(.*?)\n```", cleaned, re.DOTALL)
        if match:
            candidate = match.group(1).strip()
        else:
            # Strategy 2: Find the outermost JSON object braces.
            left = cleaned.find("{")
            right = cleaned.rfind("}")
            if left != -1 and right != -1 and right > left:
                candidate = cleaned[left : right + 1]
            else:
                candidate = cleaned  # Fallback to the full cleaned string.

        # If the candidate has unbalanced braces/brackets, the model almost
        # certainly hit the token limit and returned a truncated JSON object.
        if _looks_truncated_json(candidate):
            debug_path = _write_debug_output(cleaned, candidate)
            raise HackLuminaryError(
                ErrorCode.RUNTIME_ERROR,
                "Model output JSON appears truncated (model likely hit token limit).",
                hint=f"Increase ai.max_tokens or simplify slides. Raw model output written to: {debug_path}",
            )

        try:
            return json.loads(candidate)
        except json.JSONDecodeError as exc:
            debug_path = _write_debug_output(cleaned, candidate)
            raise HackLuminaryError(
                ErrorCode.RUNTIME_ERROR,
                "Model output was not valid JSON.",
                hint=f"{exc}. Raw model output written to: {debug_path}",
            ) from exc
