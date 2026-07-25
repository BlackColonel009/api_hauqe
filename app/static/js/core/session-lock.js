const STORAGE_KEY = "hauqe-session-lock-settings";
const ACTIVITY_EVENTS = ["pointerdown", "keydown", "scroll", "touchstart"];

function settings() {
  try { return { enabled: false, code: "", timeoutMinutes: 15, ...JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}") }; }
  catch { return { enabled: false, code: "", timeoutMinutes: 15 }; }
}

export function initSessionLock() {
  const modal = document.querySelector("#sessionLock");
  const form = document.querySelector("#sessionUnlockForm");
  const input = document.querySelector("#sessionUnlockCode");
  const error = document.querySelector("#sessionLockError");
  const toggle = document.querySelector("#toggleUnlockCode");
  const logout = document.querySelector("#sessionLogout");
  if (!modal || !form) return;

  let timer;
  let attempts = 0;
  let locked = false;

  const arm = () => {
    clearTimeout(timer);
    const config = settings();
    if (!config.enabled || !config.code || locked) return;
    timer = setTimeout(lock, Math.max(1, Number(config.timeoutMinutes) || 15) * 60_000);
  };

  function lock() {
    const config = settings();
    if (!config.enabled || !config.code) return;
    locked = true;
    attempts = 0;
    modal.hidden = false;
    document.body.classList.add("session-is-locked");
    input.value = "";
    error.textContent = "";
    setTimeout(() => input.focus(), 50);
    if (window.lucide) window.lucide.createIcons({ attrs: { "stroke-width": 1.8 } });
  }

  function unlock() {
    locked = false;
    modal.hidden = true;
    document.body.classList.remove("session-is-locked");
    attempts = 0;
    arm();
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const config = settings();
    if (input.value === config.code) return unlock();
    attempts += 1;
    input.value = "";
    error.textContent = attempts >= 5 ? "Nombre maximal de tentatives atteint. Déconnexion en cours…" : `Code incorrect — ${5 - attempts} tentative(s) restante(s).`;
    if (attempts >= 5) setTimeout(() => { location.hash = "#/connexion"; unlock(); }, 900);
    else input.focus();
  });

  toggle.addEventListener("click", () => {
    input.type = input.type === "password" ? "text" : "password";
    toggle.innerHTML = `<i data-lucide="${input.type === "password" ? "eye" : "eye-off"}"></i>`;
    if (window.lucide) window.lucide.createIcons({ attrs: { "stroke-width": 1.8 } });
  });
  logout.addEventListener("click", () => { clearTimeout(timer); unlock(); });
  ACTIVITY_EVENTS.forEach((name) => document.addEventListener(name, () => { if (!locked) arm(); }, { passive: true }));
  window.addEventListener("hauqe:session-lock-settings", arm);
  window.addEventListener("hauqe:lock-session-now", lock);
  document.addEventListener("visibilitychange", () => { if (!document.hidden && !locked) arm(); });
  arm();
}
