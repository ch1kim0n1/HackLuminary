"""Release/distribution asset tests."""

from pathlib import Path

from hackluminary.release_assets import (
    normalize_tag,
    normalize_version,
    render_homebrew_formula,
    render_winget_manifest,
)


def test_version_normalization_helpers():
    assert normalize_version("v2.1.0") == "2.1.0"
    assert normalize_version("2.1.0") == "2.1.0"
    assert normalize_tag("2.1.0") == "v2.1.0"
    assert normalize_tag("v2.1.0") == "v2.1.0"


def test_render_homebrew_formula_contains_expected_urls():
    text = render_homebrew_formula(
        version="v2.1.0",
        repo="MindCore/HackLuminary",
        arm64_sha256="a" * 64,
        x64_sha256="b" * 64,
    )
    assert "hackluminary-macos-arm64.tar.gz" in text
    assert "hackluminary-macos-x64.tar.gz" in text
    assert "version \"2.1.0\"" in text


def test_render_winget_manifest_contains_installer_reference():
    files = render_winget_manifest(
        version="2.1.0",
        repo="MindCore/HackLuminary",
        installer_sha256="c" * 64,
    )
    assert "MindCore.HackLuminary.installer.yaml" in files
    installer = files["MindCore.HackLuminary.installer.yaml"]
    assert "hackluminary-windows-x64.zip" in installer
    assert "InstallerSha256" in installer


def test_release_workflow_exists_with_standalone_job():
    workflow = Path(".github/workflows/release.yml")
    text = workflow.read_text(encoding="utf-8")
    assert "build-standalone" in text
    assert "publish-release" in text
    assert "hackluminary-macos-arm64.tar.gz" in text


def test_install_scripts_exist():
    assert Path("install/install.sh").exists()
    assert Path("install/install.ps1").exists()
