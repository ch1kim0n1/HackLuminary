"""CLI contract and backward compatibility tests."""

import json

from click.testing import CliRunner

from hackluminary.cli import _normalize_legacy_args, cli


def _make_project(tmp_path):
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
        ],
    )

    assert result.exit_code == 0, result.output
    assert output_path.exists()

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "2.1"
    assert "git_context" in payload
    assert "slides" in payload
    assert "claims" in payload["slides"][0]


def test_validate_command(tmp_path):
    _make_project(tmp_path)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["validate", str(tmp_path), "--mode", "deterministic"],
    )

    assert result.exit_code == 0, result.output
    assert "Status: pass" in result.output


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


def test_studio_help_lists_options():
    runner = CliRunner()
    result = runner.invoke(cli, ["studio", "--help"])

    assert result.exit_code == 0
    assert "--base-branch" in result.output
    assert "--port" in result.output
