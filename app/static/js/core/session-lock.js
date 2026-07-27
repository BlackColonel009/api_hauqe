/**
 * Verrouillage de reprise de session — version API.
 *
 * Le navigateur ne connaît jamais le code privé.
 * Le timer reste côté UI pour détecter l'inactivité, mais :
 * - verrouillage     -> POST /api/v1/me/security-lock/lock
 * - déverrouillage   -> POST /api/v1/me/security-lock/verify
 * - 5 erreurs        -> révocation serveur de la session
 *
 * Le serveur peut aussi répondre HTTP 423 sur n'importe quelle route privée ;
 * dans ce cas l'événement global `hauqe:session-locked` ouvre ce modal.
 */

import {
  apiGet,
  apiPost,
  clearAccessToken,
  describeApiError,
  hasAccessToken,
} from "./api.js";

const ACTIVITY_EVENTS = [
  "pointerdown",
  "keydown",
  "scroll",
  "touchstart",
];

const DEFAULT_CONFIG = Object.freeze({
  enabled: false,
  timeout_minutes: 15,
  code_configured: false,
  current_session_locked: false,
  current_session_locked_at: null,
  attempts_remaining: 5,
});

export function initSessionLock() {
  const modal = document.querySelector("#sessionLock");
  const form = document.querySelector("#sessionUnlockForm");
  const input = document.querySelector("#sessionUnlockCode");
  const error = document.querySelector("#sessionLockError");
  const toggle = document.querySelector("#toggleUnlockCode");
  const logout = document.querySelector("#sessionLogout");

  if (!modal || !form || !input) return;

  let config = { ...DEFAULT_CONFIG };
  let timer = null;
  let locked = false;
  let locking = false;

  function icons() {
    if (window.lucide) {
      window.lucide.createIcons({
        attrs: { "stroke-width": 1.8 }
      });
    }
  }

  function isAuthScreen() {
    const route = location.hash
      .replace(/^#\/?/, "")
      .split("/")[0];

    return ["connexion", "mot-de-passe-oublie"].includes(route);
  }

  function clearTimer() {
    if (timer) clearTimeout(timer);
    timer = null;
  }

  function showLock() {
    locked = true;
    clearTimer();

    modal.hidden = false;
    document.body.classList.add("session-is-locked");

    input.value = "";
    error.textContent = "";

    setTimeout(() => input.focus(), 50);
    icons();
  }

  function hideLock() {
    locked = false;

    modal.hidden = true;
    document.body.classList.remove("session-is-locked");

    input.value = "";
    error.textContent = "";

    arm();
  }

  async function refreshSettings({ quiet = true } = {}) {
    if (!hasAccessToken() || isAuthScreen()) {
      config = { ...DEFAULT_CONFIG };
      clearTimer();
      return config;
    }

    try {
      const state = await apiGet("/api/v1/me/security-lock");
      config = {
        ...DEFAULT_CONFIG,
        ...(state || {}),
      };

      if (config.current_session_locked) {
        showLock();
      } else if (!locked) {
        arm();
      }

      return config;
    } catch (apiError) {
      const info = describeApiError(apiError);

      // HTTP 423 déclenche déjà l'événement global.
      if (info.status === 423) {
        showLock();
        return config;
      }

      if (!quiet && info.status !== 401) {
        console.error("Chargement verrou session :", apiError);
      }

      return config;
    }
  }

  function arm() {
    clearTimer();

    if (
      locked
      || locking
      || isAuthScreen()
      || !hasAccessToken()
      || !config.enabled
      || !config.code_configured
    ) {
      return;
    }

    const minutes = Number(config.timeout_minutes) || 15;
    timer = setTimeout(() => {
      requestServerLock("INACTIVITY");
    }, Math.max(1, minutes) * 60_000);
  }

  async function requestServerLock(reason = "USER_REQUEST") {
    if (
      locking
      || locked
      || !hasAccessToken()
      || !config.enabled
      || !config.code_configured
    ) {
      return;
    }

    locking = true;
    clearTimer();

    try {
      const state = await apiPost(
        "/api/v1/me/security-lock/lock",
        { reason }
      );

      config = {
        ...config,
        ...(state || {}),
        current_session_locked: true,
      };

      showLock();
    } catch (apiError) {
      const info = describeApiError(apiError);

      if (info.status === 423) {
        showLock();
      } else if (info.status !== 401) {
        console.error("Verrouillage de session :", apiError);
        arm();
      }
    } finally {
      locking = false;
    }
  }

  async function verifyUnlock(code) {
    try {
      const result = await apiPost(
        "/api/v1/me/security-lock/verify",
        { code },
        {
          /*
           * Mauvais code => 401 mais la session n'est pas forcément révoquée.
           * On ne doit donc PAS supprimer le Bearer token à la première erreur.
           */
          suppressGlobalAuth: true,
        }
      );

      config = {
        ...config,
        current_session_locked: false,
        attempts_remaining: result?.attempts_remaining ?? 5,
      };

      hideLock();
      return;
    } catch (apiError) {
      const info = describeApiError(apiError);

      if (info.status !== 401) {
        error.textContent = info.message;
        input.focus();
        return;
      }

      const attemptsRemaining =
        apiError?.detail?.attempts_remaining
        ?? apiError?.detail?.detail?.attempts_remaining
        ?? null;

      input.value = "";

      if (Number(attemptsRemaining) > 0) {
        error.textContent =
          `Code incorrect — ${attemptsRemaining} tentative(s) restante(s).`;
        input.focus();
        return;
      }

      error.textContent =
        "Nombre maximal de tentatives atteint. Déconnexion en cours…";

      clearAccessToken();

      setTimeout(() => {
        hideLock();
        location.hash = "#/connexion";
      }, 900);
    }
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const code = input.value.trim();
    if (!code) {
      error.textContent = "Saisissez votre code privé.";
      input.focus();
      return;
    }

    const submit = form.querySelector('button[type="submit"]');
    if (submit) submit.disabled = true;

    try {
      await verifyUnlock(code);
    } finally {
      if (submit) submit.disabled = false;
    }
  });

  toggle?.addEventListener("click", () => {
    input.type = input.type === "password" ? "text" : "password";
    toggle.innerHTML = `
      <i data-lucide="${
        input.type === "password" ? "eye" : "eye-off"
      }"></i>
    `;
    icons();
  });

  logout?.addEventListener("click", async (event) => {
    event.preventDefault();
    clearTimer();

    try {
      await apiPost(
        "/api/v1/auth/logout",
        null,
        { suppressGlobalAuth: true }
      );
    } catch {
      // La déconnexion locale reste obligatoire même si le serveur est indisponible.
    }

    clearAccessToken();
    hideLock();
    location.hash = "#/connexion";
  });

  ACTIVITY_EVENTS.forEach((eventName) => {
    document.addEventListener(
      eventName,
      () => {
        if (!locked) arm();
      },
      { passive: true }
    );
  });

  window.addEventListener(
    "hauqe:session-lock-settings",
    (event) => {
      config = {
        ...config,
        ...(event.detail || {}),
      };
      arm();
    }
  );

  window.addEventListener(
    "hauqe:session-locked",
    () => {
      config.current_session_locked = true;
      showLock();
    }
  );

  window.addEventListener(
    "hauqe:auth-state",
    (event) => {
      if (event.detail?.authenticated) {
        refreshSettings();
      } else {
        config = { ...DEFAULT_CONFIG };
        clearTimer();
        if (locked) hideLock();
      }
    }
  );

  window.addEventListener(
    "hauqe:lock-session-now",
    () => requestServerLock("MANUAL_TEST")
  );

  window.addEventListener("hashchange", () => {
    if (isAuthScreen()) {
      clearTimer();
      return;
    }
    refreshSettings();
  });

  document.addEventListener("visibilitychange", () => {
    if (!document.hidden && !locked) arm();
  });

  refreshSettings();
}
