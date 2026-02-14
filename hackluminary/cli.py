"""HackLuminary v2 CLI."""

from __future__ import annotations

import json
import shutil
import sys
import traceback
import webbrowser
from pathlib import Path

import click

from . import __version__
from .errors import ErrorCode, HackLuminaryError
from .models import install_model, list_models
from .pipeline import run_generation, run_validation
from .studio_server import run_studio_server


def _normalize_legacy_args(argv: list[str]) -> list[str]:
    """Support old top-level usage by rewriting it to `generate ...`."""

    if not argv:
        return ["generate"]

    top_level = {"generate", "validate", "models", "studio", "--help", "-h", "--version"}
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


def _build_overrides(
    fmt: str | None,
    theme: str | None,
    mode: str | None,
    base_branch: str | None,
    no_branch_context: bool,
    strict_quality: bool | None,
    copy_output_dir: str | None,
    auto_open: bool,
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
    }
    return overrides


def _copy_outputs(copy_output_dir: str | None, html_path: Path | None, md_path: Path | None, json_path: Path | None) -> None:
    if not copy_output_dir:
        return

    target_dir = Path(copy_output_dir).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    for file_path in [html_path, md_path, json_path]:
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
@click.option("--slides", type=str, default=None, help="Comma-separated slide ids.")
@click.option("--max-slides", type=click.IntRange(min=1), default=None)
@click.option("--docs", "docs", multiple=True, type=click.Path(), help="Additional docs within project.")
@click.option("--theme", type=click.Choice(["default", "dark", "minimal", "colorful", "auto"]), default=None)
@click.option("--mode", type=click.Choice(["deterministic", "ai", "hybrid"]), default=None)
@click.option("--base-branch", type=str, default=None)
@click.option("--no-branch-context", is_flag=True, default=False)
@click.option("--strict-quality", "strict_quality", flag_value=True, default=None)
@click.option("--no-strict-quality", "strict_quality", flag_value=False)
@click.option("--open", "auto_open", is_flag=True, default=False)
@click.option("--copy-output-dir", type=click.Path(), default=None)
@click.option("--debug", is_flag=True, default=False)
def generate_command(
    project_dir: str | None,
    project_dir_opt: str | None,
    output: str,
    fmt: str | None,
    slides: str | None,
    max_slides: int | None,
    docs: tuple[str, ...],
    theme: str | None,
    mode: str | None,
    base_branch: str | None,
    no_branch_context: bool,
    strict_quality: bool | None,
    auto_open: bool,
    copy_output_dir: str | None,
    debug: bool,
) -> None:
    """Generate presentation outputs for a project directory."""

    project = _resolve_project_dir(project_dir, project_dir_opt)
    requested_slide_types = _parse_slide_types(slides)
    overrides = _build_overrides(
        fmt=fmt,
        theme=theme,
        mode=mode,
        base_branch=base_branch,
        no_branch_context=no_branch_context,
        strict_quality=strict_quality,
        copy_output_dir=copy_output_dir,
        auto_open=auto_open,
    )

    result = run_generation(
        project_dir=project,
        additional_docs=list(docs),
        requested_slide_types=requested_slide_types,
        max_slides=max_slides,
        cli_overrides=overrides,
    )

    payload = result["payload"]
    resolved_fmt = result["config"]["general"]["format"]

    if debug:
        click.echo(json.dumps(payload, indent=2))

    output_path = Path(output).resolve()
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

    _copy_outputs(copy_output_dir or result["config"]["output"].get("copy_output_dir"), html_path, md_path, json_path)

    for warning in result.get("warnings", []):
        click.echo(f"Warning: {warning}", err=True)

    if auto_open and html_path and html_path.exists():
        webbrowser.open(str(html_path))


@cli.command("validate")
@click.argument("project_dir", required=False)
@click.option("--project-dir", "project_dir_opt", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--slides", type=str, default=None)
@click.option("--max-slides", type=click.IntRange(min=1), default=None)
@click.option("--docs", "docs", multiple=True, type=click.Path())
@click.option("--mode", type=click.Choice(["deterministic", "ai", "hybrid"]), default=None)
@click.option("--base-branch", type=str, default=None)
@click.option("--no-branch-context", is_flag=True, default=False)
@click.option("--strict-quality", "strict_quality", flag_value=True, default=None)
@click.option("--no-strict-quality", "strict_quality", flag_value=False)
@click.option("--debug", is_flag=True, default=False)
def validate_command(
    project_dir: str | None,
    project_dir_opt: str | None,
    slides: str | None,
    max_slides: int | None,
    docs: tuple[str, ...],
    mode: str | None,
    base_branch: str | None,
    no_branch_context: bool,
    strict_quality: bool | None,
    debug: bool,
) -> None:
    """Run analyzers and quality gates without writing outputs."""

    project = _resolve_project_dir(project_dir, project_dir_opt)
    requested_slide_types = _parse_slide_types(slides)

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
    }

    report = run_validation(
        project_dir=project,
        additional_docs=list(docs),
        requested_slide_types=requested_slide_types,
        max_slides=max_slides,
        cli_overrides=overrides,
    )

    click.echo(f"Status: {report['status']}")
    click.echo(f"Slides: {report['slide_count']}")
    click.echo(f"Evidence entries: {report['evidence_count']}")

    if report["warnings"]:
        for warning in report["warnings"]:
            click.echo(f"Warning: {warning}", err=True)

    if report["errors"]:
        for err in report["errors"]:
            click.echo(f"Error: {err}", err=True)
        raise SystemExit(1)

    if debug:
        click.echo(json.dumps(report, indent=2))


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
