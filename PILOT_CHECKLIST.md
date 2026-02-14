# HackLuminary v2.2 Pilot Checklist

Use this checklist before rolling out to hackathon teams.

## 1) Release Integrity

- [ ] `python -m pytest` passes on macOS and Windows CI.
- [ ] Release artifacts include wheel, sdist, and standalone binaries.
- [ ] `sha256` verification passes for all uploaded artifacts.
- [ ] Signing gate passes for macOS and Windows artifacts.
- [ ] Homebrew and Winget manifests are generated from release version.

## 2) Offline Runtime Verification

- [ ] `hackluminary generate` runs with network disabled.
- [ ] `hackluminary validate` runs with network disabled.
- [ ] `hackluminary studio` runs with network disabled.
- [ ] Exported deck HTML loads without external URLs.

## 3) Visual Quality

- [ ] Run corpus benchmark: `hackluminary images benchmark <CORPUS_DIR>`.
- [ ] Confirm image coverage target is acceptable for pilot corpus.
- [ ] Tune `images.min_confidence` based on benchmark output.
- [ ] Review strict mode failures for actionable remediation quality.

## 4) Studio UX Readiness

- [ ] Evidence panel, draft board, media panel, and presenter mode are keyboard-usable.
- [ ] `Auto-Fix Visuals` and `Fix All` produce deterministic edits.
- [ ] Session autosave/restore works after process restart.

## 5) Telemetry (Opt-In Only)

- [ ] Telemetry is disabled by default in config.
- [ ] Pilot teams explicitly opt in using `hackluminary telemetry enable --endpoint ...`.
- [ ] `hackluminary telemetry status` shows endpoint + queued events.
- [ ] `hackluminary telemetry flush` succeeds for opted-in projects.
- [ ] No source paths, code content, or secrets are sent.

## 6) Hackathon Workflow Fit

- [ ] `hackluminary sample` + `generate --preset demo-day --bundle` under 2 minutes on pilot hardware.
- [ ] `hackluminary package devpost` output is accepted by pilot submission flow.
- [ ] GitHub Action deck generation works on PR and produces downloadable artifacts.

## 7) Pilot Exit Criteria

- [ ] At least 5 pilot teams complete end-to-end flow without manual debugging.
- [ ] At least 80% pilot teams rate output quality as “good” or better.
- [ ] Top 3 friction points are documented and converted into tracked issues.
