# HackLuminary v2.1

Offline-first, branch-aware presentation system with a NotebookLM-style local Studio and production deck renderer.

## Highlights

- Hybrid workflow: `studio` for drafting + `generate` for exports
- Source-grounded citations with snippet/line provenance
- Evidence explorer with search/filter/sort and per-slide evidence pinning
- Self-contained offline HTML deck output
- Presenter mode with notes, timer, progress timeline, jump controls
- Slide outline + reorder controls with keyboard shortcuts
- JSON schema `2.1` with claims and enriched evidence metadata
- Strict local runtime (no CDN, no cloud calls in generate/validate/studio)

## Commands

- `hackluminary generate [PROJECT_DIR]`
- `hackluminary validate [PROJECT_DIR]`
- `hackluminary studio [PROJECT_DIR]`
- `hackluminary models list`
- `hackluminary models install <alias>`

## Installation

### Recommended

```bash
pipx install .
```

### Development

```bash
python -m pip install -e '.[dev]'
```

### Optional local AI dependencies

```bash
python -m pip install -e '.[ml]'
```

## Quick Start

### Launch Studio

```bash
hackluminary studio . --base-branch main
```

### Generate deck outputs

```bash
hackluminary generate . --mode deterministic --format both --output deck
```

### Validate quality gates only

```bash
hackluminary validate . --mode deterministic
```

## `generate` options

- `--project-dir PATH`
- `--output PATH`
- `--format html|markdown|json|both`
- `--slides title,problem,solution,demo,impact,tech,future,delta,closing`
- `--max-slides N`
- `--docs PATH` (repeatable)
- `--theme default|dark|minimal|colorful|auto`
- `--mode deterministic|ai|hybrid`
- `--base-branch NAME`
- `--no-branch-context`
- `--strict-quality` / `--no-strict-quality`
- `--open`
- `--copy-output-dir PATH`
- `--debug`

## `studio` options

- `--project-dir PATH`
- `--base-branch NAME`
- `--theme default|dark|minimal|colorful|auto`
- `--port INT`
- `--read-only`
- `--debug`

## Configuration (`hackluminary.toml`)

Precedence:
1. CLI flags
2. Project config
3. User config (`~/.config/hackluminary/config.toml`)
4. Defaults

Sections:
- `[general]`: `mode`, `format`, `theme`, `max_slides`, `strict_quality`
- `[git]`: `base_branch`, `include_branch_context`
- `[ai]`: `enabled`, `backend`, `model_alias`, `max_tokens`, `top_p`, `temperature`
- `[output]`: `copy_output_dir`, `open_after_generate`
- `[studio]`: `enabled`, `default_view`, `autosave_interval_sec`, `port`, `read_only`
- `[ui]`: `density`, `motion`, `code_font_scale`, `presenter_timer_default_min`
- `[features]`: `studio_enabled`, `production_theme_enabled`, `presenter_pro_enabled`
- `[privacy]`: `telemetry=false`

## JSON schema `2.1`

Top-level fields:
- `schema_version`
- `metadata`
- `git_context`
- `slides`
- `evidence`
- `quality_report`

Slide additions:
- `claims[]`: `{ text, evidence_refs, confidence }`
- `notes`

Evidence additions:
- `source_path`
- `source_kind`
- `start_line`
- `end_line`
- `snippet`
- `snippet_hash`

## Studio Session

Studio persists workspace state in:

- `.hackluminary/studio/session.json`

Includes slide ordering, draft overrides, note blocks, pinned evidence, presenter state, and last validation.

## Testing

```bash
python -m pytest
```

## Browser Support

Studio and exported decks target current:
- Chrome
- Edge
- Safari
- Firefox

## License

MIT
