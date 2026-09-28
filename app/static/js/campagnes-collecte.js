(function () {
  "use strict";

  const $ = (selector) => document.querySelector(selector);
  let apiGet;
  let apiPost;
  let apiPatch;
  let currentUser = null;
  let campaigns = [];
  let searchTimer = null;
  let loadSequence = 0;
  let actionInProgress = false;
  let campaignWizardStep = 1;

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function icon(name) { return `<i data-lucide="${name}"></i>`; }
  function refreshIcons() { window.lucide?.createIcons({ attrs: { "stroke-width": 1.8 } }); }
  function canManage() { return currentUser?.permissions?.includes("COLLECTE.AFFECTER"); }

  function formatDate(value) {
    if (!value) return "—";
    const date = new Date(`${value}T00:00:00`);
    return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat("fr-FR", { dateStyle: "medium" }).format(date);
  }

  function isActive(status) {
    return ["ACTIF", "ACTIVE", "EN_COURS"].includes(String(status || "").toUpperCase());
  }

  function serializeCampaign(campaign) {
    return encodeURIComponent(JSON.stringify({
      id: campaign.id,
      code: campaign.code,
      nom: campaign.nom,
      objet: campaign.objet,
      objectif: campaign.objectif,
      date_debut: campaign.date_debut,
      date_fin: campaign.date_fin,
      statut: campaign.statut,
      responsable_id: campaign.responsable_id,
    }));
  }

  function campaignFromButton(button) {
    try {
      return JSON.parse(decodeURIComponent(button.dataset.campaignPayload || ""));
    } catch {
      return null;
    }
  }

  function showState(message, error = false) {
    const node = $("#campaignApiState");
    node.hidden = false;
    node.className = `dashboard-api-state ${error ? "error" : ""}`.trim();
    node.innerHTML = `${icon(error ? "triangle-alert" : "info")}<div><strong>${error ? "Opération impossible" : "Information"}</strong><span>${escapeHtml(message)}</span></div>`;
    refreshIcons();
  }

  function hideState() { $("#campaignApiState").hidden = true; }

  function render() {
    const body = $("#campaignRows");
    const empty = $("#campaignEmpty");
    if (!campaigns.length) {
      body.innerHTML = "";
      empty.hidden = false;
      refreshIcons();
      return;
    }
    empty.hidden = true;
    body.innerHTML = campaigns.map((campaign) => {
      const active = isActive(campaign.statut);
      const payload = escapeHtml(serializeCampaign(campaign));
      return `<tr data-campaign-id="${escapeHtml(campaign.id)}">
        <td><div class="collecte-reference"><strong>${escapeHtml(campaign.code)}</strong><small>${escapeHtml(campaign.nom || "Sans intitulé")}</small></div></td>
        <td>${escapeHtml(campaign.objet || campaign.objectif || "—")}</td>
        <td><span class="campaign-period">${escapeHtml(formatDate(campaign.date_debut))}<small>→ ${escapeHtml(formatDate(campaign.date_fin))}</small></span></td>
        <td><span class="campaign-status ${active ? "active" : "inactive"}">${active ? "Active" : "Désactivée"}</span></td>
        <td><button class="btn btn-outline-secondary app-btn campaign-missions" type="button" data-missions="${escapeHtml(campaign.id)}">${icon("list-tree")}Voir les missions</button></td>
        <td><div class="campaign-row-actions" data-campaign-action-slot data-campaign-payload="${payload}" data-campaign-active="${active ? "true" : "false"}"></div></td>
      </tr>`;
    }).join("");

    // Les actions sont ajoutées après les lignes, comme le bouton « Corriger »
    // d'une mission liée. Elles ne dépendent ni du HTML initial ni d'un clic
    // délégué sur une ligne qui vient juste d'être chargée.
    hydrateCampaignActionButtons();
    refreshIcons();
  }

  function createCampaignActionButton({ label, iconName, danger = false, handler }) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `campaign-action-button${danger ? " campaign-disable" : ""}`;
    button.setAttribute("aria-label", label);
    button.setAttribute("title", label);
    button.setAttribute("data-no-action-loader", "true");
    button.innerHTML = icon(iconName);
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      handler();
    });
    return button;
  }

  function hydrateCampaignActionButtons() {
    document.querySelectorAll("[data-campaign-action-slot]").forEach((slot) => {
      const campaign = campaignFromButton(slot);
      if (!campaign?.id) return;

      slot.replaceChildren(createCampaignActionButton({
        label: "Modifier la campagne",
        iconName: "pencil",
        handler: () => openDialog(campaign),
      }));

      if (slot.dataset.campaignActive === "true") {
        slot.appendChild(createCampaignActionButton({
          label: "Désactiver la campagne",
          iconName: "ban",
          danger: true,
          handler: () => disableCampaign(campaign),
        }));
      }
    });
  }

  async function loadCampaigns() {
    const requestSequence = ++loadSequence;
    hideState();
    const params = new URLSearchParams({ limit: "200", offset: "0" });
    const search = $("#campaignSearch").value.trim();
    const statut = $("#campaignStatus").value;
    if (search) params.set("search", search);
    if (statut) params.set("statut", statut);
    try {
      const payload = await apiGet(`/api/v1/campagnes?${params}`);
      // Une recherche ou un rafraîchissement plus récent ne doit jamais être
      // remplacé par la réponse, arrivée en retard, d'une requête précédente.
      if (requestSequence !== loadSequence) return;
      campaigns = payload.items || [];
      render();
    } catch (error) {
      if (requestSequence !== loadSequence) return;
      showState(error?.message || "Chargement des campagnes impossible.", true);
    }
  }

  async function proposeCampaignCode() {
    const field = $("#campaignCode");
    field.placeholder = "Proposition automatique…";
    try {
      const proposal = await apiGet("/api/v1/collectes/codes/proposer?type=CAMPAGNE");
      if (!field.value.trim()) field.value = proposal.code || "";
    } catch {
      // Le serveur attribuera le code à l'enregistrement si la proposition
      // ne peut pas être chargée à cet instant.
      field.placeholder = "Code attribué automatiquement à l’enregistrement";
    }
  }

  function campaignWizardValidation(stepToValidate = campaignWizardStep) {
    if (stepToValidate === 3) {
      const start = $("#campaignStart").value;
      const end = $("#campaignEnd").value;
      if (start && end && end < start) {
        showState("La date de fin ne peut pas précéder la date de début.", true);
        $("#campaignWizardProgress").textContent = "La date de fin doit être postérieure ou égale à la date de début.";
        $("#campaignWizardProgress").classList.add("campaign-wizard-error");
        $("#campaignEnd").focus();
        return false;
      }
    }
    return true;
  }

  function renderCampaignWizard() {
    document.querySelectorAll("[data-campaign-wizard-step]").forEach((panel) => {
      const active = Number(panel.dataset.campaignWizardStep) === campaignWizardStep;
      panel.hidden = !active;
      if (active) panel.scrollTop = 0;
    });
    document.querySelectorAll("[data-campaign-wizard-go]").forEach((button) => {
      const target = Number(button.dataset.campaignWizardGo);
      button.classList.toggle("active", target === campaignWizardStep);
      button.disabled = target > campaignWizardStep;
      button.setAttribute("aria-current", target === campaignWizardStep ? "step" : "false");
    });
    $("#campaignWizardPrevious").hidden = campaignWizardStep === 1;
    $("#campaignWizardNext").hidden = campaignWizardStep === 3;
    $("#campaignWizardSave").hidden = campaignWizardStep !== 3;
    $("#campaignWizardProgress").textContent =
      `Étape ${campaignWizardStep} sur 3 · les champs marqués * sont obligatoires.`;
    $("#campaignWizardProgress").classList.remove("campaign-wizard-error");
    refreshIcons();
  }

  function goToCampaignWizardStep(targetStep) {
    const nextStep = Math.max(1, Math.min(3, Number(targetStep) || 1));
    if (nextStep > campaignWizardStep && !campaignWizardValidation(campaignWizardStep)) return;
    campaignWizardStep = nextStep;
    renderCampaignWizard();
  }

  function openDialog(campaign = null) {
    if (campaign === undefined) return;
    const dialog = $("#campaignDialog");
    const form = $("#campaignForm");
    form.dataset.campaignId = campaign?.id || "";
    form.dataset.responsibleId = campaign?.responsable_id || currentUser.id;
    $("#campaignDialogTitle").textContent = campaign ? "Modifier la campagne" : "Nouvelle campagne";
    $("#campaignCode").value = campaign?.code || "";
    $("#campaignName").value = campaign?.nom || "";
    $("#campaignObject").value = campaign?.objet || "";
    $("#campaignGoal").value = campaign?.objectif || "";
    $("#campaignStart").value = campaign?.date_debut || "";
    $("#campaignEnd").value = campaign?.date_fin || "";
    $("#campaignFormStatus").value = campaign
      ? (isActive(campaign.statut) ? "ACTIVE" : "INACTIVE")
      : "ACTIVE";
    campaignWizardStep = 1;
    renderCampaignWizard();
    if (!dialog.open) dialog.showModal();
    if (!campaign) void proposeCampaignCode();
    refreshIcons();
  }

  function closeDialog() { $("#campaignDialog").close(); }

  async function saveCampaign(event) {
    event.preventDefault();
    if (campaignWizardStep < 3) {
      goToCampaignWizardStep(campaignWizardStep + 1);
      return;
    }
    const form = event.currentTarget;
    const code = $("#campaignCode").value.trim().toUpperCase();
    const start = $("#campaignStart").value;
    const end = $("#campaignEnd").value;
    if (!campaignWizardValidation(1) || !campaignWizardValidation(3)) return;
    const payload = {
      // Le serveur attribue le prochain code si l'utilisateur laisse le
      // champ vide (par exemple si la proposition n'a pas pu être chargée).
      code: code || null,
      nom: $("#campaignName").value.trim() || null,
      objet: $("#campaignObject").value.trim() || null,
      objectif: $("#campaignGoal").value.trim() || null,
      date_debut: start || null,
      date_fin: end || null,
      statut: $("#campaignFormStatus").value,
    };
    try {
      if (form.dataset.campaignId) {
        await apiPatch(`/api/v1/campagnes/${form.dataset.campaignId}`, payload);
      } else {
        await apiPost("/api/v1/campagnes", { ...payload, responsable_id: form.dataset.responsibleId });
      }
      closeDialog();
      await loadCampaigns();
      showState("Campagne enregistrée. Les missions liées affichent les informations communes mises à jour.");
    } catch (error) {
      showState(error?.message || "Enregistrement de la campagne impossible.", true);
    }
  }

  async function disableCampaign(campaign) {
    if (!campaign || actionInProgress) return;
    if (!window.confirm(`Désactiver la campagne « ${campaign.code} » ? Les missions et collectes existantes seront conservées.`)) return;
    actionInProgress = true;
    try {
      await apiPatch(`/api/v1/campagnes/${campaign.id}`, { statut: "INACTIVE" });
      await loadCampaigns();
      showState("Campagne désactivée. Elle ne sera plus proposée pour une nouvelle mission.");
    } catch (error) {
      showState(error?.message || "Désactivation impossible.", true);
    } finally {
      actionInProgress = false;
    }
  }

  // Les lignes sont redessinées après recherche, rafraîchissement ou sauvegarde.
  // Le gestionnaire est donc posé une seule fois sur leur conteneur persistant :
  // les actions restent disponibles dès le premier clic, y compris sur une ligne
  // qui vient d'être créée ou actualisée.
  function bindRowActions() {
    $("#campaignRows").addEventListener("click", (event) => {
      const button = event.target.closest("button[data-missions], button[data-mission-id]");
      if (!button || !event.currentTarget.contains(button)) return;
      event.preventDefault();
      event.stopPropagation();

      if (button.dataset.missions) {
        toggleMissions(button.dataset.missions);
        return;
      }
      if (button.dataset.missionId) {
        const campaignId = button.dataset.campaignId;
        openMissionDialog(campaignId, {
          id: button.dataset.missionId,
          code: button.dataset.missionCode || "",
          objet: button.dataset.missionObject || "",
        });
      }
    });
  }

  async function toggleMissions(campaignId) {
    const row = document.querySelector(`tr[data-campaign-id="${CSS.escape(String(campaignId))}"]`);
    const next = row?.nextElementSibling;
    if (next?.classList.contains("campaign-missions-row")) { next.remove(); return; }
    try {
      const payload = await apiGet(`/api/v1/campagnes/${campaignId}/missions?limit=200&offset=0`);
      const items = payload.items || [];
      const detail = document.createElement("tr");
      detail.className = "campaign-missions-row";
      detail.innerHTML = `<td colspan="6"><div class="campaign-missions-detail"><strong>Missions liées (${items.length})</strong>${items.length ? `<ul>${items.map((mission) => `<li><b>${escapeHtml(mission.code || "Sans référence")}</b><span>${escapeHtml(mission.objet || "Sans objet")} · ${escapeHtml(mission.statut || "—")}</span><button type="button" class="btn btn-outline-secondary app-btn mission-reference-edit" data-mission-id="${escapeHtml(mission.id)}" data-campaign-id="${escapeHtml(campaignId)}" data-mission-code="${escapeHtml(mission.code || "")}" data-mission-object="${escapeHtml(mission.objet || "")}">${icon("pencil")}Corriger</button></li>`).join("")}</ul>` : "<span>Aucune mission rattachée.</span>"}</div></td>`;
      row.after(detail);
      refreshIcons();
    } catch (error) {
      showState(error?.message || "Lecture des missions impossible.", true);
    }
  }

  function openMissionDialog(campaignId, mission) {
    const form = $("#missionReferenceForm");
    form.dataset.campaignId = campaignId;
    form.dataset.missionId = mission.id;
    $("#missionReferenceCode").value = mission.code || "";
    $("#missionReferenceObject").value = mission.objet || "";
    $("#missionReferenceDialog").showModal();
    refreshIcons();
  }

  async function saveMissionReference(event) {
    event.preventDefault();
    const form = event.currentTarget;
    try {
      await apiPatch(
        `/api/v1/campagnes/${form.dataset.campaignId}/missions/${form.dataset.missionId}`,
        {
          code: $("#missionReferenceCode").value.trim() || null,
          objet: $("#missionReferenceObject").value.trim() || null,
        }
      );
      $("#missionReferenceDialog").close();
      await loadCampaigns();
      showState("Référence de mission corrigée. Les fiches liées affichent la nouvelle référence.");
    } catch (error) {
      showState(error?.message || "Correction de la mission impossible.", true);
    }
  }

  async function bootstrap() {
    const api = await import("/static/js/core/api.js");
    apiGet = api.apiGet; apiPost = api.apiPost; apiPatch = api.apiPatch;
    currentUser = await apiGet("/api/v1/me");
    if (!canManage()) { $("#newCampaign").hidden = true; showState("Cette rubrique est réservée aux coordonnateurs et administrateurs habilités.", true); return; }
    $("#newCampaign").addEventListener("click", () => openDialog());
    bindRowActions();
    $("#campaignForm").addEventListener("submit", saveCampaign);
    $("#campaignWizardPrevious").addEventListener("click", () => goToCampaignWizardStep(campaignWizardStep - 1));
    $("#campaignWizardNext").addEventListener("click", () => goToCampaignWizardStep(campaignWizardStep + 1));
    document.querySelectorAll("[data-campaign-wizard-go]").forEach((button) => {
      button.addEventListener("click", () => goToCampaignWizardStep(button.dataset.campaignWizardGo));
    });
    $("#missionReferenceForm").addEventListener("submit", saveMissionReference);
    document.querySelectorAll("[data-close-campaign-dialog]").forEach((button) => button.addEventListener("click", closeDialog));
    document.querySelectorAll("[data-close-mission-dialog]").forEach((button) => button.addEventListener("click", () => $("#missionReferenceDialog").close()));
    $("#campaignSearch").addEventListener("input", () => { clearTimeout(searchTimer); searchTimer = setTimeout(loadCampaigns, 300); });
    $("#campaignStatus").addEventListener("change", loadCampaigns);
    $("#refreshCampaigns").addEventListener("click", loadCampaigns);
    await loadCampaigns();
    refreshIcons();
  }

  bootstrap().catch((error) => showState(error?.message || "Préparation de la gestion des campagnes impossible.", true));
})();
