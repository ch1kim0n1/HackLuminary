"""Local image validation and metadata helpers."""

from __future__ import annotations

import base64
import hashlib
import mimetypes
import re
from pathlib import Path


def normalize_allowed_extensions(extensions: list[str] | tuple[str, ...] | set[str]) -> set[str]:
    normalized: set[str] = set()
    for item in extensions:
        ext = str(item).strip().lower()
        if not ext:
            continue
        if not ext.startswith("."):
            ext = f".{ext}"
        normalized.add(ext)
    return normalized


def safe_relative_path(project_root: Path, candidate: Path) -> str:
    root = Path(project_root).resolve()
    path = Path(candidate).resolve()
    return str(path.relative_to(root))


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 256)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def inspect_image(
    path: Path,
    project_root: Path,
    allowed_extensions: set[str],
    max_image_bytes: int,
) -> dict:
    absolute = Path(path).resolve()
    rel = safe_relative_path(Path(project_root).resolve(), absolute)

    ext = absolute.suffix.lower()
    if ext not in allowed_extensions:
        raise ValueError(f"Unsupported image extension: {ext}")

    size = absolute.stat().st_size
    if size > int(max_image_bytes):
        raise ValueError(f"Image exceeds max size ({size} bytes > {max_image_bytes})")

    raw = absolute.read_bytes()
    mime = sniff_mime(absolute, raw)
    if not mime.startswith("image/"):
        raise ValueError(f"Unsupported image mime type: {mime}")

    width, height = detect_dimensions(raw, ext, mime)

    if ext == ".svg":
        text = raw.decode("utf-8", errors="ignore").lower()
        if "<script" in text or "onload=" in text or "javascript:" in text:
            raise ValueError("SVG contains disallowed scripting content")

    return {
        "source_path": rel,
        "mime": mime,
        "width": width,
        "height": height,
        "sha256": hash_file(absolute),
        "bytes": size,
    }


def to_data_uri(path: Path, mime: str) -> str:
    raw = path.read_bytes()
    encoded = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def sniff_mime(path: Path, raw: bytes) -> str:
    guessed, _ = mimetypes.guess_type(str(path))
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if raw.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if raw.startswith(b"GIF87a") or raw.startswith(b"GIF89a"):
        return "image/gif"
    if raw.startswith(b"RIFF") and raw[8:12] == b"WEBP":
        return "image/webp"
    if raw.lstrip().startswith(b"<svg") or b"<svg" in raw[:300].lower():
        return "image/svg+xml"
    return guessed or "application/octet-stream"


def detect_dimensions(raw: bytes, ext: str, mime: str) -> tuple[int | None, int | None]:
    if mime == "image/png" and len(raw) >= 24:
        return int.from_bytes(raw[16:20], "big"), int.from_bytes(raw[20:24], "big")

    if mime == "image/gif" and len(raw) >= 10:
        return int.from_bytes(raw[6:8], "little"), int.from_bytes(raw[8:10], "little")

    if mime == "image/jpeg":
        dims = _jpeg_dimensions(raw)
        if dims:
            return dims

    if mime == "image/webp":
        dims = _webp_dimensions(raw)
        if dims:
            return dims

    if ext == ".svg" or mime == "image/svg+xml":
        dims = _svg_dimensions(raw)
        if dims:
            return dims

    return (None, None)


def _jpeg_dimensions(raw: bytes) -> tuple[int, int] | None:
    if len(raw) < 4 or raw[0:2] != b"\xff\xd8":
        return None

    i = 2
    while i + 1 < len(raw):
        if raw[i] != 0xFF:
            i += 1
            continue

        while i < len(raw) and raw[i] == 0xFF:
            i += 1
        if i >= len(raw):
            break

        marker = raw[i]
        i += 1

        if marker in {0xD8, 0xD9, 0x01} or 0xD0 <= marker <= 0xD7:
            continue

        if i + 1 >= len(raw):
            break
        segment_len = int.from_bytes(raw[i : i + 2], "big")
        if segment_len < 2 or i + segment_len > len(raw):
            break

        if marker in {
            0xC0,
            0xC1,
            0xC2,
            0xC3,
            0xC5,
            0xC6,
            0xC7,
            0xC9,
            0xCA,
            0xCB,
            0xCD,
            0xCE,
            0xCF,
        }:
            if i + 7 <= len(raw):
                height = int.from_bytes(raw[i + 3 : i + 5], "big")
                width = int.from_bytes(raw[i + 5 : i + 7], "big")
                return (width, height)

        i += segment_len

    return None


def _webp_dimensions(raw: bytes) -> tuple[int, int] | None:
    if len(raw) < 30 or raw[0:4] != b"RIFF" or raw[8:12] != b"WEBP":
        return None

    chunk = raw[12:16]
    if chunk == b"VP8X" and len(raw) >= 30:
        width = 1 + int.from_bytes(raw[24:27], "little")
        height = 1 + int.from_bytes(raw[27:30], "little")
        return (width, height)

    if chunk == b"VP8L" and len(raw) >= 25:
        b0 = raw[21]
        b1 = raw[22]
        b2 = raw[23]
        b3 = raw[24]
        width = 1 + (((b1 & 0x3F) << 8) | b0)
        height = 1 + (((b3 & 0x0F) << 10) | (b2 << 2) | ((b1 & 0xC0) >> 6))
        return (width, height)

    return None


def _svg_dimensions(raw: bytes) -> tuple[int, int] | None:
    text = raw.decode("utf-8", errors="ignore")

    width_match = re.search(r'\bwidth\s*=\s*"([0-9.]+)(px)?"', text, flags=re.IGNORECASE)
    height_match = re.search(r'\bheight\s*=\s*"([0-9.]+)(px)?"', text, flags=re.IGNORECASE)

    if width_match and height_match:
        try:
            return int(float(width_match.group(1))), int(float(height_match.group(1)))
        except ValueError:
            pass

    viewbox_match = re.search(
        r'\bviewBox\s*=\s*"\s*[-0-9.]+\s+[-0-9.]+\s+([0-9.]+)\s+([0-9.]+)\s*"',
        text,
        flags=re.IGNORECASE,
    )
    if viewbox_match:
        try:
            return int(float(viewbox_match.group(1))), int(float(viewbox_match.group(2)))
        except ValueError:
            pass

    return None
