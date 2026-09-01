(() => {
  "use strict";

  const isVerification = () => /^#\/verifications\//.test(location.hash);
  const $ = (selector) => document.querySelector(selector);

  function suggestedCode() {
    const values = [...document.querySelectorAll("#vdContent .audit-table tbody tr td:first-child strong")]
      .map((node) => node.textContent.trim())
      .map((value) => /^PV-(\d+)$/i.exec(value)?.[1])
      .filter(Boolean)
      .map(Number);
    let sequence = 1;
    while (values.includes(sequence)) sequence += 1;
    return `PV-${String(sequence).padStart(3, "0")}`;
  }

  function improveForms() {
    if (!isVerification()) return;
    const code = $("#pCode");
    if (code) {
      if (!code.value) code.value = suggestedCode();
      code.placeholder = "Ex. PV-001";
      code.title = "Code proposé automatiquement ; il doit être unique dans ce dossier.";
    }
    const label = $("#pLabel");
    if (label) label.placeholder = "Ex. Vérifier la validité du certificat ISO 9001 déclaré";
    const category = $("#pCat");
    if (category) {
      category.placeholder = "Ex. DOCUMENTATION ou CERTIFICATION";
      category.title = "Classement du contrôle, distinct des données collectées : IDENTITÉ, DOCUMENTATION, CERTIFICATION, OFFRE ou CONFORMITÉ.";
    }
    const observation = $("#pObs");
    if (observation) observation.placeholder = "Ex. Certificat lisible, valide jusqu’au 31/12/2026 et cohérent avec la déclaration.";
    const anomaly = $("#aDesc");
    if (anomaly) anomaly.placeholder = "Ex. Le certificat transmis est expiré ; une preuve de renouvellement est attendue.";

    const confirmationButton = $("#cAdd");
    const confirmationGrid = confirmationButton?.previousElementSibling;
    if (confirmationButton && confirmationGrid && !$("#cMessage")) {
      confirmationGrid.insertAdjacentHTML("beforeend", '<div class="form-field full"><label>Message de la demande</label><textarea id="cMessage" rows="4" placeholder="Bonjour, nous vous prions de confirmer l’authenticité et la portée de la certification mentionnée…"></textarea><small class="field-help">Ce contenu sera conservé dans Échanges organismes et envoyé par e-mail.</small></div>');
    }
  }

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("#cAdd");
    if (!button || !isVerification()) return;
    event.preventDefault();
    event.stopImmediatePropagation();

    const destination = $("#cDest")?.value.trim();
    const subject = $("#cObj")?.value.trim();
    if (!destination || !subject) return;

    const dossierId = location.hash.replace(/^#\/verifications\//, "").split("/")[0];
    try {
      const api = await import("/static/js/core/api.js");
      await api.apiPost(`/api/v1/verifications/${dossierId}/confirmations`, {
        organisme_id: $("#cOrg")?.value || null,
        canal: $("#cCanal")?.value.trim() || "EMAIL",
        destinataire: destination,
        objet: subject,
        contenu_demande: $("#cMessage")?.value.trim() || "",
        informations_partagees: [...document.querySelectorAll(".sharing-context input:checked")].map((input) => input.value),
        date_envoi: $("#cSent")?.value || null,
        date_echeance: $("#cDue")?.value || null,
        statut: "EN_ATTENTE",
      });
      location.reload();
    } catch (error) {
      const state = $("#vdState");
      if (state) {
        state.hidden = false;
        state.className = "dashboard-api-state error";
        state.textContent = error?.message || "Création de confirmation impossible.";
      }
    }
  }, true);

  new MutationObserver(improveForms).observe(document.documentElement, { childList: true, subtree: true });
  window.addEventListener("hashchange", improveForms);
  improveForms();
})();
