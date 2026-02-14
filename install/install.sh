#!/usr/bin/env bash
set -euo pipefail

REPO="${HACKLUMINARY_REPO:-MindCore/HackLuminary}"
VERSION="${HACKLUMINARY_VERSION:-latest}"
INSTALL_DIR="${HACKLUMINARY_INSTALL_DIR:-$HOME/.local/bin}"

uname_s="$(uname -s)"
uname_m="$(uname -m)"

case "${uname_s}" in
  Darwin) os="macos" ;;
  Linux) os="linux" ;;
  *)
    echo "Unsupported OS: ${uname_s}" >&2
    exit 1
    ;;
esac

case "${uname_m}" in
  x86_64|amd64) arch="x64" ;;
  arm64|aarch64) arch="arm64" ;;
  *)
    echo "Unsupported architecture: ${uname_m}" >&2
    exit 1
    ;;
esac

asset="hackluminary-${os}-${arch}.tar.gz"
if [[ "${VERSION}" == "latest" ]]; then
  url="https://github.com/${REPO}/releases/latest/download/${asset}"
else
  tag="${VERSION}"
  [[ "${tag}" != v* ]] && tag="v${tag}"
  url="https://github.com/${REPO}/releases/download/${tag}/${asset}"
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "${tmp_dir}"' EXIT

echo "Downloading ${url}"
curl -fsSL "${url}" -o "${tmp_dir}/${asset}"
tar -xzf "${tmp_dir}/${asset}" -C "${tmp_dir}"

mkdir -p "${INSTALL_DIR}"
install -m 0755 "${tmp_dir}/hackluminary" "${INSTALL_DIR}/hackluminary"

echo "Installed hackluminary to ${INSTALL_DIR}/hackluminary"
echo "Run: hackluminary --help"

