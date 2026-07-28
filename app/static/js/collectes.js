(function () {
  "use strict";

  const $ = (selector) => document.querySelector(selector);
  const PAGE_SIZE = 25;

  let apiGet;
  let currentUser = null;
  let offset = 0;
  let total = 0;
  let timer = null;

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

  function renderRows(payload) {
    total = Number(payload?.total || 0);
    const items = Array.isArray(payload?.items)
      ? payload.items
      : [];

    renderSummary(payload?.summary || {});

    $("#collecteCount").textContent =
      `${total} mission${total > 1 ? "s" : ""}`;

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

    if (!items.length) {
      tbody.innerHTML = "";
      empty.hidden = false;
      refreshIcons();
      return;
    }

    empty.hidden = true;

    tbody.innerHTML = items.map((item) => {
      const completeness = (
        item.completeness === null
        || item.completeness === undefined
      )
        ? "—"
        : `${Number(item.completeness).toFixed(0)} %`;

      const ficheLabel = item.fiche_id
        ? (item.fiche_status || "Fiche")
        : "Sans fiche";

      return `
        <tr
          data-mission-id="${escapeHtml(item.mission_id)}"
          tabindex="0"
        >
          <td>
            <div class="collecte-reference">
              <strong>
                ${escapeHtml(item.mission_code || "Mission")}
              </strong>
              <small>
                ${escapeHtml(item.mission_object || item.mission_status || "—")}
              </small>
            </div>
          </td>

          <td>
            <div class="collecte-company">
              <strong>${escapeHtml(item.campaign_code)}</strong>
              <small>${escapeHtml(item.campaign_name || "—")}</small>
            </div>
          </td>

          <td>
            <div class="collecte-company">
              <strong>${escapeHtml(item.zone_name || "—")}</strong>
              <small>${escapeHtml(item.zone_type || "")}</small>
            </div>
          </td>

          <td>
            ${escapeHtml(item.assigned_names || "Non affectée")}
          </td>

          <td>
            <div class="collecte-company">
              <strong>
                ${escapeHtml(item.entreprise_name || "Non renseignée")}
              </strong>
              <small>
                ${item.entreprise_id ? "Entreprise liée" : "À sélectionner"}
              </small>
            </div>
          </td>

          <td>
            <div class="collecte-status-stack">
              <span
                class="collecte-status ${statusClass(item.fiche_status)}"
              >
                <i></i>${escapeHtml(ficheLabel)}
              </span>
              <small>
                Complétude ${escapeHtml(completeness)}
                ${item.revision_number
                  ? ` · rév. ${escapeHtml(item.revision_number)}`
                  : ""}
              </small>
            </div>
          </td>

          <td>
            <div class="collecte-company">
              <strong>${escapeHtml(formatDate(item.planned_start))}</strong>
              <small>
                ${item.planned_end
                  ? `→ ${escapeHtml(formatDate(item.planned_end))}`
                  : ""}
              </small>
            </div>
          </td>

          <td>
            <button
              class="more-button"
              type="button"
              aria-label="Ouvrir la mission"
            >
              ${icon("chevron-right")}
            </button>
          </td>
        </tr>
      `;
    }).join("");

    tbody.querySelectorAll("[data-mission-id]").forEach((row) => {
      const open = () => {
        location.hash =
          `#/collectes/modifier/${row.dataset.missionId}`;
      };

      row.addEventListener("click", open);
      row.addEventListener("keydown", (event) => {
        if (event.key === "Enter") open();
      });
    });

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

    bind();

    try {
      currentUser = await apiGet("/api/v1/me");

      const canCreateMission =
        hasPermission("COLLECTE.AFFECTER")
        && hasPermission("COLLECTE.CREER");

      $("#newCollectionAction").hidden = !canCreateMission;

      await Promise.all([
        loadFilters(),
        loadRegistry(),
      ]);
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
