(function () {
  "use strict";

  const $ = (selector) => document.querySelector(selector);
  const PAGE_SIZE = 25;

  let apiGet;
  let apiBlob;
  let ApiError;

  let offset = 0;
  let total = 0;
  let searchTimer = null;

  const filters = {
    search: "",
    statut: "",
    pays: "",
    accrediteur: "",
    domaine: "",
    sort: "name_asc",
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

  function statusClass(value) {
    const status = String(value || "").toUpperCase();

    if (["RECONNU", "VALIDE", "ACTIF"].includes(status)) return "valid";
    if (["SUSPENDU", "SUSPENDED"].includes(status)) return "suspended";
    if (status.includes("VERIFIER")) return "verify";
    if (["RETIRE", "RETRAIT", "INACTIF"].includes(status)) return "expired";

    return "verify";
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

  function showState(message, { error = false } = {}) {
    const node = $("#bodyApiState");
    if (!node) return;

    node.hidden = false;
    node.className = `dashboard-api-state ${error ? "error" : ""}`.trim();
    node.innerHTML = `
      ${icon(error ? "triangle-alert" : "info")}
      <div>
        <strong>${error ? "Impossible de charger les organismes" : "Information"}</strong>
        <span>${escapeHtml(message)}</span>
      </div>
    `;
    refreshIcons();
  }

  function hideState() {
    const node = $("#bodyApiState");
    if (node) node.hidden = true;
  }

  function fillSelect(select, allLabel, values) {
    if (!select) return;

    select.innerHTML = `<option value="">${escapeHtml(allLabel)}</option>`
      + (values || []).map(
        (value) => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`
      ).join("");

    select.disabled = false;
  }

  function renderKpis(summary) {
    const values = [
      ["green", "landmark", "Organismes", summary?.total ?? 0, "Dans le registre"],
      ["blue", "shield-check", "Reconnus", summary?.recognized ?? 0, "Statut reconnu/valide"],
      ["orange", "search-check", "À vérifier", summary?.to_verify ?? 0, "Contrôle requis"],
      ["red", "shield-x", "Suspendus", summary?.suspended ?? 0, "Suivi renforcé"],
      ["green", "badge-check", "Certifications", summary?.certifications_total ?? 0, "Liées aux organismes"],
    ];

    $("#bodyKpis").innerHTML = values.map(
      ([tone, iconName, label, value, detail]) => `
        <article class="cert-kpi ${tone}">
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
    const items = Array.isArray(payload?.items) ? payload.items : [];

    renderKpis(payload?.summary || {});

    $("#bodyCount").textContent = `${total} organisme${total > 1 ? "s" : ""}`;

    const start = total ? offset + 1 : 0;
    const end = Math.min(offset + items.length, total);
    $("#bodyRange").textContent = total
      ? `${start}–${end} sur ${total}`
      : "Aucune donnée enregistrée";
    $("#bodyPaginationInfo").textContent = total
      ? `Affichage ${start} à ${end}`
      : "0 résultat";

    $("#bodyPrev").disabled = offset <= 0;
    $("#bodyNext").disabled = offset + PAGE_SIZE >= total;

    const tbody = $("#bodyRows");

    if (!items.length) {
      tbody.innerHTML = `
        <tr>
          <td colspan="8">
            <div class="priority-empty">
              Aucun organisme ne correspond aux critères.
            </div>
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = items.map((item) => `
      <tr data-id="${escapeHtml(item.id)}" tabindex="0">
        <td>
          <div class="cert-main">
            <span class="cert-logo">${escapeHtml(item.sigle || "OC")}</span>
            <div>
              <strong>${escapeHtml(item.nom_officiel || "Organisme")}</strong>
              <small>${escapeHtml(item.type_organisme || item.identifiant_national || "Organisme certificateur")}</small>
            </div>
          </div>
        </td>

        <td>${escapeHtml(item.pays || "—")}</td>

        <td>
          <div class="cert-stack">
            <strong>${escapeHtml(item.accreditation_count ?? 0)}</strong>
            <small>${escapeHtml(item.accreditors || "Aucun accréditeur renseigné")}</small>
          </div>
        </td>

        <td>${escapeHtml(item.domains || "—")}</td>

        <td>
          <strong>${escapeHtml(item.certification_count ?? 0)}</strong>
        </td>

        <td>
          <div class="cert-stack">
            <strong>${escapeHtml(formatDate(item.date_derniere_verification))}</strong>
            <small>
              ${
                item.next_accreditation_expiration
                  ? `Prochaine accréditation : ${escapeHtml(formatDate(item.next_accreditation_expiration))}`
                  : "Aucune échéance renseignée"
              }
            </small>
          </div>
        </td>

        <td>
          <span class="cert-status ${statusClass(item.statut)}">
            <i></i>${escapeHtml(item.statut || "Non renseigné")}
          </span>
        </td>

        <td>
          <button class="more-button" type="button" aria-label="Ouvrir">
            ${icon("chevron-right")}
          </button>
        </td>
      </tr>
    `).join("");

    tbody.querySelectorAll("tr[data-id]").forEach((row) => {
      const open = () => {
        location.hash = `#/organismes/${row.dataset.id}`;
      };

      row.addEventListener("click", open);
      row.addEventListener("keydown", (event) => {
        if (event.key === "Enter") open();
      });
    });

    refreshIcons();
  }

  function queryString({ includePaging = true } = {}) {
    const params = new URLSearchParams();

    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.set(key, value);
    });

    if (includePaging) {
      params.set("limit", String(PAGE_SIZE));
      params.set("offset", String(offset));
    }

    return params.toString();
  }

  async function loadFilters() {
    const payload = await apiGet("/api/v1/organismes/filters");

    fillSelect($("#bodyStatus"), "Tous les statuts", payload.statuses);
    fillSelect($("#bodyCountry"), "Tous les pays", payload.countries);
    fillSelect($("#bodyAccreditor"), "Tous les accréditeurs", payload.accreditors);
    fillSelect($("#bodyDomain"), "Tous les domaines", payload.domains);
  }

  async function loadRegistry({
    button = null,
    message = "Chargement du registre",
  } = {}) {
    hideState();

    const task = async () => {
      const payload = await apiGet(
        `/api/v1/organismes/registry?${queryString()}`
      );
      renderRows(payload);
    };

    try {
      if (window.HAUQE_ACTION_LOADER) {
        await window.HAUQE_ACTION_LOADER.run(task, {
          button,
          title: "Organismes certificateurs",
          message,
          detail: "Lecture du registre national.",
          minVisibleMs: 300,
        });
      } else {
        await task();
      }
    } catch (error) {
      showState(error?.message || "Erreur de chargement.", { error: true });
    }
  }

  function bind() {
    $("#bodySearch").addEventListener("input", (event) => {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(() => {
        filters.search = event.target.value.trim();
        offset = 0;
        loadRegistry({ message: "Recherche des organismes" });
      }, 350);
    });

    [
      ["#bodyStatus", "statut"],
      ["#bodyCountry", "pays"],
      ["#bodyAccreditor", "accrediteur"],
      ["#bodyDomain", "domaine"],
      ["#bodySort", "sort"],
    ].forEach(([selector, key]) => {
      $(selector).addEventListener("change", (event) => {
        filters[key] = event.target.value;
        offset = 0;
        loadRegistry({ message: "Application des filtres" });
      });
    });

    $("#resetBodies").addEventListener("click", async (event) => {
      filters.search = "";
      filters.statut = "";
      filters.pays = "";
      filters.accrediteur = "";
      filters.domaine = "";
      filters.sort = "name_asc";
      offset = 0;

      $("#bodySearch").value = "";
      $("#bodyStatus").value = "";
      $("#bodyCountry").value = "";
      $("#bodyAccreditor").value = "";
      $("#bodyDomain").value = "";
      $("#bodySort").value = "name_asc";

      await loadRegistry({
        button: event.currentTarget,
        message: "Réinitialisation du registre",
      });
    });

    $("#bodyPrev").addEventListener("click", async (event) => {
      offset = Math.max(0, offset - PAGE_SIZE);
      await loadRegistry({
        button: event.currentTarget,
        message: "Chargement de la page précédente",
      });
    });

    $("#bodyNext").addEventListener("click", async (event) => {
      offset += PAGE_SIZE;
      await loadRegistry({
        button: event.currentTarget,
        message: "Chargement de la page suivante",
      });
    });

    $("#bodyExport").addEventListener("click", async (event) => {
      const motif = window.prompt(
        "Motif de l’export du registre des organismes :"
      );

      if (!motif?.trim()) return;

      const task = async () => {
        const params = new URLSearchParams(queryString({ includePaging: false }));
        params.set("motif", motif.trim());

        const blob = await apiBlob(
          `/api/v1/organismes/export?${params.toString()}`
        );

        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `hauqe-organismes-${new Date().toISOString().slice(0, 10)}.csv`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
      };

      try {
        if (window.HAUQE_ACTION_LOADER) {
          await window.HAUQE_ACTION_LOADER.run(task, {
            button: event.currentTarget,
            title: "Export des organismes",
            message: "Génération du fichier",
            detail: "Le serveur applique les filtres et trace le motif d’export.",
          });
        } else {
          await task();
        }
      } catch (error) {
        showState(error?.message || "Export impossible.", { error: true });
      }
    });
  }

  async function bootstrap() {
    const api = await import("/static/js/core/api.js");
    apiGet = api.apiGet;
    apiBlob = api.apiBlob;
    ApiError = api.ApiError;

    bind();

    try {
      await Promise.all([
        loadFilters(),
        loadRegistry({ message: "Chargement des organismes" }),
      ]);
    } catch (error) {
      showState(error?.message || "Erreur de chargement.", { error: true });
    }

    refreshIcons();
  }

  bootstrap();
})();
