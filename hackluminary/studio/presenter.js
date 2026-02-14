(() => {
  const state = {
    timerSeconds: 0,
    timerRef: null,
    targetMinutes: 7,
  };

  const timerDisplay = () => document.getElementById("timerDisplay");
  const timerRemaining = () => document.getElementById("timerRemaining");
  const timerTargetMin = () => document.getElementById("timerTargetMin");

  function fmt(seconds) {
    const mm = String(Math.floor(seconds / 60)).padStart(2, "0");
    const ss = String(seconds % 60).padStart(2, "0");
    return `${mm}:${ss}`;
  }

  function refreshTimer() {
    const el = timerDisplay();
    if (el) {
      el.textContent = fmt(state.timerSeconds);
    }

    const remainingNode = timerRemaining();
    if (remainingNode) {
      const remaining = Math.max(0, (state.targetMinutes * 60) - state.timerSeconds);
      remainingNode.textContent = fmt(remaining);
      remainingNode.dataset.state = state.timerSeconds > (state.targetMinutes * 60) ? "over" : "ok";
    }
  }

  function startTimer() {
    if (state.timerRef) return;
    state.timerRef = setInterval(() => {
      state.timerSeconds += 1;
      refreshTimer();
    }, 1000);
  }

  function pauseTimer() {
    if (!state.timerRef) return;
    clearInterval(state.timerRef);
    state.timerRef = null;
  }

  function resetTimer() {
    pauseTimer();
    state.timerSeconds = 0;
    refreshTimer();
  }

  function setTargetMinutes(value) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric) || numeric < 1) return;
    state.targetMinutes = Math.min(180, Math.floor(numeric));
    const input = timerTargetMin();
    if (input) input.value = String(state.targetMinutes);
    refreshTimer();
  }

  function enablePresenterMode(enable) {
    document.body.classList.toggle("presenter", enable);
    const panel = document.getElementById("presenterPanel");
    if (panel) panel.hidden = !enable;
  }

  window.HackLuminaryPresenter = {
    setTitles(current, next) {
      const curr = document.getElementById("presenterCurrent");
      const nxt = document.getElementById("presenterNext");
      if (curr) curr.textContent = current || "-";
      if (nxt) nxt.textContent = next || "-";
    },
    setTargetMinutes,
    enablePresenterMode,
  };

  document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("timerStartBtn")?.addEventListener("click", startTimer);
    document.getElementById("timerPauseBtn")?.addEventListener("click", pauseTimer);
    document.getElementById("timerResetBtn")?.addEventListener("click", resetTimer);
    timerTargetMin()?.addEventListener("change", () => setTargetMinutes(timerTargetMin()?.value));
    refreshTimer();
  });
})();
