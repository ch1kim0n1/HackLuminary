"""Model catalog and install/list helpers for local inference."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .errors import ErrorCode, HackLuminaryError


BUILTIN_MODELS: dict[str, dict[str, str]] = {
    "qwen2.5-3b-instruct-q4_k_m": {
        "repo_id": "Qwen/Qwen2.5-3B-Instruct-GGUF",
        "filename": "qwen2.5-3b-instruct-q4_k_m.gguf",
        "license": "apache-2.0",
    },
    "phi-3.5-mini-instruct-q4_k_m": {
        "repo_id": "bartowski/Phi-3.5-mini-instruct-GGUF",
        "filename": "Phi-3.5-mini-instruct-Q4_K_M.gguf",
        "license": "mit",
    },
}


def get_models_root() -> Path:
    return Path.home() / ".local" / "share" / "hackluminary" / "models"


def get_registry_path() -> Path:
    return get_models_root() / "registry.json"


def _load_registry() -> dict[str, Any]:
    path = get_registry_path()
    if not path.exists():
        return {"installed": {}}

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - defensive
        raise HackLuminaryError(
            ErrorCode.RUNTIME_ERROR,
            f"Model registry is corrupted: {path}",
            hint=str(exc),
        ) from exc

    installed = payload.get("installed", {})
    if not isinstance(installed, dict):
        return {"installed": {}}

    return {"installed": installed}


def _save_registry(registry: dict[str, Any]) -> None:
    root = get_models_root()
    root.mkdir(parents=True, exist_ok=True)
    get_registry_path().write_text(json.dumps(registry, indent=2), encoding="utf-8")


def list_models() -> list[dict[str, Any]]:
    """List built-in models and installation status."""

    registry = _load_registry()["installed"]
    rows: list[dict[str, Any]] = []

    for alias in sorted(BUILTIN_MODELS):
        model = BUILTIN_MODELS[alias]
        path = registry.get(alias)
        installed = bool(path and Path(path).exists())
        rows.append(
            {
                "alias": alias,
                "installed": installed,
                "path": str(path) if path else "",
                "license": model.get("license", "unknown"),
            }
        )

    for alias, path in sorted(registry.items()):
        if alias in BUILTIN_MODELS:
            continue
        rows.append(
            {
                "alias": alias,
                "installed": Path(path).exists(),
                "path": str(path),
                "license": "unknown",
            }
        )

    return rows


def resolve_model_path(alias: str) -> Path | None:
    """Resolve the path of an installed model alias."""

    registry = _load_registry()["installed"]
    raw = registry.get(alias)
    if raw:
        path = Path(raw)
        if path.exists():
            return path

    default_candidate = get_models_root() / alias / "model.gguf"
    if default_candidate.exists():
        return default_candidate

    return None


def install_model(alias: str, force: bool = False) -> Path:
    """Install a GGUF model from Hugging Face into local model storage."""

    if alias not in BUILTIN_MODELS:
        known = ", ".join(sorted(BUILTIN_MODELS))
        raise HackLuminaryError(
            ErrorCode.INVALID_INPUT,
            f"Unknown model alias '{alias}'.",
            hint=f"Use one of: {known}",
        )

    model = BUILTIN_MODELS[alias]
    target_dir = get_models_root() / alias
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / "model.gguf"

    if target_path.exists() and not force:
        return target_path

    try:
        from huggingface_hub import hf_hub_download
    except ImportError as exc:
        raise HackLuminaryError(
            ErrorCode.MODEL_NOT_AVAILABLE,
            "huggingface_hub is required for model installation.",
            hint="Install with: pip install 'hackluminary[ml]'",
        ) from exc

    try:
        downloaded = hf_hub_download(
            repo_id=model["repo_id"],
            filename=model["filename"],
            local_dir=str(target_dir),
            local_dir_use_symlinks=False,
        )
    except Exception as exc:  # pragma: no cover - network-sensitive
        raise HackLuminaryError(
            ErrorCode.MODEL_NOT_AVAILABLE,
            f"Failed to download model '{alias}'.",
            hint=str(exc),
        ) from exc

    downloaded_path = Path(downloaded)
    if downloaded_path != target_path:
        downloaded_path.replace(target_path)

    registry = _load_registry()
    registry.setdefault("installed", {})[alias] = str(target_path)
    _save_registry(registry)

    return target_path
