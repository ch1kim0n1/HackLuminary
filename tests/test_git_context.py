"""Git context collection tests."""

import subprocess

from hackluminary.git_context import collect_git_context


def _run(cwd, *args):
    subprocess.run(args, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def test_collect_git_context_from_repo(tmp_path):
    _run(tmp_path, "git", "init")
    _run(tmp_path, "git", "config", "user.email", "test@example.com")
    _run(tmp_path, "git", "config", "user.name", "Tester")

    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    _run(tmp_path, "git", "add", ".")
    _run(tmp_path, "git", "commit", "-m", "init")

    _run(tmp_path, "git", "checkout", "-b", "feature/demo")
    (tmp_path / "app.py").write_text("print('x')\n", encoding="utf-8")
    _run(tmp_path, "git", "add", ".")
    _run(tmp_path, "git", "commit", "-m", "add app")

    context = collect_git_context(tmp_path, include_branch_context=True, base_branch=None)

    assert context["available"] is True
    assert context["branch"] == "feature/demo"
    assert context["base_branch"] in {"main", "master", "origin/main", "origin/master"}
    assert context["changed_files_count"] >= 1


def test_collect_git_context_non_repo(tmp_path):
    context = collect_git_context(tmp_path, include_branch_context=True, base_branch=None)

    assert context["available"] is False
    assert context["changed_files_count"] == 0
