# HackLuminary v2.2 Examples

## 1) Open Notebook-style Studio

```bash
hackluminary studio . --base-branch main
```

Studio provides:
- evidence explorer
- claim->citation inspector
- draft board editing
- presenter HUD

## 2) Deterministic export bundle with manifest

```bash
hackluminary generate . --preset quick --images auto --output pitch --bundle
```

Outputs:
- `pitch.html` (self-contained)
- `pitch.md`
- `notes.md`
- `talk-track.md`
- `manifest.json`

## 3) JSON payload for automation pipelines

```bash
hackluminary generate . --mode deterministic --format json --output payload.json
```

Includes schema `2.2` with claims, media catalog, and enriched evidence metadata.

## 4) Image diagnostics

```bash
hackluminary images scan .
hackluminary images report . --json
hackluminary images benchmark ./corpus --max-projects 10
```

## 5) Branch-aware technical deck

```bash
hackluminary generate . \
  --mode deterministic \
  --slides title,problem,solution,tech,delta,closing \
  --base-branch main \
  --output branch-review
```

## 6) Validate quality gates in CI

```bash
hackluminary validate . --preset demo-day
```

## 7) Save outputs to shared artifact directory

```bash
hackluminary generate . \
  --mode deterministic \
  --format both \
  --output sprint-demo \
  --copy-output-dir ./artifacts
```

## 8) Install local model and run hybrid mode

```bash
hackluminary models list
hackluminary models install qwen2.5-3b-instruct-q4_k_m
hackluminary generate . --mode hybrid --format both --output ai-pitch
```

## 9) Sample project config

```toml
[general]
mode = "deterministic"
format = "both"
theme = "default"
strict_quality = true

[git]
base_branch = "main"
include_branch_context = true

[images]
enabled = true
mode = "auto"
image_dirs = []
max_images_per_slide = 1
min_confidence = 0.72
visual_style = "mixed"

[telemetry]
enabled = false
anonymous = true
endpoint = ""

[studio]
enabled = true
default_view = "notebook"
autosave_interval_sec = 20
port = 0
read_only = false

[ui]
density = "comfortable"
motion = "normal"
code_font_scale = 1.0
presenter_timer_default_min = 7

[features]
studio_enabled = true
production_theme_enabled = true
presenter_pro_enabled = true

```

## 10) First-run setup workflow

```bash
hackluminary doctor .
hackluminary init .
hackluminary presets
```

## 11) Create a runnable sample project

```bash
hackluminary sample
hackluminary generate ./hackluminary-sample --preset quick --bundle
```

## 12) Build standalone binary locally

```bash
python -m pip install -e '.[release]'
python scripts/release/build_standalone.py --platform-tag macos-arm64 --release-version v2.2.0
```

Artifacts are written under `dist/release/` with matching `.sha256` files.

## 13) Render Homebrew and Winget manifests

```bash
python scripts/release/render_homebrew_formula.py \
  --version v2.2.0 \
  --repo MindCore/HackLuminary \
  --arm64-sha256 <arm64-sha> \
  --x64-sha256 <x64-sha> \
  --output dist/manifests/homebrew/hackluminary.rb

python scripts/release/render_winget_manifest.py \
  --version v2.2.0 \
  --repo MindCore/HackLuminary \
  --installer-sha256 <windows-sha> \
  --output-dir dist/manifests/winget
```

## 14) Devpost package helper

```bash
hackluminary package devpost . --output ./artifacts/devpost.zip
```

## 15) Opt-in telemetry operations

```bash
hackluminary telemetry enable . --endpoint https://example.invalid/ingest
hackluminary telemetry status .
hackluminary telemetry flush . --max-events 100
hackluminary telemetry disable .
```
