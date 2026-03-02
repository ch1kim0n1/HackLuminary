"""Remote image fetching from Wikimedia Commons for slide enrichment.

Images are fetched once and cached in ~/.local/share/hackluminary/image_cache/
so repeated generation runs within a hackathon session are instant and offline.
All network errors are caught and silently skipped — generation never fails due
to a failed image fetch.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from .image_processor import sniff_mime

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Slide-ID → ordered fallback query lists
# Queries are tried in order; first successful Wikimedia File-namespace hit wins.
# ---------------------------------------------------------------------------

# Per-language logo queries — proven common in Wikimedia File namespace.
_LANG_QUERIES: dict[str, str] = {
    "Python":      "Python programming language",
    "JavaScript":  "JavaScript logo",
    "TypeScript":  "TypeScript logo",
    "Rust":        "Rust programming language",
    "Go":          "Go gopher programming language",
    "Java":        "Java programming language",
    "C++":         "ISO C++ logo",
    "C":           "C programming language logo",
    "Ruby":        "Ruby programming language logo",
    "PHP":         "PHP logo",
    "Swift":       "Swift logo Apple",
    "Kotlin":      "Kotlin programming language",
    "C#":          "C sharp programming language logo",
    "Scala":       "Scala programming language",
    "R":           "R programming language",
    "Dart":        "Dart programming language",
    "Haskell":     "Haskell programming language",
    "Elixir":      "Elixir programming language",
    "HTML":        "HTML5 logo",
    "CSS":         "CSS3 logo",
    "Shell":       "Bash logo Unix shell",
}

# Fallback query list per slide ID. Each inner list is tried in order.
_SLIDE_FALLBACKS: dict[str, list[str]] = {
    "problem": [
        "Bug icon software",
        "Warning sign icon",
        "Magnifying glass icon",
        "Computer virus icon",
        "Software bug cartoon",
    ],
    "solution": [
        "{project} software",
        "{lang}",
        "Flowchart algorithm",
        "Gear mechanism solution",
        "Puzzle solution icon",
    ],
    "demo": [
        "{project}",
        "Command line interface terminal",
        "Screenshot software application",
        "Computer terminal emulator",
        "Software demonstration",
    ],
    "tech": [
        "{lang}",
        "{lang} logo",
        "Programming language logo",
        "Software development tools",
    ],
    "impact": [
        "Bar chart statistics",
        "Line chart performance",
        "Data visualization diagram",
        "Graph chart statistics",
        "Pie chart diagram",
    ],
    "future": [
        "Roadmap direction sign",
        "Timeline project planning",
        "Road sign direction",
        "Signpost future direction",
        "Technology innovation diagram",
    ],
    "delta": [
        "Git logo",
        "GitHub logo",
        "Version control branching",
        "Source code repository",
        "Software version control",
    ],
}


def _build_queries_for_slide(slide_id: str, code_analysis: dict) -> list[str]:
    """Return an ordered list of Wikimedia queries to try for *slide_id*."""
    project = str(code_analysis.get("project_name", "") or "").strip()
    primary_lang = str(code_analysis.get("primary_language", "") or "").strip()
    lang_query = _LANG_QUERIES.get(primary_lang, f"{primary_lang} programming logo") if primary_lang else ""

    fallbacks = _SLIDE_FALLBACKS.get(slide_id, ["{project} software", "{lang}"])

    results: list[str] = []
    seen: set[str] = set()

    for template in fallbacks:
        q = template
        if "{project}" in q:
            q = q.replace("{project}", project if project else "software project")
        if "{lang}" in q:
            q = q.replace("{lang}", lang_query if lang_query else "programming language logo")
        q = q.strip()
        if q and q not in seen:
            seen.add(q)
            results.append(q)

    return results


def derive_query_for_slide(slide: dict, code_analysis: dict) -> str:
    """Return the primary Wikimedia query for the given slide (first fallback)."""
    slide_id = str(slide.get("id", slide.get("type", ""))).lower()
    queries = _build_queries_for_slide(slide_id, code_analysis)
    return queries[0] if queries else ""


# ---------------------------------------------------------------------------
# Wikimedia Commons API helpers
# ---------------------------------------------------------------------------

_WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"
_ALLOWED_MIME = {"image/png", "image/jpeg", "image/webp", "image/svg+xml", "image/gif"}
_MIME_EXT = {
    "image/png":     ".png",
    "image/jpeg":    ".jpg",
    "image/webp":    ".webp",
    "image/svg+xml": ".svg",
    "image/gif":     ".gif",
}


def _get_json(url: str, timeout: float) -> Any:
    """Fetch URL and parse JSON; return None on any error."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "HackLuminary/1.0 (hackathon slide generator; https://github.com/ch1kim0n1/HackLuminary)"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception as exc:  # noqa: BLE001
        log.debug("Wikimedia API request failed: %s", exc)
        return None


def _search_wikimedia(query: str, timeout: float) -> str | None:
    """Return the best Wikimedia File-namespace title for *query*, or None."""
    params = urllib.parse.urlencode({
        "action": "query",
        "list": "search",
        "srnamespace": 6,       # File: namespace
        "srsearch": query,
        "srlimit": 8,
        "srwhat": "text",
        "format": "json",
    })
    data = _get_json(f"{_WIKIMEDIA_API}?{params}", timeout=timeout)
    if not data:
        return None

    hits = data.get("query", {}).get("search", [])
    for hit in hits:
        title: str = str(hit.get("title", ""))
        if title.startswith("File:"):
            return title
    return None


def _get_image_url(file_title: str, timeout: float, max_width: int = 640) -> tuple[str, str] | None:
    """Return (download_url, api_mime) for a Wikimedia file title, or None.

    Note: for SVG originals Wikimedia returns PNG bytes via thumburl — the true
    mime is always determined from content bytes later with sniff_mime().
    """
    params = urllib.parse.urlencode({
        "action": "query",
        "titles": file_title,
        "prop": "imageinfo",
        "iiprop": "url|mime|size",
        "iiurlwidth": max_width,
        "format": "json",
    })
    data = _get_json(f"{_WIKIMEDIA_API}?{params}", timeout=timeout)
    if not data:
        return None

    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        for info in page.get("imageinfo", []):
            mime = str(info.get("mime", ""))
            if mime not in _ALLOWED_MIME:
                continue
            url = str(info.get("thumburl") or info.get("url") or "")
            if url.startswith("http"):
                return url, mime
    return None


def _download_bytes(url: str, timeout: float, max_bytes: int) -> bytes | None:
    """Download *url* and return raw bytes, or None on failure / size excess."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "HackLuminary/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(max_bytes + 1)
        if len(raw) > max_bytes:
            log.debug("Remote image too large (%d bytes), skipping: %s", len(raw), url)
            return None
        return raw
    except Exception as exc:  # noqa: BLE001
        log.debug("Image download failed %s: %s", url, exc)
        return None


def _validate_image(raw: bytes) -> bool:
    """Return True if *raw* looks like a supported image format."""
    if not raw or len(raw) < 8:
        return False
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return True
    if raw.startswith(b"\xff\xd8\xff"):
        return True
    if raw.startswith(b"GIF87a") or raw.startswith(b"GIF89a"):
        return True
    if raw.startswith(b"RIFF") and raw[8:12] == b"WEBP":
        return True
    if raw.lstrip().startswith(b"<svg") or b"<svg" in raw[:400].lower():
        return True
    return False


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def _query_cache_path(cache_dir: Path, query: str) -> Path | None:
    """Return existing cached file for *query*, or None if not cached."""
    query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
    for ext in (".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif"):
        p = cache_dir / f"{query_hash}{ext}"
        if p.exists():
            return p
    return None


def _save_to_cache(cache_dir: Path, query: str, raw: bytes, true_mime: str) -> Path:
    """Persist *raw* bytes to cache under a content-mime-correct filename."""
    query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
    ext = _MIME_EXT.get(true_mime, ".png")
    cache_path = cache_dir / f"{query_hash}{ext}"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(raw)
    return cache_path


def _build_catalog_entry(raw: bytes, cache_path: Path, slide_id: str, query: str) -> dict | None:
    """Build a media catalog entry from image bytes and metadata.

    The mime type is sniffed from *raw* content bytes — NOT inferred from the
    file extension — because Wikimedia thumburls return PNG bytes even when the
    original file is SVG, which causes browsers to reject data:image/svg+xml URIs
    that actually contain PNG data.
    """
    if not raw:
        return None

    true_mime = sniff_mime(cache_path, raw)
    if true_mime not in _ALLOWED_MIME:
        log.debug("Unrecognised image content for %r (sniffed: %s)", query, true_mime)
        return None

    sha256 = hashlib.sha256(raw).hexdigest()
    media_id = f"remote.{sha256[:12]}"
    data_uri = f"data:{true_mime};base64,{base64.b64encode(raw).decode('ascii')}"

    tags = [tok.lower() for tok in re.split(r"[^a-zA-Z0-9]+", query) if len(tok) >= 3]
    tags.append(slide_id)

    return {
        "id": media_id,
        "source_path": str(cache_path),
        "kind": "remote_fetched",
        "mime": true_mime,
        "width": None,
        "height": None,
        "sha256": sha256,
        "tags": tags,
        "alt": query,
        "preview_data_uri": data_uri,
        "assigned_slide_id": slide_id,
    }



def fetch_wikimedia_image(
    query: str,
    slide_id: str,
    cache_dir: Path,
    timeout: float = 5.0,
    max_bytes: int = 2_097_152,
) -> dict | None:
    """
    Search Wikimedia Commons for *query* and return a media catalog entry dict,
    or None if the fetch fails for any reason.

    Images are cached by query-hash so re-runs are instant and offline.
    The mime is sniffed from raw content bytes — never trusted from the API or
    file extension — so SVG files that Wikimedia serves as PNG thumbnails are
    correctly labelled as image/png.
    """
    # --- Cache hit ---
    cached_path = _query_cache_path(cache_dir, query)
    if cached_path:
        try:
            raw = cached_path.read_bytes()
            if _validate_image(raw):
                log.debug("Cache hit for %r: %s", query, cached_path)
                return _build_catalog_entry(raw, cached_path, slide_id, query)
            cached_path.unlink(missing_ok=True)   # corrupt entry
        except OSError:
            pass

    # --- Wikimedia search ---
    file_title = _search_wikimedia(query, timeout=timeout)
    if not file_title:
        log.debug("No Wikimedia File: result for query %r", query)
        return None

    result = _get_image_url(file_title, timeout=timeout)
    if not result:
        return None
    image_url, _api_mime = result

    # --- Download ---
    raw = _download_bytes(image_url, timeout=timeout, max_bytes=max_bytes)
    if not raw:
        return None

    # --- Validate content ---
    if not _validate_image(raw):
        log.debug("Downloaded bytes are not a valid image for %r", query)
        return None

    # --- Sniff true mime from bytes (ignores API hint / file extension) ---
    true_mime = sniff_mime(Path("probe.bin"), raw)
    if true_mime not in _ALLOWED_MIME:
        log.debug("Unrecognised mime %r for %r, skipping", true_mime, query)
        return None

    # --- Persist with correct extension ---
    cache_path = _save_to_cache(cache_dir, query, raw, true_mime)

    return _build_catalog_entry(raw, cache_path, slide_id, query)


# ---------------------------------------------------------------------------
# Public batch runner called by pipeline.py
# ---------------------------------------------------------------------------

def fetch_images_for_slides(
    slides: list[dict],
    code_analysis: dict,
    config: dict,
) -> list[dict]:
    """
    Fetch a Wikimedia Commons image for every non-title, non-closing slide.

    For each slide a list of fallback queries is tried in order until one
    succeeds.  All failures are silenced — slides simply stay without an image.
    """
    remote_cfg = config.get("images", {}).get("remote", {})
    if not remote_cfg.get("enabled", True):
        return []

    timeout = float(remote_cfg.get("timeout_sec", 5.0))
    max_bytes = int(remote_cfg.get("max_image_bytes", 2_097_152))

    cache_dir_cfg = remote_cfg.get("cache_dir") or None
    if cache_dir_cfg:
        cache_dir = Path(cache_dir_cfg).expanduser().resolve()
    else:
        cache_dir = Path(os.path.expanduser("~")) / ".local" / "share" / "hackluminary" / "image_cache"

    results: list[dict] = []
    seen_slide_ids: set[str] = set()

    for slide in slides:
        slide_type = str(slide.get("type", "")).lower()
        if slide_type in {"title", "closing"}:
            continue

        slide_id = str(slide.get("id", slide_type)).lower()
        if slide_id in seen_slide_ids:
            continue
        seen_slide_ids.add(slide_id)

        queries = _build_queries_for_slide(slide_id, code_analysis)

        entry: dict | None = None
        for query in queries:
            entry = fetch_wikimedia_image(
                query=query,
                slide_id=slide_id,
                cache_dir=cache_dir,
                timeout=timeout,
                max_bytes=max_bytes,
            )
            if entry:
                log.info("Remote image for slide %r via query %r", slide_id, query)
                break
            log.debug("No result for slide %r query %r, trying next", slide_id, query)

        if entry:
            results.append(entry)
        else:
            log.debug("All queries exhausted for slide %r — no image.", slide_id)

    return results
