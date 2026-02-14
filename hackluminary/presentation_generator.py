"""Offline presentation renderers (HTML + Markdown)."""

from __future__ import annotations

import html


class PresentationGenerator:
    """Render sanitized slide data into portable formats."""

    THEMES = {
        "default": {
            "bg": "#0b1020",
            "panel": "#11172b",
            "panel_alt": "#0f1526",
            "text": "#eef2ff",
            "muted": "#a8b2d1",
            "accent": "#24d3b5",
            "accent2": "#4db2ff",
            "warning": "#f59e0b",
            "danger": "#ef4444",
            "ok": "#22c55e",
        },
        "dark": {
            "bg": "#020617",
            "panel": "#0b1223",
            "panel_alt": "#0a1120",
            "text": "#f3f4f6",
            "muted": "#9ca3af",
            "accent": "#38bdf8",
            "accent2": "#a78bfa",
            "warning": "#f59e0b",
            "danger": "#f87171",
            "ok": "#34d399",
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
        },
        "colorful": {
            "bg": "#1b1028",
            "panel": "#24173a",
            "panel_alt": "#2f1c48",
            "text": "#faf5ff",
            "muted": "#d8b4fe",
            "accent": "#f97316",
            "accent2": "#f43f5e",
            "warning": "#facc15",
            "danger": "#fb7185",
            "ok": "#4ade80",
        },
    }

    def __init__(self, slides: list[dict], metadata: dict, theme: str = "default"):
        self.slides = slides
        self.metadata = metadata
        self.theme_name = theme
        self.theme = self._resolve_theme(theme)

    def generate(self) -> str:
        return self.generate_html()

    def generate_html(self) -> str:
        project_name = self._safe(self.metadata.get("project", "HackLuminary"))
        css_vars = self._theme_css_vars()
        timeline = "".join(
            f"<button class='timeline-dot' data-goto='{index}' aria-label='Go to slide {index + 1}'></button>"
            for index in range(len(self.slides))
        )

        sections = "\n".join(self._render_html_slide(index, slide) for index, slide in enumerate(self.slides, start=1))

        return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:;\">
<title>{project_name} - HackLuminary Presentation</title>
<style>
:root {{{css_vars}}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  font-family: "Avenir Next", "Segoe UI", "SF Pro Text", system-ui, sans-serif;
  background:
    radial-gradient(circle at 20% 10%, color-mix(in srgb, var(--accent2) 20%, transparent), transparent 45%),
    radial-gradient(circle at 80% 90%, color-mix(in srgb, var(--accent) 20%, transparent), transparent 50%),
    var(--bg);
  color: var(--text);
  min-height: 100vh;
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
  min-height: 76vh;
  margin: 16px 0;
  border-radius: 22px;
  background: linear-gradient(165deg, var(--panel), var(--panel_alt));
  border: 1px solid color-mix(in srgb, var(--accent) 32%, transparent);
  padding: 28px;
  box-shadow: 0 20px 52px rgba(2, 6, 23, 0.36);
  position: relative;
}}
.slide h1, .slide h2 {{ margin: 0 0 14px; line-height: 1.18; letter-spacing: -0.015em; }}
.slide h1 {{ font-size: clamp(2rem, 3.2vw, 3.2rem); }}
.slide h2 {{ font-size: clamp(1.5rem, 2.3vw, 2.4rem); }}
.subtitle {{ font-size: 1.08rem; line-height: 1.6; color: var(--muted); max-width: 90ch; }}
.content {{ font-size: 1.05rem; line-height: 1.72; white-space: pre-wrap; }}
.slide-list {{ margin: 0; padding-left: 1.1rem; columns: 2 320px; column-gap: 1.8rem; }}
.slide-list li {{
  break-inside: avoid;
  margin: 0.48rem 0;
  line-height: 1.6;
  background: color-mix(in srgb, var(--panel_alt) 90%, white 10%);
  border: 1px solid color-mix(in srgb, var(--accent) 20%, transparent);
  border-radius: 12px;
  padding: 10px 12px;
  list-style-position: inside;
}}
.slide.slide-problem {{ border-left: 5px solid var(--danger); }}
.slide.slide-solution {{ border-left: 5px solid var(--ok); }}
.slide.slide-tech {{ border-left: 5px solid var(--accent2); }}
.slide.slide-delta {{ border-left: 5px solid var(--warning); }}
.claims {{ margin-top: 18px; display: flex; flex-wrap: wrap; gap: 8px; }}
.claim-chip {{
  border: 1px solid color-mix(in srgb, var(--accent) 42%, transparent);
  background: color-mix(in srgb, var(--panel_alt) 88%, var(--accent) 12%);
  color: var(--text);
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 0.82rem;
  cursor: pointer;
}}
.evidence-strip {{ margin-top: 16px; display: flex; gap: 8px; flex-wrap: wrap; }}
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
  font-size: 0.8rem;
  color: var(--muted);
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
  padding: 7px 11px;
  cursor: pointer;
}}
.timeline {{ display: flex; gap: 4px; margin-left: 8px; }}
.timeline-dot {{
  width: 13px;
  height: 13px;
  border-radius: 50%;
  border: 1px solid color-mix(in srgb, var(--accent2) 52%, transparent);
  background: transparent;
  padding: 0;
  cursor: pointer;
}}
.timeline-dot.active {{ background: var(--accent2); }}
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
  background: rgba(2, 6, 23, 0.62);
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
  .presenter-hud {{ width: calc(100vw - 24px); right: 12px; left: 12px; }}
}}
@media (prefers-reduced-motion: reduce) {{
  * {{ scroll-behavior: auto !important; transition: none !important; animation: none !important; }}
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
    <span class="timer" id="hudTimer">00:00</span>
    <button class="control-btn" id="timerStart">Start</button>
    <button class="control-btn" id="timerPause">Pause</button>
    <button class="control-btn" id="timerReset">Reset</button>
  </div>
  <div class="hud-row">
    <label for="jumpInput">Jump</label>
    <input id="jumpInput" type="number" min="1" max="{len(self.slides)}" style="width:70px;" />
    <button class="control-btn" id="jumpBtn">Go</button>
  </div>
</aside>
<div class="command-palette" id="palette" aria-hidden="true">
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
  <div class="timeline" id="timeline">{timeline}</div>
</div>
<script>
(() => {{
  const slides = Array.from(document.querySelectorAll('.slide'));
  const timelineDots = Array.from(document.querySelectorAll('.timeline-dot'));
  const palette = document.getElementById('palette');
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

  function go(idx) {{
    if (!slides.length) return;
    current = Math.max(0, Math.min(idx, slides.length - 1));
    slides[current].scrollIntoView({{ behavior: 'smooth', block: 'start' }});
    refreshHUD();
  }}

  function togglePresenter() {{
    document.body.classList.toggle('presenter-mode');
    refreshHUD();
  }}

  function togglePalette(show) {{
    const visible = typeof show === 'boolean' ? show : !palette.classList.contains('visible');
    palette.classList.toggle('visible', visible);
    palette.setAttribute('aria-hidden', visible ? 'false' : 'true');
  }}

  function onClaimClick(event) {{
    const ids = event.currentTarget.getAttribute('data-evidence') || '';
    if (!ids) return;
    alert('Evidence refs: ' + ids); // local inline UX fallback for exported deck
  }}

  document.querySelectorAll('.claim-chip').forEach((chip) => chip.addEventListener('click', onClaimClick));

  document.addEventListener('keydown', (event) => {{
    if (event.key === '?' ) {{ event.preventDefault(); togglePalette(); return; }}
    if (event.key === 'Escape') {{ togglePalette(false); return; }}
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

  document.getElementById('timerStart')?.addEventListener('click', startTimer);
  document.getElementById('timerPause')?.addEventListener('click', pauseTimer);
  document.getElementById('timerReset')?.addEventListener('click', resetTimer);
  document.getElementById('jumpBtn')?.addEventListener('click', () => {{
    const target = Number(jumpInput.value || '1');
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

        if slide_type in {"title", "closing"}:
            body = f"<h1>{title}</h1><p class='subtitle'>{subtitle}</p>"
        elif slide_type in {"list", "tech", "delta", "demo", "impact", "future"}:
            items = slide.get("list_items", [])
            list_html = "".join(f"<li>{self._safe(item)}</li>" for item in items)
            body = f"<h2>{title}</h2><ul class='slide-list'>{list_html}</ul>"
        elif slide_type in {"problem", "solution", "content"}:
            body = f"<h2>{title}</h2><div class='content'>{content}</div>"
        else:
            body = f"<h2>{title}</h2><div class='content'>{content}</div>"

        claims_html = f"<div class='claims'>{''.join(claim_chips)}</div>" if claim_chips else ""
        evidence_html = f"<div class='evidence-strip'>{evidence_badges}</div>" if evidence_badges else ""

        meta = f"<div class='meta'>Slide {index}/{len(self.slides)}"
        if refs:
            meta += f" · {len(refs)} evidence reference(s)"
        meta += "</div>"

        return (
            f"<section class='slide slide-{self._safe(slide_type)}' id='slide-{index}' data-index='{index}'>"
            f"{body}{claims_html}{evidence_html}{notes_html}{meta}</section>"
        )

    def _resolve_theme(self, requested: str) -> dict:
        if requested == "auto":
            requested = "default"
        return self.THEMES.get(requested, self.THEMES["default"])

    def _theme_css_vars(self) -> str:
        return "; ".join(f"--{key}: {value}" for key, value in self.theme.items())

    def _safe(self, value: object) -> str:
        return html.escape(str(value), quote=True)
