"""Helpers for generating release distribution assets."""

from __future__ import annotations


def normalize_version(version: str) -> str:
    cleaned = str(version).strip()
    if cleaned.startswith("v"):
        return cleaned[1:]
    return cleaned


def normalize_tag(version: str) -> str:
    cleaned = str(version).strip()
    if cleaned.startswith("v"):
        return cleaned
    return f"v{cleaned}"


def render_homebrew_formula(
    version: str,
    repo: str,
    arm64_sha256: str,
    x64_sha256: str,
) -> str:
    ver = normalize_version(version)
    tag = normalize_tag(ver)
    arm_url = f"https://github.com/{repo}/releases/download/{tag}/hackluminary-macos-arm64.tar.gz"
    x64_url = f"https://github.com/{repo}/releases/download/{tag}/hackluminary-macos-x64.tar.gz"

    return f"""class Hackluminary < Formula
  desc "Offline-first, branch-aware hackathon presentation generator"
  homepage "https://github.com/{repo}"
  version "{ver}"
  license "MIT"

  on_macos do
    if Hardware::CPU.arm?
      url "{arm_url}"
      sha256 "{arm64_sha256}"
    else
      url "{x64_url}"
      sha256 "{x64_sha256}"
    end
  end

  def install
    bin.install "hackluminary"
  end

  test do
    assert_match "HackLuminary", shell_output("#{{bin}}/hackluminary --help")
  end
end
"""


def render_winget_manifest(
    version: str,
    repo: str,
    installer_sha256: str,
) -> dict[str, str]:
    ver = normalize_version(version)
    tag = normalize_tag(ver)
    package_identifier = "MindCore.HackLuminary"
    installer_url = f"https://github.com/{repo}/releases/download/{tag}/hackluminary-windows-x64.zip"

    version_file = f"""PackageIdentifier: {package_identifier}
PackageVersion: {ver}
DefaultLocale: en-US
ManifestType: version
ManifestVersion: 1.6.0
"""

    installer_file = f"""PackageIdentifier: {package_identifier}
PackageVersion: {ver}
Installers:
- Architecture: x64
  InstallerType: zip
  NestedInstallerType: portable
  NestedInstallerFiles:
  - RelativeFilePath: hackluminary.exe
    PortableCommandAlias: hackluminary
  InstallerUrl: {installer_url}
  InstallerSha256: {installer_sha256}
ManifestType: installer
ManifestVersion: 1.6.0
"""

    locale_file = f"""PackageIdentifier: {package_identifier}
PackageVersion: {ver}
PackageLocale: en-US
Publisher: MindCore
PackageName: HackLuminary
License: MIT
ShortDescription: Offline-first, branch-aware hackathon presentation generator
ManifestType: defaultLocale
ManifestVersion: 1.6.0
"""

    return {
        "MindCore.HackLuminary.yaml": version_file,
        "MindCore.HackLuminary.installer.yaml": installer_file,
        "MindCore.HackLuminary.locale.en-US.yaml": locale_file,
    }

