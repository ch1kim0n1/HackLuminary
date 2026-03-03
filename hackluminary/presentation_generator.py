"""Offline presentation renderers (HTML + Markdown)."""

from __future__ import annotations

import base64
import html
import json
import mimetypes
from pathlib import Path


class PresentationGenerator:
    """Render sanitized slide data into portable formats."""

    THEMES = {
        "default": {
            "bg": "#0b1020",
            "panel": "#11172b",
            "panel_alt": "#0f1526",
            "text": "#eef2ff",
            "muted": "#c5cce8",  # WCAG AA contrast on --bg
            "accent": "#24d3b5",
            "accent2": "#4db2ff",
            "warning": "#f59e0b",
            "danger": "#ef4444",
            "ok": "#22c55e",
            "overlay": "rgba(2, 6, 23, 0.84)",
        },
        "dark": {
            "bg": "#020617",
            "panel": "#0b1223",
            "panel_alt": "#0a1120",
            "text": "#f3f4f6",
            "muted": "#b8bfc9",
            "accent": "#38bdf8",
            "accent2": "#a78bfa",
            "warning": "#f59e0b",
            "danger": "#f87171",
            "ok": "#34d399",
            "overlay": "rgba(2, 6, 23, 0.84)",
        },
        "minimal": {
            "bg": "#f4f7fb",
            "panel": "#ffffff",
            "panel_alt": "#f8fafc",
            "text": "#0f172a",
            "muted": "#475569",
            "accent": "#0ea5a5",
            "accent2": "#0284c7",
            "warning": "#b45309",
            "danger": "#b91c1c",
            "ok": "#15803d",
            "overlay": "rgba(15, 23, 42, 0.84)",
        },
        "colorful": {
            "bg": "#1b1028",
            "panel": "#24173a",
            "panel_alt": "#2f1c48",
            "text": "#faf5ff",
            "muted": "#e9d5ff",
            "accent": "#f97316",
            "accent2": "#f43f5e",
            "warning": "#facc15",
            "danger": "#fb7185",
            "ok": "#4ade80",
            "overlay": "rgba(27, 16, 40, 0.84)",
        },
    }

    def __init__(
        self,
        slides: list[dict],
        metadata: dict,
        theme: str = "default",
        project_root: Path | None = None,
        evidence: list[dict] | None = None,
        config: dict | None = None,
    ):
        self.slides = slides
        self.metadata = metadata
        self.theme_name = theme
        self.theme = self._resolve_theme(theme)
        self.project_root = Path(project_root).resolve() if project_root else None
        self.evidence = evidence or []
        self.config = config or {}

    def generate(self) -> str:
        return self.generate_html()

    def generate_html(self) -> str:
        project_name = self._safe(self.metadata.get("project", "HackLuminary"))
        css_vars = self._theme_css_vars()
        slide_count = len(self.slides)
        timeline = "".join(
            f"<button class='timeline-dot' data-goto='{index}' aria-label='Go to slide {index + 1}'></button>"
            for index in range(slide_count)
        )

        evidence_map = self._build_evidence_map()
        evidence_json = json.dumps(evidence_map).replace("</", "<\\/")

        if slide_count == 0:
            sections = "<section class='slide slide-content'><h2>No slides</h2><p class='subtitle'>This presentation has no slides yet.</p></section>"
        else:
            sections = "\n".join(
                self._render_html_slide(index, slide) for index, slide in enumerate(self.slides, start=1)
            )

        return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src 'self' data:;\">
<title>{project_name} - HackLuminary Presentation</title>
<style>
:root {{{css_vars}}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  font-family: "Avenir Next", "Segoe UI", "SF Pro Text", system-ui, sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
}}
@supports (color: color-mix(in srgb, red, blue)) {{
  body {{
    background:
      radial-gradient(circle at 20% 10%, color-mix(in srgb, var(--accent2) 20%, transparent), transparent 45%),
      radial-gradient(circle at 80% 90%, color-mix(in srgb, var(--accent) 20%, transparent), transparent 50%),
      var(--bg);
  }}
}}
.skip-link {{
  position: absolute;
  top: -40px;
  left: 10px;
  background: var(--accent);
  color: #001b17;
  padding: 8px 10px;
  border-radius: 8px;
}}
.skip-link:focus {{ top: 10px; z-index: 9999; }}
.deck {{
  max-width: 1160px;
  margin: 0 auto;
  padding: 20px 16px 120px;
}}
.slide {{
  margin: 16px 0;
  border-radius: 22px;
  background: linear-gradient(165deg, var(--panel), var(--panel_alt));
  border: 1px solid color-mix(in srgb, var(--accent) 32%, transparent);
  padding: 32px 32px;
  box-shadow: 0 20px 52px rgba(2, 6, 23, 0.36);
  position: relative;
  display: flex;
  flex-direction: column;
}}
.slide.slide-title {{
  min-height: 88vh;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  border: none;
  border-radius: 22px;
  overflow: hidden;
  background:
    radial-gradient(ellipse at 30% 40%, color-mix(in srgb, var(--accent2) 28%, transparent), transparent 65%),
    radial-gradient(ellipse at 75% 70%, color-mix(in srgb, var(--accent) 24%, transparent), transparent 60%),
    linear-gradient(160deg, var(--panel), var(--panel_alt));
  box-shadow:
    0 0 0 1px color-mix(in srgb, var(--accent2) 40%, transparent),
    0 32px 80px rgba(2, 6, 23, 0.60);
}}
.slide.slide-title .title-hero {{
  max-width: 820px;
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
}}
.slide.slide-title .title-logo {{
    max-width: 120px;
    max-height: 120px;
}}
.slide.slide-title h1 {{
  font-size: clamp(3rem, 7vw, 5.5rem);
  letter-spacing: -0.03em;
  background: linear-gradient(135deg, var(--text) 40%, var(--accent2));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 18px;
}}
.slide.slide-title .subtitle {{
  font-size: clamp(1rem, 1.8vw, 1.35rem);
  color: var(--muted);
  max-width: 60ch;
  margin: 0 auto;
  line-height: 1.7;
}}
.slide h1, .slide h2 {{ margin: 0 0 20px; line-height: 1.18; letter-spacing: -0.015em; }}
.slide h1 {{ font-size: clamp(2rem, 3.2vw, 3.2rem); }}
.slide h2 {{ font-size: clamp(1.5rem, 2.3vw, 2.4rem); }}
.subtitle {{ font-size: 1.08rem; line-height: 1.6; color: var(--muted); max-width: 90ch; }}
.content {{ font-size: 1.08rem; line-height: 1.8; }}
.content p {{ margin: 0 0 14px; }}
.content ul {{ margin: 10px 0; padding-left: 0; list-style: none; }}
.content ul li {{
  margin: 8px 0;
  padding: 12px 16px;
  background: color-mix(in srgb, var(--panel_alt) 90%, white 10%);
  border: 1px solid color-mix(in srgb, var(--accent) 20%, transparent);
  border-radius: 12px;
  line-height: 1.6;
}}
.content strong {{ color: var(--accent2); font-weight: 700; }}
.content code {{ font-family: "SF Mono", Menlo, Consolas, monospace; font-size: 0.88em;
  background: color-mix(in srgb, var(--accent2) 15%, transparent);
  padding: 2px 6px; border-radius: 5px; }}
.content blockquote {{
    border-left: 4px solid var(--accent);
    margin: 16px 0;
    padding: 8px 16px;
    background: color-mix(in srgb, var(--accent) 10%, transparent);
    border-radius: 0 8px 8px 0;
}}
.slide-list {{ margin: 0; padding-left: 1.1rem; columns: 2 320px; column-gap: 1.8rem; }}
.slide-list li {{
  break-inside: avoid;
  margin: 0.52rem 0;
  line-height: 1.6;
  background: color-mix(in srgb, var(--panel_alt) 90%, white 10%);
  border: 1px solid color-mix(in srgb, var(--accent) 20%, transparent);
  border-radius: 12px;
  padding: 12px 16px 12px 42px;
  list-style: none;
  position: relative;
}}
.slide-list li::before {{
  content: "—";
  position: absolute;
  left: 14px;
  top: 12px;
  color: var(--accent2);
  font-weight: 700;
  font-size: 0.85em;
  line-height: 1.6;
}}
.slide.slide-problem, [data-slide-id="problem"] {{ border-left: 5px solid var(--danger); }}
.slide.slide-solution, [data-slide-id="solution"] {{ border-left: 5px solid var(--ok); }}
.slide.slide-tech, [data-slide-id="tech"] {{ border-left: 5px solid var(--accent2); }}
.slide.slide-delta, [data-slide-id="delta"] {{ border-left: 5px solid var(--warning); }}
[data-slide-id="demo"] {{ border-left: 5px solid var(--accent); }}
[data-slide-id="impact"] {{ border-left: 5px solid var(--warning); }}
[data-slide-id="future"] {{ border-left: 5px solid var(--accent); }}
[data-slide-id="problem"] h2 {{ color: var(--danger); }}
[data-slide-id="solution"] h2 {{ color: var(--ok); }}
[data-slide-id="tech"] h2 {{ color: var(--accent2); }}
[data-slide-id="demo"] h2 {{ color: var(--accent); }}
[data-slide-id="impact"] h2 {{ color: var(--warning); }}
[data-slide-id="future"] h2 {{ color: var(--accent); }}
.slide.slide-closing {{
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  background:
    radial-gradient(ellipse at 60% 30%, color-mix(in srgb, var(--ok) 15%, transparent), transparent 60%),
    linear-gradient(160deg, var(--panel), var(--panel_alt));
  border-color: color-mix(in srgb, var(--ok) 30%, transparent);
  padding: 80px 40px;
}}
.closing-stats {{
  display: flex;
  gap: 10px;
  justify-content: center;
  align-items: center;
  margin-top: 22px;
  flex-wrap: wrap;
}}
.stat-item {{
  font-size: 0.92rem;
  color: var(--muted);
  letter-spacing: 0.02em;
}}
.stat-sep {{
  color: color-mix(in srgb, var(--muted) 40%, transparent);
  font-size: 0.85rem;
  user-select: none;
}}
.slide-body {{
    flex: 1;
}}
.slide-layout-default {{
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(280px, 0.8fr);
  gap: 18px;
  align-items: start;
  height: 100%;
}}
.slide-layout-centered {{
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    height: 100%;
}}
.slide-layout-two-col {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
    align-items: start;
    height: 100%;
}}
.slide-main {{ min-width: 0; }}
.visual-panel {{
  border: 1px solid color-mix(in srgb, var(--accent2) 24%, transparent);
  border-radius: 14px;
  background: color-mix(in srgb, var(--panel_alt) 92%, black 8%);
  padding: 10px;
  display: grid;
  gap: 10px;
}}
.visual-item {{ margin: 0; }}
.visual-thumb {{
  width: 100%;
  border: 0;
  background: transparent;
  padding: 0;
  cursor: zoom-in;
}}
.visual-thumb img {{
  width: 100%;
  height: auto;
  border-radius: 10px;
  border: 1px solid color-mix(in srgb, var(--accent2) 30%, transparent);
  display: block;
}}
.visual-caption {{
  font-size: 0.8rem;
  color: var(--muted);
  margin-top: 6px;
  line-height: 1.5;
}}
.image-modal {{
  position: fixed;
  inset: 0;
  background: var(--overlay);
  display: none;
  align-items: center;
  justify-content: center;
  z-index: 90;
  padding: 24px;
}}
.image-modal.visible {{ display: flex; }}
.image-modal-card {{
  max-width: min(96vw, 1200px);
  max-height: 92vh;
  background: color-mix(in srgb, var(--panel) 92%, black 8%);
  border: 1px solid color-mix(in srgb, var(--accent2) 30%, transparent);
  border-radius: 14px;
  padding: 12px;
}}
.image-modal-card img {{
  max-width: 100%;
  max-height: 76vh;
  border-radius: 10px;
  display: block;
  margin: 0 auto;
}}
.image-modal-caption {{
  color: var(--muted);
  font-size: 0.86rem;
  margin-top: 8px;
  text-align: center;
}}
.claims {{ margin-top: 18px; display: none; flex-wrap: wrap; gap: 8px; }}
body.evidence-mode .claims {{ display: flex; }}
.claim-chip {{
  border: 1px solid color-mix(in srgb, var(--accent) 42%, transparent);
  background: color-mix(in srgb, var(--panel_alt) 88%, var(--accent) 12%);
  color: var(--text);
  border-radius: 999px;
  padding: 10px 16px;
  min-height: 44px;
  font-size: 0.82rem;
  cursor: pointer;
}}
.evidence-strip {{ margin-top: 16px; display: none; gap: 8px; flex-wrap: wrap; }}
body.evidence-mode .evidence-strip {{ display: flex; }}
.evidence-badge {{
  display: inline-block;
  font-size: 0.75rem;
  border-radius: 6px;
  border: 1px solid color-mix(in srgb, var(--accent2) 35%, transparent);
  color: var(--muted);
  padding: 4px 7px;
}}
.speaker-notes {{
  margin-top: 12px;
  border-top: 1px dashed color-mix(in srgb, var(--accent) 28%, transparent);
  padding-top: 10px;
  color: var(--muted);
  display: none;
}}
body.presenter-mode .speaker-notes {{ display: block; }}
.meta {{
  margin-top: 16px;
  padding-top: 9px;
  border-top: 1px dashed color-mix(in srgb, var(--accent2) 28%, transparent);
  font-size: 0.78rem;
  color: color-mix(in srgb, var(--muted) 60%, transparent);
  letter-spacing: 0.04em;
}}
.toolbar {{
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: color-mix(in srgb, var(--bg) 85%, #000 15%);
  border-top: 1px solid color-mix(in srgb, var(--accent) 25%, transparent);
  padding: 9px 12px;
  display: flex;
  gap: 8px;
  justify-content: center;
  align-items: center;
  z-index: 50;
}}
.control-btn {{
  border: 1px solid color-mix(in srgb, var(--accent) 50%, transparent);
  background: color-mix(in srgb, var(--panel) 84%, var(--accent) 16%);
  color: var(--text);
  border-radius: 9px;
  padding: 12px 18px;
  min-height: 44px;
  min-width: 44px;
  cursor: pointer;
}}
.timeline {{ display: flex; gap: 6px; margin-left: 8px; align-items: center; }}
.timeline-dot {{
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid color-mix(in srgb, var(--accent2) 52%, transparent);
  background: transparent;
  padding: 0;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.15s, transform 0.15s;
}}
.timeline-dot:hover {{ background: color-mix(in srgb, var(--accent2) 40%, transparent); transform: scale(1.3); }}
.timeline-dot.active {{ background: var(--accent2); transform: scale(1.1); }}
.presenter-hud {{
  position: fixed;
  top: 12px;
  right: 12px;
  width: min(400px, 42vw);
  background: color-mix(in srgb, var(--panel) 92%, black 8%);
  border: 1px solid color-mix(in srgb, var(--accent) 24%, transparent);
  border-radius: 12px;
  padding: 12px;
  z-index: 60;
  display: none;
}}
body.presenter-mode .presenter-hud {{ display: block; }}
.hud-title {{ margin: 0 0 8px; font-size: 0.95rem; color: var(--muted); }}
.hud-main, .hud-next {{
  padding: 8px;
  border-radius: 8px;
  background: color-mix(in srgb, var(--panel_alt) 88%, black 12%);
  margin-bottom: 8px;
  font-size: 0.9rem;
}}
.hud-row {{ display: flex; gap: 8px; align-items: center; margin-top: 8px; }}
.timer {{ font-weight: 700; letter-spacing: 0.02em; min-width: 76px; }}
.command-palette {{
  position: fixed;
  inset: 0;
  background: var(--overlay);
  display: none;
  align-items: center;
  justify-content: center;
  z-index: 70;
}}
.command-body {{
  width: min(680px, 92vw);
  background: var(--panel);
  border: 1px solid color-mix(in srgb, var(--accent2) 35%, transparent);
  border-radius: 12px;
  padding: 18px;
}}
.command-palette.visible {{ display: flex; }}
code {{ font-family: "SF Mono", Menlo, Consolas, monospace; font-size: 0.85em; }}
@media (max-width: 900px) {{
  .slide-list {{ columns: 1; }}
  .slide-layout {{ grid-template-columns: 1fr; }}
  .presenter-hud {{ width: calc(100vw - 24px); right: 12px; left: 12px; }}
}}
@media (prefers-reduced-motion: reduce) {{
  * {{ scroll-behavior: auto !important; transition: none !important; animation: none !important; }}
}}
@media print {{
  .toolbar, .presenter-hud, .command-palette, .image-modal, .skip-link, .evidence-panel-overlay {{
    display: none !important;
  }}
  body {{ background: var(--bg); }}
  .slide {{ box-shadow: none; break-inside: avoid; }}
}}
.evidence-panel-overlay {{
  position: fixed;
  inset: 0;
  background: var(--overlay);
  display: none;
  align-items: center;
  justify-content: center;
  z-index: 95;
  padding: 24px;
}}
.evidence-panel-overlay.visible {{ display: flex; }}
.evidence-panel {{
  max-width: min(560px, 92vw);
  max-height: 80vh;
  overflow: auto;
  background: var(--panel);
  border: 1px solid color-mix(in srgb, var(--accent2) 35%, transparent);
  border-radius: 14px;
  padding: 20px;
}}
.evidence-panel h3 {{ margin: 0 0 12px; font-size: 1rem; }}
.evidence-panel-item {{
  margin: 12px 0;
  padding: 12px;
  border-radius: 10px;
  background: color-mix(in srgb, var(--panel_alt) 92%, black 8%);
  border: 1px solid color-mix(in srgb, var(--accent2) 22%, transparent);
}}
.evidence-panel-item .id {{ font-weight: 600; color: var(--accent2); }}
.evidence-panel-item .snippet {{ font-size: 0.88rem; white-space: pre-wrap; margin-top: 6px; }}
.visual-thumb img[data-error="true"] {{
  min-height: 80px;
  background: color-mix(in srgb, var(--panel_alt) 90%, black 10%);
  object-fit: none;
}}
</style>
</head>
<body>
<a href="#deck" class="skip-link">Skip to slides</a>
<main class="deck" id="deck" role="main">{sections}</main>
<aside class="presenter-hud" aria-live="polite" aria-label="Presenter HUD">
  <p class="hud-title">Presenter</p>
  <div class="hud-main" id="hudCurrent">Current: -</div>
  <div class="hud-next" id="hudNext">Next: -</div>
  <div class="hud-row">
    <span class="timer" id="hudTimer" aria-live="assertive" aria-atomic="true">00:00</span>
    <button class="control-btn" id="timerStart">Start</button>
    <button class="control-btn" id="timerPause">Pause</button>
    <button class="control-btn" id="timerReset">Reset</button>
  </div>
  <div class="hud-row">
    <label for="jumpInput">Jump</label>
    <input id="jumpInput" type="number" min="1" max="{max(1, slide_count)}" style="width:70px;" />
    <button class="control-btn" id="jumpBtn">Go</button>
  </div>
</aside>
<div class="command-palette" id="palette" aria-hidden="true" role="dialog" aria-modal="true" aria-label="Keyboard shortcuts">
  <div class="command-body">
    <h3>Keyboard Shortcuts</h3>
    <p><code>→/↓/Space</code> next, <code>←/↑</code> previous, <code>Home/End</code> first/last</p>
    <p><code>P</code> presenter mode, <code>?</code> command palette, <code>J</code> jump prompt</p>
    <p><code>Esc</code> close overlays</p>
  </div>
</div>
<div class="toolbar" role="navigation" aria-label="Slide controls">
  <button class="control-btn" data-nav="first">First</button>
  <button class="control-btn" data-nav="prev">Prev</button>
  <button class="control-btn" data-nav="next">Next</button>
  <button class="control-btn" data-nav="last">Last</button>
  <button class="control-btn" id="togglePresenter">Presenter</button>
  <button class="control-btn" id="togglePalette">Shortcuts</button>
  <button class="control-btn" id="toggleEvidence" title="Show/hide evidence references">Evidence</button>
  <div class="timeline" id="timeline">{timeline}</div>
</div>
<div class="image-modal" id="imageModal" aria-hidden="true" role="dialog" aria-modal="true" aria-label="Image preview">
  <div class="image-modal-card">
    <img id="imageModalImg" alt="" />
    <div class="image-modal-caption" id="imageModalCaption"></div>
    <div style="text-align:center; margin-top:10px;">
      <button class="control-btn" id="closeImageModal">Close</button>
    </div>
  </div>
</div>
<div class="evidence-panel-overlay" id="evidencePanel" aria-hidden="true" role="dialog" aria-modal="true" aria-labelledby="evidencePanelTitle" aria-label="Evidence references">
  <div class="evidence-panel">
    <h3 id="evidencePanelTitle">Evidence</h3>
    <div id="evidencePanelContent"></div>
    <button class="control-btn" id="closeEvidencePanel" style="margin-top:12px;">Close</button>
  </div>
</div>
<script type="application/json" id="evidenceData">{evidence_json}</script>
<script>
(() => {{
  const slides = Array.from(document.querySelectorAll('.slide'));
  const timelineDots = Array.from(document.querySelectorAll('.timeline-dot'));
  const palette = document.getElementById('palette');
  const imageModal = document.getElementById('imageModal');
  const imageModalImg = document.getElementById('imageModalImg');
  const imageModalCaption = document.getElementById('imageModalCaption');
  const hudCurrent = document.getElementById('hudCurrent');
  const hudNext = document.getElementById('hudNext');
  const timerEl = document.getElementById('hudTimer');
  const jumpInput = document.getElementById('jumpInput');

  let current = 0;
  let timerSeconds = 0;
  let timerRef = null;

  function fmt(s) {{
    const mm = String(Math.floor(s / 60)).padStart(2, '0');
    const ss = String(s % 60).padStart(2, '0');
    return mm + ':' + ss;
  }}

  function updateTimer() {{
    timerEl.textContent = fmt(timerSeconds);
  }}

  function startTimer() {{
    if (timerRef) return;
    timerRef = setInterval(() => {{ timerSeconds += 1; updateTimer(); }}, 1000);
  }}

  function pauseTimer() {{
    if (!timerRef) return;
    clearInterval(timerRef);
    timerRef = null;
  }}

  function resetTimer() {{
    pauseTimer();
    timerSeconds = 0;
    updateTimer();
  }}

  function refreshHUD() {{
    const currTitle = slides[current]?.querySelector('h1,h2')?.textContent || '-';
    const nextTitle = slides[current + 1]?.querySelector('h1,h2')?.textContent || 'End';
    hudCurrent.textContent = 'Current: ' + currTitle;
    hudNext.textContent = 'Next: ' + nextTitle;

    timelineDots.forEach((dot, idx) => {{
      if (idx === current) dot.classList.add('active');
      else dot.classList.remove('active');
    }});
  }}

  const prefersReducedMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function go(idx) {{
    if (!slides.length) return;
    current = Math.max(0, Math.min(idx, slides.length - 1));
    slides[current].scrollIntoView({{ behavior: prefersReducedMotion() ? 'auto' : 'smooth', block: 'start' }});
    refreshHUD();
  }}

  function togglePresenter() {{
    document.body.classList.toggle('presenter-mode');
    refreshHUD();
  }}

  let palettePrevFocus = null;
  function togglePalette(show) {{
    const visible = typeof show === 'boolean' ? show : !palette.classList.contains('visible');
    palette.classList.toggle('visible', visible);
    palette.setAttribute('aria-hidden', visible ? 'false' : 'true');
    if (visible) {{
      palettePrevFocus = document.activeElement;
      const firstFocus = palette.querySelector('button, [href], input');
      if (firstFocus) firstFocus.focus();
      palette._keyHandler = (e) => {{
        if (e.key === 'Tab') {{
          const focusable = palette.querySelectorAll('button, [href], input');
          const first = focusable[0], last = focusable[focusable.length - 1];
          if (e.shiftKey && document.activeElement === first) {{ e.preventDefault(); last?.focus(); }}
          else if (!e.shiftKey && document.activeElement === last) {{ e.preventDefault(); first?.focus(); }}
        }}
      }};
      palette.addEventListener('keydown', palette._keyHandler);
    }} else {{
      if (palette._keyHandler) {{ palette.removeEventListener('keydown', palette._keyHandler); palette._keyHandler = null; }}
      if (palettePrevFocus && palettePrevFocus.focus) palettePrevFocus.focus();
      palettePrevFocus = null;
    }}
  }}

  let imageModalPrevFocus = null;
  function openImageModal(src, alt, caption) {{
    if (!imageModal || !imageModalImg || !imageModalCaption) return;
    imageModalPrevFocus = document.activeElement;
    imageModalImg.src = src || '';
    imageModalImg.alt = alt || '';
    imageModalImg.removeAttribute('data-error');
    imageModalCaption.textContent = caption || alt || '';
    imageModal.classList.add('visible');
    imageModal.setAttribute('aria-hidden', 'false');
    const closeBtn = document.getElementById('closeImageModal');
    if (closeBtn) {{ closeBtn.focus(); trapFocus(imageModal); }}
  }}

  function closeImageModal() {{
    if (!imageModal || !imageModalImg) return;
    imageModal.classList.remove('visible');
    imageModal.setAttribute('aria-hidden', 'true');
    imageModalImg.src = '';
    if (imageModal._keyHandler) {{
      imageModal.removeEventListener('keydown', imageModal._keyHandler);
      imageModal._keyHandler = null;
    }}
    if (imageModalPrevFocus && imageModalPrevFocus.focus) imageModalPrevFocus.focus();
    imageModalPrevFocus = null;
  }}

  imageModalImg?.addEventListener('error', () => {{
    if (imageModalImg) imageModalImg.setAttribute('data-error', 'true');
    imageModalCaption.textContent = 'Image failed to load';
  }});

  function getEvidenceData() {{
    try {{
      const el = document.getElementById('evidenceData');
      return el ? JSON.parse(el.textContent || '{{}}') : {{}};
    }} catch {{ return {{}}; }}
  }}

  function openEvidencePanel(ids) {{
    const panel = document.getElementById('evidencePanel');
    const content = document.getElementById('evidencePanelContent');
    if (!panel || !content) return;
    const idList = String(ids || '').split(',').map(s => s.trim()).filter(Boolean);
    const data = getEvidenceData();
    let html = '';
    idList.forEach(id => {{
      const ev = data[id] || {{}};
      html += '<div class="evidence-panel-item"><span class="id">' + escapeHtml(id) + '</span>';
      if (ev.source_path) html += '<div class="muted">' + escapeHtml(ev.source_path) + '</div>';
      if (ev.snippet) html += '<pre class="snippet">' + escapeHtml(ev.snippet) + '</pre>';
      if (!ev.snippet && !ev.source_path) html += '<span class="muted">No details</span>';
      html += '</div>';
    }});
    content.innerHTML = html || '<p class="muted">No evidence details</p>';
    panel.classList.add('visible');
    panel.setAttribute('aria-hidden', 'false');
    const closeBtn = document.getElementById('closeEvidencePanel');
    if (closeBtn) {{ closeBtn.focus(); trapFocus(panel); }}
  }}

  function closeEvidencePanel() {{
    const panel = document.getElementById('evidencePanel');
    if (!panel) return;
    panel.classList.remove('visible');
    panel.setAttribute('aria-hidden', 'true');
    releaseFocus();
  }}

  function escapeHtml(s) {{
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
  }}

  let focusTrapPrev = null;
  function trapFocus(container) {{
    focusTrapPrev = document.activeElement;
    const focusable = container.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (first) first.focus();
    container._keyHandler = (e) => {{
      if (e.key !== 'Tab') return;
      if (e.shiftKey) {{ if (document.activeElement === first) {{ e.preventDefault(); last?.focus(); }} }}
      else {{ if (document.activeElement === last) {{ e.preventDefault(); first?.focus(); }} }}
    }};
    container.addEventListener('keydown', container._keyHandler);
  }}

  function releaseFocus() {{
    const panel = document.getElementById('evidencePanel');
    if (panel && panel._keyHandler) {{
      panel.removeEventListener('keydown', panel._keyHandler);
      panel._keyHandler = null;
    }}
    if (focusTrapPrev && focusTrapPrev.focus) focusTrapPrev.focus();
    focusTrapPrev = null;
  }}

  function onClaimClick(event) {{
    const ids = event.currentTarget.getAttribute('data-evidence') || '';
    if (!ids) return;
    openEvidencePanel(ids);
  }}

  document.querySelectorAll('.claim-chip').forEach((chip) => chip.addEventListener('click', onClaimClick));
  document.getElementById('closeEvidencePanel')?.addEventListener('click', closeEvidencePanel);
  document.getElementById('evidencePanel')?.addEventListener('click', (e) => {{ if (e.target.id === 'evidencePanel') closeEvidencePanel(); }});

  document.addEventListener('keydown', (event) => {{
    if (event.key === '?' ) {{ event.preventDefault(); togglePalette(); return; }}
    if (event.key === 'Escape') {{
      if (document.getElementById('evidencePanel')?.classList.contains('visible')) {{ closeEvidencePanel(); return; }}
      if (imageModal?.classList.contains('visible')) {{ closeImageModal(); return; }}
      togglePalette(false);
      return;
    }}
    if (event.key.toLowerCase() === 'p') {{ event.preventDefault(); togglePresenter(); return; }}
    if (event.key.toLowerCase() === 'j') {{ event.preventDefault(); jumpInput?.focus(); return; }}

    if (['ArrowRight', 'ArrowDown', ' '].includes(event.key)) {{ event.preventDefault(); go(current + 1); }}
    if (['ArrowLeft', 'ArrowUp'].includes(event.key)) {{ event.preventDefault(); go(current - 1); }}
    if (event.key === 'Home') {{ event.preventDefault(); go(0); }}
    if (event.key === 'End') {{ event.preventDefault(); go(slides.length - 1); }}
  }});

  document.querySelectorAll('[data-nav]').forEach((button) => {{
    button.addEventListener('click', () => {{
      const nav = button.getAttribute('data-nav');
      if (nav === 'first') go(0);
      if (nav === 'prev') go(current - 1);
      if (nav === 'next') go(current + 1);
      if (nav === 'last') go(slides.length - 1);
    }});
  }});

  timelineDots.forEach((dot) => {{
    dot.addEventListener('click', () => {{
      const target = Number(dot.getAttribute('data-goto') || '0');
      go(target);
    }});
  }});

  document.getElementById('togglePresenter')?.addEventListener('click', togglePresenter);
  document.getElementById('togglePalette')?.addEventListener('click', () => togglePalette());
  document.getElementById('toggleEvidence')?.addEventListener('click', () => {{
    document.body.classList.toggle('evidence-mode');
  }});
  document.getElementById('closeImageModal')?.addEventListener('click', closeImageModal);
  imageModal?.addEventListener('click', (event) => {{
    if (event.target === imageModal) closeImageModal();
  }});

  document.querySelectorAll('.visual-thumb').forEach((button) => {{
    button.addEventListener('click', () => {{
      const src = button.getAttribute('data-modal-src') || '';
      const alt = button.getAttribute('data-modal-alt') || '';
      const caption = button.getAttribute('data-modal-caption') || '';
      if (src) openImageModal(src, alt, caption);
    }});
  }});

  document.getElementById('timerStart')?.addEventListener('click', startTimer);
  document.getElementById('timerPause')?.addEventListener('click', pauseTimer);
  document.getElementById('timerReset')?.addEventListener('click', resetTimer);
  document.getElementById('jumpBtn')?.addEventListener('click', () => {{
    const raw = jumpInput?.value || '1';
    const target = Math.floor(Number(raw));
    const maxSlide = Math.max(1, slides.length);
    if (!Number.isFinite(target) || target < 1 || target > maxSlide) {{
      jumpInput.value = String(current + 1);
      jumpInput.setCustomValidity('Enter 1 to ' + maxSlide);
      jumpInput.reportValidity?.();
      return;
    }}
    jumpInput.setCustomValidity?.('');
    go(target - 1);
  }});

  const observer = new IntersectionObserver((entries) => {{
    entries.forEach((entry) => {{
      if (entry.isIntersecting) {{
        const idx = slides.indexOf(entry.target);
        if (idx >= 0) {{
          current = idx;
          refreshHUD();
        }}
      }}
    }});
  }}, {{ threshold: 0.52 }});

  slides.forEach((slide) => observer.observe(slide));
  updateTimer();
  refreshHUD();
}})();
</script>
</body>
</html>
"""

    def generate_markdown(self) -> str:
        lines = ["---", "marp: true", f"theme: {self.theme_name if self.theme_name != 'auto' else 'default'}", "paginate: true", "---", ""]

        for slide in self.slides:
            lines.append("---")
            lines.append("")

            slide_type = slide.get("type")
            title = str(slide.get("title", "")).strip()
            lines.append(f"# {title}" if slide_type in {"title", "closing"} else f"## {title}")
            lines.append("")

            subtitle = str(slide.get("subtitle", "")).strip()
            content = str(slide.get("content", "")).strip()
            items = slide.get("list_items", [])

            if subtitle:
                lines.append(subtitle)
                lines.append("")

            if content:
                lines.append(content)
                lines.append("")

            if isinstance(items, list) and items:
                for item in items:
                    lines.append(f"- {item}")
                lines.append("")

            visuals = slide.get("visuals", [])
            if isinstance(visuals, list) and visuals:
                lines.append("Visuals:")
                for visual in visuals[:2]:
                    if not isinstance(visual, dict):
                        continue
                    source = str(visual.get("source_path", "")).strip()
                    alt = str(visual.get("alt", "Visual")).strip() or "Visual"
                    caption = str(visual.get("caption", "")).strip()
                    if source:
                        lines.append(f"![{alt}]({source})")
                    if caption:
                        lines.append(f"_{caption}_")
                lines.append("")

            claims = slide.get("claims", [])
            if claims:
                lines.append("Claims:")
                for claim in claims[:8]:
                    claim_text = str(claim.get("text", "")).strip()
                    if claim_text:
                        lines.append(f"- {claim_text}")
                lines.append("")

            refs = slide.get("evidence_refs", [])
            if refs:
                lines.append("Evidence: " + ", ".join(refs))
                lines.append("")

            notes = str(slide.get("notes", "")).strip()
            if notes:
                lines.append("Speaker Notes:")
                lines.append(notes)
                lines.append("")

        return "\n".join(lines).strip() + "\n"

    def _render_html_slide(self, index: int, slide: dict) -> str:
        slide_type = slide.get("type", "content")
        title = self._safe(slide.get("title", ""))
        subtitle = self._safe(slide.get("subtitle", ""))
        content = self._safe(slide.get("content", ""))
        refs = [self._safe(ref) for ref in slide.get("evidence_refs", [])]

        claims = slide.get("claims", []) or []
        claim_chips = []
        for claim in claims[:8]:
            text = self._safe(claim.get("text", ""))
            if not text:
                continue
            claim_refs = claim.get("evidence_refs", refs)
            data_refs = ",".join(self._safe(ref) for ref in claim_refs)
            confidence = claim.get("confidence")
            label = text if len(text) <= 80 else text[:77] + "..."
            claim_chips.append(
                f"<button class='claim-chip' data-evidence='{data_refs}' aria-label='Claim evidence'>{label} ({confidence})</button>"
            )

        evidence_badges = "".join(f"<span class='evidence-badge'>{ref}</span>" for ref in refs)

        notes = self._safe(slide.get("notes", ""))
        notes_html = f"<aside class='speaker-notes' aria-label='Speaker notes'>{notes}</aside>" if notes else ""
        visual_html = self._render_visual_panel(slide)

        if slide_type in {"title", "closing"}:
            subtitle_rendered = self._render_inline_md(slide.get("subtitle", ""))
            if slide_type == "closing":
                stats = slide.get("stats") or {}
                stats_parts: list[str] = []
                if stats.get("files"):
                    stats_parts.append(f"<span class='stat-item'>{self._safe(str(stats['files']))} files</span>")
                if stats.get("lines"):
                    lines_fmt = f"{int(stats['lines']):,}"
                    stats_parts.append(f"<span class='stat-item'>{lines_fmt} lines</span>")
                if stats.get("language"):
                    stats_parts.append(f"<span class='stat-item'>{self._safe(str(stats['language']))}</span>")
                if stats.get("frameworks"):
                    fw = ", ".join(self._safe(str(f)) for f in stats["frameworks"][:3])
                    stats_parts.append(f"<span class='stat-item'>{fw}</span>")
                sep = "<span class='stat-sep'>&middot;</span>"
                stats_html = (
                    f"<div class='closing-stats'>{sep.join(stats_parts)}</div>"
                    if stats_parts else ""
                )
                body = f"<div class='title-hero'><h1>{title}</h1><p class='subtitle'>{subtitle_rendered}</p>{stats_html}</div>"
            else:
                logo_html = self._render_logo()
                body = f"<div class='title-hero'>{logo_html}<div><h1>{title}</h1><p class='subtitle'>{subtitle_rendered}</p></div></div>"
        else:
            layout_class = 'slide-layout-default'
            if not visual_html:
                content_length = len(slide.get("content", "")) + len(slide.get("subtitle", ""))
                if content_length < 200 and not slide.get("list_items"):
                    layout_class = 'slide-layout-centered'
                elif content_length > 400 and not slide.get("list_items"):
                    layout_class = 'slide-layout-two-col'

            if slide_type in {"list", "tech", "delta", "demo", "impact", "future"}:
                items = slide.get("list_items", [])
                list_html = "".join(f"<li>{self._render_inline_md(str(item))}</li>" for item in items)
                main = f"<h2>{title}</h2><ul class='slide-list'>{list_html}</ul>"
            else:
                rendered_content = self._render_md(slide.get("content", ""))
                main = f"<h2>{title}</h2><div class='content'>{rendered_content}</div>"

            if layout_class == 'slide-layout-default':
                body = f"<div class='slide-body {layout_class}'><div class='slide-main'>{main}</div>{visual_html}</div>"
            else:
                body = f"<div class='slide-body {layout_class}'>{main}</div>"



        claims_html = f"<div class='claims'>{''.join(claim_chips)}</div>" if claim_chips else ""
        evidence_html = f"<div class='evidence-strip'>{evidence_badges}</div>" if evidence_badges else ""

        meta = f"<div class='meta'>{index} / {len(self.slides)}</div>"

        title_id = f"slide-title-{index}"
        if slide_type in {"title", "closing"}:
            body = body.replace("<h1>", f"<h1 id='{title_id}'>", 1)
        else:
            body = body.replace("<h2>", f"<h2 id='{title_id}'>", 1)
        slide_id_attr = self._safe(slide.get("id", slide_type))
        return (
            f"<section class='slide slide-{self._safe(slide_type)}' id='slide-{index}' data-index='{index}' "
            f"data-slide-id='{slide_id_attr}' aria-labelledby='{title_id}' role='region'>"
            f"{body}{claims_html}{evidence_html}{notes_html}{meta}</section>"
        )

    def _render_visual_panel(self, slide: dict) -> str:
        visuals = slide.get("visuals", [])
        if not isinstance(visuals, list) or not visuals:
            return ""

        blocks: list[str] = []
        for visual in visuals[:2]:
            if not isinstance(visual, dict):
                continue
            src = self._resolve_visual_src(visual)
            if not src:
                continue

            alt = self._safe(visual.get("alt", "Slide visual"))
            caption = self._safe(visual.get("caption", ""))
            modal_src = self._safe(src)

            caption_html = f"<figcaption class='visual-caption'>{caption}</figcaption>" if caption else ""
            blocks.append(
                "<figure class='visual-item'>"
                f"<button class='visual-thumb' type='button' data-modal-src='{modal_src}' data-modal-alt='{alt}' data-modal-caption='{caption}'>"
                f"<img src='{modal_src}' alt='{alt}' loading='lazy' decoding='async' "
                "onerror=\"this.setAttribute('data-error','true');this.alt='Image failed to load';\" />"
                "</button>"
                f"{caption_html}"
                "</figure>"
            )

        if not blocks:
            return ""

        return f"<aside class='visual-panel' aria-label='Slide visuals'>{''.join(blocks)}</aside>"

    def _resolve_visual_src(self, visual: dict) -> str:
        # Remote-fetched entries carry an embedded data URI — use it directly.
        preview = str(visual.get("preview_data_uri", "")).strip()
        if preview.startswith("data:"):
            return preview

        source = str(visual.get("source_path", "")).strip()
        if not source:
            return ""
        if source.startswith("http://") or source.startswith("https://"):
            return ""
        if source.startswith("data:"):
            return source

        candidate = Path(source)
        if candidate.is_absolute():
            # Absolute paths are allowed for remote-cache files outside project root.
            if not candidate.exists() or not candidate.is_file():
                return ""
        else:
            if not self.project_root:
                return ""
            candidate = (self.project_root / source).resolve()
            try:
                candidate.relative_to(self.project_root)
            except ValueError:
                return ""
            if not candidate.exists() or not candidate.is_file():
                return ""

        mime = str(visual.get("mime", "")).strip()
        if not mime:
            mime = mimetypes.guess_type(str(candidate))[0] or "application/octet-stream"

        raw = candidate.read_bytes()
        encoded = base64.b64encode(raw).decode("ascii")
        return f"data:{mime};base64,{encoded}"

    def _resolve_theme(self, requested: str) -> dict:
        if requested == "custom":
            custom_theme = self.config.get("theme", {}).get("custom", {})
            theme = self.THEMES["default"].copy()
            for key, value in custom_theme.items():
                if value:
                    theme[key] = value
            return theme

        if requested == "auto":
            requested = "default"
        return self.THEMES.get(requested, self.THEMES["default"])

    def _render_logo(self) -> str:
        logo_path = self.config.get("general", {}).get("logo")
        if not logo_path:
            return ""
        
        logo_path = Path(logo_path)
        if not logo_path.is_absolute():
            if not self.project_root:
                return ""
            logo_path = (self.project_root / logo_path).resolve()

        if not logo_path.exists() or not logo_path.is_file():
            return ""

        try:
            raw = logo_path.read_bytes()
            encoded = base64.b64encode(raw).decode("ascii")
            mime = mimetypes.guess_type(str(logo_path))[0] or "application/octet-stream"
            return f"<img src='data:{mime};base64,{encoded}' alt='Logo' class='title-logo' />"
        except Exception:
            return ""


    def _theme_css_vars(self) -> str:
        return "; ".join(f"--{key}: {value}" for key, value in self.theme.items())

    def _build_evidence_map(self) -> dict[str, dict]:
        """Build id -> {title, snippet, source_path} for in-page evidence panel."""
        out: dict[str, dict] = {}
        for item in self.evidence:
            if not isinstance(item, dict):
                continue
            eid = str(item.get("id", "")).strip()
            if not eid:
                continue
            out[eid] = {
                "title": str(item.get("title", eid))[:200],
                "snippet": str(item.get("snippet", ""))[:500],
                "source_path": str(item.get("source_path", ""))[:200],
            }
        return out

    def _render_inline_md(self, raw: str) -> str:
        """Convert inline Markdown (bold, italic, backtick-code) to safe HTML.

        Unlike ``_render_md`` this does not produce block-level wrappers, making
        it safe for use inside ``<li>`` and ``<p>`` elements.
        """
        import re as _re
        text = html.escape(str(raw), quote=False)
        # **bold** / __bold__
        text = _re.sub(
            r"\*\*(.+?)\*\*|__(.+?)__",
            lambda m: f"<strong>{m.group(1) or m.group(2)}</strong>",
            text,
        )
        # *italic* / _italic_ (not inside words)
        text = _re.sub(
            r"(?<![\w])\*(.+?)\*(?![\w])|(?<![\w])_(.+?)_(?![\w])",
            lambda m: f"<em>{m.group(1) or m.group(2)}</em>",
            text,
        )
        # `code`
        text = _re.sub(
            r"`(.+?)`",
            lambda m: f"<code>{html.escape(m.group(1))}</code>",
            text,
        )
        # >>quote<<
        text = _re.sub(
            r">>(.+?)<<",
            lambda m: f"<blockquote>{m.group(1)}</blockquote>",
            text,
        )
        return text

    def _render_md(self, raw: str) -> str:
        """Convert a subset of Markdown to safe HTML for slide content."""
        import re as _re

        # Split into lines and process block-level elements.
        lines = raw.splitlines()
        out: list[str] = []
        in_list = False

        def _inline(text: str) -> str:
            """Apply inline markdown conversions to already-escaped HTML text."""
            # We receive plain text; escape it first, then apply patterns.
            text = html.escape(text, quote=False)
            # **bold** / __bold__
            text = _re.sub(r"\*\*(.+?)\*\*|__(.+?)__",
                           lambda m: f"<strong>{m.group(1) or m.group(2)}</strong>", text)
            # *italic* / _italic_  (not inside words)
            text = _re.sub(r"(?<![\w])\*(.+?)\*(?![\w])|(?<![\w])_(.+?)_(?![\w])",
                           lambda m: f"<em>{m.group(1) or m.group(2)}</em>", text)
            # `code`
            text = _re.sub(r"`(.+?)`",
                           lambda m: f"<code>{html.escape(m.group(1))}</code>", text)
            return text

        for line in lines:
            stripped = line.strip()
            # Bullet list items
            m = _re.match(r"^[-*]\s+(.*)", stripped)
            if m:
                if not in_list:
                    out.append("<ul>")
                    in_list = True
                out.append(f"<li>{_inline(m.group(1))}</li>")
                continue
            # Close list if we were in one
            if in_list:
                out.append("</ul>")
                in_list = False
            if not stripped:
                continue
            out.append(f"<p>{_inline(stripped)}</p>")

        if in_list:
            out.append("</ul>")

        return "\n".join(out)

    def _safe(self, value: object) -> str:
        return html.escape(str(value), quote=True)
