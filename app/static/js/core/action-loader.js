/**
 * HAUQE Action Loader
 * ============================================================
 * Loader modal commun pour toute opération asynchrone déclenchée
 * par une action utilisateur.
 *
 * Objectifs :
 * - retour visuel immédiat après clic ;
 * - éviter le double clic ;
 * - laisser au navigateur une frame pour afficher le modal avant
 *   l'appel réseau / le traitement ;
 * - API simple réutilisable par toutes les pages.
 *
 * Exposition globale :
 *   window.HAUQE_ACTION_LOADER
 *
 * Exemple :
 *   await HAUQE_ACTION_LOADER.run(
 *     () => apiPost("/api/v1/..."),
 *     {
 *       button,
 *       title: "Enregistrement",
 *       message: "Enregistrement"
 *     }
 *   );
 */

const DEFAULTS = Object.freeze({
  title: "Traitement en cours",
  message: "Chargement",
  detail: "Veuillez patienter quelques instants.",
  minVisibleMs: 360,
});

let overlay = null;
let card = null;
let titleNode = null;
let messageNode = null;
let detailNode = null;
let activeSince = 0;
let sequence = 0;
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

export function showActionLoader(options = {}) {
  const root = ensureDom();
  const config = { ...DEFAULTS, ...options };
  const token = ++sequence;

  titleNode.textContent = config.title;
  messageNode.textContent = config.message;
  detailNode.textContent = config.detail;

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

  const token = showActionLoader(options);

  // Deux frames : garantit que le navigateur peint réellement le modal
  // avant de commencer le traitement ou l'appel réseau.
  await nextPaint();

  try {
    return await task();
  } finally {
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

  window.HAUQE_ACTION_LOADER = Object.freeze({
    show: showActionLoader,
    update: updateActionLoader,
    hide: hideActionLoader,
    run: runWithActionLoader,
    bind: bindActionLoader,
  });

  // Si la session se verrouille, son écran reste souverain.
  window.addEventListener("hauqe:session-locked", () => {
    if (overlay && !overlay.hidden) {
      overlay.hidden = true;
      overlay.classList.remove("is-visible");
      document.body.classList.remove("hauqe-action-loading");
      document.body.removeAttribute("aria-busy");
    }
  });

  return window.HAUQE_ACTION_LOADER;
}
