"""CLI contract and backward compatibility tests."""

import base64
import json

from click.testing import CliRunner

from hackluminary.cli import _normalize_legacy_args, cli


def _make_project(tmp_path):
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "README.md").write_text(
        """
# Demo Project

## Problem
Pitch prep is slow.

## Solution
Automate evidence-based slides.

## Features
- Offline mode
""".strip(),
        encoding="utf-8",
    )
    (tmp_path / "main.py").write_text("print('hello')\n", encoding="utf-8")


def test_generate_json_output(tmp_path):
    _make_project(tmp_path)
    output_path = tmp_path / "deck.json"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "generate",
            str(tmp_path),
            "--mode",
            "deterministic",
            "--format",
            "json",
            "--output",
            str(output_path),
            "--preset",
            "quick",
        ],
    )

    assert result.exit_code == 0, result.output
    assert output_path.exists()

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "2.2"
    assert "git_context" in payload
    assert "slides" in payload
    assert "media_catalog" in payload
    assert "claims" in payload["slides"][0]
    assert "Preset applied: quick" in result.output


def test_validate_command(tmp_path):
    _make_project(tmp_path)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["validate", str(tmp_path), "--mode", "deterministic"],
    )

    assert result.exit_code == 0, result.output
    assert "Status: pass" in result.output


def test_generate_bundle_writes_notes_and_talk_track(tmp_path):
    _make_project(tmp_path)
    output_path = tmp_path / "deck"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "generate",
            str(tmp_path),
            "--mode",
            "deterministic",
            "--format",
            "html",
            "--output",
            str(output_path),
            "--bundle",
        ],
    )

    assert result.exit_code == 0, result.output
    assert (tmp_path / "notes.md").exists()
    assert (tmp_path / "talk-track.md").exists()
    assert (tmp_path / "manifest.json").exists()


def test_legacy_args_are_rewritten_to_generate():
    assert _normalize_legacy_args([".", "--format", "json"]) == ["generate", ".", "--format", "json"]
    assert _normalize_legacy_args(["generate", "."]) == ["generate", "."]


def test_models_list_command():
    runner = CliRunner()
    result = runner.invoke(cli, ["models", "list"])

    assert result.exit_code == 0
    assert "qwen2.5-3b-instruct-q4_k_m" in result.output


def test_generate_help_lists_documented_options():
    runner = CliRunner()
    result = runner.invoke(cli, ["generate", "--help"])

    assert result.exit_code == 0
    assert "--slides" in result.output
    assert "--max-slides" in result.output
    assert "--copy-output-dir" in result.output
    assert "--preset" in result.output
    assert "--bundle" in result.output
    assert "--images" in result.output
    assert "--image-dirs" in result.output
    assert "--visual-style" in result.output


def test_studio_help_lists_options():
    runner = CliRunner()
    result = runner.invoke(cli, ["studio", "--help"])

    assert result.exit_code == 0
    assert "--base-branch" in result.output
    assert "--port" in result.output


def test_presets_command_lists_known_profiles():
    runner = CliRunner()
    result = runner.invoke(cli, ["presets"])
    assert result.exit_code == 0
    assert "quick" in result.output
    assert "demo-day" in result.output
    assert "investor" in result.output
    assert "hackathon-judges" in result.output
    assert "hackathon-finals" in result.output


def test_init_non_interactive_creates_config(tmp_path):
    _make_project(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["init", str(tmp_path), "--non-interactive", "--preset", "quick"],
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "hackluminary.toml").exists()


def test_doctor_json_output(tmp_path):
    _make_project(tmp_path)
    runner = CliRunner()
    result = runner.invoke(cli, ["doctor", str(tmp_path), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert "checks" in payload
    assert "summary" in payload


def test_sample_command_creates_project(tmp_path):
    target = tmp_path / "sample"
    runner = CliRunner()
    result = runner.invoke(cli, ["sample", str(target)])
    assert result.exit_code == 0, result.output
    assert (target / "README.md").exists()
    assert (target / "main.py").exists()
    assert (target / "hackluminary.toml").exists()


def test_images_scan_and_report_commands(tmp_path):
    _make_project(tmp_path)
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "ui.png").write_bytes(
        base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII=")
    )

    runner = CliRunner()
    scan = runner.invoke(cli, ["images", "scan", str(tmp_path)])
    assert scan.exit_code == 0, scan.output
    assert "Indexed images:" in scan.output

    report = runner.invoke(cli, ["images", "report", str(tmp_path), "--json"])
    assert report.exit_code == 0, report.output
    payload = json.loads(report.output)
    assert "image_coverage" in payload


def test_images_benchmark_command(tmp_path):
    _make_project(tmp_path / "proj-a")
    _make_project(tmp_path / "proj-b")

    runner = CliRunner()
    result = runner.invoke(cli, ["images", "benchmark", str(tmp_path), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["project_count"] >= 2
    assert payload["recommended_min_confidence"] is not None


def test_package_devpost_command(tmp_path):
    _make_project(tmp_path)
    runner = CliRunner()
    output_zip = tmp_path / "devpost.zip"
    result = runner.invoke(cli, ["package", "devpost", str(tmp_path), "--output", str(output_zip)])
    assert result.exit_code == 0, result.output
    assert output_zip.exists()


def test_telemetry_enable_command_updates_project_config(tmp_path):
    _make_project(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["telemetry", "enable", str(tmp_path), "--endpoint", "https://telemetry.example.invalid"],
    )
    assert result.exit_code == 0, result.output
    content = (tmp_path / "hackluminary.toml").read_text(encoding="utf-8")
    assert "[telemetry]" in content
    assert "enabled = true" in content

    status = runner.invoke(cli, ["telemetry", "status", str(tmp_path), "--json"])
    assert status.exit_code == 0, status.output
    status_payload = json.loads(status.output)
    assert status_payload["enabled"] is True

    dry = runner.invoke(cli, ["telemetry", "flush", str(tmp_path), "--dry-run", "--json"])
    assert dry.exit_code == 0, dry.output
    dry_payload = json.loads(dry.output)
    assert "status" in dry_payload

    disable = runner.invoke(cli, ["telemetry", "disable", str(tmp_path)])
    assert disable.exit_code == 0, disable.output


def test_generate_images_strict_fails_when_coverage_low(tmp_path):
    _make_project(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "generate",
            str(tmp_path),
            "--mode",
            "deterministic",
            "--format",
            "json",
            "--images",
            "strict",
            "--output",
            str(tmp_path / "deck.json"),
        ],
    )
    assert result.exit_code != 0
    assert result.exception is not None
