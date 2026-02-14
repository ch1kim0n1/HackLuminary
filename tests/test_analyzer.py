"""Tests for the v2 deterministic codebase analyzer."""

from pathlib import Path

from hackluminary.analyzer import CodebaseAnalyzer


def test_analyzer_detects_code_languages_and_ignores_markdown(tmp_path):
    (tmp_path / "main.py").write_text("print('x')\n", encoding="utf-8")
    (tmp_path / "web.js").write_text("console.log('x');\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")

    result = CodebaseAnalyzer(tmp_path).analyze()

    assert result["file_count"] == 2
    assert result["languages"]["Python"] == 1
    assert result["languages"]["JavaScript"] == 1
    assert "Markdown" not in result["languages"]


def test_analyzer_ignores_common_build_dirs(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('ok')\n", encoding="utf-8")

    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "lib.js").write_text("console.log('ignore')\n", encoding="utf-8")

    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "tool.py").write_text("print('ignore')\n", encoding="utf-8")

    (tmp_path / ".venv-codex").mkdir()
    (tmp_path / ".venv-codex" / "site.py").write_text("print('ignore')\n", encoding="utf-8")

    result = CodebaseAnalyzer(tmp_path).analyze()

    assert result["file_count"] == 1
    assert result["primary_language"] == "Python"


def test_analyzer_detects_dependencies_from_pyproject(tmp_path):
    (tmp_path / "main.py").write_text("print('ok')\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "demo"
dependencies = ["fastapi>=0.100", "uvicorn>=0.20"]
""".strip(),
        encoding="utf-8",
    )

    result = CodebaseAnalyzer(tmp_path).analyze()

    assert "fastapi" in [dep.lower() for dep in result["dependencies"]]
    assert "FastAPI" in result["frameworks"]


def test_analyzer_tracks_key_files(tmp_path):
    (tmp_path / "main.py").write_text("def run():\n    return 1\n", encoding="utf-8")
    (tmp_path / "worker.py").write_text("def task():\n    return 1\n", encoding="utf-8")

    result = CodebaseAnalyzer(tmp_path).analyze()

    assert "main.py" in result["key_files"]
