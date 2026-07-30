(function () {
  "use strict";

  const $ = (selector) => document.querySelector(selector);
  const integrationId = location.hash.replace(/^#\//, "").split("/")[1];

  let apiGet;
  let apiPost;
  let currentUser = null;
  let integration = null;
  let context = null;
  let plan = null;
  let activeTab = "overview";

  const statusLabels = {
    EN_ATTENTE: "À analyser",
    PRECONTROLE: "Prête",
    INTEGRATION_EN_COURS: "Intégration en cours",
    INTEGREE: "Intégrée",
    BLOQUE: "Bloquée",
    ECHEC: "Échec — analyse requise",
  };

  const icon = (name) => `<i data-lucide="${name}"></i>`;

  function refreshIcons() {
    window.lucide?.createIcons({ attrs: { "stroke-width": 1.8 } });
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function hasPermission(code) {
    return Array.isArray(currentUser?.permissions) && currentUser.permissions.includes(code);
  }

  function statusClass(value) {
    const key = String(value || "").toUpperCase();
    if (key === "INTEGREE") return "integrated";
    if (key === "ECHEC" || key === "BLOQUE") return "failed";
    if (key === "INTEGRATION_EN_COURS") return "running";
    if (key === "PRECONTROLE") return "precontrol";
    return "waiting";
  }

  function itemStatusClass(value) {
    const key = String(value || "").toUpperCase();
    if (key === "INTEGRE") return "integrated";
    if (key === "BLOQUE" || key === "ECHEC") return "blocked";
    return "ready";
  }

  function itemStatusLabel(value) {
    return {
      PRET: "Prêt",
      INTEGRE: "Intégré",
      BLOQUE: "Bloqué",
      ECHEC: "Échec",
    }[String(value || "").toUpperCase()] || String(value || "—").replaceAll("_", " ");
  }

  function formatDate(value) {
    if (!value) return "—";
    const parsed = new Date(`${value}T00:00:00`);
    if (Number.isNaN(parsed.getTime())) return String(value);
    return new Intl.DateTimeFormat("fr-FR", {
      day: "2-digit",
      month: "long",
      year: "numeric",
    }).format(parsed);
  }

  function showState(message, error = false) {
    const node = $("#integrationDetailState");
    node.hidden = false;
    node.className = `dashboard-api-state ${error ? "error" : ""}`.trim();
    node.innerHTML = `${icon(error ? "triangle-alert" : "info")}<div><strong>${
      error ? "Opération impossible" : "Information"
    }</strong><span>${escapeHtml(message)}</span></div>`;
    refreshIcons();
  }

  function hideState() {
    $("#integrationDetailState").hidden = true;
  }

  function closeDialog(id) {
    const dialog = document.getElementById(id);
    if (dialog?.open) dialog.close();
  }

  function renderHeader() {
    const company = context.entreprise_name || plan?.entreprise_nom || "Entreprise non renseignée";
    $("#integrationBreadcrumb").textContent = `${company} · ${context.mission_code || "Mission"}`;
    $("#integrationDetailTitle").textContent = company;
    $("#integrationDetailSubtitle").textContent =
      [context.mission_code, context.campaign_code, context.zone_name]
        .filter(Boolean)
        .join(" · ") || "Intégration BNEC";

    const badge = $("#integrationDetailStatus");
    badge.className = `integration-status ${statusClass(integration.statut)}`;
    badge.innerHTML = `<i></i>${escapeHtml(
      statusLabels[integration.statut] || integration.statut || "—"
    )}`;

    $("#integrationDetailRefs").innerHTML = `
      <span><b>Fiche</b>Révision ${escapeHtml(context.fiche_revision || "—")}</span>
      <span><b>Validation N2</b>${escapeHtml(context.validation_decision || "—")}</span>
      <span><b>Validée le</b>${escapeHtml(formatDate(context.validation_date))}</span>
      <span><b>Transaction</b>${escapeHtml(integration.sauvegarde_reference || "À créer")}</span>`;

    renderLifecycle();
    renderKpis();
    renderActions();
    refreshIcons();
  }

  function renderLifecycle() {
    const status = String(integration.statut || "").toUpperCase();
    const integrated = status === "INTEGREE";
    const executing = status === "INTEGRATION_EN_COURS";
    const blocked = ["BLOQUE", "ECHEC"].includes(status) || !plan?.ready;
    const steps = [
      ["Analyse automatique", true, plan?.ready ? "Dossier prêt" : "Correction requise"],
      ["Intégration & codification", integrated || executing, integrated ? "Terminée" : "En attente"],
      ["BNEC officielle", integrated, integrated ? "Ressources publiées" : "Non intégrée"],
    ];

    $("#integrationLifecycle").innerHTML = `
      <div class="integration-stepper integration-v4-stepper">
        ${steps.map(([label, done, detail], index) => `
          <div class="integration-step ${done ? "done" : ""} ${
            (!done && index === (integrated ? 3 : executing ? 1 : 0)) ? "active" : ""
          } ${blocked && index === 0 ? "blocked" : ""}">
            <span>${done ? icon("check") : index + 1}</span>
            <div><strong>${escapeHtml(label)}</strong><small>${escapeHtml(detail)}</small></div>
          </div>${index < 2 ? '<i class="integration-step-line"></i>' : ""}`
        ).join("")}
      </div>`;
    refreshIcons();
  }

  function renderKpis() {
    const cards = [
      ["blue", "list-checks", "Ressources", plan?.total || 0, "Détectées depuis la fiche validée"],
      ["green", "binary", "Codification", plan?.codification_ready ? "Prête" : "Bloquée", plan?.codification_ready ? "Modèles publiés disponibles" : "Modèle publié requis"],
      ["orange", "triangle-alert", "Blocages", (plan?.blocked_count || 0) + (plan?.error_count || 0), "Aucun blocage requis avant intégration"],
      ["gray", "badge-check", "Résultat", integration.statut === "INTEGREE" ? "Officiel" : "En attente", integration.statut === "INTEGREE" ? "Visible dans les registres BNEC" : "Confirmation non exécutée"],
    ];
    $("#integrationDetailKpis").innerHTML = cards.map(([tone, cardIcon, label, value, detail]) => `
      <article class="integration-detail-kpi ${tone}">
        <span>${icon(cardIcon)}</span>
        <div><small>${escapeHtml(label)}</small><strong>${escapeHtml(value)}</strong><em>${escapeHtml(detail)}</em></div>
      </article>`).join("");
    $("#integrationElementCount").textContent = String(plan?.total || 0);
    refreshIcons();
  }

  function renderActions() {
    const status = String(integration.statut || "").toUpperCase();
    const closed = status === "INTEGREE";
    const required = [
      "INTEGRATION.EXECUTER",
      "INTEGRATION.PRECONTROLER",
      "INTEGRATION.POSTCONTROLER",
      "INTEGRATION.CLOTURER",
    ];
    const canExecute = required.every(hasPermission);
    $("#integrationPrepare").hidden = closed || !hasPermission("INTEGRATION.EXECUTER");
    $("#integrationExecute").hidden = closed || !canExecute || !plan?.ready;
    $("#integrationExecute").disabled = !plan?.ready;
    refreshIcons();
  }

  function infoCell(label, value) {
    return `<div class="cert-info"><small>${escapeHtml(label)}</small><strong>${escapeHtml(value || "—")}</strong></div>`;
  }

  function renderOverview() {
    const missing = plan?.missing_codification_models || [];
    const blockers = (plan?.items || []).filter((item) => item.blocage);
    const readyMessage = plan?.ready
      ? "Le dossier a déjà subi la vérification, le contrôle FUCCS et la double validation. Il est prêt pour une intégration transactionnelle en un clic."
      : "L’intégration reste bloquée tant que l’analyse automatique signale une anomalie.";

    $("#integrationTabContent").innerHTML = `
      <div class="integration-overview-grid bnec-overview-grid">
        <article class="panel bnec-overview-panel">
          <div class="panel-heading"><div><h2>État du passage BNEC</h2><p>${escapeHtml(readyMessage)}</p></div></div>
          <div class="cert-info-grid">
            ${infoCell("Statut", statusLabels[integration.statut] || integration.statut)}
            ${infoCell("Décision N2", context.validation_decision)}
            ${infoCell("Résultat FUCCS", context.control_rate ? `${context.control_rate} %` : "—")}
            ${infoCell("Révision source", context.fiche_revision)}
            ${infoCell("Précontrôle", integration.precontrole || "Automatique")}
            ${infoCell("Postcontrôle", integration.postcontrole || "Automatique")}
            ${infoCell("Début", formatDate(integration.date_debut))}
            ${infoCell("Fin", formatDate(integration.date_fin))}
          </div>
          ${integration.resume ? `<div class="integration-summary-note"><i data-lucide="message-square-text"></i><span>${escapeHtml(integration.resume)}</span></div>` : ""}
        </article>

        <aside class="panel bnec-readiness-panel ${plan?.ready ? "ready" : "blocked"}">
          <span>${icon(plan?.ready ? "shield-check" : "shield-alert")}</span>
          <div>
            <small>Analyse automatique</small>
            <strong>${plan?.ready ? "Prête à intégrer" : "Intégration bloquée"}</strong>
            <p>${plan?.ready ? "Aucune ressaisie ni validation supplémentaire n’est demandée." : "Corrigez les points listés puis actualisez l’analyse."}</p>
          </div>
          ${missing.length ? `<section><b>Modèles manquants</b><ul>${missing.map((item) => `<li>Codification ${escapeHtml(item)}</li>`).join("")}</ul></section>` : ""}
          ${blockers.length ? `<section><b>Points bloquants</b><ul>${blockers.slice(0, 6).map((item) => `<li>${escapeHtml(item.blocage)}</li>`).join("")}</ul></section>` : ""}
        </aside>
      </div>`;
    refreshIcons();
  }

  function renderCodification(item) {
    if (!item.codification_requise && !item.code_genere) {
      return `<div class="bnec-code-strip neutral"><i data-lucide="minus"></i><span>Aucune nouvelle codification requise pour cette ressource.</span></div>`;
    }
    const code = item.code_genere || item.code_propose;
    const definitive = Boolean(item.code_genere && item.statut === "INTEGRE");
    return `
      <section class="bnec-code-strip ${definitive ? "definitive" : item.codification_modele ? "proposed" : "blocked"}">
        <span>${icon(definitive ? "badge-check" : "binary")}</span>
        <div>
          <small>${definitive ? "Code définitif" : "Code proposé"}</small>
          <strong>${escapeHtml(code || "Modèle indisponible")}</strong>
          <em>${escapeHtml(item.codification_modele || item.codification_logical_code || "Aucun modèle publié")} ${item.codification_version ? `· v${escapeHtml(item.codification_version)}` : ""}</em>
        </div>
      </section>`;
  }

  function renderPlanItem(item, index) {
    const technical = [
      ["Élément", item.element_id],
      ["Source", item.ressource_source_id],
      ["Cible", item.ressource_cible_id],
      ["Révision", item.revision_source],
      ["Règle", item.codification_logical_code],
      ["Version", item.codification_version],
      ["Format", item.codification_format],
    ];
    return `
      <article class="panel bnec-plan-card ${itemStatusClass(item.statut)}">
        <header>
          <div class="bnec-item-heading"><span>${index + 1}</span><div><small>${escapeHtml(item.type_libelle)}</small><strong>${escapeHtml(item.source_titre)}</strong></div></div>
          <span class="bnec-item-status ${itemStatusClass(item.statut)}">${escapeHtml(itemStatusLabel(item.statut))}</span>
        </header>
        <div class="bnec-plan-flow">
          <div class="bnec-flow-side source"><small>Donnée validée</small><strong>${escapeHtml(item.source_titre)}</strong><ul>${(item.source_details || []).map((detail) => `<li>${escapeHtml(detail)}</li>`).join("")}</ul></div>
          <div class="bnec-flow-action">${icon(item.action === "CREER" ? "plus" : item.action === "CONFIRMER" ? "check" : "git-merge")}<strong>${escapeHtml(item.action_libelle)}</strong></div>
          <div class="bnec-flow-side target"><small>Résultat BNEC</small><strong>${escapeHtml(item.cible_titre || "À déterminer")}</strong><ul>${(item.cible_details || []).map((detail) => `<li>${escapeHtml(detail)}</li>`).join("")}</ul></div>
        </div>
        ${renderCodification(item)}
        ${item.blocage ? `<div class="bnec-blocking-message">${icon("triangle-alert")}<span>${escapeHtml(item.blocage)}</span></div>` : ""}
        <details class="bnec-technical-details"><summary>${icon("braces")}Détails techniques en lecture seule</summary><div>${technical.map(([label, value]) => `<span><b>${escapeHtml(label)}</b><code>${escapeHtml(value || "—")}</code></span>`).join("")}</div></details>
      </article>`;
  }

  function renderPlan() {
    $("#integrationTabContent").innerHTML = `
      <section class="bnec-plan-intro panel">
        <span>${icon("route")}</span>
        <div><strong>Plan automatique de création et de rapprochement</strong><small>Les codes proposés proviennent des modèles publiés dans Règles & codification. Les UUID restent strictement informatifs.</small></div>
      </section>
      <div class="bnec-plan-list">${(plan?.items || []).map(renderPlanItem).join("") || '<div class="priority-empty">Aucun élément détecté.</div>'}</div>`;
    refreshIcons();
  }

  function showTab(name) {
    activeTab = name;
    document.querySelectorAll(".detail-tabs button").forEach((button) => {
      button.classList.toggle("active", button.dataset.tab === name);
    });
    if (name === "plan") renderPlan();
    else renderOverview();
  }

  function openExecuteDialog() {
    const coded = (plan?.items || []).filter((item) => item.code_propose || item.code_genere);
    $("#integrationExecutionSummary").innerHTML = `
      <span>${icon("database-zap")}</span>
      <div><strong>${escapeHtml(plan.total)} ressource(s) à traiter</strong><small>${escapeHtml(coded.length)} code(s) institutionnel(s) affiché(s) · aucun conflit bloquant</small></div>`;
    $("#integrationCodesPreview").innerHTML = coded.length
      ? coded.map((item) => `<article><span>${escapeHtml(item.type_libelle)}</span><strong>${escapeHtml(item.code_genere || item.code_propose)}</strong><small>${escapeHtml(item.codification_modele || "Code existant conservé")}${item.codification_version ? ` · v${escapeHtml(item.codification_version)}` : ""}</small></article>`).join("")
      : '<div class="priority-empty compact">Aucun nouveau code à générer.</div>';
    $("#integrationExecuteSummary").value = "";
    $("#integrationExecuteDialog").showModal();
    refreshIcons();
  }

  async function reloadAll() {
    [integration, context, plan] = await Promise.all([
      apiGet(`/api/v1/integrations-bnec/${integrationId}`),
      apiGet(`/api/v1/integrations-bnec/workspace/${integrationId}`),
      apiGet(`/api/v1/integrations-bnec/${integrationId}/plan`),
    ]);
  }

  function renderAll() {
    renderHeader();
    showTab(activeTab);
  }

  async function preparePlan(event) {
    const task = async () => {
      await apiPost(`/api/v1/integrations-bnec/${integrationId}/prepare`, {});
      await reloadAll();
      renderAll();
      showState(plan.ready
        ? "Analyse actualisée : le dossier est prêt à intégrer."
        : "Analyse actualisée : des corrections restent nécessaires.",
        !plan.ready);
    };
    try {
      if (window.HAUQE_ACTION_LOADER) {
        await window.HAUQE_ACTION_LOADER.run(task, {
          button: event.currentTarget,
          title: "Analyse BNEC",
          message: "Actualisation des rapprochements et des codes",
          detail: "Lecture de la dernière révision validée.",
        });
      } else await task();
    } catch (error) {
      showState(error?.message || "Impossible d’actualiser l’analyse.", true);
    }
  }

  async function submitExecution(event) {
    event.preventDefault();
    const task = async () => {
      await apiPost(`/api/v1/integrations-bnec/${integrationId}/start`, {
        resume: $("#integrationExecuteSummary").value.trim() || null,
      });
      closeDialog("integrationExecuteDialog");
      await reloadAll();
      activeTab = "overview";
      renderAll();
      showState("Intégration terminée : les codes définitifs ont été attribués et les ressources sont visibles dans la BNEC.");
    };
    try {
      if (window.HAUQE_ACTION_LOADER) {
        await window.HAUQE_ACTION_LOADER.run(task, {
          button: $("#confirmIntegrationExecution"),
          title: "Intégration BNEC",
          message: "Codification et création des ressources officielles",
          detail: "Transaction unique avec rollback complet en cas d’erreur.",
        });
      } else await task();
    } catch (error) {
      closeDialog("integrationExecuteDialog");
      await reloadAll().catch(() => null);
      renderAll();
      showState(error?.message || "L’intégration a été annulée.", true);
    }
  }

  function bindEvents() {
    document.querySelectorAll(".detail-tabs button").forEach((button) => {
      button.addEventListener("click", () => showTab(button.dataset.tab));
    });
    $("#integrationPrepare").addEventListener("click", preparePlan);
    $("#integrationExecute").addEventListener("click", openExecuteDialog);
    $("#integrationExecuteForm").addEventListener("submit", submitExecution);
    document.querySelectorAll('[data-close-dialog="integrationExecuteDialog"]').forEach((button) => {
      button.addEventListener("click", () => closeDialog("integrationExecuteDialog"));
    });
  }

  async function boot() {
    if (!integrationId) {
      showState("Identifiant d’intégration absent.", true);
      return;
    }
    const api = await import("/static/js/core/api.js");
    apiGet = api.apiGet;
    apiPost = api.apiPost;
    bindEvents();
    try {
      [currentUser, integration, context, plan] = await Promise.all([
        apiGet("/api/v1/me"),
        apiGet(`/api/v1/integrations-bnec/${integrationId}`),
        apiGet(`/api/v1/integrations-bnec/workspace/${integrationId}`),
        apiGet(`/api/v1/integrations-bnec/${integrationId}/plan`),
      ]);
      hideState();
      renderAll();
    } catch (error) {
      showState(error?.message || "Impossible de charger le dossier d’intégration.", true);
    }
    refreshIcons();
  }

  boot();
})();
