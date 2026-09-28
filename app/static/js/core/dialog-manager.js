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
let lastModalForm = null;
const pendingInvalidForms = new Map();

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

const CUSTOM_DIALOG_SELECTOR = [
  ".reference-modal",
  ".dependency-modal",
  ".company-dialog",
  ".company-detail-dialog",
  ".assign-alert-dialog",
  ".deadline-dialog",
  ".return-modal",
  ".operational-modal",
  ".validation-modal",
  ".integration-modal",
].join(",");

function allOpenDialogs() {
  return [...document.querySelectorAll("dialog[open]")];
}

function allOpenCustomDialogs() {
  return [...document.querySelectorAll(CUSTOM_DIALOG_SELECTOR)]
    .filter((element) => !element.hidden && getComputedStyle(element).display !== "none");
}

function isVisibleDialogRoot(root) {
  if (!(root instanceof Element)) return false;
  if (root instanceof HTMLDialogElement) return root.open;
  return !root.hidden && getComputedStyle(root).display !== "none";
}

function activeDialogRoot() {
  if (lastModalForm?.isConnected) {
    const remembered = closestDialogOrOverlay(lastModalForm);
    if (isVisibleDialogRoot(remembered)) return remembered;
  }

  return allOpenDialogs().at(-1)
    || allOpenCustomDialogs().at(-1)
    || null;
}

function formForDialog(dialog) {
  if (!dialog) return null;
  return dialog.querySelector("form") || null;
}

function cleanLabel(value) {
  return String(value || "")
    .replace(/\*/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

function fieldLabel(field) {
  if (!(field instanceof HTMLElement)) return "Ce champ";
  const explicit = field.labels?.[0]?.textContent;
  const ancestor = field.closest("label")?.textContent;
  return cleanLabel(explicit || ancestor || field.getAttribute("aria-label") || field.name || field.id)
    || "Ce champ";
}

function validationMessage(field) {
  if (field.validity?.valueMissing) return "Ce champ est obligatoire.";
  if (field.validity?.typeMismatch) return "Le format renseigné n’est pas valide.";
  if (field.validity?.tooShort) return `Saisissez au moins ${field.minLength} caractères.`;
  if (field.validity?.tooLong) return `Saisissez au plus ${field.maxLength} caractères.`;
  if (field.validity?.rangeUnderflow || field.validity?.rangeOverflow) return "La valeur doit respecter la plage autorisée.";
  if (field.validity?.patternMismatch) return "Le format renseigné ne respecte pas le format attendu.";
  return field.validationMessage || "La valeur renseignée est invalide.";
}

function feedbackRegion(form, dialog) {
  const scope = form || dialog;
  if (!scope) return null;
  return scope.querySelector([
    ".hauqe-dialog-scroll-region",
    ".dialog-body",
    ".operational-dialog-body",
    ".dialog-form",
    ".assign-alert-form",
    ".reference-form",
    ".modal-body",
    ".form-body",
    ".dialog-content",
    "[data-dialog-scroll]",
  ].join(",")) || form || dialog;
}

function feedbackBox(form, dialog) {
  const scope = form || dialog;
  if (!scope) return null;
  let box = scope.querySelector(".modal-form-feedback");
  if (box) return box;

  box = document.createElement("section");
  box.className = "modal-form-feedback";
  box.hidden = true;
  box.setAttribute("role", "alert");
  box.setAttribute("aria-live", "assertive");
  feedbackRegion(form, dialog)?.prepend(box);
  return box;
}

function clearFieldFeedback(field) {
  if (!(field instanceof HTMLElement)) return;
  field.classList.remove("modal-field-invalid");
  field.removeAttribute("aria-invalid");
  const message = field.parentElement?.querySelector(`:scope > .modal-field-error[data-for="${CSS.escape(field.id || field.name || "")}"]`)
    || field.nextElementSibling?.matches?.(".modal-field-error") && field.nextElementSibling;
  message?.remove?.();
}

function markFieldInvalid(field, message) {
  if (!(field instanceof HTMLElement)) return;
  const key = field.id || field.name || "";
  clearFieldFeedback(field);
  field.classList.add("modal-field-invalid");
  field.setAttribute("aria-invalid", "true");

  const help = document.createElement("small");
  help.className = "modal-field-error";
  if (key) help.dataset.for = key;
  help.textContent = message;
  field.insertAdjacentElement("afterend", help);
}

function clearModalFeedback(form, { fields = false } = {}) {
  if (!form) return;
  const box = form.querySelector(".modal-form-feedback");
  if (box) {
    box.hidden = true;
    box.innerHTML = "";
  }
  if (fields) {
    form.querySelectorAll(".modal-field-invalid").forEach(clearFieldFeedback);
  }
}

function showModalFeedback({ form, dialog, message, issues = [] }) {
  const targetDialog = dialog || closestDialogOrOverlay(form) || activeDialogRoot();
  const targetForm = form || formForDialog(targetDialog);
  if (!targetDialog || !isVisibleDialogRoot(targetDialog) || !targetForm) return false;

  lastModalForm = targetForm;
  const usableIssues = issues.filter((issue) => issue?.field instanceof HTMLElement);
  usableIssues.forEach((issue) => markFieldInvalid(issue.field, issue.message));

  const box = feedbackBox(targetForm, targetDialog);
  if (!box) return false;
  const summary = message || "Certaines informations sont à corriger.";
  box.hidden = false;
  box.innerHTML = `
    <span class="modal-form-feedback-icon" aria-hidden="true">!</span>
    <div>
      <strong>Informations à corriger</strong>
      <p>${summary}</p>
      ${usableIssues.length > 1 ? `<small>${usableIssues.length} champs nécessitent une correction.</small>` : ""}
    </div>`;

  const first = usableIssues[0]?.field || targetForm.querySelector(".modal-field-invalid");
  requestAnimationFrame(() => {
    box.scrollIntoView({ block: "nearest", behavior: "smooth" });
    first?.focus?.({ preventScroll: true });
  });
  return true;
}

function findField(form, name) {
  if (!form || !name) return null;
  const normalized = String(name).replace(/\[\d+\]/g, "").split(".").at(-1);
  return form.querySelector(`[name="${CSS.escape(normalized)}"],#${CSS.escape(normalized)},[data-field="${CSS.escape(normalized)}"]`);
}

function apiIssuesForForm(form, detail) {
  if (!Array.isArray(detail)) return [];
  return detail.map((item) => {
    const location = Array.isArray(item?.loc) ? item.loc : [];
    const field = findField(form, location.at(-1));
    return field ? { field, message: item?.msg || "La valeur renseignée est invalide." } : null;
  }).filter(Boolean);
}

function rememberModalForm(event) {
  const target = event.target;
  if (!(target instanceof Element)) return;
  const dialog = closestDialogOrOverlay(target);
  const form = target.closest("form") || formForDialog(dialog);
  if (dialog && isVisibleDialogRoot(dialog) && form) lastModalForm = form;
}

function flushInvalidFeedback(form) {
  const issues = pendingInvalidForms.get(form) || [];
  pendingInvalidForms.delete(form);
  if (!issues.length) return;
  showModalFeedback({
    form,
    message: issues.length === 1
      ? `${fieldLabel(issues[0].field)} : ${issues[0].message}`
      : "Certains champs obligatoires ou invalides doivent être corrigés avant de continuer.",
    issues,
  });
}

function handleInvalid(event) {
  const field = event.target;
  if (!(field instanceof HTMLElement)) return;
  const dialog = closestDialogOrOverlay(field);
  const form = field.closest("form") || formForDialog(dialog);
  if (!dialog || !isVisibleDialogRoot(dialog) || !form) return;

  event.preventDefault();
  const issues = pendingInvalidForms.get(form) || [];
  if (!issues.some((item) => item.field === field)) {
    issues.push({ field, message: validationMessage(field) });
  }
  pendingInvalidForms.set(form, issues);
  queueMicrotask(() => flushInvalidFeedback(form));
}

function handleFieldInput(event) {
  const field = event.target;
  if (!(field instanceof HTMLElement) || !field.matches("input, select, textarea")) return;
  const form = field.closest("form");
  const dialog = closestDialogOrOverlay(field);
  if (!form || !dialog || !isVisibleDialogRoot(dialog)) return;

  clearFieldFeedback(field);
  if (!form.querySelector(".modal-field-invalid")) clearModalFeedback(form);
}

function handleApiError(event) {
  const error = event.detail?.error;
  const dialog = activeDialogRoot();
  const form = formForDialog(dialog);
  if (!dialog || !form || !isVisibleDialogRoot(dialog)) return;
  showModalFeedback({
    form,
    dialog,
    message: error?.message || "L’enregistrement est impossible. Corrigez les informations puis réessayez.",
    issues: apiIssuesForForm(form, error?.detail),
  });
}

function copyPageStateError(element) {
  if (!(element instanceof Element) || !element.matches(".dashboard-api-state.error,.company-form-api-state.error,.companies-api-state.error")) return;
  if (element.hidden || !element.textContent.trim()) return;
  const dialog = activeDialogRoot();
  const form = formForDialog(dialog);
  if (!dialog || !form || !isVisibleDialogRoot(dialog)) return;
  showModalFeedback({
    form,
    dialog,
    message: cleanLabel(element.querySelector("span")?.textContent || element.textContent) || "L’enregistrement est impossible.",
  });
}

function syncPageErrorMutation(mutation) {
  const candidates = new Set();
  const addCandidate = (node) => {
    if (!(node instanceof Element)) return;
    if (node.matches(".dashboard-api-state.error,.company-form-api-state.error,.companies-api-state.error")) {
      candidates.add(node);
    }
    node.querySelectorAll?.(".dashboard-api-state.error,.company-form-api-state.error,.companies-api-state.error")
      .forEach((element) => candidates.add(element));
  };

  addCandidate(mutation.target);
  if (mutation.type === "childList") mutation.addedNodes.forEach(addCandidate);
  candidates.forEach(copyPageStateError);
}

function syncBodyLock() {
  document.body.classList.toggle(
    "hauqe-dialog-open",
    allOpenDialogs().length > 0 || allOpenCustomDialogs().length > 0
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

  return element.closest(`dialog,${CUSTOM_DIALOG_SELECTOR},[role='dialog']`);
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
    const form = formForDialog(dialog);
    clearModalFeedback(form, { fields: true });
    if (lastModalForm === form) lastModalForm = null;
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
  if (root instanceof Element && root.matches(CUSTOM_DIALOG_SELECTOR)) {
    root.classList.add("hauqe-custom-dialog-managed");
  }
  root.querySelectorAll?.(CUSTOM_DIALOG_SELECTOR).forEach((element) => {
    element.classList.add("hauqe-custom-dialog-managed");
  });
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

  allOpenCustomDialogs().forEach((overlay) => closeDialog(overlay));
}

export function installDialogManager() {
  if (installed) return;
  installed = true;

  patchDialogMethods();
  normalizeTree(document);

  document.addEventListener("click", handleClick, true);
  document.addEventListener("click", rememberModalForm, true);
  document.addEventListener("submit", rememberModalForm, true);
  document.addEventListener("invalid", handleInvalid, true);
  document.addEventListener("input", handleFieldInput, true);
  document.addEventListener("change", handleFieldInput, true);
  document.addEventListener("keydown", handleKeydown, true);
  document.addEventListener("hauqe:dialog-opened", handleOpenEvent, true);
  window.addEventListener("hauqe:api-error", handleApiError);

  window.HAUQE_MODAL_FEEDBACK = Object.freeze({
    show(message, options = {}) {
      const dialog = options.dialog || activeDialogRoot();
      const form = options.form || formForDialog(dialog);
      return showModalFeedback({ form, dialog, message, issues: options.issues || [] });
    },
    clear(form = lastModalForm) {
      clearModalFeedback(form, { fields: true });
    },
  });

  window.addEventListener("hauqe:page-ready", () => {
    closeAllDialogs();
    lastModalForm = null;
    normalizeTree(document.querySelector("#pageContent") || document);
  });

  window.addEventListener("hashchange", closeAllDialogs);

  observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      if (mutation.type === "childList") {
        mutation.addedNodes.forEach((node) => {
          if (node instanceof Element) normalizeTree(node);
        });
      }
      syncPageErrorMutation(mutation);
    }
    syncBodyLock();
  });

  observer.observe(document.body, {
    attributes: true,
    attributeFilter: ["hidden", "class", "open"],
    childList: true,
    subtree: true,
  });
}
