(() => {
  const state = {
    context: null,
    slides: [],
    evidence: [],
    media: [],
    session: {},
    mode: "notebook",
    selectedEvidenceId: null,
    selectedMediaId: null,
    selectedSlideId: null,
    readOnly: false,
    autosaveRef: null,
    paneWeights: {
      left: 0.95,
      center: 1.5,
      right: 1.1,
    },
  };

  const els = {
    projectTitle: () => document.getElementById("projectTitle"),
    projectMeta: () => document.getElementById("projectMeta"),
    evidenceList: () => document.getElementById("evidenceList"),
    evidenceSearch: () => document.getElementById("evidenceSearch"),
    evidenceKindFilter: () => document.getElementById("evidenceKindFilter"),
    evidenceSort: () => document.getElementById("evidenceSort"),
    slideList: () => document.getElementById("slideList"),
    slideOutline: () => document.getElementById("slideOutline"),
    citationCard: () => document.getElementById("citationCard"),
    qualityIssues: () => document.getElementById("qualityIssues"),
    fixAllBtn: () => document.getElementById("fixAllBtn"),
    autoFixVisualsBtn: () => document.getElementById("autoFixVisualsBtn"),
    qualityStatus: () => document.getElementById("qualityStatus"),
    branchStatus: () => document.getElementById("branchStatus"),
    messageStatus: () => document.getElementById("messageStatus"),
    mediaList: () => document.getElementById("mediaList"),
    overlay: () => document.getElementById("overlay"),
  };

  async function request(path, options = {}) {
    const response = await fetch(path, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    const data = await response.json();
    if (!response.ok || data.ok === false) {
      throw new Error(data?.error?.message || `Request failed: ${path}`);
    }
    return data.data ?? data;
  }

  function setMessage(text, type = "info") {
    const node = els.messageStatus();
    if (!node) return;
    node.textContent = text;
    node.dataset.type = type;
  }

  function currentSlideIndex() {
    if (!state.selectedSlideId) return 0;
    const idx = state.slides.findIndex((slide) => slide.id === state.selectedSlideId);
    return idx >= 0 ? idx : 0;
  }

  function currentSlideId() {
    return state.slides[currentSlideIndex()]?.id || null;
  }

  function pinnedSetForSlide(slideId) {
    const pins = state.session?.pinned_evidence || {};
    const values = pins[slideId];
    return new Set(Array.isArray(values) ? values : []);
  }

  function evidenceById(id) {
    return state.evidence.find((item) => item.id === id) || null;
  }

  function mediaById(id) {
    return state.media.find((item) => item.id === id) || null;
  }

  function renderContext() {
    if (!state.context) return;
    const titleNode = els.projectTitle();
    const metaNode = els.projectMeta();
    const qualityNode = els.qualityStatus();
    const branchNode = els.branchStatus();

    if (titleNode) titleNode.textContent = `HackLuminary Studio · ${state.context.metadata.project || "Project"}`;
    if (metaNode) {
      const lang = Object.keys(state.context.metadata.languages || {}).join(", ") || "Unknown";
      metaNode.textContent = `${state.context.metadata.file_count} files · ${lang}`;
    }
    if (qualityNode) qualityNode.textContent = `Quality: ${state.context.quality_report.status}`;
    if (branchNode) {
      const git = state.context.git_context || {};
      branchNode.textContent = `Branch: ${git.branch || "n/a"} vs ${git.base_branch || "n/a"}`;
    }

    applyUIConfig();
    renderQualityIssues();
  }

  function extractSlideIdFromIssue(issue) {
    const m = /Slide '([^']+)'/.exec(String(issue || ""));
    return m ? m[1] : "";
  }

  function isFixableIssue(issue) {
    const text = String(issue || "").toLowerCase();
    return (
      text.includes("no evidence references") ||
      text.includes("banned phrase") ||
      text.includes("unsupported claim") ||
      text.includes("evidence coverage") ||
      text.includes("too many list items") ||
      text.includes("is too dense") ||
      text.includes("has many list items") ||
      text.includes("weak title")
    );
  }

  function renderQualityIssues() {
    const container = els.qualityIssues();
    if (!container) return;

    const report = state.context?.quality_report || {};
    const errors = Array.isArray(report.errors) ? report.errors : [];
    const warnings = Array.isArray(report.warnings) ? report.warnings : [];

    if (!errors.length && !warnings.length) {
      container.innerHTML = "<p class='muted'>No issues.</p>";
      return;
    }

    container.innerHTML = "";

    const entries = [
      ...errors.map((text) => ({ level: "error", text })),
      ...warnings.map((text) => ({ level: "warning", text })),
    ];

    entries.forEach((entry) => {
      const row = document.createElement("article");
      row.className = "quality-issue";
      row.dataset.level = entry.level;

      const fixable = isFixableIssue(entry.text);
      row.innerHTML = `
        <div class="quality-issue-row">
          <span>${escapeHtml(entry.text)}</span>
          <button type="button" data-action="fix-issue" ${!fixable || state.readOnly ? "disabled" : ""}>Fix This</button>
        </div>
      `;

      const button = row.querySelector("button[data-action='fix-issue']");
      button?.addEventListener("click", async () => {
        await autoFixIssues([entry.text]);
      });
      container.appendChild(row);
    });
  }

  function applyUIConfig() {
    const ui = state.context?.config?.ui || {};
    const density = String(ui.density || "comfortable");
    const motion = String(ui.motion || "normal");
    const codeScale = Number(ui.code_font_scale || 1.0);
    const defaultTimer = Number(ui.presenter_timer_default_min || 7);

    document.body.dataset.density = density;
    document.body.classList.toggle("motion-none", motion === "none");
    document.documentElement.style.setProperty("--code-scale", String(Math.max(0.8, Math.min(1.6, codeScale))));
    window.HackLuminaryPresenter?.setTargetMinutes(defaultTimer);
  }

  function applyPaneWeights() {
    document.documentElement.style.setProperty("--pane-left", `${state.paneWeights.left}fr`);
    document.documentElement.style.setProperty("--pane-center", `${state.paneWeights.center}fr`);
    document.documentElement.style.setProperty("--pane-right", `${state.paneWeights.right}fr`);
  }

  function resizePanes(direction) {
    const step = 0.1;
    const min = 0.65;
    const max = 2.1;

    if (direction === "left-smaller") state.paneWeights.left = Math.max(min, state.paneWeights.left - step);
    if (direction === "left-larger") state.paneWeights.left = Math.min(max, state.paneWeights.left + step);
    if (direction === "right-smaller") state.paneWeights.right = Math.max(min, state.paneWeights.right - step);
    if (direction === "right-larger") state.paneWeights.right = Math.min(max, state.paneWeights.right + step);

    applyPaneWeights();
    setMessage("Pane layout updated", "ok");
  }

  function compareEvidence(a, b, sortBy) {
    const av = String(a?.[sortBy] || "").toLowerCase();
    const bv = String(b?.[sortBy] || "").toLowerCase();
    return av.localeCompare(bv);
  }

  function renderEvidence() {
    const list = els.evidenceList();
    if (!list) return;

    const query = (els.evidenceSearch()?.value || "").toLowerCase().trim();
    const kindFilter = (els.evidenceKindFilter()?.value || "").toLowerCase().trim();
    const sort = (els.evidenceSort()?.value || "id").trim();
    const sortField = sort === "path" ? "source_path" : (sort === "kind" ? "source_kind" : "id");
    const currentPins = pinnedSetForSlide(currentSlideId());

    const items = state.evidence
      .filter((item) => {
        if (kindFilter && String(item.source_kind || "").toLowerCase() !== kindFilter) return false;
        if (!query) return true;
        return [item.id, item.title, item.source_path, item.snippet]
          .map((v) => String(v || "").toLowerCase())
          .some((v) => v.includes(query));
      })
      .sort((a, b) => compareEvidence(a, b, sortField));

    list.innerHTML = "";

    items.forEach((item) => {
      const row = document.createElement("button");
      row.className = "evidence-row" + (state.selectedEvidenceId === item.id ? " active" : "");
      row.type = "button";
      const isPinned = currentPins.has(item.id);
      row.innerHTML = `
        <div><strong>${escapeHtml(item.title)}</strong></div>
        <div class="evidence-meta">${escapeHtml(item.id)} · ${escapeHtml(item.source_kind || "")}</div>
        <div class="evidence-meta">${isPinned ? "Pinned · " : ""}${escapeHtml(item.source_path || "")}${item.start_line ? `:${item.start_line}` : ""}</div>
        <div class="evidence-snippet">${escapeHtml(item.snippet || "")}</div>
      `;
      row.addEventListener("click", () => selectEvidence(item.id));
      list.appendChild(row);
    });
  }

  function renderMedia() {
    const list = els.mediaList();
    if (!list) return;

    const slideId = currentSlideId();
    const slide = state.slides.find((item) => item.id === slideId) || null;
    const attachedIds = new Set(Array.isArray(slide?.visuals) ? slide.visuals.map((v) => v.id) : []);

    list.innerHTML = "";
    if (!state.media.length) {
      list.innerHTML = "<p class='muted'>No local media indexed.</p>";
      return;
    }

    state.media.forEach((media) => {
      const card = document.createElement("article");
      card.className = "media-card";
      const preview = media.preview_data_uri
        ? `<img src="${escapeAttr(media.preview_data_uri)}" alt="${escapeAttr(media.alt || media.source_path || "media")}" loading="lazy" />`
        : "<div class='muted'>No preview</div>";
      const dims = media.width && media.height ? `${media.width}x${media.height}` : "unknown size";
      const attachedLabel = attachedIds.has(media.id) ? "Attached" : "";

      card.innerHTML = `
        ${preview}
        <div class="media-meta">${escapeHtml(media.source_path || media.id || "")}</div>
        <div class="media-meta">${escapeHtml(media.kind || "repo_image")} · ${escapeHtml(dims)} ${attachedLabel ? "· " + attachedLabel : ""}</div>
        <div class="media-actions">
          <button type="button" data-action="attach-media" data-media-id="${escapeAttr(media.id)}" ${state.readOnly ? "disabled" : ""}>Attach</button>
          <button type="button" data-action="replace-media" data-media-id="${escapeAttr(media.id)}" ${state.readOnly ? "disabled" : ""}>Replace</button>
        </div>
      `;
      list.appendChild(card);
    });

    list.querySelectorAll("button[data-action='attach-media']").forEach((button) => {
      button.addEventListener("click", async () => {
        const mediaId = button.getAttribute("data-media-id");
        if (!mediaId) return;
        await attachMediaToCurrentSlide(mediaId, false);
      });
    });

    list.querySelectorAll("button[data-action='replace-media']").forEach((button) => {
      button.addEventListener("click", async () => {
        const mediaId = button.getAttribute("data-media-id");
        if (!mediaId) return;
        await attachMediaToCurrentSlide(mediaId, true);
      });
    });
  }

  function renderOutline() {
    const outline = els.slideOutline();
    if (!outline) return;
    outline.innerHTML = "";

    state.slides.forEach((slide, idx) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "outline-item" + (slide.id === state.selectedSlideId ? " active" : "");
      button.textContent = `${idx + 1}. ${slide.title || slide.id || "Slide"}`;
      button.addEventListener("click", () => selectSlide(slide.id, true));
      outline.appendChild(button);
    });
  }

  function selectSlide(slideId, focusCard = false) {
    state.selectedSlideId = slideId;
    renderOutline();
    renderSlides();
    renderEvidence();
    renderMedia();
    if (focusCard) {
      const section = document.querySelector(`.slide-card[data-slide-id="${CSS.escape(slideId)}"]`);
      section?.scrollIntoView({ behavior: "smooth", block: "center" });
    }

    const idx = currentSlideIndex();
    const currentTitle = state.slides[idx]?.title || "-";
    const nextTitle = state.slides[idx + 1]?.title || "End";
    window.HackLuminaryPresenter?.setTitles(currentTitle, nextTitle);
  }

  function renderSlides() {
    const list = els.slideList();
    if (!list) return;

    list.innerHTML = "";

    state.slides.forEach((slide, idx) => {
      const card = document.createElement("section");
      card.className = "slide-card" + (slide.id === state.selectedSlideId ? " active" : "");
      card.dataset.slideId = slide.id;
      const claimButtons = (slide.claims || []).map((claim, cidx) => {
        const refs = (claim.evidence_refs || []).join(",");
        const label = String(claim.text || "").slice(0, 90);
        return `<button type="button" class="claim-chip" data-slide="${idx}" data-claim="${cidx}" data-refs="${escapeHtml(refs)}">${escapeHtml(label)}</button>`;
      }).join("");
      const visualSummary = Array.isArray(slide.visuals) && slide.visuals.length
        ? slide.visuals.map((visual) => escapeHtml(visual.source_path || visual.id || "image")).join(", ")
        : "No visuals attached";

      const listText = (slide.list_items || []).join("\n");
      const disableAttr = state.readOnly ? "disabled" : "";

      card.innerHTML = `
        <h3>${idx + 1}. ${escapeHtml(slide.title || slide.id || "Slide")}</h3>
        <div class="slide-fields">
          <label>Title <input data-field="title" data-index="${idx}" value="${escapeAttr(slide.title || "")}" ${disableAttr} /></label>
          ${slide.subtitle !== undefined ? `<label>Subtitle <textarea data-field="subtitle" data-index="${idx}" ${disableAttr}>${escapeHtml(slide.subtitle || "")}</textarea></label>` : ""}
          ${slide.content !== undefined ? `<label>Content <textarea data-field="content" data-index="${idx}" ${disableAttr}>${escapeHtml(slide.content || "")}</textarea></label>` : ""}
          ${slide.list_items ? `<label>List Items (one per line)<textarea data-field="list_items" data-index="${idx}" ${disableAttr}>${escapeHtml(listText)}</textarea></label>` : ""}
          <label>Speaker Notes <textarea data-field="notes" data-index="${idx}" ${disableAttr}>${escapeHtml(slide.notes || "")}</textarea></label>
          <div class="muted">Visuals: ${visualSummary}</div>
          <div class="claims-row">${claimButtons || "<span class='muted'>No claims</span>"}</div>
          <div class="slide-actions">
            <button type="button" data-action="select-slide" data-index="${idx}">Focus</button>
            <button type="button" data-action="move-up" data-index="${idx}" ${idx === 0 || state.readOnly ? "disabled" : ""}>Move Up</button>
            <button type="button" data-action="move-down" data-index="${idx}" ${idx === state.slides.length - 1 || state.readOnly ? "disabled" : ""}>Move Down</button>
            <button type="button" data-action="save-slide" data-index="${idx}" ${disableAttr}>Save Slide</button>
          </div>
        </div>
      `;
      list.appendChild(card);
    });

    list.querySelectorAll("button[data-action='select-slide']").forEach((button) => {
      button.addEventListener("click", () => {
        const idx = Number(button.dataset.index || "0");
        const slide = state.slides[idx];
        if (!slide) return;
        selectSlide(slide.id, false);
      });
    });

    list.querySelectorAll("button[data-action='move-up']").forEach((button) => {
      button.addEventListener("click", async () => {
        const idx = Number(button.dataset.index || "0");
        moveSlide(idx, -1);
        await saveSession({ silent: true });
      });
    });

    list.querySelectorAll("button[data-action='move-down']").forEach((button) => {
      button.addEventListener("click", async () => {
        const idx = Number(button.dataset.index || "0");
        moveSlide(idx, 1);
        await saveSession({ silent: true });
      });
    });

    list.querySelectorAll("button[data-action='save-slide']").forEach((button) => {
      button.addEventListener("click", async () => {
        const idx = Number(button.dataset.index || "0");
        selectSlide(state.slides[idx]?.id || state.selectedSlideId);
        await saveSlide(idx);
      });
    });

    list.querySelectorAll(".claim-chip").forEach((button) => {
      button.addEventListener("click", () => {
        const idx = Number(button.getAttribute("data-slide") || "0");
        const slide = state.slides[idx];
        if (slide) selectSlide(slide.id);
        const refs = String(button.getAttribute("data-refs") || "").split(",").filter(Boolean);
        if (refs.length) {
          selectEvidence(refs[0]);
        }
      });
    });

    list.querySelectorAll(".slide-card").forEach((section) => {
      section.addEventListener("click", () => {
        const slideId = section.getAttribute("data-slide-id");
        if (slideId) selectSlide(slideId);
      });
    });
  }

  function renderCitationCard(item) {
    const card = els.citationCard();
    if (!card) return;

    if (!item) {
      card.innerHTML = "<h3>No citation selected</h3><p class='muted'>Click a claim chip or evidence row.</p>";
      return;
    }

    const slideId = currentSlideId();
    const pinned = slideId ? pinnedSetForSlide(slideId).has(item.id) : false;
    const pinButton = slideId
      ? `<button type="button" data-action="pin-evidence" data-evidence-id="${escapeAttr(item.id)}" ${state.readOnly ? "disabled" : ""}>${pinned ? "Unpin" : "Pin"} for current slide</button>`
      : "";

    card.innerHTML = `
      <h3>${escapeHtml(item.title)}</h3>
      <p class="muted">${escapeHtml(item.id)} · ${escapeHtml(item.source_kind || "")} · ${escapeHtml(item.source_path || "")}</p>
      <p class="muted">${item.start_line ? `Lines ${item.start_line}-${item.end_line || item.start_line}` : "Line context unavailable"}</p>
      <pre>${escapeHtml(item.snippet || "")}</pre>
      <p class="muted">hash: ${escapeHtml(item.snippet_hash || "")}</p>
      ${pinButton}
    `;

    const pinAction = card.querySelector("button[data-action='pin-evidence']");
    pinAction?.addEventListener("click", async () => {
      await toggleEvidencePin(item.id);
    });
  }

  function selectEvidence(id) {
    state.selectedEvidenceId = id;
    renderEvidence();
    renderCitationCard(evidenceById(id));
  }

  async function toggleEvidencePin(evidenceId) {
    const slideId = currentSlideId();
    if (!slideId) {
      setMessage("Select a slide before pinning evidence.", "warn");
      return;
    }
    if (state.readOnly) {
      setMessage("Studio is read-only.", "warn");
      return;
    }

    if (!state.session.pinned_evidence || typeof state.session.pinned_evidence !== "object") {
      state.session.pinned_evidence = {};
    }

    const existing = new Set(Array.isArray(state.session.pinned_evidence[slideId]) ? state.session.pinned_evidence[slideId] : []);
    if (existing.has(evidenceId)) existing.delete(evidenceId);
    else existing.add(evidenceId);

    state.session.pinned_evidence[slideId] = Array.from(existing);
    await saveSession({ silent: true });
    renderEvidence();
    renderCitationCard(evidenceById(evidenceId));
    setMessage(`Evidence ${existing.has(evidenceId) ? "pinned" : "unpinned"}`, "ok");
  }

  function toSlideVisual(slide, media, confidence = 0.9) {
    const refs = Array.isArray(slide?.evidence_refs) ? slide.evidence_refs.slice(0, 3) : [];
    return {
      id: media.id,
      type: "image",
      source_path: media.source_path,
      alt: media.alt || `Visual for ${slide?.title || "slide"}`,
      caption: media.alt || media.source_path || "",
      evidence_refs: refs,
      confidence,
      width: media.width,
      height: media.height,
      sha256: media.sha256,
    };
  }

  async function attachMediaToCurrentSlide(mediaId, replace) {
    if (state.readOnly) {
      setMessage("Studio is read-only.", "warn");
      return;
    }

    const slideId = currentSlideId();
    const slide = state.slides.find((item) => item.id === slideId);
    const media = mediaById(mediaId);
    if (!slide || !media) {
      setMessage("Select a slide and media item first.", "warn");
      return;
    }

    const existing = Array.isArray(slide.visuals) ? [...slide.visuals] : [];
    const visual = toSlideVisual(slide, media);
    let visuals = [];
    if (replace || !existing.length) visuals = [visual];
    else {
      visuals = [existing[0], visual].filter(Boolean).slice(0, 2);
    }

    const payload = await request("/api/slides", {
      method: "POST",
      body: JSON.stringify({ slides: [{ id: slide.id, visuals }] }),
    });
    state.slides = payload.slides || state.slides;
    state.context.quality_report = payload.quality_report || state.context.quality_report;
    renderContext();
    renderOutline();
    renderSlides();
    renderMedia();
    await saveSession({ silent: true });
    setMessage(`${replace ? "Replaced" : "Attached"} visual for ${slide.title || slide.id}`, "ok");
  }

  async function autoFixVisuals() {
    if (state.readOnly) {
      setMessage("Studio is read-only.", "warn");
      return;
    }
    const payload = await request("/api/visuals/auto-fix", {
      method: "POST",
      body: JSON.stringify({ slide_ids: [currentSlideId()] }),
    });
    state.slides = payload.slides || state.slides;
    state.context.quality_report = payload.quality_report || state.context.quality_report;
    renderContext();
    renderOutline();
    renderSlides();
    renderMedia();
    await saveSession({ silent: true });
    setMessage("Auto-fixed visuals for current slide.", "ok");
  }

  function defaultEvidenceRefs() {
    const preferred = ["doc.description", "doc.title", "repo.project", "repo.languages", "git.branch"];
    const available = new Set((state.evidence || []).map((item) => String(item.id || "")));
    const refs = preferred.filter((ref) => available.has(ref));
    if (refs.length) return refs.slice(0, 2);
    const first = state.evidence?.[0]?.id;
    return first ? [first] : [];
  }

  function normalizeText(text) {
    return String(text || "").replace(/\s{2,}/g, " ").replace(/\n{3,}/g, "\n\n").trim();
  }

  function removePhrase(text, phrase) {
    if (!phrase) return normalizeText(text);
    const escaped = phrase.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const re = new RegExp(escaped, "ig");
    return normalizeText(String(text || "").replace(re, ""));
  }

  function fixWeakTitle(slide) {
    const weak = new Set(["overview", "summary", "details", "slide", "content", "misc"]);
    const current = String(slide.title || "").trim();
    const lc = current.toLowerCase();
    if (!current || current.length <= 3 || weak.has(lc)) {
      const slideType = String(slide.type || "Slide");
      slide.title = `${slideType.charAt(0).toUpperCase()}${slideType.slice(1)} Snapshot`;
      return true;
    }
    return false;
  }

  function applyIssueFix(issue, workingSlides, fallbackRefs) {
    const text = String(issue || "");
    const lower = text.toLowerCase();
    const slideId = extractSlideIdFromIssue(text);
    let changed = false;

    const targetSlide = slideId ? workingSlides.find((slide) => slide.id === slideId) : null;
    const targets = targetSlide ? [targetSlide] : workingSlides;

    if (lower.includes("no evidence references") && targetSlide) {
      if (!Array.isArray(targetSlide.evidence_refs) || !targetSlide.evidence_refs.length) {
        targetSlide.evidence_refs = [...fallbackRefs];
        changed = true;
      }
    }

    if (lower.includes("banned phrase")) {
      const phraseMatch = /banned phrase: '([^']+)'/i.exec(text);
      const phrase = phraseMatch ? phraseMatch[1] : "";
      targets.forEach((slide) => {
        const before = JSON.stringify(slide);
        slide.title = removePhrase(slide.title, phrase);
        slide.subtitle = removePhrase(slide.subtitle, phrase);
        slide.content = removePhrase(slide.content, phrase);
        if (Array.isArray(slide.list_items)) {
          slide.list_items = slide.list_items.map((item) => removePhrase(item, phrase)).filter(Boolean);
        }
        if (Array.isArray(slide.claims)) {
          slide.claims = slide.claims.map((claim) => ({
            ...claim,
            text: removePhrase(claim.text, phrase),
          })).filter((claim) => claim.text);
        }
        if (JSON.stringify(slide) !== before) changed = true;
      });
    }

    if (lower.includes("unsupported claim") && targetSlide) {
      if (!Array.isArray(targetSlide.evidence_refs) || !targetSlide.evidence_refs.length) {
        targetSlide.evidence_refs = [...fallbackRefs];
        changed = true;
      }
    }

    if ((lower.includes("too many list items") || lower.includes("has many list items")) && targetSlide) {
      if (Array.isArray(targetSlide.list_items) && targetSlide.list_items.length > 7) {
        targetSlide.list_items = targetSlide.list_items.slice(0, 7);
        changed = true;
      }
    }

    if (lower.includes("is too dense") && targetSlide) {
      const before = JSON.stringify(targetSlide);
      if (targetSlide.content && String(targetSlide.content).length > 700) {
        targetSlide.content = String(targetSlide.content).slice(0, 700).trim() + "...";
      }
      if (Array.isArray(targetSlide.list_items) && targetSlide.list_items.length > 6) {
        targetSlide.list_items = targetSlide.list_items.slice(0, 6);
      }
      if (JSON.stringify(targetSlide) !== before) changed = true;
    }

    if (lower.includes("weak title") && targetSlide) {
      changed = fixWeakTitle(targetSlide) || changed;
    }

    if (lower.includes("evidence coverage")) {
      workingSlides.forEach((slide) => {
        if (["title", "closing"].includes(String(slide.type || ""))) return;
        if (!Array.isArray(slide.evidence_refs) || !slide.evidence_refs.length) {
          slide.evidence_refs = [...fallbackRefs];
          changed = true;
        }
      });
    }

    return changed;
  }

  async function autoFixIssues(issueTexts) {
    if (state.readOnly) {
      setMessage("Studio is read-only.", "warn");
      return;
    }

    const issues = Array.isArray(issueTexts) ? issueTexts : [];
    if (!issues.length) {
      setMessage("No issues to fix.", "warn");
      return;
    }

    const fallbackRefs = defaultEvidenceRefs();
    const working = structuredClone(state.slides);
    let changed = false;

    issues.forEach((issue) => {
      changed = applyIssueFix(issue, working, fallbackRefs) || changed;
    });

    if (!changed) {
      setMessage("No automatic fix available for selected issue(s).", "warn");
      return;
    }

    const patches = [];
    working.forEach((slide, idx) => {
      if (JSON.stringify(slide) !== JSON.stringify(state.slides[idx])) {
        patches.push(slide);
      }
    });

    if (!patches.length) {
      setMessage("No slide changes produced by auto-fix.", "warn");
      return;
    }

    const payload = await request("/api/slides", {
      method: "POST",
      body: JSON.stringify({ slides: patches }),
    });
    state.slides = payload.slides || [];
    state.context.quality_report = payload.quality_report || state.context.quality_report;
    renderContext();
    renderOutline();
    renderSlides();
    renderEvidence();
    renderMedia();
    await saveSession({ silent: true });
    setMessage(`Applied ${patches.length} auto-fix update(s).`, "ok");
  }

  function moveSlide(index, direction) {
    if (state.readOnly) return;
    const target = index + direction;
    if (target < 0 || target >= state.slides.length) return;
    const copy = [...state.slides];
    const [item] = copy.splice(index, 1);
    copy.splice(target, 0, item);
    state.slides = copy;
    state.selectedSlideId = item.id;
    renderOutline();
    renderSlides();
    setMessage(`Moved slide to position ${target + 1}`, "ok");
  }

  async function saveSlide(index) {
    if (state.readOnly) {
      setMessage("Studio is read-only.", "warn");
      return;
    }

    const slide = structuredClone(state.slides[index]);
    const container = els.slideList();
    if (!container || !slide) return;

    const fields = container.querySelectorAll(`[data-index='${index}'][data-field]`);
    fields.forEach((field) => {
      const key = field.getAttribute("data-field");
      if (!key) return;
      if (key === "list_items") {
        slide.list_items = field.value.split("\n").map((line) => line.trim()).filter(Boolean);
      } else {
        slide[key] = field.value;
      }
    });

    const payload = await request("/api/slides", {
      method: "POST",
      body: JSON.stringify({ slides: [slide] }),
    });

    state.slides = payload.slides;
    state.context.quality_report = payload.quality_report;
    renderContext();
    renderOutline();
    renderSlides();
    renderMedia();
    await saveSession({ silent: true });
    setMessage(`Saved slide ${index + 1}`, "ok");
  }

  async function saveSession(options = {}) {
    if (state.readOnly) return;
    const payload = {
      slide_order: state.slides.map((slide) => slide.id),
      note_blocks: Object.fromEntries(state.slides.map((slide) => [slide.id, slide.notes || ""])),
      pinned_evidence: state.session.pinned_evidence || {},
      last_validation: state.context.quality_report || {},
      presenter: {
        timer_minutes: Number(document.getElementById("timerTargetMin")?.value || "7"),
        last_slide_index: currentSlideIndex(),
      },
    };

    const result = await request("/api/session", {
      method: "PUT",
      body: JSON.stringify(payload),
    });
    if (result?.session) {
      state.session = result.session;
    }
    if (!options.silent) setMessage("Session saved", "ok");
  }

  async function validateSlides() {
    const payload = await request("/api/validate", {
      method: "POST",
      body: JSON.stringify({ slides: state.slides }),
    });
    state.context.quality_report = payload.quality_report;
    renderContext();
    setMessage(`Validation: ${payload.quality_report.status}`, payload.quality_report.status === "pass" ? "ok" : "warn");
  }

  async function exportSlides(format) {
    const payload = await request("/api/export", {
      method: "POST",
      body: JSON.stringify({ format, slides: state.slides }),
    });
    setMessage(`Export completed (${format})`, "ok");
    if (payload.paths?.length) {
      setMessage(`Exported: ${payload.paths.join(", ")}`, "ok");
    }
  }

  function bindUI() {
    els.evidenceSearch()?.addEventListener("input", renderEvidence);
    els.evidenceKindFilter()?.addEventListener("change", renderEvidence);
    els.evidenceSort()?.addEventListener("change", renderEvidence);

    document.querySelectorAll(".mode-btn").forEach((button) => {
      button.addEventListener("click", () => {
        const mode = button.getAttribute("data-mode") || "notebook";
        setMode(mode, true);
      });
    });

    document.getElementById("saveSessionBtn")?.addEventListener("click", saveSession);
    document.getElementById("validateBtn")?.addEventListener("click", validateSlides);
    els.fixAllBtn()?.addEventListener("click", async () => {
      const report = state.context?.quality_report || {};
      const issues = [
        ...(Array.isArray(report.errors) ? report.errors : []),
        ...(Array.isArray(report.warnings) ? report.warnings : []),
      ];
      await autoFixIssues(issues);
    });
    els.autoFixVisualsBtn()?.addEventListener("click", autoFixVisuals);

    document.getElementById("exportBtn")?.addEventListener("click", () => {
      const overlay = els.overlay();
      if (overlay) overlay.hidden = false;
    });

    document.querySelectorAll("[data-export]").forEach((button) => {
      button.addEventListener("click", async () => {
        const format = button.getAttribute("data-export") || "html";
        await exportSlides(format);
        const overlay = els.overlay();
        if (overlay) overlay.hidden = true;
      });
    });

    document.getElementById("closeOverlayBtn")?.addEventListener("click", () => {
      const overlay = els.overlay();
      if (overlay) overlay.hidden = true;
    });

    document.addEventListener("keydown", (event) => {
      if (event.altKey && event.shiftKey && event.key === "ArrowLeft") {
        event.preventDefault();
        resizePanes("left-smaller");
      }
      if (event.altKey && event.shiftKey && event.key === "ArrowRight") {
        event.preventDefault();
        resizePanes("left-larger");
      }
      if (event.altKey && event.shiftKey && event.key === "ArrowUp") {
        event.preventDefault();
        resizePanes("right-larger");
      }
      if (event.altKey && event.shiftKey && event.key === "ArrowDown") {
        event.preventDefault();
        resizePanes("right-smaller");
      }
      if (event.ctrlKey && event.key === "ArrowUp") {
        event.preventDefault();
        moveSlide(currentSlideIndex(), -1);
      }
      if (event.ctrlKey && event.key === "ArrowDown") {
        event.preventDefault();
        moveSlide(currentSlideIndex(), 1);
      }
    });
  }

  function setMode(mode, announce = false) {
    if (!["notebook", "deck", "presenter"].includes(mode)) {
      mode = "notebook";
    }
    state.mode = mode;
    document.body.classList.toggle("presenter", mode === "presenter");
    window.HackLuminaryPresenter?.enablePresenterMode(mode === "presenter");
    document.querySelectorAll(".mode-btn").forEach((button) => {
      const active = button.getAttribute("data-mode") === mode;
      button.setAttribute("aria-pressed", active ? "true" : "false");
    });
    if (announce) setMessage(`Mode: ${mode}`);
  }

  function applyReadOnlyMode() {
    if (!state.readOnly) return;
    const saveBtn = document.getElementById("saveSessionBtn");
    if (saveBtn) saveBtn.setAttribute("disabled", "disabled");
    const fixBtn = els.fixAllBtn();
    if (fixBtn) fixBtn.setAttribute("disabled", "disabled");
    const visualBtn = els.autoFixVisualsBtn();
    if (visualBtn) visualBtn.setAttribute("disabled", "disabled");
    setMessage("Read-only mode enabled", "warn");
  }

  function beginAutosave() {
    const sec = Number(state.context?.config?.studio?.autosave_interval_sec || 0);
    if (!Number.isFinite(sec) || sec < 5 || state.readOnly) return;
    if (state.autosaveRef) clearInterval(state.autosaveRef);
    state.autosaveRef = setInterval(() => {
      saveSession({ silent: true }).catch((error) => {
        console.error(error);
      });
    }, sec * 1000);
  }

  async function loadAll() {
    const [context, slides, evidence, media, session] = await Promise.all([
      request("/api/context"),
      request("/api/slides"),
      request("/api/evidence"),
      request("/api/media"),
      request("/api/session"),
    ]);

    state.context = context;
    state.slides = slides.slides || [];
    state.evidence = evidence.evidence || [];
    state.media = media.media_catalog || [];
    state.session = session.session || {};
    state.readOnly = Boolean(context.read_only);
    state.selectedSlideId = state.slides[0]?.id || null;

    renderContext();
    renderOutline();
    renderEvidence();
    renderMedia();
    renderSlides();
    applyReadOnlyMode();
    applyPaneWeights();

    const presenter = state.session?.presenter || {};
    const selectedIndex = Number(presenter.last_slide_index || 0);
    if (selectedIndex > 0 && selectedIndex < state.slides.length) {
      state.selectedSlideId = state.slides[selectedIndex].id;
    }
    const timerMin = Number(presenter.timer_minutes || state.context?.config?.ui?.presenter_timer_default_min || 7);
    window.HackLuminaryPresenter?.setTargetMinutes(timerMin);

    const defaultMode = String(state.context?.config?.studio?.default_view || "notebook");
    setMode(defaultMode, false);
    selectSlide(state.selectedSlideId || state.slides[0]?.id || "", false);
    beginAutosave();
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function escapeAttr(value) {
    return escapeHtml(value).replace(/\n/g, "&#10;");
  }

  document.addEventListener("DOMContentLoaded", async () => {
    bindUI();
    try {
      await loadAll();
      setMessage("Studio ready", "ok");
    } catch (error) {
      setMessage(`Failed to initialize studio: ${error.message}`, "error");
      console.error(error);
    }
  });
})();
