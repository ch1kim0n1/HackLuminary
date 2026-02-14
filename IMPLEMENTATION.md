# HackLuminary v2.1 Implementation Summary

## Overview

HackLuminary v2.1 delivers a dual workflow:
- NotebookLM-style local Studio for source-grounded drafting
- Production-ready deck/presenter export path

All runtime generation remains offline-first and evidence-grounded.

## Core Modules

- `hackluminary/cli.py`
  - Commands: `generate`, `validate`, `studio`, `models`
- `hackluminary/pipeline.py`
  - End-to-end generation orchestration
- `hackluminary/slides.py`
  - Deterministic slide model with `claims` + `notes`
- `hackluminary/evidence.py`
  - Enriched evidence records with snippet/line metadata
- `hackluminary/presentation_generator.py`
  - Type-specific slide templates, citation badges, presenter HUD
- `hackluminary/studio_server.py`
  - Local loopback Studio API + static asset serving
- `hackluminary/studio_session.py`
  - Project-local session file persistence
- `hackluminary/studio/*`
  - Vanilla JS/CSS Studio UI assets

## Studio API Endpoints

- `GET /api/context`
- `GET /api/slides`
- `POST /api/slides`
- `GET /api/evidence`
- `GET /api/session`
- `PUT /api/session`
- `POST /api/export`
- `POST /api/validate`

## Schema Evolution

Payload schema version updated to `2.1`.

Additions:
- Slide-level `claims[]` and `notes`
- Evidence metadata:
  - `source_path`
  - `source_kind`
  - `start_line`
  - `end_line`
  - `snippet`
  - `snippet_hash`

Backward compatibility:
- Existing keys (`id`, `type`, `title`, `value`, `evidence_refs`) are preserved.

## Security / Offline Constraints

- No CDN in generated HTML
- CSP enforced on deck and studio HTML
- Path safety checks for Studio export paths (must stay within project root)
- Static assets served locally only
- Session writes can be disabled via `--read-only`

## Accessibility / UX Baseline

- Keyboard-operable controls in Studio and deck
- Focus-visible states and reduced-motion support
- Semantic regions and control labels
- Responsive desktop-first layout with mobile fallback

## Session Persistence

Studio session stored at:
- `.hackluminary/studio/session.json`

Contains:
- slide selection/order
- draft overrides
- note blocks
- pinned evidence
- presenter state
- last validation snapshot

## Testing Coverage Added

- Evidence enrichment and line mapping
- Session persistence/migration
- Studio API health + edit/validate/export/session flows
- Presenter asset timer controls
- Claim/evidence linkage checks

## Release Note

Version bumped to `2.1.0` with Notebook-style Studio + Pro Deck integration.
