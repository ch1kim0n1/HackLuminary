"""Preset profiles for easy deck generation workflows."""

from __future__ import annotations

from copy import deepcopy

PRESETS: dict[str, dict] = {
    "quick": {
        "description": "Fast deterministic deck for a rapid demo run.",
        "general": {
            "mode": "deterministic",
            "theme": "minimal",
            "strict_quality": True,
            "format": "both",
        },
        "slides": ["title", "problem", "solution", "demo", "delta", "closing"],
        "max_slides": 6,
    },
    "demo-day": {
        "description": "Balanced hackathon judging deck with technical depth.",
        "general": {
            "mode": "hybrid",
            "theme": "default",
            "strict_quality": True,
            "format": "both",
        },
        "slides": ["title", "problem", "solution", "demo", "tech", "impact", "delta", "closing"],
        "max_slides": 8,
    },
    "investor": {
        "description": "Story-first pitch emphasizing outcomes and traction.",
        "general": {
            "mode": "hybrid",
            "theme": "colorful",
            "strict_quality": True,
            "format": "both",
        },
        "slides": ["title", "problem", "solution", "impact", "demo", "future", "closing"],
        "max_slides": 7,
    },
    "hackathon-judges": {
        "description": "Judge-optimized flow with clear branch delta and evidence-rich visuals.",
        "general": {
            "mode": "hybrid",
            "theme": "default",
            "strict_quality": True,
            "format": "both",
        },
        "slides": ["title", "problem", "solution", "demo", "tech", "impact", "delta", "closing"],
        "max_slides": 8,
    },
    "hackathon-finals": {
        "description": "Final round pacing with stronger narrative and polished close.",
        "general": {
            "mode": "hybrid",
            "theme": "colorful",
            "strict_quality": True,
            "format": "both",
        },
        "slides": ["title", "problem", "solution", "demo", "impact", "tech", "future", "closing"],
        "max_slides": 8,
    },
}


def list_presets() -> list[tuple[str, str]]:
    rows = []
    for name in sorted(PRESETS):
        rows.append((name, PRESETS[name].get("description", "")))
    return rows


def resolve_preset(name: str | None) -> dict | None:
    if not name:
        return None
    preset = PRESETS.get(name)
    if not preset:
        return None
    return deepcopy(preset)
