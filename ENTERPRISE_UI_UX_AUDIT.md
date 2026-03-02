# Enterprise UI/UX Audit: HackLuminary

**Verdict: Not production-ready for enterprise.** Multiple blockers would fail a formal design review, accessibility audit, or security assessment.

---

## Critical (Blockers)

### 1. `alert()` in Exported Deck

**Location:** `hackluminary/presentation_generator.py` (lines 471–475)

```javascript
function onClaimClick(event) {
  const ids = event.currentTarget.getAttribute('data-evidence') || '';
  if (!ids) return;
  alert('Evidence refs: ' + ids); // local inline UX fallback for exported deck
}
```

- Blocks the main thread and breaks screen readers.
- Unacceptable in any production UI.
- **Required:** Replace with an in-page evidence panel or tooltip that stays in the DOM and is keyboard-accessible.

---

### 2. No Focus Management in Modals

- Image modal and command palette have no focus trap.
- Focus can escape to content behind the overlay.
- No `aria-modal="true"` on the dialog.
- No focus return when closing.
- **Required:** Implement focus trap (first/last tab cycles inside modal), `aria-modal="true"`, and return focus to the trigger on close.

---

### 3. Content Security Policy

**Location:** `hackluminary/presentation_generator.py` (line 90)

```html
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src 'self' data:;">
```

- `style-src 'unsafe-inline'` and `script-src 'unsafe-inline'` weaken CSP.
- **Required:** Move styles to external CSS and scripts to external JS, or use nonces/hashes.

---

### 4. CORS Configuration

**Location:** `hackluminary/studio_server.py` (line 352)

```python
self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1")
```

- Hardcoded to `http://127.0.0.1`; fails for `localhost`, different ports, or IPv6.
- **Required:** Use the request `Origin` when safe, or support configurable allowed origins.

---

### 5. Empty Deck Handling

- With 0 slides, `slides[current]` and `slides.length - 1` can misbehave.
- Jump input `max` can be 0.
- **Required:** Handle 0-slide case with a clear empty state and no JS errors.

---

### 6. Touch Target Size (WCAG 2.5.5)

- Timeline dots: 13×13px.
- Control buttons: ~7px padding.
- WCAG 2.5.5 expects at least 44×44px for touch targets.
- **Required:** Increase size or add padding so effective touch area is ≥44×44px.

---

## High (Must Fix for Enterprise)

### 7. Color Contrast

- `--muted: #a8b2d1` on `--bg: #0b1020` and `--panel: #11172b` likely fails WCAG AA (4.5:1 for normal text).
- **Required:** Measure and adjust until all text meets WCAG AA (or AAA where required).

---

### 8. `color-mix()` Browser Support

- `color-mix(in srgb, ...)` is used widely.
- No fallbacks for older browsers (e.g. Safari < 16.4).
- **Required:** Provide fallback colors or feature detection so older browsers still render correctly.

---

### 9. Hardcoded Theme Values

- `rgba(2, 6, 23, 0.84)` and similar values are hardcoded instead of using theme variables.
- Breaks consistency when switching themes.
- **Required:** Derive overlays and similar colors from theme variables.

---

### 10. Image Error Handling

- No `onerror` for images.
- Broken or missing images leave blank areas with no feedback.
- **Required:** Add error handling and a fallback (placeholder or message).

---

### 11. Print Support

- No `@media print` rules.
- Decks will not print well (backgrounds, layout, toolbar).
- **Required:** Add print styles (e.g. hide toolbar, simplify backgrounds, ensure readability).

---

### 12. Studio Error Handling

- `setMessage(error.message)` only; no structured error UI.
- No retry for failed requests.
- **Required:** Dedicated error UI, retry, and clear recovery paths.

---

## Medium (Enterprise Expectations)

### 13. Design System

- No documented design tokens, spacing scale, or typography scale.
- **Required:** Document tokens and usage for consistency and future theming.

---

### 14. Internationalization

- All strings are hardcoded in English.
- **Required:** Extract strings and support i18n for enterprise deployments.

---

### 15. Loading States

- Studio fetches without loading indicators.
- **Required:** Skeletons or spinners during initial load and API calls.

---

### 16. Reduced Motion

- `scrollIntoView({ behavior: 'smooth' })` ignores `prefers-reduced-motion`.
- **Required:** Use `behavior: 'auto'` when `prefers-reduced-motion: reduce`.

---

### 17. Evidence UX in Deck

- Claim chips only show evidence IDs; no snippet or context.
- **Required:** In-page evidence panel with snippet and source, not `alert()`.

---

### 18. Form Validation

- Jump input accepts any number; no feedback for out-of-range values.
- **Required:** Validate range and show clear error/feedback.

---

## Low (Polish for Enterprise)

### 19. Semantic Structure

- Slides use `<section>` but lack `aria-labelledby` or similar for screen readers.
- **Required:** Add proper landmarks and labels for slide navigation.

---

### 20. Presenter HUD

- No `aria-live="assertive"` for timer overrun.
- **Required:** Use assertive live region for important time updates.

---

### 21. Studio Overlay

- Overlay has no focus trap.
- **Required:** Trap focus when overlay is open.

---

## Summary

| Category  | Count | Status   |
|-----------|-------|----------|
| Critical  | 6     | Blockers |
| High      | 6     | Must fix |
| Medium    | 6     | Expected |
| Low       | 3     | Polish   |

**Recommendation:** Do not ship to enterprise customers until all Critical and High items are addressed. The current implementation is suitable for internal or hackathon use, but not for regulated environments, accessibility compliance, or strict security requirements.
