/**
 * HAUQE Dialog Manager — Correction consolidée 2.0
 * ============================================================
 * Gestion transversale des fenêtres et formulaires :
 * - fermeture par X / Annuler / Échap / clic sur le fond ;
 * - compatibilité avec les attributs data-close-* historiques ;
 * - restauration du focus ;
 * - verrouillage du scroll de la page ;
 * - défilement interne des formulaires longs ;
 * - fonctionnement avec les vues chargées dynamiquement par le routeur.
 */

let installed = false;
let lastFocusedElement = null;
let observer = null;

const DIALOG_CLOSE_SELECTOR = [
  "[data-dialog-close]",
  "[data-close-dialog]",
  "[data-close-inst-dialog]",
  "[data-close-user-dialog]",
  "[data-close-score-dialog]",
  "[data-close-scoring-dialog]",
  "[data-close-sncc-dialog]",
  "[data-close-watch-dialog]",
  "[data-close-alert-dialog]",
  "[data-close-deadline-dialog]",
  "[data-close-deadline-action]",
  "[data-close-validation-dialog]",
  "[data-close-integration-dialog]",
  ".dialog-close",
  ".operational-dialog-close",
  ".assign-close",
].join(",");

const SCROLL_REGION_SELECTORS = [
  ".dialog-body",
  ".dialog-form",
  ".assign-alert-form",
  ".reference-form",
  ".modal-body",
  ".form-body",
  ".dialog-content",
  "[data-dialog-scroll]",
];

function allOpenDialogs() {
  return [...document.querySelectorAll("dialog[open]")];
}

function syncBodyLock() {
  document.body.classList.toggle(
    "hauqe-dialog-open",
    allOpenDialogs().length > 0
  );
}

function dataCloseTarget(button) {
  if (!(button instanceof HTMLElement)) return null;

  for (const attribute of [...button.attributes]) {
    if (!attribute.name.startsWith("data-close")) continue;
    if (!attribute.value) continue;

    const target = document.getElementById(attribute.value);
    if (target) return target;
  }

  return null;
}

function closestDialogOrOverlay(element) {
  if (!(element instanceof Element)) return null;

  return element.closest([
    "dialog",
    ".reference-modal",
    ".dependency-modal",
    ".company-dialog",
    ".company-detail-dialog",
    ".assign-alert-dialog",
    ".deadline-dialog",
    "[role='dialog']",
  ].join(","));
}

export function closeDialog(target, { returnValue = "cancel" } = {}) {
  if (!target) return false;

  if (target instanceof HTMLDialogElement) {
    if (target.open) {
      target.close(returnValue);
    }
  } else if ("hidden" in target) {
    target.hidden = true;
    target.classList.remove("open", "show", "is-open");
    target.setAttribute("aria-hidden", "true");
  } else {
    return false;
  }

  syncBodyLock();

  const focusTarget = lastFocusedElement;
  lastFocusedElement = null;

  if (focusTarget instanceof HTMLElement && document.contains(focusTarget)) {
    requestAnimationFrame(() => focusTarget.focus({ preventScroll: true }));
  }

  window.dispatchEvent(new CustomEvent("hauqe:dialog-closed", {
    detail: { id: target.id || null },
  }));

  return true;
}

function markScrollRegion(dialog) {
  if (!(dialog instanceof HTMLDialogElement)) return;

  const existing = SCROLL_REGION_SELECTORS
    .map((selector) => dialog.querySelector(selector))
    .find(Boolean);

  if (existing) {
    existing.classList.add("hauqe-dialog-scroll-region");
    return;
  }

  const shell = dialog.querySelector(":scope > form, :scope > div") || dialog;
  const children = [...shell.children];

  const candidate = children.find((child) => {
    const tag = child.tagName.toLowerCase();
    if (["header", "footer"].includes(tag)) return false;
    if (child.classList.contains("dialog-close")) return false;
    return true;
  });

  candidate?.classList.add("hauqe-dialog-scroll-region");
}

function normalizeDialog(dialog) {
  if (!(dialog instanceof HTMLDialogElement)) return;

  dialog.classList.add("hauqe-dialog-managed");
  dialog.setAttribute("role", dialog.getAttribute("role") || "dialog");
  dialog.setAttribute("aria-modal", "true");

  dialog.querySelectorAll(DIALOG_CLOSE_SELECTOR).forEach((button) => {
    if (button instanceof HTMLButtonElement) {
      button.type = "button";
    }
  });

  markScrollRegion(dialog);

  if (dialog.dataset.hauqeDialogBound === "true") return;
  dialog.dataset.hauqeDialogBound = "true";

  dialog.addEventListener("close", () => {
    syncBodyLock();
    window.dispatchEvent(new CustomEvent("hauqe:dialog-closed", {
      detail: { id: dialog.id || null },
    }));
  });

  dialog.addEventListener("cancel", (event) => {
    if (dialog.dataset.static === "true") {
      event.preventDefault();
      return;
    }

    event.preventDefault();
    closeDialog(dialog);
  });

  dialog.addEventListener("click", (event) => {
    if (event.target !== dialog || dialog.dataset.static === "true") return;

    const rect = dialog.getBoundingClientRect();
    const inside = (
      event.clientX >= rect.left
      && event.clientX <= rect.right
      && event.clientY >= rect.top
      && event.clientY <= rect.bottom
    );

    if (!inside) closeDialog(dialog);
  });
}

function normalizeTree(root = document) {
  if (root instanceof HTMLDialogElement) normalizeDialog(root);
  root.querySelectorAll?.("dialog").forEach(normalizeDialog);
}

function closeFromButton(button) {
  const explicit = dataCloseTarget(button);
  const target = explicit || closestDialogOrOverlay(button);
  return closeDialog(target);
}

function shouldTreatAsCustomClose(button) {
  if (!(button instanceof HTMLElement)) return false;
  if (!closestDialogOrOverlay(button)) return false;

  const id = String(button.id || "").toLowerCase();
  const text = String(button.textContent || "").trim().toLowerCase();
  const value = String(button.getAttribute("value") || "").toLowerCase();

  return (
    id.startsWith("close")
    || id.startsWith("cancel")
    || value === "cancel"
    || text === "annuler"
    || text === "fermer"
  );
}

function handleClick(event) {
  const target = event.target;
  if (!(target instanceof Element)) return;

  const closeButton = target.closest(DIALOG_CLOSE_SELECTOR);
  if (closeButton) {
    event.preventDefault();
    event.stopPropagation();
    closeFromButton(closeButton);
    return;
  }

  const genericButton = target.closest("button, [role='button']");
  if (genericButton && shouldTreatAsCustomClose(genericButton)) {
    event.preventDefault();
    event.stopPropagation();
    closeFromButton(genericButton);
  }
}

function handleKeydown(event) {
  if (event.key !== "Escape") return;

  const dialog = allOpenDialogs().at(-1);
  if (!dialog || dialog.dataset.static === "true") return;

  event.preventDefault();
  closeDialog(dialog);
}

function handleOpenEvent(event) {
  const dialog = event.target;
  if (!(dialog instanceof HTMLDialogElement)) return;

  normalizeDialog(dialog);
  lastFocusedElement = document.activeElement;
  syncBodyLock();

  requestAnimationFrame(() => {
    const first = dialog.querySelector([
      "[autofocus]",
      "input:not([type='hidden']):not([disabled])",
      "select:not([disabled])",
      "textarea:not([disabled])",
      "button:not([disabled])",
    ].join(","));

    first?.focus?.({ preventScroll: true });
  });
}

function patchDialogMethods() {
  if (HTMLDialogElement.prototype.__hauqePatched) return;

  const nativeShowModal = HTMLDialogElement.prototype.showModal;
  const nativeShow = HTMLDialogElement.prototype.show;

  HTMLDialogElement.prototype.showModal = function (...args) {
    normalizeDialog(this);
    lastFocusedElement = document.activeElement;

    if (!this.open) {
      nativeShowModal.apply(this, args);
    }

    syncBodyLock();
    this.dispatchEvent(new CustomEvent("hauqe:dialog-opened", {
      bubbles: true,
    }));
  };

  HTMLDialogElement.prototype.show = function (...args) {
    normalizeDialog(this);
    lastFocusedElement = document.activeElement;

    if (!this.open) {
      nativeShow.apply(this, args);
    }

    syncBodyLock();
    this.dispatchEvent(new CustomEvent("hauqe:dialog-opened", {
      bubbles: true,
    }));
  };

  Object.defineProperty(HTMLDialogElement.prototype, "__hauqePatched", {
    value: true,
    configurable: false,
  });
}

export function closeAllDialogs() {
  allOpenDialogs().reverse().forEach((dialog) => closeDialog(dialog));

  document.querySelectorAll([
    ".reference-modal:not([hidden])",
    ".dependency-modal:not([hidden])",
    ".company-dialog:not([hidden])",
    ".company-detail-dialog:not([hidden])",
  ].join(",")).forEach((overlay) => closeDialog(overlay));
}

export function installDialogManager() {
  if (installed) return;
  installed = true;

  patchDialogMethods();
  normalizeTree(document);

  document.addEventListener("click", handleClick, true);
  document.addEventListener("keydown", handleKeydown, true);
  document.addEventListener("hauqe:dialog-opened", handleOpenEvent, true);

  window.addEventListener("hauqe:page-ready", () => {
    closeAllDialogs();
    normalizeTree(document.querySelector("#pageContent") || document);
  });

  window.addEventListener("hashchange", closeAllDialogs);

  observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      mutation.addedNodes.forEach((node) => {
        if (node instanceof Element) normalizeTree(node);
      });
    }
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true,
  });
}
