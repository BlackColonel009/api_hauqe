/**
 * HAUQE Action Loader — V2
 * ============================================================
 * Retour visuel commun pour les opérations asynchrones.
 *
 * Deux modes coexistent :
 * 1. mode explicite : HAUQE_ACTION_LOADER.run(...)
 * 2. mode automatique : tout fetch /api/* déclenché immédiatement
 *    après une action utilisateur met uniquement son bouton en attente.
 *
 * Le modal plein écran est réservé au mode explicite. Les appels
 * périodiques ou de fond ne déclenchent aucun indicateur,
 * car ils ne sont pas précédés d'une interaction utilisateur.
 */

const DEFAULTS = Object.freeze({
  title: "Traitement en cours",
  message: "Chargement",
  detail: "Veuillez patienter quelques instants.",
  minVisibleMs: 380,
  messageRotateMs: 1850,
});

const DEFAULT_MESSAGE_VARIANTS = Object.freeze([
  "Chargement",
  "Patientez",
  "Ce sera prêt",
]);

const AUTO_ACTION_WINDOW_MS = 2200;
const AUTO_SETTLE_MS = 180;

let overlay = null;
let card = null;
let titleNode = null;
let messageNode = null;
let detailNode = null;
let activeSince = 0;
let sequence = 0;
let messageTimer = null;
let messageIndex = 0;
let manualDepth = 0;
let recentAction = null;
let autoPending = 0;
let autoToken = null;
let autoButton = null;
let autoHideTimer = null;

const buttonStates = new WeakMap();

function nextPaint() {
  return new Promise((resolve) => {
    requestAnimationFrame(() => {
      requestAnimationFrame(resolve);
    });
  });
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function ensureDom() {
  if (overlay && document.body.contains(overlay)) {
    return overlay;
  }

  overlay = document.createElement("div");
  overlay.id = "hauqeActionLoader";
  overlay.className = "hauqe-action-loader";
  overlay.hidden = true;
  overlay.setAttribute("role", "dialog");
  overlay.setAttribute("aria-modal", "true");
  overlay.setAttribute("aria-labelledby", "hauqeActionLoaderTitle");
  overlay.setAttribute("aria-describedby", "hauqeActionLoaderMessage");

  overlay.innerHTML = `
    <div class="hauqe-action-loader-backdrop" aria-hidden="true"></div>

    <section class="hauqe-action-loader-card">
      <div class="hauqe-action-loader-brand" aria-hidden="true">
        <div class="hauqe-action-h">
          <svg viewBox="0 0 92 92">
            <circle class="action-ring" cx="46" cy="46" r="39"></circle>
            <circle class="action-orbit" cx="46" cy="46" r="39"></circle>
            <path class="action-letter" d="M29 24V68M63 24V68M29 46H63"></path>
            <path class="action-leaf" d="M68 25c8-8 14-4 13-13-9-1-14 5-13 13Z"></path>
          </svg>
        </div>
      </div>

      <div class="hauqe-action-loader-copy">
        <p class="hauqe-action-loader-eyebrow">HAUQE CERTIF</p>
        <h2 id="hauqeActionLoaderTitle">Traitement en cours</h2>

        <p class="hauqe-action-loader-message" id="hauqeActionLoaderMessage">
          <span data-action-message>Chargement</span>
          <span class="hauqe-loading-dots" aria-hidden="true">
            <i></i><i></i><i></i>
          </span>
        </p>

        <small data-action-detail>Veuillez patienter quelques instants.</small>
      </div>

      <div class="hauqe-action-loader-progress" aria-hidden="true">
        <span></span>
      </div>
    </section>
  `;

  document.body.appendChild(overlay);

  card = overlay.querySelector(".hauqe-action-loader-card");
  titleNode = overlay.querySelector("#hauqeActionLoaderTitle");
  messageNode = overlay.querySelector("[data-action-message]");
  detailNode = overlay.querySelector("[data-action-detail]");

  return overlay;
}

function setButtonBusy(button, busy) {
  if (!(button instanceof HTMLElement)) return;

  if (busy) {
    if (!buttonStates.has(button)) {
      buttonStates.set(button, {
        disabled: "disabled" in button ? button.disabled : false,
        ariaBusy: button.getAttribute("aria-busy"),
      });
    }

    if ("disabled" in button) {
      button.disabled = true;
    }

    button.setAttribute("aria-busy", "true");
    button.classList.add("hauqe-button-busy");
    return;
  }

  const previous = buttonStates.get(button);

  if (previous) {
    if ("disabled" in button) {
      button.disabled = previous.disabled;
    }

    if (previous.ariaBusy === null) {
      button.removeAttribute("aria-busy");
    } else {
      button.setAttribute("aria-busy", previous.ariaBusy);
    }

    buttonStates.delete(button);
  } else {
    button.removeAttribute("aria-busy");
  }

  button.classList.remove("hauqe-button-busy");
}

function emit(name, detail = {}) {
  window.dispatchEvent(new CustomEvent(name, { detail }));
}

function stopMessageRotation() {
  if (messageTimer) {
    clearInterval(messageTimer);
    messageTimer = null;
  }
}

function startMessageRotation(config) {
  stopMessageRotation();

  const variants = [
    config.message,
    ...(Array.isArray(config.messageVariants)
      ? config.messageVariants
      : DEFAULT_MESSAGE_VARIANTS),
  ]
    .map((value) => String(value || "").trim())
    .filter(Boolean)
    .filter((value, index, values) => values.indexOf(value) === index);

  if (!variants.length) return;

  messageIndex = 0;
  messageNode.textContent = variants[0];

  if (variants.length === 1 || config.rotateMessages === false) {
    return;
  }

  messageTimer = setInterval(() => {
    if (!overlay || overlay.hidden) return;

    messageIndex = (messageIndex + 1) % variants.length;
    messageNode.classList.remove("is-switching");

    requestAnimationFrame(() => {
      messageNode.textContent = variants[messageIndex];
      messageNode.classList.add("is-switching");
    });
  }, Number(config.messageRotateMs || DEFAULTS.messageRotateMs));
}

function normalizeActionText(element) {
  if (!(element instanceof Element)) return "";

  return String(
    element.getAttribute("aria-label")
    || element.getAttribute("title")
    || element.textContent
    || ""
  )
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
}

function copyForAction(element) {
  const text = normalizeActionText(element);

  const mappings = [
    [/publier/, "Publication en cours"],
    [/préremplir|pre-remplir/, "Préparation de la grille"],
    [/enregistrer|sauvegarder/, "Enregistrement en cours"],
    [/créer|ajouter|nouveau|ouvrir/, "Création en cours"],
    [/modifier|mettre à jour|actualiser/, "Mise à jour en cours"],
    [/supprimer|retirer|annuler/, "Traitement en cours"],
    [/valider|confirmer|finaliser/, "Validation en cours"],
    [/affecter|attribuer|rôle/, "Mise à jour des accès"],
    [/rechercher|filtrer|charger|voir|détail/, "Chargement des données"],
    [/exporter|télécharger/, "Préparation du fichier"],
  ];

  const match = mappings.find(([pattern]) => pattern.test(text));

  return {
    title: match?.[1] || DEFAULTS.title,
    message: DEFAULTS.message,
    detail: text
      ? `Action demandée : ${text.slice(0, 90)}.`
      : DEFAULTS.detail,
  };
}

function findInteractiveElement(target) {
  if (!(target instanceof Element)) return null;

  const direct = target.closest([
    "button",
    "[role='button']",
    "input[type='submit']",
    "input[type='button']",
    ".app-btn",
    ".dashboard-clickable",
    ".user-action",
    "summary",
  ].join(","));

  if (direct) return direct;

  let current = target;
  for (let depth = 0; current && depth < 5; depth += 1) {
    try {
      if (getComputedStyle(current).cursor === "pointer") {
        return current;
      }
    } catch {}
    current = current.parentElement;
  }

  return null;
}

function shouldIgnoreAction(element) {
  if (!(element instanceof Element)) return true;

  if (element.closest([
    "#menuToggle",
    "#sidebarBackdrop",
    ".sidebar-mobile-close",
    "#themeSwitch",
    "[data-no-action-loader]",
    "[data-close-inst-dialog]",
    "[data-close-user-dialog]",
    "[data-close-alert-dialog]",
    "[data-close-watch-dialog]",
    "[data-close-deadline-dialog]",
    ".dialog-close",
  ].join(","))) {
    return true;
  }

  const anchor = element.closest("a[href]");
  if (anchor) {
    const href = String(anchor.getAttribute("href") || "");
    if (href.startsWith("#") || anchor.hasAttribute("download")) {
      return true;
    }
  }

  return false;
}

function rememberAction(element) {
  if (!(element instanceof Element) || shouldIgnoreAction(element)) {
    return;
  }

  recentAction = {
    element,
    button: element.closest("button, input[type='submit'], input[type='button']"),
    at: performance.now(),
    copy: copyForAction(element),
  };
}

function installActionTracking() {
  if (document.documentElement.dataset.hauqeActionTracking === "true") {
    return;
  }

  document.documentElement.dataset.hauqeActionTracking = "true";

  document.addEventListener("click", (event) => {
    if (!event.isTrusted) return;
    const element = findInteractiveElement(event.target);
    if (element) rememberAction(element);
  }, true);

  document.addEventListener("submit", (event) => {
    if (!event.isTrusted) return;
    rememberAction(event.submitter || event.target);
  }, true);

  document.addEventListener("change", (event) => {
    if (!event.isTrusted) return;
    const target = event.target;
    if (
      target instanceof HTMLSelectElement
      || (target instanceof HTMLInputElement
        && ["checkbox", "radio"].includes(target.type))
    ) {
      rememberAction(target);
    }
  }, true);
}

function requestUrl(input) {
  if (typeof input === "string") return input;
  if (input instanceof URL) return input.href;
  if (input instanceof Request) return input.url;
  return "";
}

function requestMethod(input, init = {}) {
  if (init?.method) return String(init.method).toUpperCase();
  if (input instanceof Request) return String(input.method || "GET").toUpperCase();
  return "GET";
}

function isBackgroundApi(url, method) {
  const value = String(url || "");

  if (/\/api\/v1\/presence\/heartbeat(?:\?|$)/.test(value)) {
    return true;
  }

  if (
    method === "GET"
    && /\/api\/v1\/(?:presence\/users|notifications)(?:\?|$)/.test(value)
  ) {
    return true;
  }

  return false;
}

function beginAutomaticRequest(input, init = {}) {
  const url = requestUrl(input);
  const method = requestMethod(input, init);

  if (
    manualDepth > 0
    || !url.includes("/api/")
    || isBackgroundApi(url, method)
    || !recentAction
    || performance.now() - recentAction.at > AUTO_ACTION_WINDOW_MS
  ) {
    return null;
  }

  if (autoHideTimer) {
    clearTimeout(autoHideTimer);
    autoHideTimer = null;
  }

  autoPending += 1;

  if (autoPending === 1) {
    autoButton = recentAction.button instanceof HTMLElement
      ? recentAction.button
      : null;

    /*
     * Une requête automatique ne doit jamais neutraliser toute l'interface.
     * Le bouton déclencheur porte seul l'état d'attente. Les opérations qui
     * exigent réellement un verrouillage utilisent runWithActionLoader().
     */
    autoToken = null;
    setButtonBusy(autoButton, true);
  }

  return { token: autoToken };
}

function endAutomaticRequest(handle) {
  if (!handle) return;

  autoPending = Math.max(0, autoPending - 1);
  if (autoPending > 0) return;

  if (autoHideTimer) clearTimeout(autoHideTimer);

  autoHideTimer = setTimeout(async () => {
    const token = autoToken;
    const button = autoButton;

    autoToken = null;
    autoButton = null;
    autoHideTimer = null;
    recentAction = null;

    setButtonBusy(button, false);
  }, AUTO_SETTLE_MS);
}

function installFetchBridge() {
  if (window.__HAUQE_FETCH_LOADER_PATCHED__) return;

  const originalFetch = window.fetch.bind(window);

  window.fetch = async function hauqeFetch(input, init = {}) {
    const handle = beginAutomaticRequest(input, init);

    try {
      return await originalFetch(input, init);
    } finally {
      endAutomaticRequest(handle);
    }
  };

  window.__HAUQE_FETCH_LOADER_PATCHED__ = true;
}

export function showActionLoader(options = {}) {
  const root = ensureDom();
  const config = { ...DEFAULTS, ...options };
  const token = ++sequence;

  titleNode.textContent = config.title;
  detailNode.textContent = config.detail;
  startMessageRotation(config);

  root.hidden = false;
  root.dataset.token = String(token);
  document.body.classList.add("hauqe-action-loading");
  document.body.setAttribute("aria-busy", "true");

  if (options.button) {
    setButtonBusy(options.button, true);
  }

  activeSince = performance.now();

  requestAnimationFrame(() => {
    root.classList.add("is-visible");
    card?.classList.add("is-visible");
  });

  emit("hauqe:action-loader-show", {
    token,
    title: config.title,
    message: config.message,
  });

  return token;
}

export function updateActionLoader(options = {}) {
  if (!overlay || overlay.hidden) return;

  if (options.title !== undefined) {
    titleNode.textContent = options.title;
  }

  if (options.message !== undefined) {
    messageNode.textContent = options.message;
  }

  if (options.detail !== undefined) {
    detailNode.textContent = options.detail;
  }
}

export async function hideActionLoader({
  token = null,
  button = null,
  minVisibleMs = DEFAULTS.minVisibleMs,
} = {}) {
  if (!overlay || overlay.hidden) {
    if (button) setButtonBusy(button, false);
    return;
  }

  if (
    token !== null
    && overlay.dataset.token
    && Number(overlay.dataset.token) !== Number(token)
  ) {
    if (button) setButtonBusy(button, false);
    return;
  }

  const elapsed = performance.now() - activeSince;
  const remaining = Math.max(0, Number(minVisibleMs || 0) - elapsed);

  if (remaining > 0) {
    await sleep(remaining);
  }

  stopMessageRotation();
  overlay.classList.remove("is-visible");
  card?.classList.remove("is-visible");

  await sleep(150);

  overlay.hidden = true;
  document.body.classList.remove("hauqe-action-loading");
  document.body.removeAttribute("aria-busy");

  if (button) {
    setButtonBusy(button, false);
  }

  emit("hauqe:action-loader-hide", { token });
}

export async function runWithActionLoader(task, options = {}) {
  if (typeof task !== "function") {
    throw new TypeError("runWithActionLoader attend une fonction.");
  }

  manualDepth += 1;
  const token = showActionLoader(options);

  await nextPaint();

  try {
    return await task();
  } finally {
    manualDepth = Math.max(0, manualDepth - 1);

    await hideActionLoader({
      token,
      button: options.button || null,
      minVisibleMs: options.minVisibleMs ?? DEFAULTS.minVisibleMs,
    });
  }
}

export function bindActionLoader(button, handler, options = {}) {
  if (!(button instanceof HTMLElement)) {
    throw new TypeError("bindActionLoader attend un bouton valide.");
  }

  if (typeof handler !== "function") {
    throw new TypeError("bindActionLoader attend un handler.");
  }

  const listener = async (event) => {
    if (button.getAttribute("aria-busy") === "true") {
      event.preventDefault();
      return;
    }

    await runWithActionLoader(
      () => handler(event),
      {
        ...options,
        button,
      }
    );
  };

  button.addEventListener("click", listener);

  return () => {
    button.removeEventListener("click", listener);
  };
}

export function installActionLoader() {
  ensureDom();
  installActionTracking();
  installFetchBridge();

  window.HAUQE_ACTION_LOADER = Object.freeze({
    show: showActionLoader,
    update: updateActionLoader,
    hide: hideActionLoader,
    run: runWithActionLoader,
    bind: bindActionLoader,
  });

  window.addEventListener("hauqe:session-locked", () => {
    stopMessageRotation();
    recentAction = null;
    autoPending = 0;
    autoToken = null;
    setButtonBusy(autoButton, false);
    autoButton = null;

    if (autoHideTimer) {
      clearTimeout(autoHideTimer);
      autoHideTimer = null;
    }

    if (overlay && !overlay.hidden) {
      overlay.hidden = true;
      overlay.classList.remove("is-visible");
      card?.classList.remove("is-visible");
      document.body.classList.remove("hauqe-action-loading");
      document.body.removeAttribute("aria-busy");
    }
  });

  return window.HAUQE_ACTION_LOADER;
}
