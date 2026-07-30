(function () {
  "use strict";

  const $ = (selector) => document.querySelector(selector);
  const PAGE_SIZE = 25;

  let apiGet;
  let apiPost;
  let currentUser = null;
  let activeGrid = null;
  let offset = 0;
  let total = 0;
  let timer = null;

  const filters = {
    search: "",
    statut: "",
    sort: "started",
  };
  const verificationOpinionLabel = (value) => ({
    verified_compliant: "Vérifié conforme",
    verified_with_reservation: "Vérifié avec réserve",
    not_verified: "Non vérifié",
    suspect: "Suspect",
    rejected: "Rejeté",
  }[String(value || "").toLowerCase()] || value || "—");

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

  function hasPermission(code) {
    return Array.isArray(currentUser?.permissions)
      && currentUser.permissions.includes(code);
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

  function statusClass(value) {
    const status = String(value || "").toUpperCase();

    if (status === "FINALISE") return "valid";
    if (status === "BROUILLON") return "watch";

    return "verify";
  }

  function showState(message, { error = false } = {}) {
    const node = $("#fuccsApiState");

    node.hidden = false;
    node.className =
      `dashboard-api-state ${error ? "error" : ""}`.trim();

    node.innerHTML = `
      ${icon(error ? "triangle-alert" : "info")}
      <div>
        <strong>
          ${error ? "Impossible de charger le contrôle FUCCS" : "Information"}
        </strong>
        <span>${escapeHtml(message)}</span>
      </div>
    `;

    refreshIcons();
  }

  function hideState() {
    $("#fuccsApiState").hidden = true;
  }

  function fillSelect(node, label, values) {
    node.innerHTML =
      `<option value="">${escapeHtml(label)}</option>`
      + (values || []).map((value) => `
        <option value="${escapeHtml(value)}">
          ${escapeHtml(value)}
        </option>
      `).join("");

    node.disabled = false;
  }

  function renderGridBanner() {
    const container = $("#fuccsGridBanner");

    if (!activeGrid) {
      container.className =
        "fuccs-grid-banner unavailable";

      container.innerHTML = `
        <span>${icon("shield-alert")}</span>
        <div>
          <strong>Aucune grille FUCCS publiée active</strong>
          <small>
            Un contrôle ne peut pas démarrer tant qu’une grille publiée
            n’est pas disponible.
          </small>
        </div>
      `;

      refreshIcons();
      return;
    }

    container.className = "fuccs-grid-banner";

    container.innerHTML = `
      <span>${icon("layout-list")}</span>

      <div>
        <strong>
          ${escapeHtml(
            activeGrid.label
            || activeGrid.code
            || "Grille FUCCS"
          )}
        </strong>

        <small>
          Version ${escapeHtml(activeGrid.version || "—")}
          · ${escapeHtml(activeGrid.rubrics_count)} rubrique(s)
          · ${escapeHtml(activeGrid.criteria_count)} critère(s)
          · score maximal ${escapeHtml(activeGrid.maximum_score)}
          · effet ${escapeHtml(formatDate(activeGrid.effective_date))}
        </small>
      </div>

      <span class="fuccs-published-badge">
        ${icon("badge-check")}
        Publiée
      </span>
    `;

    refreshIcons();
  }

  function renderKpis(summary) {
    const cards = [
      [
        "blue",
        "clipboard-list",
        "Contrôles",
        summary?.total ?? 0,
        "Périmètre filtré",
      ],
      [
        "orange",
        "file-pen-line",
        "Brouillons",
        summary?.drafts ?? 0,
        "En cours de notation",
      ],
      [
        "green",
        "badge-check",
        "Finalisés",
        summary?.finalized ?? 0,
        "Contrôles verrouillés",
      ],
      [
        "purple",
        "list-checks",
        "Grille complète",
        summary?.complete_notes ?? 0,
        "Tous les critères notés",
      ],
      [
        "gray",
        "circle-dashed",
        "Incomplets",
        summary?.incomplete_notes ?? 0,
        "Critères restant à noter",
      ],
    ];

    $("#fuccsKpis").innerHTML = cards.map(
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
    const items = Array.isArray(payload?.items)
      ? payload.items
      : [];

    renderKpis(payload?.summary || {});

    $("#fuccsCount").textContent =
      `${total} contrôle${total > 1 ? "s" : ""}`;

    const start = total ? offset + 1 : 0;
    const end = Math.min(offset + items.length, total);

    $("#fuccsRange").textContent = total
      ? `${start}–${end} sur ${total}`
      : "Aucun contrôle";

    $("#fuccsPagination").textContent = total
      ? `Affichage ${start} à ${end}`
      : "0 résultat";

    $("#fuccsPrev").disabled = offset <= 0;
    $("#fuccsNext").disabled =
      offset + PAGE_SIZE >= total;

    const tbody = $("#fuccsRows");
    const empty = $("#fuccsEmpty");

    if (!items.length) {
      tbody.innerHTML = "";
      empty.hidden = false;
      refreshIcons();
      return;
    }

    empty.hidden = true;

    tbody.innerHTML = items.map((item) => {
      const criteria = Number(item.criteria_count || 0);
      const notes = Number(item.notes_count || 0);

      const progress = criteria > 0
        ? Math.min(
            100,
            Math.round((notes / criteria) * 100)
          )
        : 0;

      return `
        <tr
          data-control-id="${escapeHtml(item.control_id)}"
          tabindex="0"
        >
          <td>
            <div class="cert-stack">
              <strong>
                ${escapeHtml(item.controller_name || "Contrôleur")}
              </strong>
              <small>
                Début ${escapeHtml(formatDate(item.started_on))}
              </small>
            </div>
          </td>

          <td>
            <div class="cert-stack">
              <strong>
                ${escapeHtml(item.entreprise_name || "Entreprise non liée")}
              </strong>
              <small>
                ${escapeHtml(item.entreprise_identifiant || "—")}
              </small>
            </div>
          </td>

          <td>
            <div class="cert-stack">
              <strong>
                ${escapeHtml(verificationOpinionLabel(item.verification_opinion))}
              </strong>
              <small>
                Risque ${escapeHtml(item.verification_risk || "—")}
                · ${escapeHtml(item.mission_code || "Mission")}
              </small>
            </div>
          </td>

          <td>
            <div class="cert-stack">
              <strong>
                ${escapeHtml(item.grid_code || item.grid_label || "FUCCS")}
              </strong>
              <small>
                v${escapeHtml(item.grid_version || "—")}
                · ${escapeHtml(criteria)} critère(s)
              </small>
            </div>
          </td>

          <td>
            <div class="fuccs-progress-cell">
              <div>
                <span style="width:${progress}%"></span>
              </div>
              <small>
                ${escapeHtml(notes)} / ${escapeHtml(criteria)}
                · ${progress} %
              </small>
            </div>
          </td>

          <td>
            <div class="cert-stack">
              <strong>
                ${escapeHtml(item.raw_score ?? "0")}
                /
                ${escapeHtml(item.maximum_score ?? "0")}
              </strong>
              <small>
                ${escapeHtml(item.rate || "0.00")} %
              </small>
            </div>
          </td>

          <td>
            <span
              class="cert-status ${statusClass(item.control_status)}"
            >
              <i></i>
              ${escapeHtml(item.control_status || "Non renseigné")}
            </span>
          </td>

          <td>
            <button
              class="more-button"
              type="button"
              aria-label="Ouvrir"
            >
              ${icon("chevron-right")}
            </button>
          </td>
        </tr>
      `;
    }).join("");

    tbody
      .querySelectorAll("[data-control-id]")
      .forEach((row) => {
        const open = () => {
          location.hash =
            `#/controle/${row.dataset.controlId}`;
        };

        row.addEventListener("click", open);
        row.addEventListener("keydown", (event) => {
          if (event.key === "Enter") open();
        });
      });

    refreshIcons();
  }

  function renderEligible(payload) {
    const container = $("#fuccsEligible");
    const items = Array.isArray(payload?.items)
      ? payload.items
      : [];

    if (!items.length) {
      container.innerHTML = `
        <div class="priority-empty">
          Aucun dossier de vérification admissible au FUCCS.
        </div>
      `;
      return;
    }

    container.innerHTML = items.map((item) => `
      <article class="cert-doc-row fuccs-eligible-row">
        <span>${icon("folder-check")}</span>

        <div>
          <strong>
            ${escapeHtml(
              item.entreprise_name || "Entreprise non renseignée"
            )}
          </strong>

          <small>
            ${escapeHtml(item.mission_code || "Mission")}
            · ${escapeHtml(item.campaign_code || "—")}
            · ${escapeHtml(item.zone_name || "—")}
            · avis ${escapeHtml(verificationOpinionLabel(item.verification_opinion))}
            · risque ${escapeHtml(item.verification_risk || "—")}
            · clôturée ${escapeHtml(formatDate(item.verification_closed_on))}
          </small>
        </div>

        <div class="fuccs-existing-control">
          ${
            item.controls_count
              ? `
                <strong>
                  ${escapeHtml(item.controls_count)}
                  contrôle(s)
                </strong>
                <small>
                  Dernier : ${escapeHtml(item.latest_control_status || "—")}
                </small>
              `
              : `
                <strong>Aucun contrôle</strong>
                <small>Dossier prêt</small>
              `
          }
        </div>

        ${
          hasPermission("FUCCS.CONTROLER")
          && activeGrid
            ? `
              ${
                item.latest_control_id
                  ? `
                    <a
                      href="#/controle/${escapeHtml(item.latest_control_id)}"
                      class="btn btn-primary app-btn"
                    >
                      ${icon(
                        String(item.latest_control_status || "").toUpperCase()
                          === "FINALISE"
                          ? "eye"
                          : "play"
                      )}
                      ${
                        String(item.latest_control_status || "").toUpperCase()
                          === "FINALISE"
                          ? "Consulter"
                          : "Reprendre"
                      }
                    </a>
                  `
                  : `
                    <button
                      class="btn btn-primary app-btn"
                      type="button"
                      data-start-fuccs="${escapeHtml(item.dossier_id)}"
                    >
                      ${icon("play")}
                      Démarrer
                    </button>
                  `
              }
            `
            : item.latest_control_id
              ? `
                <a
                  href="#/controle/${escapeHtml(item.latest_control_id)}"
                  class="btn btn-outline-secondary app-btn"
                >
                  ${icon("eye")}
                  Consulter
                </a>
              `
              : ""
        }
      </article>
    `).join("");

    container
      .querySelectorAll("[data-start-fuccs]")
      .forEach((button) => {
        button.addEventListener(
          "click",
          (event) => startControl(
            event,
            button.dataset.startFuccs
          )
        );
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
      "/api/v1/fuccs/workspace/filters"
    );

    activeGrid = payload.active_grid || null;

    fillSelect(
      $("#fuccsStatus"),
      "Tous les statuts",
      payload.statuses
    );

    renderGridBanner();
  }

  async function loadRegistry({
    button = null,
    message = "Chargement des contrôles",
  } = {}) {
    hideState();

    const task = async () => {
      const payload = await apiGet(
        `/api/v1/fuccs/workspace/registry?${queryString()}`
      );

      renderRows(payload);
    };

    try {
      if (window.HAUQE_ACTION_LOADER) {
        await window.HAUQE_ACTION_LOADER.run(task, {
          button,
          title: "Contrôle FUCCS",
          message,
          detail: "Lecture des contrôles et scores enregistrés.",
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

  async function loadEligible() {
    try {
      const params = new URLSearchParams({
        limit: "20",
        offset: "0",
      });

      if (filters.search) {
        params.set("search", filters.search);
      }

      const payload = await apiGet(
        `/api/v1/fuccs/workspace/eligible-verifications?${params}`
      );

      renderEligible(payload);
    } catch (error) {
      $("#fuccsEligible").innerHTML = `
        <div class="priority-empty">
          ${escapeHtml(
            error?.message
            || "Impossible de charger les dossiers admissibles."
          )}
        </div>
      `;
    }
  }

  async function startControl(event, dossierId) {
    if (!activeGrid) {
      showState(
        "Aucune grille FUCCS publiée active.",
        { error: true }
      );
      return;
    }

    const task = async () => {
      const control = await apiPost(
        `/api/v1/verifications/${dossierId}/fuccs-controles`,
        {
          grille_fuccs_id: activeGrid.id,
        }
      );

      location.hash =
        `#/controle/${control.id}`;
    };

    try {
      if (window.HAUQE_ACTION_LOADER) {
        await window.HAUQE_ACTION_LOADER.run(task, {
          button: event.currentTarget,
          title: "Nouveau contrôle FUCCS",
          message: "Initialisation du contrôle",
          detail: "La grille publiée active est figée sur ce contrôle.",
        });
      } else {
        await task();
      }
    } catch (error) {
      showState(
        error?.message || "Création impossible.",
        { error: true }
      );
    }
  }

  function bind() {
    $("#fuccsSearch").addEventListener(
      "input",
      (event) => {
        clearTimeout(timer);

        timer = setTimeout(async () => {
          filters.search = event.target.value.trim();
          offset = 0;

          await Promise.all([
            loadRegistry({
              message: "Recherche des contrôles",
            }),
            loadEligible(),
          ]);
        }, 350);
      }
    );

    $("#fuccsStatus").addEventListener(
      "change",
      async (event) => {
        filters.statut = event.target.value;
        offset = 0;

        await loadRegistry({
          message: "Filtrage par statut",
        });
      }
    );

    $("#fuccsSort").addEventListener(
      "change",
      async (event) => {
        filters.sort = event.target.value;
        offset = 0;

        await loadRegistry({
          message: "Application du tri",
        });
      }
    );

    $("#resetFuccs").addEventListener(
      "click",
      async (event) => {
        Object.assign(filters, {
          search: "",
          statut: "",
          sort: "started",
        });

        offset = 0;

        $("#fuccsSearch").value = "";
        $("#fuccsStatus").value = "";
        $("#fuccsSort").value = "started";

        await Promise.all([
          loadRegistry({
            button: event.currentTarget,
            message: "Réinitialisation",
          }),
          loadEligible(),
        ]);
      }
    );

    $("#fuccsPrev").addEventListener(
      "click",
      async (event) => {
        offset = Math.max(0, offset - PAGE_SIZE);

        await loadRegistry({
          button: event.currentTarget,
          message: "Page précédente",
        });
      }
    );

    $("#fuccsNext").addEventListener(
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

    try {
      currentUser = await apiGet("/api/v1/me");

      await loadFilters();

      await Promise.all([
        loadRegistry(),
        loadEligible(),
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
