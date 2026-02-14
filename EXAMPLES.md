# HackLuminary v2.1 Examples

## 1) Open Notebook-style Studio

```bash
hackluminary studio . --base-branch main
```

Studio provides:
- evidence explorer
- claim->citation inspector
- draft board editing
- presenter HUD

## 2) Deterministic export bundle

```bash
hackluminary generate . --mode deterministic --format both --output pitch
```

Outputs:
- `pitch.html` (self-contained)
- `pitch.md`

## 3) JSON payload for automation pipelines

```bash
hackluminary generate . --mode deterministic --format json --output payload.json
```

Includes schema `2.1` with claims and enriched evidence metadata.

## 4) Branch-aware technical deck

```bash
hackluminary generate . \
  --mode deterministic \
  --slides title,problem,solution,tech,delta,closing \
  --base-branch main \
  --output branch-review
```

## 5) Validate quality gates in CI

```bash
hackluminary validate . --mode deterministic
```

## 6) Save outputs to shared artifact directory

```bash
hackluminary generate . \
  --mode deterministic \
  --format both \
  --output sprint-demo \
  --copy-output-dir ./artifacts
```

## 7) Install local model and run hybrid mode

```bash
hackluminary models list
hackluminary models install qwen2.5-3b-instruct-q4_k_m
hackluminary generate . --mode hybrid --format both --output ai-pitch
```

## 8) Sample project config

```toml
[general]
mode = "deterministic"
format = "both"
theme = "default"
strict_quality = true

[git]
base_branch = "main"
include_branch_context = true

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

[privacy]
telemetry = false
```
