"""Auxiliary artifacts for speaker notes and talk tracks."""

from __future__ import annotations

from pathlib import Path


def build_notes_markdown(slides: list[dict]) -> str:
    lines = ["# Speaker Notes", ""]
    for index, slide in enumerate(slides, start=1):
        title = str(slide.get("title", slide.get("id", f"Slide {index}"))).strip() or f"Slide {index}"
        lines.append(f"## {index}. {title}")
        lines.append("")

        note = str(slide.get("notes", "")).strip()
        if note:
            lines.append(note)
        else:
            # Provide a useful fallback note based on slide body.
            fallback = _slide_summary(slide)
            lines.append(fallback or "Keep this section concise and tie it to repository evidence.")

        refs = slide.get("evidence_refs", [])
        if isinstance(refs, list) and refs:
            lines.append("")
            lines.append("Evidence refs: " + ", ".join(str(ref) for ref in refs))

        lines.append("")

    return "\n".join(lines).strip() + "\n"


def build_talk_track_markdown(slides: list[dict], durations: tuple[int, ...] = (30, 60, 180)) -> str:
    lines = ["# Talk Track", ""]
    for seconds in durations:
        lines.extend(_build_duration_track(slides, seconds))
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def write_bundle_artifacts(output_base: Path, slides: list[dict]) -> dict[str, str]:
    """Write notes/talk-track artifacts next to generated outputs."""

    output_base = output_base.resolve()
    bundle_dir = output_base.parent
    bundle_dir.mkdir(parents=True, exist_ok=True)

    notes_path = bundle_dir / "notes.md"
    talk_track_path = bundle_dir / "talk-track.md"

    notes_path.write_text(build_notes_markdown(slides), encoding="utf-8")
    talk_track_path.write_text(build_talk_track_markdown(slides), encoding="utf-8")

    return {
        "notes": str(notes_path),
        "talk_track": str(talk_track_path),
    }


def _build_duration_track(slides: list[dict], seconds: int) -> list[str]:
    title = _duration_title(seconds)
    lines = [f"## {title}", ""]

    if not slides:
        lines.append("No slides available.")
        return lines

    remaining = max(1, seconds)
    per_slide = max(1, remaining // len(slides))

    for index, slide in enumerate(slides, start=1):
        slide_title = str(slide.get("title", slide.get("id", f"Slide {index}"))).strip() or f"Slide {index}"
        lines.append(f"- [{per_slide:02d}s] {slide_title}: {_slide_summary(slide)}")

    return lines


def _slide_summary(slide: dict) -> str:
    subtitle = str(slide.get("subtitle", "")).strip()
    content = str(slide.get("content", "")).strip()
    items = slide.get("list_items", [])

    if subtitle:
        return subtitle[:200]
    if content:
        return content[:200]
    if isinstance(items, list) and items:
        first = str(items[0]).strip()
        return first[:200]
    claims = slide.get("claims", [])
    if isinstance(claims, list) and claims:
        text = str(claims[0].get("text", "")).strip()
        if text:
            return text[:200]
    return "Present key point and connect to evidence."


def _duration_title(seconds: int) -> str:
    if seconds == 30:
        return "30 Second Pitch"
    if seconds == 60:
        return "60 Second Pitch"
    if seconds == 180:
        return "3 Minute Pitch"
    return f"{seconds} Second Pitch"

