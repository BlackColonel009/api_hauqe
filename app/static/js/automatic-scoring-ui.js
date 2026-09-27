/* Interface commune des calculs automatiques explicables. */
window.HAUQEAutomaticScoringReady = (async function () {
  "use strict";

  const api = await import("/static/js/core/api.js");
  const { refreshCurrentRoute } = await import("/static/js/core/router.js");
  const escapeHtml = (value) => String(value ?? "—")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/\"/g, "&quot;").replace(/'/g, "&#039;");

  function dialog() {
    let node = document.getElementById("automaticScoringReportDialog");
    if (node) return node;
    node = document.createElement("dialog");
    node.id = "automaticScoringReportDialog";
    node.className = "hauqe-dialog scoring-evaluation-dialog";
    node.innerHTML = `
      <form method="dialog">
        <header>
          <div><p class="eyebrow">Calcul automatique</p><h2 id="automaticScoringReportTitle">Rapport d'évaluation</h2></div>
          <button class="dialog-close" value="cancel" aria-label="Fermer"><i data-lucide="x"></i></button>
        </header>
        <div class="dialog-body" id="automaticScoringReportBody"></div>
        <footer><button class="btn btn-primary app-btn" value="cancel"><i data-lucide="check"></i>Fermer</button></footer>
      </form>`;
    document.body.appendChild(node);
    return node;
  }

  function reportTitle(operation) {
    return {
      CLASSIFICATION_ENTREPRISE: "Rapport de classification entreprise",
      INFC: "Rapport de calcul INFC",
      SNCC: "Rapport de classement SNCC",
    }[operation] || "Rapport de calcul automatique";
  }

  function show(payload) {
    const report = payload?.rapport || {};
    const node = dialog();
    document.getElementById("automaticScoringReportTitle").textContent = reportTitle(report.operation);
    const score = report.score == null ? "Non calculé" : escapeHtml(report.score);
    const result = payload.execute
      ? "Calcul enregistré automatiquement"
      : "Calcul non enregistré : des prérequis restent à traiter";
    const problems = (title, values, kind) => values?.length ? `
      <section class="score-preview ${kind}"><strong>${escapeHtml(title)}</strong><ul>${values.map((value) => `<li>${escapeHtml(value)}</li>`).join("")}</ul></section>` : "";
    const findings = (report.constats || []).map((item) => `
      <tr><td><strong>${escapeHtml(item.libelle)}</strong></td><td>${escapeHtml(item.valeur == null ? "—" : `${item.valeur}%`)}</td><td><span class="scoring-result-status ${String(item.statut || "").toLowerCase()}">${escapeHtml(item.statut)}</span></td><td>${escapeHtml(item.detail)}</td></tr>`).join("");
    document.getElementById("automaticScoringReportBody").innerHTML = `
      <section class="score-model-context"><strong>${escapeHtml(result)}</strong><small>Score : ${score}${report.classe ? ` · Classe : ${escapeHtml(report.classe)}` : ""}${report.statut_administratif ? ` · Statut : ${escapeHtml(report.statut_administratif)}` : ""}${report.niveau != null ? ` · Niveau : ${escapeHtml(report.niveau)}` : ""}${report.niveau_risque ? ` · Risque : ${escapeHtml(report.niveau_risque)}` : ""}</small><small>Modèle : ${escapeHtml(report.modele_code || "non disponible")} · version ${escapeHtml(report.modele_version || "—")}</small>${report.regle_risque_code ? `<small>Règle de risque : ${escapeHtml(report.regle_risque_code)} · version ${escapeHtml(report.regle_risque_version || "—")}</small>` : ""}</section>
      ${problems("Éléments bloquants", report.blocages, "error")}
      ${problems("Points à surveiller", report.alertes, "warning")}
      <section class="panel score-details"><header><div><h3>Pourquoi cette note ?</h3><p>Chaque ligne provient d'une donnée tracée du dossier et des règles publiées.</p></div></header><div class="table-responsive"><table class="table score-table"><thead><tr><th>Étape</th><th>Valeur</th><th>État</th><th>Constat</th></tr></thead><tbody>${findings || "<tr><td colspan='4'>Aucun constat disponible.</td></tr>"}</tbody></table></div></section>`;
    node.onclose = () => { if (payload.execute) refreshCurrentRoute(); };
    node.showModal();
    window.lucide?.createIcons({ attrs: { "stroke-width": 1.8 } });
  }

  const endpointFor = (operation, id) => ({
    CLASSIFICATION_ENTREPRISE: `/api/v1/entreprises/${id}/classifications/automatic-evaluate`,
    INFC: `/api/v1/certifications/${id}/infc/automatic-calculate`,
    SNCC: `/api/v1/certifications/${id}/sncc/automatic-classify`,
  })[operation];

  async function run({ operation, id, button }) {
    if (!id || !endpointFor(operation, id)) return;
    const previous = button?.innerHTML;
    if (button) { button.disabled = true; button.innerHTML = '<i data-lucide="loader-circle"></i>Calcul en cours…'; }
    try {
      show(await api.apiPost(endpointFor(operation, id), {}));
    } catch (error) {
      show({ execute: false, rapport: { operation, pret: false, blocages: [error?.message || "Calcul automatique impossible."], alertes: [], constats: [] } });
    } finally {
      if (button) { button.disabled = false; button.innerHTML = previous; window.lucide?.createIcons({ attrs: { "stroke-width": 1.8 } }); }
    }
  }

  function bindSnccButtons() {
    if (!location.hash.startsWith("#/classement-sncc")) return;
    let recreated = false;
    document.querySelectorAll("[data-create], [data-reclass]").forEach((source) => {
      if (source.dataset.automaticScoringBound === "true") return;
      const id = source.dataset.create || source.dataset.reclass;
      if (!id) return;
      const button = source.cloneNode(false);
      button.dataset.automaticScoringBound = "true";
      button.className = "btn btn-primary app-btn scoring-action-button";
      button.type = "button";
      button.innerHTML = '<i data-lucide="calculator"></i>Calculer automatiquement';
      button.addEventListener("click", (event) => {
        event.preventDefault(); event.stopPropagation();
        run({ operation: "SNCC", id, button });
      });
      source.replaceWith(button);
      recreated = true;
    });
    // Le moteur d'icônes modifie le DOM. Ne l'exécuter qu'après une vraie
    // recréation de bouton, sinon l'observateur déclencherait une boucle.
    if (recreated) window.lucide?.createIcons({ attrs: { "stroke-width": 1.8 } });
  }

  let observer = null;
  function activate() {
    observer?.disconnect();
    bindSnccButtons();
    observer = new MutationObserver(bindSnccButtons);
    observer.observe(document.querySelector("#pageContent") || document.body, { childList: true, subtree: true });
  }

  window.HAUQEAutomaticScoring = { run };
  window.addEventListener("hauqe:page-ready", activate);
  // Le routeur peut avoir déjà émis l'évènement lorsque ce script dynamique
  // termine de charger. Démarrer aussi maintenant couvre ce cas.
  activate();
  window.dispatchEvent(new CustomEvent("hauqe:automatic-scoring-ready"));
})();
