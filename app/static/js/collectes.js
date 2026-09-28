(function () {
  "use strict";

  const $ = (selector) => document.querySelector(selector);
  const PAGE_SIZE = 25;

  let apiGet;
  let apiPost;
  let currentUser = null;
  let workspaceFilters = null;
  let offset = 0;
  let total = 0;
  let timer = null;
  const expandedCampaigns = new Set();

  const filters = {
    search: "",
    campagne_id: "",
    mission_statut: "",
    fiche_statut: "",
    zone_id: "",
    assigned_user_id: "",
    sort: "planned",
  };

  function icon(name) {
    return `<i data-lucide="${name}"></i>`;
  }

  function refreshIcons() {
    if (window.lucide) {
      window.lucide.createIcons({
        attrs: { "stroke-width": 1.8 },
      });
    }
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function formatDate(value) {
    if (!value) return "—";
    const date = new Date(`${value}T00:00:00`);
    if (Number.isNaN(date.getTime())) return String(value);

    return new Intl.DateTimeFormat("fr-FR", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    }).format(date);
  }

  function hasPermission(code) {
    return Array.isArray(currentUser?.permissions)
      && currentUser.permissions.includes(code);
  }

  function statusClass(value) {
    const status = String(value || "").toUpperCase();

    if (status === "BROUILLON") return "draft";
    if (status === "SOUMISE") return "submitted";
    if (
      status.includes("CORRIG")
      || status === "CORRECTION"
    ) {
      return "correction";
    }

    if (
      status.includes("TERM")
      || status.includes("CLOT")
      || status.includes("VALID")
    ) {
      return "validated";
    }

    return "progress";
  }

  function showState(message, { error = false } = {}) {
    const node = $("#collectApiState");
    node.hidden = false;
    node.className =
      `dashboard-api-state ${error ? "error" : ""}`.trim();

    node.innerHTML = `
      ${icon(error ? "triangle-alert" : "info")}
      <div>
        <strong>
          ${error ? "Impossible de charger les collectes" : "Information"}
        </strong>
        <span>${escapeHtml(message)}</span>
      </div>
    `;

    refreshIcons();
  }

  function hideState() {
    $("#collectApiState").hidden = true;
  }

  function fillSelect(
    node,
    allLabel,
    items,
    mapper = (value) => ({ value, label: value })
  ) {
    node.innerHTML =
      `<option value="">${escapeHtml(allLabel)}</option>`
      + (items || []).map((item) => {
        const mapped = mapper(item);

        return `
          <option value="${escapeHtml(mapped.value)}">
            ${escapeHtml(mapped.label)}
          </option>
        `;
      }).join("");

    node.disabled = false;
  }

  function renderSummary(summary) {
    const average = summary?.average_completeness;

    const cards = [
      [
        "blue",
        "clipboard-list",
        "Missions",
        summary?.total_missions ?? 0,
        "Périmètre filtré",
      ],
      [
        "purple",
        "file-pen-line",
        "Brouillons",
        summary?.drafts ?? 0,
        "Fiches modifiables",
      ],
      [
        "green",
        "send",
        "Soumises",
        summary?.submitted ?? 0,
        "Transmises à la HAUQE",
      ],
      [
        "orange",
        "file-question",
        "Sans fiche",
        summary?.without_fiche ?? 0,
        "Mission à démarrer",
      ],
      [
        "gray",
        "gauge",
        "Complétude moyenne",
        average === null || average === undefined
          ? "—"
          : `${Number(average).toFixed(1)} %`,
        "Calcul backend",
      ],
    ];

    $("#collecteKpis").innerHTML = cards.map(
      ([tone, iconName, label, value, detail]) => `
        <article class="collecte-kpi ${tone}">
          <span>${icon(iconName)}</span>
          <div>
            <small>${escapeHtml(label)}</small>
            <strong>${escapeHtml(value)}</strong>
            <em>${escapeHtml(detail)}</em>
          </div>
        </article>
      `
    ).join("");

    refreshIcons();
  }

  function createCollecteActionButton({
    label,
    iconName,
    className = "",
    handler,
  }) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = className;
    button.setAttribute("aria-label", label);
    button.setAttribute("title", label);
    button.setAttribute("data-no-action-loader", "true");
    button.innerHTML = `${icon(iconName)}<span>${escapeHtml(label)}</span>`;
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      if (button.disabled) return;
      handler();
    });
    return button;
  }

  function openCollection(missionId, ficheId) {
    if (!missionId || !ficheId) return;
    const destination = `#/collectes/modifier/${encodeURIComponent(missionId)}/${encodeURIComponent(ficheId)}`;
    if (location.hash === destination) {
      window.dispatchEvent(new HashChangeEvent("hashchange"));
      return;
    }
    location.hash = destination;
  }

  function collectionMarkup(item, groupIndex) {
    const completeness = (
      item.completeness === null
      || item.completeness === undefined
    )
      ? "—"
      : `${Number(item.completeness).toFixed(0)} %`;
    const ficheLabel = item.fiche_id
      ? (item.fiche_status || "Fiche")
      : "Sans fiche";

    if (!item.fiche_id) {
      return `<div class="collecte-fiche-empty">Aucune collecte entreprise démarrée.</div>`;
    }

    return `
      <div class="collecte-fiche-item">
        <div class="collecte-company">
          <strong>${escapeHtml(item.entreprise_name || "Entreprise non renseignée")}</strong>
          <small>Responsable : ${escapeHtml(item.fiche_responsable_name || "Non renseigné")}</small>
        </div>
        <div class="collecte-status-stack">
          <span class="collecte-status ${statusClass(item.fiche_status)}">
            <i></i>${escapeHtml(ficheLabel)}
          </span>
          <small>Complétude ${escapeHtml(completeness)}${item.revision_number ? ` · rév. ${escapeHtml(item.revision_number)}` : ""}</small>
        </div>
        <span data-collecte-fiche-open-slot="${groupIndex}:${escapeHtml(item.mission_id)}:${escapeHtml(item.fiche_id)}"></span>
      </div>
    `;
  }

  function missionMarkup(mission, groupIndex) {
    const collectionCount = mission.collections.filter((item) => item.fiche_id).length;
    return `
      <tr class="collecte-mission-row">
        <td>
          <div class="collecte-reference">
            <strong>${escapeHtml(mission.mission_code || "Mission sans référence")}</strong>
            <small>${escapeHtml(mission.mission_object || mission.mission_status || "Objet non renseigné")}</small>
          </div>
        </td>
        <td>
          <div class="collecte-company">
            <strong>${escapeHtml(mission.zone_name || "Zone non renseignée")}</strong>
            <small>${escapeHtml(mission.zone_type || "")}</small>
          </div>
        </td>
        <td>${escapeHtml(mission.assigned_names || "Non affectée")}</td>
        <td>
          <div class="collecte-collection-list">
            <small class="collecte-collection-caption">${collectionCount} collecte${collectionCount > 1 ? "s" : ""} entreprise</small>
            ${mission.collections.map((item) => collectionMarkup(item, groupIndex)).join("")}
          </div>
        </td>
        <td>
          <div class="collecte-company">
            <strong>${escapeHtml(formatDate(mission.planned_start))}</strong>
            <small>${mission.planned_end ? `→ ${escapeHtml(formatDate(mission.planned_end))}` : ""}</small>
          </div>
        </td>
        <td class="collecte-mission-status">${escapeHtml(mission.mission_status || "—")}</td>
        <td><div class="collecte-mission-actions"><span data-collecte-mission-agents-slot="${groupIndex}:${escapeHtml(mission.mission_id)}"></span><span data-collecte-mission-new-slot="${groupIndex}:${escapeHtml(mission.mission_id)}"></span></div></td>
      </tr>
    `;
  }

  function groupByCampaign(items) {
    const groups = [];
    const byCampaignId = new Map();
    const showEmptyCampaigns = !filters.search
      && !filters.zone_id
      && !filters.assigned_user_id
      && !filters.mission_statut
      && !filters.fiche_statut;
    if (showEmptyCampaigns) {
      (workspaceFilters?.campaigns || []).forEach((campaign) => {
        if (filters.campagne_id && String(campaign.id) !== String(filters.campagne_id)) return;
        const group = {
          id: String(campaign.id),
          code: campaign.code || campaign.label || "Campagne non renseignée",
          name: String(campaign.label || "").replace(/^.*?\s+—\s+/, ""),
          missions: [],
          missionById: new Map(),
        };
        byCampaignId.set(group.id, group);
        groups.push(group);
      });
    }
    items.forEach((item) => {
      const id = String(item.campaign_id || "sans-campagne");
      let group = byCampaignId.get(id);
      if (!group) {
        group = {
          id,
          code: item.campaign_code || "Campagne non renseignée",
          name: item.campaign_name || "",
          missions: [],
          missionById: new Map(),
        };
        byCampaignId.set(id, group);
        groups.push(group);
      }
      const missionId = String(item.mission_id);
      let mission = group.missionById.get(missionId);
      if (!mission) {
        mission = { ...item, collections: [] };
        group.missionById.set(missionId, mission);
        group.missions.push(mission);
      }
      mission.collections.push(item);
    });
    return groups;
  }

  function hydrateCampaignTreeButtons(groups) {
    groups.forEach((group, groupIndex) => {
      const detail = document.querySelector(
        `[data-collecte-campaign-detail="${CSS.escape(String(groupIndex))}"]`
      );
      const toggleSlot = document.querySelector(
        `[data-collecte-campaign-toggle-slot="${CSS.escape(String(groupIndex))}"]`
      );
      if (detail && toggleSlot) {
        const refreshToggle = () => {
          const expanded = expandedCampaigns.has(group.id);
          detail.hidden = !expanded;
          toggleSlot.replaceChildren(createCollecteActionButton({
            label: expanded
              ? "Masquer les missions"
              : `Voir les ${group.missions.length} mission${group.missions.length > 1 ? "s" : ""}`,
            iconName: expanded ? "chevron-up" : "list-tree",
            className: "collecte-campaign-toggle",
            handler: () => {
              if (expandedCampaigns.has(group.id)) {
                expandedCampaigns.delete(group.id);
              } else {
                expandedCampaigns.add(group.id);
              }
              refreshToggle();
            },
          }));
          toggleSlot.querySelector("button")?.setAttribute(
            "aria-expanded",
            String(expanded)
          );
          refreshIcons();
        };
        refreshToggle();
      }

      const createSlot = document.querySelector(
        `[data-collecte-mission-create-slot="${CSS.escape(String(groupIndex))}"]`
      );
      if (createSlot && canManageMission()) {
        createSlot.replaceChildren(createCollecteActionButton({
          label: "Créer une mission",
          iconName: "plus",
          className: "collecte-mission-create",
          handler: () => openCreateMissionDialog(group),
        }));
      }

      group.missions.forEach((mission) => {
        const agentsSlot = document.querySelector(
          `[data-collecte-mission-agents-slot="${CSS.escape(`${groupIndex}:${mission.mission_id}`)}"]`
        );
        if (agentsSlot && canManageMission()) {
          agentsSlot.replaceChildren(createCollecteActionButton({
            label: "Agents",
            iconName: "users-round",
            className: "collecte-mission-agents",
            handler: () => openMissionAgentsDialog(mission),
          }));
        }
        const newSlot = document.querySelector(
          `[data-collecte-mission-new-slot="${CSS.escape(`${groupIndex}:${mission.mission_id}`)}"]`
        );
        if (newSlot && hasPermission("COLLECTE.CREER")) {
          newSlot.replaceChildren(createCollecteActionButton({
            label: "Nouvelle collecte",
            iconName: "file-plus-2",
            className: "collecte-mission-open",
            handler: () => { location.hash = `#/collectes/nouveau/${mission.mission_id}`; },
          }));
        }
        mission.collections.filter((item) => item.fiche_id).forEach((item) => {
          const ficheSlot = document.querySelector(
            `[data-collecte-fiche-open-slot="${CSS.escape(`${groupIndex}:${mission.mission_id}:${item.fiche_id}`)}"]`
          );
          if (!ficheSlot) return;
          ficheSlot.replaceChildren(createCollecteActionButton({
            label: "Ouvrir la collecte",
            iconName: "folder-open",
            className: "collecte-fiche-open",
            handler: () => openCollection(mission.mission_id, item.fiche_id),
          }));
        });
      });
    });
  }

  function renderRows(payload) {
    total = Number(payload?.total || 0);
    const items = Array.isArray(payload?.items)
      ? payload.items
      : [];

    renderSummary(payload?.summary || {});

    const campaignGroups = groupByCampaign(items);
    const missionCount = campaignGroups.reduce((count, group) => count + group.missions.length, 0);
    const collectionCount = items.filter((item) => item.fiche_id).length;
    $("#collecteCount").textContent = campaignGroups.length
      ? `${campaignGroups.length} campagne${campaignGroups.length > 1 ? "s" : ""} · ${missionCount} mission${missionCount > 1 ? "s" : ""} · ${collectionCount} collecte${collectionCount > 1 ? "s" : ""}`
      : "Aucune campagne";

    const start = total ? offset + 1 : 0;
    const end = Math.min(offset + items.length, total);

    $("#collecteRange").textContent = total
      ? `${start}–${end} sur ${total}`
      : "Aucune mission";

    $("#collectePagination").textContent = total
      ? `Affichage ${start} à ${end}`
      : "0 résultat";

    $("#collectePrev").disabled = offset <= 0;
    $("#collecteNextPage").disabled =
      offset + PAGE_SIZE >= total;

    const tbody = $("#collecteRows");
    const empty = $("#collecteEmpty");

    if (!campaignGroups.length) {
      tbody.innerHTML = "";
      empty.hidden = false;
      refreshIcons();
      return;
    }

    empty.hidden = true;

    tbody.innerHTML = campaignGroups.map((group, groupIndex) => `
      <tr class="collecte-campaign-row">
        <td colspan="8">
          <div class="collecte-campaign-summary">
            <span class="collecte-campaign-icon">${icon("folders")}</span>
            <div>
              <small>Campagne de collecte</small>
              <strong>${escapeHtml(group.code)}</strong>
              ${group.name ? `<em>${escapeHtml(group.name)}</em>` : ""}
            </div>
            <b>${group.missions.length} mission${group.missions.length > 1 ? "s" : ""}</b>
            <span class="collecte-mission-create-slot" data-collecte-mission-create-slot="${groupIndex}"></span>
            <span class="collecte-campaign-toggle-slot" data-collecte-campaign-toggle-slot="${groupIndex}"></span>
          </div>
        </td>
      </tr>
      <tr class="collecte-campaign-missions-row" data-collecte-campaign-detail="${groupIndex}" hidden>
        <td colspan="8">
          <div class="collecte-campaign-missions-detail">
            <table class="table collecte-missions-table">
              <thead><tr><th>Mission</th><th>Zone</th><th>Agents affectés</th><th>Collectes entreprises et responsable</th><th>Prévue</th><th>Statut mission</th><th></th></tr></thead>
              <tbody>${group.missions.map((mission) => missionMarkup(mission, groupIndex)).join("")}</tbody>
            </table>
          </div>
        </td>
      </tr>
    `).join("");

    hydrateCampaignTreeButtons(campaignGroups);

    refreshIcons();
  }

  function queryString() {
    const params = new URLSearchParams();

    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.set(key, value);
    });

    params.set("limit", String(PAGE_SIZE));
    params.set("offset", String(offset));

    return params.toString();
  }

  async function loadFilters() {
    const payload = await apiGet(
      "/api/v1/collectes/filters"
    );
    workspaceFilters = payload;

    fillSelect(
      $("#collecteCampaign"),
      "Toutes les campagnes",
      payload.campaigns,
      (item) => ({
        value: item.id,
        label: item.label,
      })
    );

    fillSelect(
      $("#collecteMissionStatus"),
      "Tous les statuts mission",
      payload.mission_statuses
    );

    fillSelect(
      $("#collecteFicheStatus"),
      "Tous les statuts fiche",
      [
        ...(payload.fiche_statuses || []),
        "SANS_FICHE",
      ]
    );

    fillSelect(
      $("#collecteZone"),
      "Toutes les zones",
      payload.zones,
      (item) => ({
        value: item.id,
        label: item.label,
      })
    );

    fillSelect(
      $("#collecteAgent"),
      "Tous les agents",
      payload.collectors,
      (item) => ({
        value: item.id,
        label: item.label,
      })
    );
  }

  function canManageMission() {
    return hasPermission("COLLECTE.AFFECTER");
  }

  function optionMarkup(items, placeholder) {
    return `<option value="">${escapeHtml(placeholder)}</option>` + (items || [])
      .map((item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.label)}</option>`)
      .join("");
  }

  async function proposeCollecteCode(type, field) {
    field.placeholder = "Proposition automatique…";
    try {
      const proposal = await apiGet(`/api/v1/collectes/codes/proposer?type=${encodeURIComponent(type)}`);
      if (!field.value.trim()) field.value = proposal.code || "";
    } catch {
      field.placeholder = "Code attribué automatiquement à l’enregistrement";
    }
  }

  async function openCreateMissionDialog(campaign) {
    if (!canManageMission()) return;
    const dialog = $("#createMissionDialog");
    const form = $("#createMissionForm");
    form.dataset.campaignId = campaign.id;
    $("#createMissionCampaignLabel").textContent = [campaign.code, campaign.name]
      .filter(Boolean).join(" — ");
    $("#newMissionCode").value = "";
    $("#newMissionObject").value = "";
    $("#newMissionStart").value = "";
    $("#newMissionEnd").value = "";
    $("#newMissionZone").innerHTML = optionMarkup(
      workspaceFilters?.zones,
      "Sélectionnez une zone"
    );
    $("#newMissionAgents").innerHTML = (workspaceFilters?.collectors || []).map((agent) => `
      <label><input type="checkbox" name="mission_agent" value="${escapeHtml(agent.id)}"><span>${escapeHtml(agent.label)}</span></label>
    `).join("") || "<small>Aucun collecteur actif n’est disponible.</small>";
    dialog.showModal();
    void proposeCollecteCode("MISSION", $("#newMissionCode"));
    refreshIcons();
  }

  function renderMissionAgentPicker({ selectedIds = [], target, inputName }) {
    const selected = new Set(selectedIds.map(String));
    target.innerHTML = (workspaceFilters?.collectors || []).map((agent) => `
      <label><input type="checkbox" name="${inputName}" value="${escapeHtml(agent.id)}"${selected.has(String(agent.id)) ? " checked" : ""}><span>${escapeHtml(agent.label)}</span></label>
    `).join("") || "<small>Aucun collecteur actif n’est disponible.</small>";
  }

  async function openMissionAgentsDialog(mission) {
    if (!canManageMission()) return;
    try {
      const assignments = await apiGet(`/api/v1/missions/${mission.mission_id}/affectations`);
      const activeIds = assignments
        .filter((assignment) => !assignment.statut || String(assignment.statut).toUpperCase() === "ACTIF")
        .map((assignment) => String(assignment.utilisateur_id));
      const form = $("#missionAgentsForm");
      form.dataset.missionId = mission.mission_id;
      form.dataset.existingAgentIds = JSON.stringify(activeIds);
      $("#missionAgentsMissionLabel").textContent = mission.mission_code || "Mission sélectionnée";
      renderMissionAgentPicker({
        selectedIds: activeIds,
        target: $("#missionAgentsPicker"),
        inputName: "mission_agent_manage",
      });
      $("#missionAgentsDialog").showModal();
      refreshIcons();
    } catch (error) {
      showState(error?.message || "Lecture des agents affectés impossible.", { error: true });
    }
  }

  async function saveMissionAgents(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const existing = new Set(JSON.parse(form.dataset.existingAgentIds || "[]"));
    const selected = [...document.querySelectorAll('[name="mission_agent_manage"]:checked')]
      .map((input) => input.value);
    const additions = selected.filter((id) => !existing.has(String(id)));
    if (!additions.length) {
      $("#missionAgentsDialog").close();
      showState("Aucun nouvel agent n’a été ajouté à cette mission.");
      return;
    }
    try {
      await apiPost(`/api/v1/missions/${form.dataset.missionId}/affectations/ajout-groupe`, {
        utilisateur_ids: additions,
      });
      $("#missionAgentsDialog").close();
      showState(`${additions.length} agent${additions.length > 1 ? "s" : ""} ajouté${additions.length > 1 ? "s" : ""} à la mission. Les fiches existantes restent inchangées.`);
      await loadRegistry({ message: "Actualisation des affectations" });
    } catch (error) {
      showState(error?.message || "Ajout des agents impossible.", { error: true });
    }
  }

  async function openMissionQuickZoneDialog() {
    $("#missionQuickZoneName").value = "";
    $("#missionQuickZoneCode").value = "";
    $("#missionQuickZoneType").value = "LOCALITE";
    $("#missionQuickZoneParent").innerHTML = optionMarkup(
      workspaceFilters?.zones,
      "Aucune"
    );
    $("#missionQuickZoneDialog").showModal();
    void proposeCollecteCode("ZONE", $("#missionQuickZoneCode"));
    refreshIcons();
  }

  async function saveMissionQuickZone(event) {
    event.preventDefault();
    try {
      const created = await apiPost("/api/v1/zones-administratives/quick-create", {
        type_zone: $("#missionQuickZoneType").value,
        code: $("#missionQuickZoneCode").value.trim() || null,
        nom: $("#missionQuickZoneName").value.trim(),
        parent_id: $("#missionQuickZoneParent").value || null,
      });
      workspaceFilters.zones = [
        ...(workspaceFilters?.zones || []),
        { id: created.id, label: created.label || created.nom || $("#missionQuickZoneName").value.trim() },
      ];
      $("#newMissionZone").innerHTML = optionMarkup(
        workspaceFilters.zones,
        "Sélectionnez une zone"
      );
      $("#newMissionZone").value = created.id;
      $("#missionQuickZoneDialog").close();
      showState("Zone créée et sélectionnée pour la mission.");
    } catch (error) {
      showState(error?.message || "Création de la zone impossible.", { error: true });
    }
  }

  async function createMission(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const agentIds = [...document.querySelectorAll('[name="mission_agent"]:checked')]
      .map((input) => input.value);
    const start = $("#newMissionStart").value || null;
    const end = $("#newMissionEnd").value || null;
    if (!agentIds.length) {
      showState("Sélectionnez au moins un agent collecteur pour cette mission.", { error: true });
      return;
    }
    if (start && end && end < start) {
      showState("La fin prévue ne peut pas précéder le début prévu.", { error: true });
      return;
    }
    try {
      await apiPost(`/api/v1/campagnes/${form.dataset.campaignId}/missions`, {
        code: $("#newMissionCode").value.trim() || null,
        objet: $("#newMissionObject").value.trim() || null,
        zone_id: $("#newMissionZone").value,
        date_debut_prevue: start,
        date_fin_prevue: end,
        progression: 0,
        statut: "PLANIFIEE",
        agent_ids: agentIds,
      });
      $("#createMissionDialog").close();
      showState("Mission créée et agents affectés. Aucune fiche entreprise n’a été créée.");
      await loadRegistry({ message: "Actualisation des missions" });
    } catch (error) {
      showState(error?.message || "Création de la mission impossible.", { error: true });
    }
  }

  async function loadRegistry({
    button = null,
    message = "Chargement des missions",
  } = {}) {
    hideState();

    const task = async () => {
      const payload = await apiGet(
        `/api/v1/collectes/registry?${queryString()}`
      );

      renderRows(payload);
    };

    try {
      if (window.HAUQE_ACTION_LOADER) {
        await window.HAUQE_ACTION_LOADER.run(task, {
          button,
          title: "Campagnes & collecte",
          message,
          detail: "Lecture des missions et fiches courantes.",
          minVisibleMs: 300,
        });
      } else {
        await task();
      }
    } catch (error) {
      showState(
        error?.message || "Erreur de chargement.",
        { error: true }
      );
    }
  }

  function bind() {
    $("#collecteSearch").addEventListener("input", (event) => {
      clearTimeout(timer);

      timer = setTimeout(() => {
        filters.search = event.target.value.trim();
        offset = 0;
        loadRegistry({ message: "Recherche des missions" });
      }, 350);
    });

    [
      ["#collecteCampaign", "campagne_id"],
      ["#collecteMissionStatus", "mission_statut"],
      ["#collecteFicheStatus", "fiche_statut"],
      ["#collecteZone", "zone_id"],
      ["#collecteAgent", "assigned_user_id"],
      ["#collecteSort", "sort"],
    ].forEach(([selector, key]) => {
      $(selector).addEventListener("change", (event) => {
        filters[key] = event.target.value;
        offset = 0;
        loadRegistry({ message: "Application des filtres" });
      });
    });

    $("#resetCollectes").addEventListener(
      "click",
      async (event) => {
        Object.assign(filters, {
          search: "",
          campagne_id: "",
          mission_statut: "",
          fiche_statut: "",
          zone_id: "",
          assigned_user_id: "",
          sort: "planned",
        });

        offset = 0;

        $("#collecteSearch").value = "";
        $("#collecteCampaign").value = "";
        $("#collecteMissionStatus").value = "";
        $("#collecteFicheStatus").value = "";
        $("#collecteZone").value = "";
        $("#collecteAgent").value = "";
        $("#collecteSort").value = "planned";

        await loadRegistry({
          button: event.currentTarget,
          message: "Réinitialisation des filtres",
        });
      }
    );

    $("#collectePrev").addEventListener(
      "click",
      async (event) => {
        offset = Math.max(0, offset - PAGE_SIZE);

        await loadRegistry({
          button: event.currentTarget,
          message: "Page précédente",
        });
      }
    );

    $("#collecteNextPage").addEventListener(
      "click",
      async (event) => {
        offset += PAGE_SIZE;

        await loadRegistry({
          button: event.currentTarget,
          message: "Page suivante",
        });
      }
    );
  }

  async function bootstrap() {
    const api = await import("/static/js/core/api.js");
    apiGet = api.apiGet;
    apiPost = api.apiPost;

    bind();
    $("#createMissionForm").addEventListener("submit", createMission);
    $("#missionAgentsForm").addEventListener("submit", saveMissionAgents);
    $("#missionQuickZoneForm").addEventListener("submit", saveMissionQuickZone);
    $("#openMissionQuickZone").addEventListener("click", openMissionQuickZoneDialog);
    document.querySelectorAll("[data-close-create-mission]").forEach((button) => {
      button.addEventListener("click", () => $("#createMissionDialog").close());
    });
    document.querySelectorAll("[data-close-mission-agents]").forEach((button) => {
      button.addEventListener("click", () => $("#missionAgentsDialog").close());
    });
    document.querySelectorAll("[data-close-mission-quick-zone]").forEach((button) => {
      button.addEventListener("click", () => $("#missionQuickZoneDialog").close());
    });

    try {
      currentUser = await apiGet("/api/v1/me");

      const canCreateCollection = hasPermission("COLLECTE.CREER");

      $("#newCollectionAction").hidden = !canCreateCollection;
      $("#manageCampaignsAction").hidden = !hasPermission("COLLECTE.AFFECTER");

      await loadFilters();
      await loadRegistry();
    } catch (error) {
      showState(
        error?.message || "Erreur de chargement.",
        { error: true }
      );
    }

    refreshIcons();
  }

  bootstrap();
})();
