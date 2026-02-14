"""Configuration loading and merge logic for HackLuminary."""

from __future__ import annotations

import copy
from pathlib import Path

from .errors import ErrorCode, HackLuminaryError

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - fallback for older runtimes
    import tomli as tomllib  # type: ignore


DEFAULT_CONFIG = {
    "general": {
        "mode": "hybrid",
        "format": "both",
        "theme": "default",
        "max_slides": None,
        "strict_quality": True,
    },
    "git": {
        "base_branch": None,
        "include_branch_context": True,
    },
    "ai": {
        "enabled": True,
        "backend": "llama.cpp",
        "model_alias": "qwen2.5-3b-instruct-q4_k_m",
        "max_tokens": 700,
        "top_p": 0.9,
        "temperature": 0.2,
    },
    "output": {
        "copy_output_dir": None,
        "open_after_generate": False,
    },
    "images": {
        "enabled": True,
        "mode": "auto",
        "image_dirs": [],
        "max_images_per_slide": 1,
        "min_confidence": 0.72,
        "visual_style": "mixed",
        "max_image_bytes": 3_145_728,
        "allowed_extensions": [".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"],
    },
    "telemetry": {
        "enabled": False,
        "anonymous": True,
        "endpoint": "",
    },
    "studio": {
        "enabled": True,
        "default_view": "notebook",
        "autosave_interval_sec": 20,
        "port": 0,
        "read_only": False,
    },
    "ui": {
        "density": "comfortable",
        "motion": "normal",
        "code_font_scale": 1.0,
        "presenter_timer_default_min": 7,
    },
    "features": {
        "studio_enabled": True,
        "production_theme_enabled": True,
        "presenter_pro_enabled": True,
    },
    "privacy": {
        "telemetry": False,
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Merge override into base recursively, ignoring None values."""

    for key, value in override.items():
        if value is None:
            continue
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def _load_toml(path: Path) -> dict:
    if not path.exists():
        return {}

    try:
        with path.open("rb") as handle:
            payload = tomllib.load(handle)
    except Exception as exc:  # pragma: no cover - defensive
        raise HackLuminaryError(
            ErrorCode.CONFIG_ERROR,
            f"Failed to parse config file: {path}",
            hint=str(exc),
        ) from exc

    if not isinstance(payload, dict):
        raise HackLuminaryError(
            ErrorCode.CONFIG_ERROR,
            f"Config file must be a TOML table: {path}",
        )

    return payload


def get_user_config_path() -> Path:
    return Path.home() / ".config" / "hackluminary" / "config.toml"


def get_project_config_path(project_path: Path) -> Path:
    return project_path / "hackluminary.toml"


def load_resolved_config(project_path: Path, cli_overrides: dict | None = None) -> dict:
    """Resolve runtime configuration using the priority order from the spec."""

    project_path = Path(project_path).resolve()
    config = copy.deepcopy(DEFAULT_CONFIG)

    user_cfg = _load_toml(get_user_config_path())
    project_cfg = _load_toml(get_project_config_path(project_path))

    _deep_merge(config, user_cfg)
    _deep_merge(config, project_cfg)

    if cli_overrides:
        _deep_merge(config, cli_overrides)

    _validate_config(config)
    return config


def _validate_config(config: dict) -> None:
    mode = config["general"].get("mode")
    if mode not in {"deterministic", "ai", "hybrid"}:
        raise HackLuminaryError(
            ErrorCode.CONFIG_ERROR,
            f"Invalid mode '{mode}'. Expected one of deterministic|ai|hybrid.",
        )

    fmt = config["general"].get("format")
    if fmt not in {"html", "markdown", "json", "both"}:
        raise HackLuminaryError(
            ErrorCode.CONFIG_ERROR,
            f"Invalid format '{fmt}'. Expected one of html|markdown|json|both.",
        )

    theme = config["general"].get("theme")
    if theme not in {"default", "dark", "minimal", "colorful", "auto"}:
        raise HackLuminaryError(
            ErrorCode.CONFIG_ERROR,
            f"Invalid theme '{theme}'.",
        )

    backend = config["ai"].get("backend")
    if backend not in {"llama.cpp"}:
        raise HackLuminaryError(
            ErrorCode.CONFIG_ERROR,
            f"Invalid AI backend '{backend}'. Only llama.cpp is supported.",
        )

    image_mode = str(config["images"].get("mode", "auto"))
    if image_mode not in {"off", "auto", "strict"}:
        raise HackLuminaryError(
            ErrorCode.CONFIG_ERROR,
            f"Invalid images.mode '{image_mode}'.",
        )

    visual_style = str(config["images"].get("visual_style", "mixed"))
    if visual_style not in {"evidence", "screenshot", "mixed"}:
        raise HackLuminaryError(
            ErrorCode.CONFIG_ERROR,
            f"Invalid images.visual_style '{visual_style}'.",
        )

    max_images = int(config["images"].get("max_images_per_slide", 1))
    if max_images < 0 or max_images > 2:
        raise HackLuminaryError(
            ErrorCode.CONFIG_ERROR,
            "images.max_images_per_slide must be between 0 and 2.",
        )

    min_conf = float(config["images"].get("min_confidence", 0.72))
    if min_conf < 0 or min_conf > 1:
        raise HackLuminaryError(
            ErrorCode.CONFIG_ERROR,
            "images.min_confidence must be between 0 and 1.",
        )

    max_bytes = int(config["images"].get("max_image_bytes", 3_145_728))
    if max_bytes < 16_384:
        raise HackLuminaryError(
            ErrorCode.CONFIG_ERROR,
            "images.max_image_bytes is too small.",
        )

    allowed_extensions = config["images"].get("allowed_extensions", [])
    if not isinstance(allowed_extensions, list) or not allowed_extensions:
        raise HackLuminaryError(
            ErrorCode.CONFIG_ERROR,
            "images.allowed_extensions must be a non-empty list.",
        )
    for ext in allowed_extensions:
        if not str(ext).startswith("."):
            raise HackLuminaryError(
                ErrorCode.CONFIG_ERROR,
                "images.allowed_extensions entries must start with '.'.",
            )

    telemetry_cfg = config.get("telemetry", {})
    if not isinstance(telemetry_cfg.get("enabled", False), bool):
        raise HackLuminaryError(
            ErrorCode.CONFIG_ERROR,
            "telemetry.enabled must be boolean.",
        )
    if not isinstance(telemetry_cfg.get("anonymous", True), bool):
        raise HackLuminaryError(
            ErrorCode.CONFIG_ERROR,
            "telemetry.anonymous must be boolean.",
        )
    if not isinstance(telemetry_cfg.get("endpoint", ""), str):
        raise HackLuminaryError(
            ErrorCode.CONFIG_ERROR,
            "telemetry.endpoint must be a string.",
        )
    endpoint = str(telemetry_cfg.get("endpoint", "")).strip()
    if endpoint and not (endpoint.startswith("http://") or endpoint.startswith("https://")):
        raise HackLuminaryError(
            ErrorCode.CONFIG_ERROR,
            "telemetry.endpoint must start with http:// or https://",
        )

    # Backward-compatible privacy gate from v2.1.
    if config["privacy"].get("telemetry") not in {False, 0, None} and not telemetry_cfg.get("enabled", False):
        raise HackLuminaryError(
            ErrorCode.CONFIG_ERROR,
            "Set [telemetry].enabled=true to explicitly enable telemetry.",
        )

    studio_view = config["studio"].get("default_view")
    if studio_view not in {"notebook", "deck", "presenter"}:
        raise HackLuminaryError(
            ErrorCode.CONFIG_ERROR,
            f"Invalid studio.default_view '{studio_view}'.",
        )

    ui_density = config["ui"].get("density")
    if ui_density not in {"compact", "comfortable", "spacious"}:
        raise HackLuminaryError(
            ErrorCode.CONFIG_ERROR,
            f"Invalid ui.density '{ui_density}'.",
        )

    ui_motion = config["ui"].get("motion")
    if ui_motion not in {"normal", "reduced", "none"}:
        raise HackLuminaryError(
            ErrorCode.CONFIG_ERROR,
            f"Invalid ui.motion '{ui_motion}'.",
        )

    for feature_key in ["studio_enabled", "production_theme_enabled", "presenter_pro_enabled"]:
        if feature_key in config["features"] and not isinstance(config["features"].get(feature_key), bool):
            raise HackLuminaryError(
                ErrorCode.CONFIG_ERROR,
                f"features.{feature_key} must be boolean.",
            )
