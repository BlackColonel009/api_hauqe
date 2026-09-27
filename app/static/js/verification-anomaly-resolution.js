/*
 * Résolution d'anomalie — Dossier de vérification
 *
 * Les actions de la liste historique sont recréées directement après chaque
 * rendu. Cela évite les anciens gestionnaires d'événement attachés à des
 * éléments qui viennent d'être remplacés par le DOM dynamique.
 */
(function () {
  "use strict";

  let apiPost;
  let anomalyId = null;
  let selectedRow = null;

  const dialogId = "verificationAnomalyResolutionDialog";
  const $ = (selector, root = document) => root.querySelector(selector);

  function dossierId() {
    return location.hash.replace(/^#\//, "").split("/")[1]?.split("?")[0] || null;
  }

  function refreshIcons() {
    window.lucide?.createIcons({ attrs: { "stroke-width": 1.8 } });
  }

  function showPageState(message, error = false) {
    const state = $("#vdState");
    if (!state) return;
    state.hidden = false;
    state.className = `dashboard-api-state ${error ? "error" : ""}`;
    state.innerHTML = `<i data-lucide="${error ? "triangle-alert" : "circle-check"}"></i><div><strong>${error ? "Opération impossible" : "Résolution enregistrée"}</strong><span>${message}</span></div>`;
    refreshIcons();
  }

  function ensureDialog() {
    let dialog = document.getElementById(dialogId);
    if (dialog) return dialog;

    dialog = document.createElement("dialog");
    dialog.id = dialogId;
    dialog.className = "operational-form-dialog";
    dialog.innerHTML = `
      <form method="dialog" id="verificationAnomalyResolutionForm" novalidate>
        <header class="operational-dialog-header">
          <div class="operational-dialog-title">
            <span class="operational-dialog-icon"><i data-lucide="circle-check-big"></i></span>
            <div>
              <p class="eyebrow">Dossier de vérification</p>
              <h2>Résoudre l’anomalie</h2>
              <small>Décrivez la mesure prise. La résolution sera ajoutée au dossier et tracée dans le journal d’audit.</small>
            </div>
          </div>
          <button class="operational-dialog-close" type="button" data-close-resolution aria-label="Fermer"><i data-lucide="x"></i></button>
        </header>
        <section class="operational-dialog-body">
          <div class="operational-form-notice">
            <span><i data-lucide="info"></i></span>
            <div><strong>Action définitive dans le dossier</strong><small>L’anomalie passera au statut « Résolue ». Elle restera visible avec sa description et la mesure renseignée.</small></div>
          </div>
          <div class="form-field full">
            <label for="verificationAnomalyResolutionText">Mesure de résolution <span aria-hidden="true">*</span></label>
            <textarea id="verificationAnomalyResolutionText" rows="5" required placeholder="Ex. Le document conforme a été reçu et contrôlé le …"></textarea>
            <small class="field-help">Indiquez ce qui a permis de traiter l’écart.</small>
          </div>
          <p class="field-help" id="verificationAnomalyResolutionError" hidden></p>
        </section>
        <footer class="operational-dialog-footer">
          <span class="operational-footer-note"><i data-lucide="shield-check"></i> La trace est conservée dans le dossier.</span>
          <div class="dialog-actions">
            <button class="btn btn-outline-secondary app-btn" type="button" data-close-resolution>Annuler</button>
            <button class="btn btn-primary app-btn" type="submit" id="verificationAnomalyResolutionSubmit"><i data-lucide="check"></i> Valider la résolution</button>
          </div>
        </footer>
      </form>`;
    document.body.appendChild(dialog);

    dialog.querySelectorAll("[data-close-resolution]").forEach((button) => {
      button.addEventListener("click", () => dialog.close());
    });
    $("#verificationAnomalyResolutionForm", dialog).addEventListener("submit", submitResolution);
    refreshIcons();
    return dialog;
  }

  function openResolution(id, row) {
    anomalyId = id;
    selectedRow = row;
    const dialog = ensureDialog();
    const field = $("#verificationAnomalyResolutionText", dialog);
    const error = $("#verificationAnomalyResolutionError", dialog);
    field.value = "";
    error.hidden = true;
    error.textContent = "";
    dialog.showModal();
    window.setTimeout(() => field.focus(), 0);
  }

  function replaceResolutionAction(button) {
    if (button.dataset.resolutionBound === "true") return;
    const replacement = document.createElement("button");
    replacement.type = "button";
    replacement.className = button.className;
    replacement.dataset.resolutionBound = "true";
    replacement.dataset.noActionLoader = "true";
    replacement.innerHTML = '<i data-lucide="circle-check"></i> Résoudre';
    replacement.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      openResolution(button.dataset.resolve, button.closest(".cert-doc-row"));
    });
    button.replaceWith(replacement);
  }

  function hydrateResolutionActions() {
    let actionRecreated = false;
    document.querySelectorAll("[data-resolve]").forEach((button) => {
      actionRecreated = true;
      replaceResolutionAction(button);
    });
    // lucide remplace lui-même des éléments du DOM. Ne le relancer que si un
    // bouton vient réellement d'être créé, sinon l'observateur entrerait dans
    // une boucle de rendu et bloquerait la page.
    if (actionRecreated) refreshIcons();
  }

  function showDialogError(message) {
    const dialog = ensureDialog();
    const error = $("#verificationAnomalyResolutionError", dialog);
    error.textContent = message;
    error.hidden = false;
  }

  async function submitResolution(event) {
    event.preventDefault();
    const dialog = ensureDialog();
    const resolution = $("#verificationAnomalyResolutionText", dialog).value.trim();
    if (!resolution) {
      showDialogError("La mesure de résolution est obligatoire.");
      return;
    }
    if (!anomalyId || !dossierId()) {
      showDialogError("Le dossier ou l’anomalie n’est plus disponible. Fermez puis rouvrez le dossier.");
      return;
    }

    const submit = $("#verificationAnomalyResolutionSubmit", dialog);
    submit.disabled = true;
    try {
      const saved = await apiPost(
        `/api/v1/verifications/${dossierId()}/anomalies/${anomalyId}/resolve`,
        { resolution },
      );
      if (!saved?.date_resolution || saved?.statut !== "RESOLUE") {
        throw new Error("Le serveur n’a pas confirmé la résolution de l’anomalie. Réessayez après avoir rechargé le dossier.");
      }
      dialog.close();
      if (selectedRow) {
        const detail = selectedRow.querySelector("div small");
        if (detail) {
          const description = detail.textContent.split("Statut :")[0].trim();
          const safeResolution = resolution.replace(/[&<>]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[char]));
          detail.innerHTML = `${description}<br>Statut : Résolue · ${safeResolution}`;
        }
        selectedRow.querySelector("button")?.remove();
      }
      showPageState("La mesure de résolution a été enregistrée.");
      anomalyId = null;
      selectedRow = null;
    } catch (error) {
      showDialogError(error?.message || "La résolution n’a pas pu être enregistrée.");
    } finally {
      submit.disabled = false;
    }
  }

  async function start() {
    try {
      ({ apiPost } = await import("/static/js/core/api.js"));
      hydrateResolutionActions();
      const content = $("#vdContent");
      if (content) {
        new MutationObserver(hydrateResolutionActions).observe(content, {
          childList: true,
          subtree: true,
        });
      }
    } catch {
      // Le contrôleur de vérification affichera son message si l'API est indisponible.
    }
  }

  start();
})();
