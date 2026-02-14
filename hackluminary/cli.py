"""HackLuminary v2 CLI."""

from __future__ import annotations

import json
import shutil
import sys
import time
import traceback
import webbrowser
from pathlib import Path

import click

from . import __version__
from .artifacts import write_bundle_artifacts
from .benchmark import benchmark_visual_coverage
from .config import get_project_config_path, load_resolved_config
from .doctor import run_doctor
from .errors import ErrorCode, HackLuminaryError
from .image_indexer import index_project_images
from .models import install_model, list_models
from .package_builder import build_devpost_package, write_manifest
from .pipeline import run_generation, run_validation
from .presets import list_presets, resolve_preset
from .studio_server import run_studio_server
from .telemetry import (
    disable_telemetry_in_project_config,
    duration_bucket,
    enable_telemetry_in_project_config,
    flush_telemetry_events,
    telemetry_status,
    write_telemetry_event,
)

PRESET_NAMES = ["quick", "demo-day", "investor", "hackathon-judges", "hackathon-finals"]


def _normalize_legacy_args(argv: list[str]) -> list[str]:
    """Support old top-level usage by rewriting it to `generate ...`."""

    if not argv:
        return ["generate"]

    top_level = {
        "generate",
        "validate",
        "models",
        "studio",
        "doctor",
        "init",
        "presets",
        "sample",
        "images",
        "package",
        "telemetry",
        "--help",
        "-h",
        "--version",
    }
    if argv[0] in top_level:
        return argv

    return ["generate", *argv]


def _resolve_project_dir(project_dir_arg: str | None, project_dir_opt: str | None) -> str:
    if project_dir_arg and project_dir_opt:
        if Path(project_dir_arg).resolve() != Path(project_dir_opt).resolve():
            raise HackLuminaryError(
                ErrorCode.INVALID_INPUT,
                "Both positional project_dir and --project-dir were provided with different values.",
            )
    return project_dir_opt or project_dir_arg or "."


def _parse_slide_types(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    return [item.strip() for item in raw.split(",") if item.strip()]


def _apply_preset_defaults(
    preset_name: str | None,
    fmt: str | None,
    theme: str | None,
    mode: str | None,
    strict_quality: bool | None,
    requested_slide_types: list[str] | None,
    max_slides: int | None,
) -> tuple[str | None, str | None, str | None, bool | None, list[str] | None, int | None, dict | None]:
    preset = resolve_preset(preset_name)
    if not preset:
        return fmt, theme, mode, strict_quality, requested_slide_types, max_slides, None

    general = preset.get("general", {})
    if fmt is None:
        fmt = general.get("format")
    if theme is None:
        theme = general.get("theme")
    if mode is None:
        mode = general.get("mode")
    if strict_quality is None:
        strict_quality = general.get("strict_quality")
    if not requested_slide_types:
        requested_slide_types = list(preset.get("slides", [])) or None
    if max_slides is None:
        max_slides = preset.get("max_slides")

    return fmt, theme, mode, strict_quality, requested_slide_types, max_slides, preset


def _print_next_step(command: str) -> None:
    click.echo(f"Next: {command}")


def _coverage_bucket(value: float) -> str:
    if value < 0.3:
        return "lt30"
    if value < 0.5:
        return "30-50"
    if value < 0.7:
        return "50-70"
    if value < 0.9:
        return "70-90"
    return "gte90"


def _build_init_config(
    mode: str,
    theme: str,
    preset: str,
    base_branch: str,
    open_after_generate: bool,
    model_alias: str,
) -> str:
    return (
        "[general]\n"
        f"mode = \"{mode}\"\n"
        "format = \"both\"\n"
        f"theme = \"{theme}\"\n"
        "strict_quality = true\n"
        "\n"
        "[git]\n"
        f"base_branch = \"{base_branch}\"\n"
        "include_branch_context = true\n"
        "\n"
        "[ai]\n"
        "enabled = true\n"
        "backend = \"llama.cpp\"\n"
        f"model_alias = \"{model_alias}\"\n"
        "max_tokens = 700\n"
        "top_p = 0.9\n"
        "temperature = 0.2\n"
        "\n"
        "[output]\n"
        f"open_after_generate = {str(bool(open_after_generate)).lower()}\n"
        "\n"
        "[images]\n"
        "enabled = true\n"
        "mode = \"auto\"\n"
        "image_dirs = []\n"
        "max_images_per_slide = 1\n"
        "min_confidence = 0.72\n"
        "visual_style = \"mixed\"\n"
        "\n"
        "[telemetry]\n"
        "enabled = false\n"
        "anonymous = true\n"
        "endpoint = \"\"\n"
        "\n"
        "[studio]\n"
        "enabled = true\n"
        "default_view = \"notebook\"\n"
        "autosave_interval_sec = 20\n"
        "read_only = false\n"
        "\n"
        "[ui]\n"
        "density = \"comfortable\"\n"
        "motion = \"normal\"\n"
        "code_font_scale = 1.0\n"
        "presenter_timer_default_min = 7\n"
        "\n"
        "[features]\n"
        "studio_enabled = true\n"
        "production_theme_enabled = true\n"
        "presenter_pro_enabled = true\n"
        "\n"
        "[privacy]\n"
        "telemetry = false\n"
        "\n"
        "# Recommended workflow preset for your team.\n"
        f"# preset = \"{preset}\"\n"
    )


def _build_overrides(
    fmt: str | None,
    theme: str | None,
    mode: str | None,
    base_branch: str | None,
    no_branch_context: bool,
    strict_quality: bool | None,
    copy_output_dir: str | None,
    auto_open: bool,
    image_mode: str | None,
    image_dirs: tuple[str, ...] | list[str],
    max_images_per_slide: int | None,
    visual_style: str | None,
) -> dict:
    overrides = {
        "general": {
            "format": fmt,
            "theme": theme,
            "mode": mode,
            "strict_quality": strict_quality,
        },
        "git": {
            "base_branch": base_branch,
            "include_branch_context": None if not no_branch_context else False,
        },
        "output": {
            "copy_output_dir": copy_output_dir,
            "open_after_generate": auto_open,
        },
        "images": {
            "mode": image_mode,
            "image_dirs": list(image_dirs),
            "max_images_per_slide": max_images_per_slide,
            "visual_style": visual_style,
        },
    }
    return overrides


def _copy_outputs(
    copy_output_dir: str | None,
    html_path: Path | None,
    md_path: Path | None,
    json_path: Path | None,
    extra_files: list[Path] | None = None,
) -> None:
    if not copy_output_dir:
        return

    target_dir = Path(copy_output_dir).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    files = [html_path, md_path, json_path]
    files.extend(extra_files or [])
    for file_path in files:
        if file_path and file_path.exists():
            shutil.copy2(file_path, target_dir / file_path.name)


@click.group(help="HackLuminary v2 - offline-first, branch-aware presentation generator.")
@click.version_option(version=__version__)
def cli() -> None:
    pass


@cli.command("generate")
@click.argument("project_dir", required=False)
@click.option("--project-dir", "project_dir_opt", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--output", "output", type=click.Path(), default="presentation.html", show_default=True)
@click.option("--format", "fmt", type=click.Choice(["html", "markdown", "json", "both"]), default=None)
@click.option("--preset", type=click.Choice(PRESET_NAMES), default=None, help="Apply audience/workflow defaults.")
@click.option("--slides", type=str, default=None, help="Comma-separated slide ids.")
@click.option("--max-slides", type=click.IntRange(min=1), default=None)
@click.option("--docs", "docs", multiple=True, type=click.Path(), help="Additional docs within project.")
@click.option("--theme", type=click.Choice(["default", "dark", "minimal", "colorful", "auto"]), default=None)
@click.option("--mode", type=click.Choice(["deterministic", "ai", "hybrid"]), default=None)
@click.option("--images", "images_mode", type=click.Choice(["off", "auto", "strict"]), default=None)
@click.option("--image-dirs", "image_dirs", multiple=True, type=click.Path(), help="Project-relative directories to scan for images.")
@click.option("--max-images-per-slide", type=click.IntRange(min=0, max=2), default=None)
@click.option("--visual-style", type=click.Choice(["evidence", "screenshot", "mixed"]), default=None)
@click.option("--base-branch", type=str, default=None)
@click.option("--no-branch-context", is_flag=True, default=False)
@click.option("--strict-quality", "strict_quality", flag_value=True, default=None)
@click.option("--no-strict-quality", "strict_quality", flag_value=False)
@click.option("--open", "auto_open", is_flag=True, default=False)
@click.option("--copy-output-dir", type=click.Path(), default=None)
@click.option("--bundle", is_flag=True, default=False, help="Write notes.md and talk-track.md next to output.")
@click.option("--debug", is_flag=True, default=False)
def generate_command(
    project_dir: str | None,
    project_dir_opt: str | None,
    output: str,
    fmt: str | None,
    preset: str | None,
    slides: str | None,
    max_slides: int | None,
    docs: tuple[str, ...],
    theme: str | None,
    mode: str | None,
    images_mode: str | None,
    image_dirs: tuple[str, ...],
    max_images_per_slide: int | None,
    visual_style: str | None,
    base_branch: str | None,
    no_branch_context: bool,
    strict_quality: bool | None,
    auto_open: bool,
    copy_output_dir: str | None,
    bundle: bool,
    debug: bool,
) -> None:
    """Generate presentation outputs for a project directory."""

    project = _resolve_project_dir(project_dir, project_dir_opt)
    requested_slide_types = _parse_slide_types(slides)
    fmt, theme, mode, strict_quality, requested_slide_types, max_slides, preset_data = _apply_preset_defaults(
        preset_name=preset,
        fmt=fmt,
        theme=theme,
        mode=mode,
        strict_quality=strict_quality,
        requested_slide_types=requested_slide_types,
        max_slides=max_slides,
    )
    overrides = _build_overrides(
        fmt=fmt,
        theme=theme,
        mode=mode,
        base_branch=base_branch,
        no_branch_context=no_branch_context,
        strict_quality=strict_quality,
        copy_output_dir=copy_output_dir,
        auto_open=auto_open,
        image_mode=images_mode,
        image_dirs=image_dirs,
        max_images_per_slide=max_images_per_slide,
        visual_style=visual_style,
    )

    started_at = time.perf_counter()
    result = run_generation(
        project_dir=project,
        additional_docs=list(docs),
        requested_slide_types=requested_slide_types,
        max_slides=max_slides,
        cli_overrides=overrides,
    )
    elapsed = time.perf_counter() - started_at

    payload = result["payload"]
    resolved_fmt = result["config"]["general"]["format"]

    if debug:
        click.echo(json.dumps(payload, indent=2))

    output_path = Path(output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    html_path: Path | None = None
    md_path: Path | None = None
    json_path: Path | None = None

    if resolved_fmt in {"html", "both"}:
        html_path = output_path if resolved_fmt == "html" else output_path.with_suffix(".html")
        html_path.write_text(result["html"], encoding="utf-8")
        click.echo(f"HTML presentation: {html_path}")

    if resolved_fmt in {"markdown", "both"}:
        md_path = output_path if resolved_fmt == "markdown" else output_path.with_suffix(".md")
        md_path.write_text(result["markdown"], encoding="utf-8")
        click.echo(f"Markdown presentation: {md_path}")

    if resolved_fmt == "json":
        json_path = output_path if output_path.suffix == ".json" else output_path.with_suffix(".json")
        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        click.echo(json.dumps(payload, indent=2))
        click.echo(f"JSON payload: {json_path}")

    artifact_paths = [path for path in [html_path, md_path, json_path] if path]

    bundle_paths = {}
    if bundle:
        bundle_paths = write_bundle_artifacts(output_path, payload.get("slides", []))
        click.echo(f"Notes: {bundle_paths['notes']}")
        click.echo(f"Talk track: {bundle_paths['talk_track']}")
        artifact_paths.append(Path(bundle_paths["notes"]))
        artifact_paths.append(Path(bundle_paths["talk_track"]))
        manifest_path = write_manifest(
            bundle_dir=output_path.resolve().parent,
            artifact_paths=[Path(path) for path in artifact_paths],
            payload=payload,
        )
        artifact_paths.append(manifest_path)
        click.echo(f"Manifest: {manifest_path}")

    extra_bundle_files: list[Path] = []
    if bundle_paths:
        extra_bundle_files.extend([Path(bundle_paths["notes"]), Path(bundle_paths["talk_track"])])
        manifest = output_path.resolve().parent / "manifest.json"
        if manifest.exists():
            extra_bundle_files.append(manifest)

    _copy_outputs(
        copy_output_dir or result["config"]["output"].get("copy_output_dir"),
        html_path,
        md_path,
        json_path,
        extra_files=extra_bundle_files,
    )

    for warning in result.get("warnings", []):
        click.echo(f"Warning: {warning}", err=True)

    if auto_open and html_path and html_path.exists():
        webbrowser.open(str(html_path))

    if preset_data:
        click.echo(f"Preset applied: {preset} - {preset_data.get('description', '').strip()}")

    quality_metrics = payload.get("quality_report", {}).get("metrics", {})
    image_coverage = float(quality_metrics.get("image_coverage", 0.0) or 0.0)
    write_telemetry_event(
        project_root=Path(project),
        config=result["config"],
        event="generate",
        payload={
            "command": "generate",
            "status": "success",
            "duration_bucket": duration_bucket(elapsed),
            "preset": preset or "",
            "image_mode": result["config"].get("images", {}).get("mode", "off"),
            "image_coverage_bucket": _coverage_bucket(image_coverage),
        },
    )

    _print_next_step(f"hackluminary validate {project} --mode {result['config']['general']['mode']}")
    _print_next_step(f"hackluminary studio {project}")


@cli.command("validate")
@click.argument("project_dir", required=False)
@click.option("--project-dir", "project_dir_opt", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--preset", type=click.Choice(PRESET_NAMES), default=None)
@click.option("--slides", type=str, default=None)
@click.option("--max-slides", type=click.IntRange(min=1), default=None)
@click.option("--docs", "docs", multiple=True, type=click.Path())
@click.option("--mode", type=click.Choice(["deterministic", "ai", "hybrid"]), default=None)
@click.option("--images", "images_mode", type=click.Choice(["off", "auto", "strict"]), default=None)
@click.option("--image-dirs", "image_dirs", multiple=True, type=click.Path())
@click.option("--max-images-per-slide", type=click.IntRange(min=0, max=2), default=None)
@click.option("--visual-style", type=click.Choice(["evidence", "screenshot", "mixed"]), default=None)
@click.option("--base-branch", type=str, default=None)
@click.option("--no-branch-context", is_flag=True, default=False)
@click.option("--strict-quality", "strict_quality", flag_value=True, default=None)
@click.option("--no-strict-quality", "strict_quality", flag_value=False)
@click.option("--debug", is_flag=True, default=False)
def validate_command(
    project_dir: str | None,
    project_dir_opt: str | None,
    preset: str | None,
    slides: str | None,
    max_slides: int | None,
    docs: tuple[str, ...],
    mode: str | None,
    images_mode: str | None,
    image_dirs: tuple[str, ...],
    max_images_per_slide: int | None,
    visual_style: str | None,
    base_branch: str | None,
    no_branch_context: bool,
    strict_quality: bool | None,
    debug: bool,
) -> None:
    """Run analyzers and quality gates without writing outputs."""

    project = _resolve_project_dir(project_dir, project_dir_opt)
    requested_slide_types = _parse_slide_types(slides)
    _, _, mode, strict_quality, requested_slide_types, max_slides, preset_data = _apply_preset_defaults(
        preset_name=preset,
        fmt=None,
        theme=None,
        mode=mode,
        strict_quality=strict_quality,
        requested_slide_types=requested_slide_types,
        max_slides=max_slides,
    )

    overrides = {
        "general": {
            "mode": mode,
            "strict_quality": strict_quality,
            "format": "json",
        },
        "git": {
            "base_branch": base_branch,
            "include_branch_context": None if not no_branch_context else False,
        },
        "images": {
            "mode": images_mode,
            "image_dirs": list(image_dirs),
            "max_images_per_slide": max_images_per_slide,
            "visual_style": visual_style,
        },
    }

    started_at = time.perf_counter()
    report = run_validation(
        project_dir=project,
        additional_docs=list(docs),
        requested_slide_types=requested_slide_types,
        max_slides=max_slides,
        cli_overrides=overrides,
    )
    elapsed = time.perf_counter() - started_at

    click.echo(f"Status: {report['status']}")
    click.echo(f"Slides: {report['slide_count']}")
    click.echo(f"Evidence entries: {report['evidence_count']}")
    click.echo(f"Media entries: {report.get('media_count', 0)}")

    if report["warnings"]:
        for warning in report["warnings"]:
            click.echo(f"Warning: {warning}", err=True)

    if report["errors"]:
        for err in report["errors"]:
            click.echo(f"Error: {err}", err=True)
        write_telemetry_event(
            project_root=Path(project),
            config=report.get("config", {}),
            event="validate",
            payload={
                "command": "validate",
                "status": "fail",
                "duration_bucket": duration_bucket(elapsed),
                "preset": preset or "",
                "image_mode": overrides["images"].get("mode") or "off",
                "image_coverage_bucket": _coverage_bucket(float(report["metrics"].get("image_coverage", 0.0) or 0.0)),
                "error_code": str(ErrorCode.QUALITY_GATE_FAILED),
            },
        )
        raise SystemExit(1)

    if debug:
        click.echo(json.dumps(report, indent=2))

    if preset_data:
        click.echo(f"Preset applied: {preset} - {preset_data.get('description', '').strip()}")

    write_telemetry_event(
        project_root=Path(project),
        config=report.get("config", {}),
        event="validate",
        payload={
            "command": "validate",
            "status": report["status"],
            "duration_bucket": duration_bucket(elapsed),
            "preset": preset or "",
            "image_mode": overrides["images"].get("mode") or "off",
            "image_coverage_bucket": _coverage_bucket(float(report["metrics"].get("image_coverage", 0.0) or 0.0)),
        },
    )

    _print_next_step(f"hackluminary generate {project} --preset {preset or 'demo-day'}")


@cli.group("models")
def models_group() -> None:
    """Manage local AI model artifacts."""


@models_group.command("list")
def models_list_command() -> None:
    rows = list_models()
    for row in rows:
        status = "installed" if row["installed"] else "missing"
        path = row["path"] or "-"
        click.echo(f"{row['alias']}: {status} | license={row['license']} | path={path}")


@models_group.command("install")
@click.argument("alias")
@click.option("--force", is_flag=True, default=False)
def models_install_command(alias: str, force: bool) -> None:
    path = install_model(alias, force=force)
    click.echo(f"Installed {alias} -> {path}")


@cli.command("presets")
def presets_command() -> None:
    """List built-in workflow presets."""

    for name, desc in list_presets():
        click.echo(f"{name}: {desc}")


@cli.command("doctor")
@click.argument("project_dir", required=False)
@click.option("--project-dir", "project_dir_opt", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--strict", is_flag=True, default=False, help="Exit nonzero when any warning or failure is present.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Print machine-readable check report.")
def doctor_command(project_dir: str | None, project_dir_opt: str | None, strict: bool, as_json: bool) -> None:
    """Check local setup, project health, and model readiness."""

    project = Path(_resolve_project_dir(project_dir, project_dir_opt)).resolve()
    report = run_doctor(project)

    if as_json:
        click.echo(json.dumps(report, indent=2))
    else:
        for check in report["checks"]:
            status = check["status"].upper()
            click.echo(f"[{status}] {check['id']}: {check['message']}")
            if check.get("hint"):
                click.echo(f"  Hint: {check['hint']}")

        summary = report["summary"]
        click.echo(
            "Summary: "
            f"{summary['passed']} passed, {summary['warnings']} warnings, {summary['failed']} failed "
            f"({summary['total']} total)"
        )

    summary = report["summary"]
    if strict and (summary["warnings"] > 0 or summary["failed"] > 0):
        raise SystemExit(1)
    if not strict and summary["failed"] > 0:
        raise SystemExit(1)

    if not as_json:
        _print_next_step(f"hackluminary init {project}")


@cli.command("init")
@click.argument("project_dir", required=False)
@click.option("--project-dir", "project_dir_opt", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--preset", type=click.Choice(PRESET_NAMES), default=None)
@click.option("--force", is_flag=True, default=False, help="Overwrite existing project config.")
@click.option("--non-interactive", is_flag=True, default=False, help="Write config using defaults.")
def init_command(
    project_dir: str | None,
    project_dir_opt: str | None,
    preset: str | None,
    force: bool,
    non_interactive: bool,
) -> None:
    """Create project config with sensible defaults for fast onboarding."""

    project = Path(_resolve_project_dir(project_dir, project_dir_opt)).resolve()
    project.mkdir(parents=True, exist_ok=True)
    config_path = get_project_config_path(project)

    if config_path.exists() and not force:
        raise HackLuminaryError(
            ErrorCode.INVALID_INPUT,
            f"Config already exists: {config_path}",
            hint="Use --force to overwrite.",
        )

    default_preset = preset or "demo-day"
    preset_data = resolve_preset(default_preset) or {}
    preset_general = preset_data.get("general", {})

    if non_interactive:
        selected_preset = default_preset
        mode = preset_general.get("mode", "hybrid")
        theme = preset_general.get("theme", "default")
        base_branch = "main"
        open_after_generate = True
        model_alias = "qwen2.5-3b-instruct-q4_k_m"
    else:
        selected_preset = click.prompt(
            "Select preset",
            type=click.Choice(PRESET_NAMES),
            default=default_preset,
            show_choices=True,
        )
        selected_data = resolve_preset(selected_preset) or {}
        selected_general = selected_data.get("general", {})

        mode = click.prompt(
            "Generation mode",
            type=click.Choice(["deterministic", "hybrid", "ai"]),
            default=selected_general.get("mode", "hybrid"),
            show_choices=True,
        )
        theme = click.prompt(
            "Theme",
            type=click.Choice(["default", "dark", "minimal", "colorful"]),
            default=selected_general.get("theme", "default"),
            show_choices=True,
        )
        base_branch = click.prompt("Base branch", default="main")
        open_after_generate = click.confirm("Open generated HTML automatically?", default=True)
        model_alias = click.prompt(
            "Model alias",
            default="qwen2.5-3b-instruct-q4_k_m",
            show_default=True,
        )

    rendered = _build_init_config(
        mode=mode,
        theme=theme,
        preset=selected_preset,
        base_branch=base_branch,
        open_after_generate=open_after_generate,
        model_alias=model_alias,
    )
    config_path.write_text(rendered, encoding="utf-8")

    click.echo(f"Created config: {config_path}")
    _print_next_step(f"hackluminary doctor {project}")
    _print_next_step(f"hackluminary generate {project} --preset {selected_preset}")


@cli.command("sample")
@click.argument("target_dir", required=False)
@click.option("--force", is_flag=True, default=False, help="Overwrite existing files in target directory.")
def sample_command(target_dir: str | None, force: bool) -> None:
    """Create a runnable sample project for first-time users."""

    root = Path(target_dir or "hackluminary-sample").resolve()
    root.mkdir(parents=True, exist_ok=True)

    files = {
        "README.md": (
            "# HackLuminary Sample\n\n"
            "## Problem\n"
            "Hackathon teams run out of time creating coherent demo decks.\n\n"
            "## Solution\n"
            "Generate evidence-grounded decks directly from the repository.\n\n"
            "## Features\n"
            "- Offline generation\n"
            "- Branch delta slides\n"
            "- Studio drafting\n"
        ),
        "main.py": "def main():\n    print('HackLuminary sample app')\n\n\nif __name__ == '__main__':\n    main()\n",
        "hackluminary.toml": _build_init_config(
            mode="deterministic",
            theme="default",
            preset="quick",
            base_branch="main",
            open_after_generate=False,
            model_alias="qwen2.5-3b-instruct-q4_k_m",
        ),
    }

    for relative, content in files.items():
        path = root / relative
        if path.exists() and not force:
            raise HackLuminaryError(
                ErrorCode.INVALID_INPUT,
                f"File already exists: {path}",
                hint="Use --force to overwrite sample files.",
            )
        path.write_text(content, encoding="utf-8")

    click.echo(f"Created sample project: {root}")
    _print_next_step(f"hackluminary doctor {root}")
    _print_next_step(f"hackluminary generate {root} --preset quick")
    _print_next_step(f"hackluminary studio {root}")


@cli.group("images")
def images_group() -> None:
    """Image indexing and coverage diagnostics."""


@images_group.command("scan")
@click.argument("project_dir", required=False)
@click.option("--project-dir", "project_dir_opt", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--images", "images_mode", type=click.Choice(["off", "auto", "strict"]), default=None)
@click.option("--image-dirs", "image_dirs", multiple=True, type=click.Path())
@click.option("--max-images-per-slide", type=click.IntRange(min=0, max=2), default=None)
@click.option("--visual-style", type=click.Choice(["evidence", "screenshot", "mixed"]), default=None)
@click.option("--json", "as_json", is_flag=True, default=False)
def images_scan_command(
    project_dir: str | None,
    project_dir_opt: str | None,
    images_mode: str | None,
    image_dirs: tuple[str, ...],
    max_images_per_slide: int | None,
    visual_style: str | None,
    as_json: bool,
) -> None:
    """Scan local images and print index summary."""

    project = Path(_resolve_project_dir(project_dir, project_dir_opt)).resolve()
    overrides = {
        "images": {
            "mode": images_mode,
            "image_dirs": list(image_dirs),
            "max_images_per_slide": max_images_per_slide,
            "visual_style": visual_style,
        }
    }
    config = load_resolved_config(project, cli_overrides=overrides)
    image_cfg = config.get("images", {})
    indexed = index_project_images(
        project_root=project,
        image_dirs=list(image_cfg.get("image_dirs", [])),
        allowed_extensions=list(image_cfg.get("allowed_extensions", [])),
        max_image_bytes=int(image_cfg.get("max_image_bytes", 3_145_728)),
    )

    if as_json:
        click.echo(json.dumps(indexed, indent=2))
        return

    summary = indexed.get("summary", {})
    click.echo(f"Indexed images: {summary.get('count', 0)}")
    by_kind = summary.get("by_kind", {})
    click.echo(
        "Kinds: "
        f"repo_image={by_kind.get('repo_image', 0)}, "
        f"doc_image={by_kind.get('doc_image', 0)}, "
        f"generated_screenshot={by_kind.get('generated_screenshot', 0)}"
    )
    for warning in indexed.get("warnings", []):
        click.echo(f"Warning: {warning}", err=True)


@images_group.command("report")
@click.argument("project_dir", required=False)
@click.option("--project-dir", "project_dir_opt", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--images", "images_mode", type=click.Choice(["off", "auto", "strict"]), default=None)
@click.option("--image-dirs", "image_dirs", multiple=True, type=click.Path())
@click.option("--max-images-per-slide", type=click.IntRange(min=0, max=2), default=None)
@click.option("--visual-style", type=click.Choice(["evidence", "screenshot", "mixed"]), default=None)
@click.option("--json", "as_json", is_flag=True, default=False)
def images_report_command(
    project_dir: str | None,
    project_dir_opt: str | None,
    images_mode: str | None,
    image_dirs: tuple[str, ...],
    max_images_per_slide: int | None,
    visual_style: str | None,
    as_json: bool,
) -> None:
    """Report visual coverage/confidence from generation quality metrics."""

    project = _resolve_project_dir(project_dir, project_dir_opt)
    overrides = {
        "general": {
            "mode": "deterministic",
            "format": "json",
            "strict_quality": False,
        },
        "images": {
            "mode": images_mode or "auto",
            "image_dirs": list(image_dirs),
            "max_images_per_slide": max_images_per_slide,
            "visual_style": visual_style,
        },
    }
    result = run_generation(project_dir=project, cli_overrides=overrides)
    payload = result["payload"]
    metrics = payload.get("quality_report", {}).get("metrics", {})
    report = {
        "schema_version": payload.get("schema_version"),
        "image_mode": result["config"].get("images", {}).get("mode", "off"),
        "image_coverage": metrics.get("image_coverage", 0.0),
        "visual_confidence_mean": metrics.get("visual_confidence_mean", 0.0),
        "slides_without_visual": metrics.get("slides_without_visual", []),
        "media_count": len(payload.get("media_catalog", [])),
        "slide_count": len(payload.get("slides", [])),
        "warnings": result.get("warnings", []),
    }

    if as_json:
        click.echo(json.dumps(report, indent=2))
    else:
        click.echo(f"Image mode: {report['image_mode']}")
        click.echo(f"Coverage: {report['image_coverage']:.2f}")
        click.echo(f"Mean confidence: {report['visual_confidence_mean']:.2f}")
        click.echo(f"Media catalog size: {report['media_count']}")
        missing = report["slides_without_visual"]
        if missing:
            click.echo("Slides without visuals: " + ", ".join(str(item) for item in missing))


@images_group.command("benchmark")
@click.argument("corpus_dir", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--max-projects", type=click.IntRange(min=1), default=12, show_default=True)
@click.option("--json", "as_json", is_flag=True, default=False)
def images_benchmark_command(corpus_dir: str, max_projects: int, as_json: bool) -> None:
    """Benchmark visual coverage across a local corpus and suggest confidence tuning."""

    result = benchmark_visual_coverage(Path(corpus_dir), max_projects=max_projects)
    if as_json:
        click.echo(json.dumps(result, indent=2))
        return

    click.echo(f"Corpus: {result['corpus_dir']}")
    click.echo(f"Projects considered: {result['project_count']}")
    for row in result.get("runs", []):
        click.echo(
            f"- min_conf={row['min_confidence']:.2f} "
            f"avg_coverage={row['avg_coverage']:.2f} "
            f"coverage>=0.70={row['coverage_ge_0_7']}/{row['coverage_samples']} "
            f"failures={row['failures']}"
        )
    click.echo(f"Recommended min_confidence: {result.get('recommended_min_confidence')}")
    click.echo(f"Elapsed: {result['elapsed_sec']}s")


@cli.group("package")
def package_group() -> None:
    """Package outputs for hackathon submission workflows."""


@package_group.command("devpost")
@click.argument("project_dir", required=False)
@click.option("--project-dir", "project_dir_opt", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--output", "output", type=click.Path(), default="devpost-package.zip", show_default=True)
@click.option("--preset", type=click.Choice(PRESET_NAMES), default="demo-day")
def package_devpost_command(project_dir: str | None, project_dir_opt: str | None, output: str, preset: str) -> None:
    """Create a Devpost-ready zip with deck, notes, talk track, screenshots, and summary."""

    project = Path(_resolve_project_dir(project_dir, project_dir_opt)).resolve()
    output_path = Path(output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    bundle_base = output_path.with_suffix("")

    requested_slide_types = None
    max_slides = None
    _, _, mode, strict_quality, requested_slide_types, max_slides, _preset_data = _apply_preset_defaults(
        preset_name=preset,
        fmt="both",
        theme=None,
        mode=None,
        strict_quality=None,
        requested_slide_types=requested_slide_types,
        max_slides=max_slides,
    )

    overrides = {
        "general": {
            "format": "both",
            "mode": mode,
            "strict_quality": strict_quality,
        },
        "images": {
            "mode": "auto",
        },
    }

    try:
        result = run_generation(
            project_dir=project,
            requested_slide_types=requested_slide_types,
            max_slides=max_slides,
            cli_overrides=overrides,
        )
    except HackLuminaryError as exc:
        if exc.code != ErrorCode.MODEL_NOT_AVAILABLE:
            raise
        # Keep packaging one-shot reliable on fresh laptops without local model install.
        overrides["general"]["mode"] = "deterministic"
        result = run_generation(
            project_dir=project,
            requested_slide_types=requested_slide_types,
            max_slides=max_slides,
            cli_overrides=overrides,
        )
    payload = result["payload"]

    html_path = bundle_base.with_suffix(".html")
    md_path = bundle_base.with_suffix(".md")
    json_path = bundle_base.with_suffix(".json")
    html_path.write_text(result["html"] or "", encoding="utf-8")
    md_path.write_text(result["markdown"] or "", encoding="utf-8")
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    bundle_paths = write_bundle_artifacts(bundle_base, payload.get("slides", []))
    manifest_path = write_manifest(
        bundle_dir=bundle_base.parent,
        artifact_paths=[html_path, md_path, json_path, Path(bundle_paths["notes"]), Path(bundle_paths["talk_track"])],
        payload=payload,
    )

    zip_path = build_devpost_package(
        project_root=project,
        output_zip=output_path,
        payload=payload,
        artifact_paths=[html_path, md_path, json_path, Path(bundle_paths["notes"]), Path(bundle_paths["talk_track"]), manifest_path],
    )
    click.echo(f"Devpost package: {zip_path}")
    write_telemetry_event(
        project_root=project,
        config=result.get("config", {}),
        event="package_devpost",
        payload={
            "command": "package_devpost",
            "status": "success",
            "preset": preset,
            "image_mode": result.get("config", {}).get("images", {}).get("mode", "off"),
            "image_coverage_bucket": _coverage_bucket(
                float(payload.get("quality_report", {}).get("metrics", {}).get("image_coverage", 0.0) or 0.0)
            ),
        },
    )
    _print_next_step(f"unzip -l {zip_path}")


@cli.group("telemetry")
def telemetry_group() -> None:
    """Opt-in anonymous telemetry controls."""


@telemetry_group.command("enable")
@click.argument("project_dir", required=False)
@click.option("--project-dir", "project_dir_opt", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--endpoint", required=True, type=str, help="Telemetry endpoint URL.")
def telemetry_enable_command(project_dir: str | None, project_dir_opt: str | None, endpoint: str) -> None:
    """Enable opt-in telemetry in project config."""

    project = Path(_resolve_project_dir(project_dir, project_dir_opt)).resolve()
    path = enable_telemetry_in_project_config(project, endpoint=endpoint)
    click.echo(f"Telemetry enabled in: {path}")
    _print_next_step(f"hackluminary doctor {project}")


@telemetry_group.command("disable")
@click.argument("project_dir", required=False)
@click.option("--project-dir", "project_dir_opt", type=click.Path(exists=True, file_okay=False, dir_okay=True))
def telemetry_disable_command(project_dir: str | None, project_dir_opt: str | None) -> None:
    """Disable telemetry in project config."""

    project = Path(_resolve_project_dir(project_dir, project_dir_opt)).resolve()
    path = disable_telemetry_in_project_config(project)
    click.echo(f"Telemetry disabled in: {path}")


@telemetry_group.command("status")
@click.argument("project_dir", required=False)
@click.option("--project-dir", "project_dir_opt", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--json", "as_json", is_flag=True, default=False)
def telemetry_status_command(project_dir: str | None, project_dir_opt: str | None, as_json: bool) -> None:
    """Show telemetry settings and queued local events."""

    project = Path(_resolve_project_dir(project_dir, project_dir_opt)).resolve()
    config = load_resolved_config(project)
    status = telemetry_status(project, config)
    if as_json:
        click.echo(json.dumps(status, indent=2))
        return
    click.echo(f"Enabled: {status['enabled']}")
    click.echo(f"Anonymous: {status['anonymous']}")
    click.echo(f"Endpoint: {status['endpoint'] or '(none)'}")
    click.echo(f"Queued events: {status['queued_events']}")
    click.echo(f"Events file: {status['events_file']}")


@telemetry_group.command("flush")
@click.argument("project_dir", required=False)
@click.option("--project-dir", "project_dir_opt", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--max-events", type=click.IntRange(min=1), default=200, show_default=True)
@click.option("--timeout-sec", type=float, default=4.0, show_default=True)
@click.option("--dry-run", is_flag=True, default=False)
@click.option("--json", "as_json", is_flag=True, default=False)
def telemetry_flush_command(
    project_dir: str | None,
    project_dir_opt: str | None,
    max_events: int,
    timeout_sec: float,
    dry_run: bool,
    as_json: bool,
) -> None:
    """Flush queued telemetry events to configured endpoint."""

    project = Path(_resolve_project_dir(project_dir, project_dir_opt)).resolve()
    config = load_resolved_config(project)
    result = flush_telemetry_events(
        project_root=project,
        config=config,
        max_events=max_events,
        timeout_sec=timeout_sec,
        dry_run=dry_run,
    )
    if as_json:
        click.echo(json.dumps(result, indent=2))
        return
    click.echo(f"Status: {result.get('status')}")
    click.echo(f"Sent: {result.get('sent', 0)}")
    if "would_send" in result:
        click.echo(f"Would send: {result.get('would_send', 0)}")
    click.echo(f"Remaining: {result.get('remaining', 0)}")
    if result.get("endpoint"):
        click.echo(f"Endpoint: {result['endpoint']}")
    if result.get("error"):
        click.echo(f"Error: {result['error']}", err=True)
        raise SystemExit(1)
    if result.get("status") in {"http-error", "network-error"}:
        raise SystemExit(1)


@cli.command("studio")
@click.argument("project_dir", required=False)
@click.option("--project-dir", "project_dir_opt", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--base-branch", type=str, default=None)
@click.option("--theme", type=click.Choice(["default", "dark", "minimal", "colorful", "auto"]), default=None)
@click.option("--port", type=int, default=None)
@click.option("--read-only", is_flag=True, default=False)
@click.option("--debug", is_flag=True, default=False)
def studio_command(
    project_dir: str | None,
    project_dir_opt: str | None,
    base_branch: str | None,
    theme: str | None,
    port: int | None,
    read_only: bool,
    debug: bool,
) -> None:
    """Run local Notebook-style Studio workspace."""

    project = _resolve_project_dir(project_dir, project_dir_opt)
    overrides = {
        "general": {
            "theme": theme,
            "format": "json",
            "mode": "deterministic",
        },
        "git": {
            "base_branch": base_branch,
        },
        "studio": {
            "read_only": read_only,
            "port": port if port is not None else 0,
        },
    }

    run_studio_server(
        project_path=project,
        cli_overrides=overrides,
        port=port or 0,
        read_only=read_only,
        auto_open=True,
        debug=debug,
    )


def main() -> None:
    """Entry point used by console script."""

    raw_argv = sys.argv[1:]
    argv = _normalize_legacy_args(raw_argv)
    debug = "--debug" in argv

    try:
        cli.main(args=argv, prog_name="hackluminary", standalone_mode=False)
    except HackLuminaryError as exc:
        click.echo(str(exc), err=True)
        if debug:
            traceback.print_exc()
        raise SystemExit(1)
    except click.ClickException as exc:
        exc.show()
        raise SystemExit(exc.exit_code)
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        click.echo(f"[{ErrorCode.RUNTIME_ERROR}] Unexpected failure: {exc}", err=True)
        if debug:
            traceback.print_exc()
        raise SystemExit(1)


if __name__ == "__main__":
    main()
