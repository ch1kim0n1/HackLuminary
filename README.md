# HackLuminary v2.2

Offline-first, branch-aware presentation system with a NotebookLM-style local Studio and production deck renderer.

## Highlights

- Hybrid workflow: `studio` for drafting + `generate` for exports
- Source-grounded citations with snippet/line provenance
- Evidence explorer with search/filter/sort and per-slide evidence pinning
- Self-contained offline HTML deck output
- Presenter mode with notes, timer, progress timeline, jump controls
- Slide outline + reorder controls with keyboard shortcuts
- One-click Studio quality fixes (`Fix This`, `Fix All`) for common quality errors
- Bundle artifacts (`notes.md`, `talk-track.md`) for presenter prep
- Conservative offline visual pipeline (auto image selection + evidence-linked captions)
- JSON schema `2.2` with `media_catalog` and per-slide `visuals`
- Strict local runtime (no CDN, no cloud calls in generate/validate/studio)

## Commands

- `hackluminary generate [PROJECT_DIR]`
- `hackluminary validate [PROJECT_DIR]`
- `hackluminary studio [PROJECT_DIR]`
- `hackluminary doctor [PROJECT_DIR]`
- `hackluminary init [PROJECT_DIR]`
- `hackluminary presets`
- `hackluminary sample [TARGET_DIR]`
- `hackluminary models list`
- `hackluminary models install <alias>`
- `hackluminary images scan [PROJECT_DIR]`
- `hackluminary images report [PROJECT_DIR] --json`
- `hackluminary images benchmark CORPUS_DIR`
- `hackluminary package devpost [PROJECT_DIR] --output PATH`
- `hackluminary telemetry enable [PROJECT_DIR] --endpoint URL`
- `hackluminary telemetry status [PROJECT_DIR]`
- `hackluminary telemetry flush [PROJECT_DIR]`
- `hackluminary telemetry disable [PROJECT_DIR]`

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

### Release Build Dependencies

```bash
python -m pip install -e '.[release]'
```

## Quick Start

### Launch Studio

```bash
hackluminary studio . --base-branch main
```

### Generate deck outputs

```bash
hackluminary generate . --preset demo-day --images auto --output deck --bundle
```

### Validate quality gates only

```bash
hackluminary validate . --mode deterministic
```

## `generate` options

- `--project-dir PATH`
- `--output PATH`
- `--format html|markdown|json|both`
- `--preset quick|demo-day|investor`
- `--slides title,problem,solution,demo,impact,tech,future,delta,closing`
- `--max-slides N`
- `--docs PATH` (repeatable)
- `--theme default|dark|minimal|colorful|auto`
- `--mode deterministic|ai|hybrid`
- `--images off|auto|strict`
- `--image-dirs PATH` (repeatable, project-relative)
- `--max-images-per-slide 0..2`
- `--visual-style evidence|screenshot|mixed`
- `--base-branch NAME`
- `--no-branch-context`
- `--strict-quality` / `--no-strict-quality`
- `--open`
- `--copy-output-dir PATH`
- `--bundle`
- `--debug`

## Setup And Onboarding

```bash
hackluminary doctor .
hackluminary init .
hackluminary presets
hackluminary sample
```

- `doctor` verifies local setup, project health, git context, model readiness, and Studio assets.
- `init` writes `hackluminary.toml` using an interactive wizard.
- `sample` creates a runnable demo project for first-time users.

## Binary Distribution

Release workflow now builds and publishes:
- standalone macOS binaries (`macos-x64`, `macos-arm64`)
- standalone Windows binary (`windows-x64`)
- standalone Linux binary (`linux-x64`)
- wheel + source distribution
- generated Homebrew formula + Winget manifests
- checksum verification before publish
- signing gate enforcement for macOS/Windows artifacts (override via `ALLOW_UNSIGNED_RELEASE=1` secret)

GitHub release automation lives in:
- `.github/workflows/release.yml`

### Direct install scripts

macOS/Linux:

```bash
bash install/install.sh
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File install/install.ps1
```

Optional environment overrides for installers:
- `HACKLUMINARY_REPO` (default `MindCore/HackLuminary`)
- `HACKLUMINARY_VERSION` (default `latest`)
- `HACKLUMINARY_INSTALL_DIR` (custom install location)

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
- `[images]`: `enabled`, `mode`, `image_dirs`, `max_images_per_slide`, `min_confidence`, `visual_style`, `max_image_bytes`, `allowed_extensions`
- `[telemetry]`: `enabled`, `anonymous`, `endpoint` (opt-in only; local event file by default)
- `[studio]`: `enabled`, `default_view`, `autosave_interval_sec`, `port`, `read_only`
- `[ui]`: `density`, `motion`, `code_font_scale`, `presenter_timer_default_min`
- `[features]`: `studio_enabled`, `production_theme_enabled`, `presenter_pro_enabled`
- `[privacy]`: `telemetry=false`

## JSON schema `2.2`

Top-level fields:
- `schema_version`
- `metadata`
- `git_context`
- `slides`
- `evidence`
- `media_catalog`
- `quality_report`

Slide additions:
- `claims[]`: `{ text, evidence_refs, confidence }`
- `notes`
- `visuals[]`: `{ id, type, source_path, alt, caption, evidence_refs, confidence, width, height, sha256 }`

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
Automatic session snapshots are written to `.hackluminary/studio/snapshots/` for crash recovery.

## Pilot Rollout

Use `/Users/pomoika/Documents/GitHub_repo/HackLuminary/PILOT_CHECKLIST.md` for release and pilot-readiness gates.

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
