(function () {
  "use strict";

  const $ = (selector) => document.querySelector(selector);

  const PAGE_SIZE = 25;
  const SEARCH_DEBOUNCE_MS = 350;

  const state = {
    search: "",
    statut: "",
    zoneId: "",
    secteur: "",
    sort: "name",
    offset: 0,
    limit: PAGE_SIZE,
    archives: false,
    total: 0,
    items: [],
    selected: new Set(),
    requestId: 0,
    searchTimer: null,
    currentMenu: null,
  };

  let apiGet;
  let apiPost;
  let apiBlob;
  let ApiError;
  let hasPermission;

  function loader() {
    return window.HAUQE_ACTION_LOADER || null;
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

  function initials(item) {
    const source = (
      item.raison_sociale
      || item.nom_commercial
      || item.identifiant_national
      || "Entreprise"
    );

    const parts = String(source)
      .trim()
      .split(/\s+/)
      .filter(Boolean);

    if (!parts.length) return "EN";
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();

    return `${parts[0][0] || ""}${parts.at(-1)?.[0] || ""}`.toUpperCase();
  }

  function displayName(item) {
    return (
      item.raison_sociale
      || item.nom_commercial
      || item.identifiant_national
      || "Entreprise"
    );
  }

  function formatNumber(value) {
    const number = Number(value);
    if (!Number.isFinite(number)) return "—";

    return new Intl.NumberFormat("fr-FR", {
      maximumFractionDigits: 2,
    }).format(number);
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

  function formatDateTime(value) {
    if (!value) return "—";

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);

    return new Intl.DateTimeFormat("fr-FR", {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    }).format(date);
  }

  function statusMeta(raw) {
    const key = String(raw || "").trim().toUpperCase();

    const map = {
      ACTIF: ["active", "Actif"],
      CERTIFIEE_ACTIVE: ["active", "Certifiée active"],
      CERTIFIE_ACTIVE: ["active", "Certifiée active"],
      CONFORME: ["active", "Conforme"],
      A_RISQUE: ["risk", "À risque"],
      A_SURVEILLER: ["risk", "À surveiller"],
      NON_CONFORME: ["noncompliant", "Non conforme"],
      EN_ATTENTE_REGULARISATION: ["risk", "En attente de régularisation"],
      A_VERIFIER: ["verify", "À vérifier"],
      ARCHIVE: ["verify", "Archivée"],
    };

    if (map[key]) return map[key];
    if (!key) return ["verify", "Non classée"];

    return [
      "verify",
      key
        .toLowerCase()
        .replaceAll("_", " ")
        .replace(/^./, (char) => char.toUpperCase()),
    ];
  }

  function statusBadge(raw) {
    const [tone, label] = statusMeta(raw);
    return `<span class="company-status ${tone}"><i></i>${escapeHtml(label)}</span>`;
  }

  function classificationDisplay(item) {
    if (item.classification_score === null || item.classification_score === undefined) {
      return `
        <div class="stacked">
          <strong>—</strong>
          <small>${escapeHtml(item.classification_classe || "Non calculée")}</small>
        </div>
      `;
    }

    const score = Math.max(0, Math.min(100, Number(item.classification_score) || 0));

    return `
      <div class="score-display">
        <strong>${formatNumber(score)}</strong>
        <span><i style="width:${score}%"></i></span>
      </div>
      <small class="company-score-class">${escapeHtml(item.classification_classe || "")}</small>
    `;
  }

  function nextExpiry(item) {
    if (!item.next_expiration) {
      return `
        <div class="stacked">
          <strong>—</strong>
          <small>Aucune échéance active</small>
        </div>
      `;
    }

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const target = new Date(`${item.next_expiration}T00:00:00`);
    const days = Math.ceil((target - today) / 86400000);

    return `
      <div class="stacked">
        <strong>${escapeHtml(formatDate(item.next_expiration))}</strong>
        <small>${days < 0 ? "Dépassée" : `${days} jour${days > 1 ? "s" : ""}`}</small>
      </div>
    `;
  }

  function identity(item) {
    return `
      <div class="company-identity">
        <span class="company-logo">${escapeHtml(initials(item))}</span>
        <div>
          <strong>${escapeHtml(displayName(item))}</strong>
          <small>${escapeHtml(item.activite_principale || "Activité non renseignée")}</small>
        </div>
      </div>
    `;
  }

  function queryString({ exportRequest = false } = {}) {
    const params = new URLSearchParams();

    if (state.search) params.set("search", state.search);
    if (state.zoneId) params.set("zone_id", state.zoneId);
    if (state.secteur) params.set("secteur", state.secteur);

    if (state.archives) {
      params.set("statut", "ARCHIVE");
      params.set("include_archived", "true");
    } else if (state.statut) {
      params.set("statut", state.statut);
    }

    params.set("sort", state.sort);

    if (!exportRequest) {
      params.set("limit", String(state.limit));
      params.set("offset", String(state.offset));
    }

    return params.toString();
  }

  function showApiState({ title, message, tone = "", retry = false }) {
    const box = $("#companiesApiState");
    if (!box) return;

    box.className = `companies-api-state ${tone}`.trim();
    box.hidden = false;
    box.innerHTML = `
      <i data-lucide="${tone === "error" ? "triangle-alert" : "info"}"></i>
      <div>
        <strong>${escapeHtml(title)}</strong>
        <span>${escapeHtml(message)}</span>
      </div>
      ${retry ? `
        <button class="btn btn-outline-secondary app-btn" id="retryCompanies" type="button">
          <i data-lucide="refresh-cw"></i>Réessayer
        </button>
      ` : ""}
    `;

    $("#retryCompanies")?.addEventListener("click", (event) => {
      loadRegistry({ button: event.currentTarget, forceLoader: true });
    });

    refreshIcons();
  }

  function hideApiState() {
    const box = $("#companiesApiState");
    if (!box) return;
    box.hidden = true;
    box.innerHTML = "";
    box.className = "companies-api-state";
  }

  function renderKpis(summary = {}) {
    const items = [
      ["", "building-2", "Entreprises enregistrées", summary.total ?? 0, "Registre courant"],
      ["blue", "badge-check", "Avec certification active", summary.certified_active ?? 0, "Calculé depuis les certifications"],
      ["orange", "triangle-alert", "À risque", summary.at_risk ?? 0, "Échéance stratégique ≤ 90 jours"],
      ["red", "shield-x", "Non conformes", summary.non_compliant ?? 0, "Statut / classification enregistrée"],
    ];

    $("#companyKpis").innerHTML = items.map((item) => `
      <article class="company-kpi ${item[0]}">
        <span><i data-lucide="${item[1]}"></i></span>
        <div>
          <small>${escapeHtml(item[2])}</small>
          <strong>${formatNumber(item[3])}</strong>
          <em>${escapeHtml(item[4])}</em>
        </div>
      </article>
    `).join("");
  }

  function renderRows() {
    const rows = $("#companyRows");
    const cards = $("#cardView");
    const empty = $("#emptyCompanies");

    rows.innerHTML = state.items.map((item) => `
      <tr data-company-id="${escapeHtml(item.id)}" tabindex="0">
        <td>
          <label class="table-check">
            <input
              class="company-select"
              type="checkbox"
              data-company-select="${escapeHtml(item.id)}"
              ${state.selected.has(String(item.id)) ? "checked" : ""}
            >
            <span></span>
          </label>
        </td>
        <td>${identity(item)}</td>
        <td>
          <div class="stacked">
            <strong>${escapeHtml(item.rccm || item.identifiant_national || "—")}</strong>
            <small>${escapeHtml(item.nif ? `NIF ${item.nif}` : item.identifiant_national || "Identifiant non renseigné")}</small>
          </div>
        </td>
        <td>
          <div class="stacked">
            <strong>${escapeHtml(item.zone_nom || "—")}</strong>
            <small>${escapeHtml(item.zone_type || "Zone non renseignée")}</small>
          </div>
        </td>
        <td><span class="cert-count">${formatNumber(item.certifications_count || 0)} certificat(s)</span></td>
        <td>${nextExpiry(item)}</td>
        <td>${classificationDisplay(item)}</td>
        <td>${statusBadge(item.statut)}</td>
        <td>
          <button
            class="more-button company-row-actions"
            type="button"
            data-company-menu="${escapeHtml(item.id)}"
            aria-label="Actions pour ${escapeHtml(displayName(item))}"
          >
            <i data-lucide="ellipsis-vertical"></i>
          </button>
        </td>
      </tr>
    `).join("");

    cards.innerHTML = state.items.map((item) => `
      <article class="company-card" data-company-card="${escapeHtml(item.id)}" tabindex="0">
        <div class="company-card-head">
          ${identity(item)}
          <button class="more-button company-row-actions" type="button" data-company-menu="${escapeHtml(item.id)}">
            <i data-lucide="ellipsis-vertical"></i>
          </button>
        </div>

        <div class="company-card-body">
          <div>
            <small>Certifications</small>
            <strong>${formatNumber(item.certifications_count || 0)}</strong>
          </div>
          <div>
            <small>Classification</small>
            <strong>${item.classification_score == null ? "—" : `${formatNumber(item.classification_score)}/100`}</strong>
          </div>
          <div>
            <small>Échéance</small>
            <strong>${escapeHtml(formatDate(item.next_expiration))}</strong>
          </div>
          <div>
            <small>Statut</small>
            ${statusBadge(item.statut)}
          </div>
        </div>
      </article>
    `).join("");

    empty.hidden = state.items.length > 0;
    $("#tableView").hidden = state.items.length === 0 || $(".view-button[data-view='cards']")?.classList.contains("active");
    cards.hidden = state.items.length === 0 || !$(".view-button[data-view='cards']")?.classList.contains("active");

    $("#companyCount").textContent = `${formatNumber(state.total)} entreprise${state.total > 1 ? "s" : ""}`;
    $("#companyScopeText").textContent = state.archives ? "Entreprises archivées" : "Registre opérationnel";

    bindRenderedRows();
    refreshIcons();
  }

  function renderPagination() {
    const container = $("#companiesPagination");
    const first = state.total ? state.offset + 1 : 0;
    const last = Math.min(state.offset + state.limit, state.total);
    const page = Math.floor(state.offset / state.limit) + 1;
    const pages = Math.max(1, Math.ceil(state.total / state.limit));

    $("#paginationText").textContent = state.total
      ? `Affichage de ${first} à ${last} sur ${state.total}`
      : "Aucune entreprise";

    const pageButtons = [];
    const start = Math.max(1, page - 2);
    const end = Math.min(pages, start + 4);

    pageButtons.push(`
      <button class="page-number" type="button" data-page-nav="prev" ${page <= 1 ? "disabled" : ""} aria-label="Page précédente">
        <i data-lucide="chevron-left"></i>
      </button>
    `);

    for (let current = start; current <= end; current += 1) {
      pageButtons.push(`
        <button class="page-number ${current === page ? "active" : ""}" type="button" data-page="${current}">
          ${current}
        </button>
      `);
    }

    pageButtons.push(`
      <button class="page-number" type="button" data-page-nav="next" ${page >= pages ? "disabled" : ""} aria-label="Page suivante">
        <i data-lucide="chevron-right"></i>
      </button>
    `);

    container.innerHTML = pageButtons.join("");

    container.querySelectorAll("[data-page]").forEach((button) => {
      button.addEventListener("click", () => {
        state.offset = (Number(button.dataset.page) - 1) * state.limit;
        state.selected.clear();
        loadRegistry({ forceLoader: true, message: "Chargement de la page" });
      });
    });

    container.querySelector("[data-page-nav='prev']")?.addEventListener("click", () => {
      state.offset = Math.max(0, state.offset - state.limit);
      state.selected.clear();
      loadRegistry({ forceLoader: true, message: "Chargement de la page précédente" });
    });

    container.querySelector("[data-page-nav='next']")?.addEventListener("click", () => {
      if (state.offset + state.limit < state.total) {
        state.offset += state.limit;
        state.selected.clear();
        loadRegistry({ forceLoader: true, message: "Chargement de la page suivante" });
      }
    });

    refreshIcons();
  }

  function updateSelectionUi() {
    const visibleIds = state.items.map((item) => String(item.id));
    const allVisibleSelected = visibleIds.length > 0 && visibleIds.every((id) => state.selected.has(id));

    const selectAll = $("#selectAll");
    selectAll.checked = allVisibleSelected;
    selectAll.indeterminate = !allVisibleSelected && visibleIds.some((id) => state.selected.has(id));

    $("#bulkActions").hidden = state.selected.size === 0 || state.archives;
  }

  function bindRenderedRows() {
    document.querySelectorAll("[data-company-select]").forEach((input) => {
      input.addEventListener("change", () => {
        const id = String(input.dataset.companySelect);
        if (input.checked) state.selected.add(id);
        else state.selected.delete(id);
        updateSelectionUi();
      });
    });

    document.querySelectorAll("[data-company-id]").forEach((row) => {
      const open = () => {
        location.hash = `#/entreprises/${row.dataset.companyId}`;
      };

      row.addEventListener("click", (event) => {
        if (event.target.closest("input,button,label")) return;
        open();
      });

      row.addEventListener("keydown", (event) => {
        if (event.key === "Enter") open();
      });
    });

    document.querySelectorAll("[data-company-card]").forEach((card) => {
      const open = () => {
        location.hash = `#/entreprises/${card.dataset.companyCard}`;
      };

      card.addEventListener("click", (event) => {
        if (event.target.closest("button")) return;
        open();
      });

      card.addEventListener("keydown", (event) => {
        if (event.key === "Enter") open();
      });
    });

    document.querySelectorAll("[data-company-menu]").forEach((button) => {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        const item = state.items.find((company) => String(company.id) === String(button.dataset.companyMenu));
        if (item) openRowMenu(button, item);
      });
    });

    updateSelectionUi();
  }

  function closeRowMenu() {
    state.currentMenu?.remove();
    state.currentMenu = null;
  }

  function openRowMenu(anchor, item) {
    closeRowMenu();

    const archived = String(item.statut || "").toUpperCase() === "ARCHIVE";
    const canEdit = hasPermission("ENTREPRISES.MODIFIER");
    const canArchive = hasPermission("ENTREPRISES.ARCHIVER");

    const menu = document.createElement("div");
    menu.className = "company-action-menu";
    menu.id = "companyActionMenu";

    menu.innerHTML = `
      <button type="button" data-action="open">
        <i data-lucide="eye"></i>
        <span><strong>Ouvrir le dossier</strong><small>${escapeHtml(displayName(item))}</small></span>
      </button>
      ${canEdit && !archived ? `
        <button type="button" data-action="edit">
          <i data-lucide="square-pen"></i>
          <span><strong>Modifier</strong><small>Informations de l’entreprise</small></span>
        </button>
      ` : ""}
      ${canArchive ? `
        <button type="button" data-action="${archived ? "restore" : "archive"}" class="${archived ? "" : "danger"}">
          <i data-lucide="${archived ? "archive-restore" : "archive"}"></i>
          <span><strong>${archived ? "Restaurer" : "Archiver"}</strong><small>${archived ? "Réintégrer au registre" : "Archivage logique audité"}</small></span>
        </button>
      ` : ""}
    `;

    document.body.appendChild(menu);
    state.currentMenu = menu;

    const rect = anchor.getBoundingClientRect();
    const width = menu.offsetWidth;
    const height = menu.offsetHeight;

    menu.style.left = `${Math.max(12, Math.min(rect.right - width, innerWidth - width - 12))}px`;
    menu.style.top = `${Math.max(12, Math.min(rect.bottom + 7, innerHeight - height - 12))}px`;

    menu.querySelector("[data-action='open']")?.addEventListener("click", () => {
      closeRowMenu();
      location.hash = `#/entreprises/${item.id}`;
    });

    menu.querySelector("[data-action='edit']")?.addEventListener("click", () => {
      closeRowMenu();
      location.hash = `#/entreprises/modifier/${item.id}`;
    });

    menu.querySelector("[data-action='archive']")?.addEventListener("click", async () => {
      closeRowMenu();
      const reason = await requestReason({
        title: "Archiver l’entreprise",
        subtitle: displayName(item),
        label: "Motif d’archivage",
        confirmLabel: "Archiver",
        icon: "archive",
        danger: true,
      });
      if (reason === null) return;
      await archiveCompanies([String(item.id)], reason);
    });

    menu.querySelector("[data-action='restore']")?.addEventListener("click", async () => {
      closeRowMenu();
      const reason = await requestReason({
        title: "Restaurer l’entreprise",
        subtitle: displayName(item),
        label: "Motif de restauration",
        confirmLabel: "Restaurer",
        icon: "archive-restore",
      });
      if (reason === null) return;
      await restoreCompany(String(item.id), reason);
    });

    refreshIcons();
  }

  function requestReason({ title, subtitle, label, confirmLabel, icon, danger = false }) {
    const dialog = $("#companyActionDialog");
    const form = $("#companyActionForm");
    const reason = $("#companyDialogReason");
    const confirm = $("#confirmCompanyDialog");

    $("#companyDialogTitle").textContent = title;
    $("#companyDialogSubtitle").textContent = subtitle;
    $("#companyDialogReasonLabel").textContent = label;
    $("#companyDialogIcon").innerHTML = `<i data-lucide="${icon}"></i>`;
    confirm.textContent = confirmLabel;
    confirm.classList.toggle("btn-danger", danger);
    confirm.classList.toggle("btn-primary", !danger);
    reason.value = "";

    refreshIcons();

    return new Promise((resolve) => {
      const cleanup = () => {
        form.removeEventListener("submit", onSubmit);
        $("#cancelCompanyDialog").removeEventListener("click", onCancel);
        dialog.removeEventListener("cancel", onCancel);
      };

      const finish = (value) => {
        cleanup();
        dialog.close();
        resolve(value);
      };

      const onSubmit = (event) => {
        event.preventDefault();
        const value = reason.value.trim();
        if (!value) {
          reason.focus();
          reason.classList.add("invalid");
          return;
        }
        finish(value);
      };

      const onCancel = (event) => {
        event?.preventDefault?.();
        finish(null);
      };

      reason.addEventListener("input", () => reason.classList.remove("invalid"), { once: true });
      form.addEventListener("submit", onSubmit);
      $("#cancelCompanyDialog").addEventListener("click", onCancel);
      dialog.addEventListener("cancel", onCancel);
      dialog.showModal();
      setTimeout(() => reason.focus(), 0);
    });
  }

  async function archiveCompanies(ids, motif) {
    if (!ids.length) return;

    const task = async () => {
      const results = await Promise.allSettled(
        ids.map((id) => apiPost(`/api/v1/entreprises/${id}/archive`, { motif }))
      );

      const failed = results.filter((result) => result.status === "rejected");

      if (failed.length) {
        throw failed[0].reason;
      }

      state.selected.clear();
      await loadRegistry({ silentLoader: true });
    };

    try {
      if (loader()) {
        await loader().run(task, {
          title: "Archivage des entreprises",
          message: ids.length > 1 ? "Archivage de la sélection" : "Archivage de l’entreprise",
          detail: "L’opération est conservée dans le journal d’audit.",
        });
      } else {
        await task();
      }
    } catch (error) {
      showApiState({
        title: "Archivage impossible",
        message: error?.message || "Une entreprise n’a pas pu être archivée.",
        tone: "error",
      });
    }
  }

  async function restoreCompany(id, motif) {
    const task = async () => {
      await apiPost(`/api/v1/entreprises/${id}/restore`, { motif });
      await loadRegistry({ silentLoader: true });
    };

    try {
      if (loader()) {
        await loader().run(task, {
          title: "Restauration de l’entreprise",
          message: "Restauration",
          detail: "L’entreprise réapparaîtra dans le registre opérationnel.",
        });
      } else {
        await task();
      }
    } catch (error) {
      showApiState({
        title: "Restauration impossible",
        message: error?.message || "L’entreprise n’a pas pu être restaurée.",
        tone: "error",
      });
    }
  }

  async function exportRegistry(button) {
    const reason = await requestReason({
      title: "Exporter le registre",
      subtitle: "L’export respecte les filtres actuellement appliqués.",
      label: "Motif de l’export",
      confirmLabel: "Générer le CSV",
      icon: "download",
    });

    if (reason === null) return;

    const task = async () => {
      const params = new URLSearchParams(queryString({ exportRequest: true }));
      params.set("motif", reason);

      const blob = await apiBlob(`/api/v1/entreprises/export?${params.toString()}`);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");

      link.href = url;
      link.download = `hauqe-entreprises-${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    };

    try {
      if (loader()) {
        await loader().run(task, {
          button,
          title: "Export du registre",
          message: "Génération du fichier",
          detail: "Le serveur prépare les entreprises correspondant aux filtres.",
        });
      } else {
        await task();
      }
    } catch (error) {
      showApiState({
        title: "Export impossible",
        message: error?.message || "Le fichier n’a pas pu être généré.",
        tone: "error",
      });
    }
  }

  async function loadFilters() {
    try {
      const payload = await apiGet("/api/v1/entreprises/filters");

      const statusSelect = $("#statusFilter");
      statusSelect.innerHTML = `<option value="">Tous les statuts</option>`;
      (payload.statuses || []).forEach((value) => {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = statusMeta(value)[1];
        statusSelect.appendChild(option);
      });
      statusSelect.disabled = false;
      statusSelect.removeAttribute("aria-busy");

      const zoneSelect = $("#regionFilter");
      zoneSelect.innerHTML = `<option value="">Toutes les régions / zones</option>`;
      (payload.zones || []).forEach((zone) => {
        const option = document.createElement("option");
        option.value = zone.id;
        option.textContent = [zone.nom, zone.type_zone ? `(${zone.type_zone})` : ""].filter(Boolean).join(" ");
        zoneSelect.appendChild(option);
      });
      zoneSelect.disabled = false;
      zoneSelect.removeAttribute("aria-busy");

      const sectorSelect = $("#sectorFilter");
      sectorSelect.innerHTML = `<option value="">Tous les secteurs / activités</option>`;
      (payload.sectors || []).forEach((sector) => {
        const option = document.createElement("option");
        option.value = sector;
        option.textContent = sector;
        sectorSelect.appendChild(option);
      });
      sectorSelect.disabled = false;
      sectorSelect.removeAttribute("aria-busy");

      $("#resetCompanies").disabled = false;
    } catch (error) {
      ["#statusFilter", "#regionFilter", "#sectorFilter"].forEach((selector) => {
        const select = $(selector);
        select.innerHTML = `<option value="">Filtre indisponible</option>`;
        select.disabled = true;
        select.removeAttribute("aria-busy");
      });

      $("#resetCompanies").disabled = true;
      console.warn("Filtres Entreprises :", error);
    }
  }

  async function loadRegistry({
    button = null,
    forceLoader = false,
    silentLoader = false,
    message = "Chargement du registre",
  } = {}) {
    const requestId = ++state.requestId;

    const task = async () => {
      const payload = await apiGet(`/api/v1/entreprises/registry?${queryString()}`);

      if (requestId !== state.requestId) return;

      state.total = Number(payload.total || 0);
      state.items = Array.isArray(payload.items) ? payload.items : [];

      hideApiState();
      renderKpis(payload.summary || {});
      renderRows();
      renderPagination();

      $("#companiesSyncAt").innerHTML = `<i data-lucide="refresh-cw"></i>Actualisé à ${new Intl.DateTimeFormat("fr-FR", { hour: "2-digit", minute: "2-digit" }).format(new Date())}`;
      refreshIcons();
    };

    try {
      if (loader() && (forceLoader || !silentLoader)) {
        await loader().run(task, {
          button,
          title: state.archives ? "Archives entreprises" : "Registre entreprises",
          message,
          detail: "Lecture sécurisée des données autorisées.",
          minVisibleMs: forceLoader ? 320 : 220,
        });
      } else {
        await task();
      }
    } catch (error) {
      if (ApiError && error instanceof ApiError && error.status === 403) {
        showApiState({
          title: "Accès au registre refusé",
          message: "Votre compte ne possède pas la permission ENTREPRISES.LIRE.",
          tone: "warning",
        });
        return;
      }

      showApiState({
        title: "Impossible de charger le registre",
        message: error?.message || "Le serveur n’a pas pu retourner les entreprises.",
        tone: "error",
        retry: true,
      });
    }
  }

  function bindStaticActions() {
    const search = $("#companySearch");

    search.addEventListener("input", () => {
      clearTimeout(state.searchTimer);
      state.searchTimer = setTimeout(() => {
        state.search = search.value.trim();
        state.offset = 0;
        state.selected.clear();
        loadRegistry({ silentLoader: true });
      }, SEARCH_DEBOUNCE_MS);
    });

    $("#statusFilter").addEventListener("change", (event) => {
      state.statut = event.target.value;
      state.offset = 0;
      state.selected.clear();
      loadRegistry({ forceLoader: true, message: "Application du filtre de statut" });
    });

    $("#regionFilter").addEventListener("change", (event) => {
      state.zoneId = event.target.value;
      state.offset = 0;
      state.selected.clear();
      loadRegistry({ forceLoader: true, message: "Application du filtre géographique" });
    });

    $("#sectorFilter").addEventListener("change", (event) => {
      state.secteur = event.target.value;
      state.offset = 0;
      state.selected.clear();
      loadRegistry({ forceLoader: true, message: "Application du filtre secteur" });
    });

    $("#companySort").addEventListener("change", (event) => {
      state.sort = event.target.value;
      state.offset = 0;
      loadRegistry({ forceLoader: true, message: "Tri du registre" });
    });

    $("#resetCompanies").addEventListener("click", (event) => {
      state.search = "";
      state.statut = "";
      state.zoneId = "";
      state.secteur = "";
      state.sort = "name";
      state.offset = 0;
      state.selected.clear();

      search.value = "";
      $("#statusFilter").value = "";
      $("#regionFilter").value = "";
      $("#sectorFilter").value = "";
      $("#companySort").value = "name";

      loadRegistry({ button: event.currentTarget, forceLoader: true, message: "Réinitialisation du registre" });
    });

    $("#selectAll").addEventListener("change", (event) => {
      state.items.forEach((item) => {
        const id = String(item.id);
        if (event.target.checked) state.selected.add(id);
        else state.selected.delete(id);
      });

      document.querySelectorAll("[data-company-select]").forEach((input) => {
        input.checked = event.target.checked;
      });

      updateSelectionUi();
    });

    $("#bulkArchive").addEventListener("click", async () => {
      const reason = await requestReason({
        title: "Archiver la sélection",
        subtitle: `${state.selected.size} entreprise(s) sélectionnée(s)`,
        label: "Motif commun d’archivage",
        confirmLabel: "Archiver",
        icon: "archive",
        danger: true,
      });

      if (reason === null) return;
      await archiveCompanies([...state.selected], reason);
    });

    $("#exportCompanies").addEventListener("click", (event) => {
      exportRegistry(event.currentTarget);
    });

    $("#toggleArchives").addEventListener("click", (event) => {
      state.archives = !state.archives;
      state.offset = 0;
      state.statut = "";
      state.selected.clear();

      $("#statusFilter").value = "";
      event.currentTarget.classList.toggle("active", state.archives);
      event.currentTarget.querySelector("span").textContent = state.archives ? "Registre actif" : "Archives";
      const currentIcon = event.currentTarget.querySelector("svg");
      if (currentIcon) {
        currentIcon.outerHTML = `<i data-lucide="${state.archives ? "building-2" : "archive"}"></i>`;
        refreshIcons();
      }

      $("#newCompanyButton").hidden = state.archives || !hasPermission("ENTREPRISES.CREER");
      $("#exportCompanies").hidden = !hasPermission("ENTREPRISES.EXPORTER");

      loadRegistry({ button: event.currentTarget, forceLoader: true, message: state.archives ? "Chargement des archives" : "Retour au registre actif" });
    });

    document.querySelectorAll(".view-button[data-view]").forEach((button) => {
      button.addEventListener("click", () => {
        document.querySelectorAll(".view-button[data-view]").forEach((item) => item.classList.remove("active"));
        button.classList.add("active");

        const cards = button.dataset.view === "cards" || button.dataset.view === "grid";
        $("#cardView").hidden = !cards || state.items.length === 0;
        $("#tableView").hidden = cards || state.items.length === 0;
        try {
          localStorage.setItem("hauqe-entreprises-view", cards ? "cards" : "table");
        } catch (_) {}
      });
    });

    const savedView = localStorage.getItem("hauqe-entreprises-view");
    if (savedView) {
      document.querySelector(`.view-button[data-view="${savedView}"]`)?.click();
    }

    document.addEventListener("click", (event) => {
      if (state.currentMenu && !event.target.closest("#companyActionMenu,[data-company-menu]")) {
        closeRowMenu();
      }
    });

    window.addEventListener("resize", closeRowMenu);
    window.addEventListener("scroll", closeRowMenu, { passive: true });
  }

  async function bootstrap() {
    const [apiModule, authModule] = await Promise.all([
      import("/static/js/core/api.js"),
      import("/static/js/core/auth.js"),
    ]);

    apiGet = apiModule.apiGet;
    apiPost = apiModule.apiPost;
    apiBlob = apiModule.apiBlob;
    ApiError = apiModule.ApiError;
    hasPermission = authModule.hasPermission;

    $("#newCompanyButton").hidden = !hasPermission("ENTREPRISES.CREER");
    $("#exportCompanies").hidden = !hasPermission("ENTREPRISES.EXPORTER");
    $("#toggleArchives").hidden = !hasPermission("ENTREPRISES.LIRE");
    $("#bulkArchive").hidden = !hasPermission("ENTREPRISES.ARCHIVER");

    bindStaticActions();

    const task = async () => {
      await loadFilters();
      await loadRegistry({ silentLoader: true });
    };

    if (loader()) {
      await loader().run(task, {
        title: "Registre des entreprises",
        message: "Chargement du registre",
        detail: "Récupération des filtres, indicateurs et entreprises.",
        minVisibleMs: 420,
      });
    } else {
      await task();
    }

    refreshIcons();
  }

  bootstrap().catch((error) => {
    console.error("Entreprises bootstrap :", error);
    showApiState({
      title: "Initialisation impossible",
      message: error?.message || "Le module Entreprises n’a pas pu démarrer.",
      tone: "error",
      retry: true,
    });
  });
})();
