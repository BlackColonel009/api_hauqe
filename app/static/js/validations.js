(function () {
  "use strict";

  const $ = (selector) => document.querySelector(selector);
  const PAGE_SIZE = 25;

  let apiGet;
  let offset = 0;
  let total = 0;
  let timer = null;

  const filters = {
    search: "",
    stage: "",
    decision: "",
  };

  const stageLabels = {
    READY_N1: "Revue N1 à prononcer",
    N1_REVIEW: "N1 à réexaminer",
    READY_N2: "Validation N2 à prononcer",
    N2_REVIEW: "N2 à réexaminer",
    CORRECTION_PENDING: "Correction en attente",
    COMPLETE: "Validation N2 favorable",
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

  function showState(message, { error = false } = {}) {
    const node = $("#validationApiState");
    node.hidden = false;
    node.className =
      `dashboard-api-state ${error ? "error" : ""}`.trim();

    node.innerHTML = `
      ${icon(error ? "triangle-alert" : "info")}
      <div>
        <strong>
          ${error ? "Impossible de charger les validations" : "Information"}
        </strong>
        <span>${escapeHtml(message)}</span>
      </div>
    `;

    refreshIcons();
  }

  function hideState() {
    $("#validationApiState").hidden = true;
  }

  function fillSelect(node, allLabel, values) {
    node.innerHTML =
      `<option value="">${escapeHtml(allLabel)}</option>`
      + (values || []).map((value) => `
        <option value="${escapeHtml(value)}">
          ${escapeHtml(stageLabels[value] || value)}
        </option>
      `).join("");

    node.disabled = false;
  }

  function decisionClass(value) {
    const decision = String(value || "").toUpperCase();

    if (decision === "VALIDE") return "validated";
    if (decision === "VALIDE_SOUS_RESERVE") return "reservation";
    if (decision === "AJOURNE") return "correction";
    if (decision === "REJETE") return "rejected";

    return "pending";
  }

  function levelCell(level) {
    if (!level?.validation_id) {
      return `
        <span class="validation-level pending">
          <i data-lucide="circle-dashed"></i>
          Non prononcé
        </span>
      `;
    }

    return `
      <div class="validation-level-stack">
        <span class="validation-level ${decisionClass(level.decision)}">
          ${escapeHtml(level.decision || "—")}
        </span>

        <small>
          ${escapeHtml(level.validator_name || "Validateur")}
          ${
            level.reserves
              ? ` · réserve`
              : ""
          }
        </small>
      </div>
    `;
  }

  function renderKpis(summary) {
    const cards = [
      [
        "blue",
        "clipboard-check",
        "Dossiers",
        summary?.total ?? 0,
        "FUCCS finalisé",
      ],
      [
        "orange",
        "badge-1",
        "Niveau 1",
        summary?.ready_n1 ?? 0,
        "À prononcer",
      ],
      [
        "purple",
        "badge-2",
        "Niveau 2",
        summary?.ready_n2 ?? 0,
        "Après N1 favorable",
      ],
      [
        "red",
        "undo-2",
        "Corrections",
        summary?.correction_pending ?? 0,
        "En attente de resoumission",
      ],
      [
        "green",
        "shield-check",
        "N2 favorables",
        summary?.complete ?? 0,
        "Éligibles à la suite",
      ],
    ];

    $("#validationKpis").innerHTML = cards.map(
      ([tone, iconName, label, value, detail]) => `
        <article class="validation-kpi ${tone}">
          <span>${icon(iconName)}</span>
          <div>
            <small>${escapeHtml(label)}</small>
            <strong>${escapeHtml(value)}</strong>
            <em>${escapeHtml(detail)}</em>
          </div>
        </article>
      `
    ).join("");

    const badge = document.querySelector(
      '[data-route="validations"] .nav-badge'
    );

    if (badge) {
      const pending =
        Number(summary?.ready_n1 || 0)
        + Number(summary?.ready_n2 || 0)
        + Number(summary?.correction_pending || 0);

      badge.textContent = String(pending);
      badge.hidden = pending === 0;
    }

    refreshIcons();
  }

  function renderRows(payload) {
    total = Number(payload?.total || 0);
    const items = Array.isArray(payload?.items)
      ? payload.items
      : [];

    renderKpis(payload?.summary || {});

    $("#validationCount").textContent =
      `${total} dossier${total > 1 ? "s" : ""}`;

    const start = total ? offset + 1 : 0;
    const end = Math.min(offset + items.length, total);

    $("#validationRange").textContent = total
      ? `${start}–${end} sur ${total}`
      : "Aucun dossier";

    $("#validationPagination").textContent = total
      ? `Affichage ${start} à ${end}`
      : "0 résultat";

    $("#validationPrev").disabled = offset <= 0;
    $("#validationNext").disabled =
      offset + PAGE_SIZE >= total;

    const tbody = $("#validationRows");
    const empty = $("#validationEmpty");

    if (!items.length) {
      tbody.innerHTML = "";
      empty.hidden = false;
      refreshIcons();
      return;
    }

    empty.hidden = true;

    tbody.innerHTML = items.map((item) => `
      <tr
        data-fiche-id="${escapeHtml(item.fiche_id)}"
        tabindex="0"
      >
        <td>
          <div class="validation-id">
            <strong>
              ${escapeHtml(
                item.entreprise_name
                || "Entreprise non renseignée"
              )}
            </strong>

            <small>
              ${escapeHtml(item.entreprise_identifiant || "—")}
              · ${escapeHtml(item.mission_code || "Mission")}
              · ${escapeHtml(item.zone_name || "—")}
            </small>
          </div>
        </td>

        <td>
          <div class="validation-fuccs-score">
            <strong>
              ${escapeHtml(item.control_score || "0")}
              /
              ${escapeHtml(item.control_maximum || "0")}
            </strong>

            <small>
              ${escapeHtml(item.control_rate || "0.00")} %
              · ${escapeHtml(item.controller_name || "Contrôleur")}
            </small>
          </div>
        </td>

        <td>${levelCell(item.level_1)}</td>
        <td>${levelCell(item.level_2)}</td>

        <td>
          ${
            item.pending_corrections_count
              ? `
                <span class="anomaly-count">
                  ${icon("undo-2")}
                  ${escapeHtml(item.pending_corrections_count)}
                  en attente
                </span>
              `
              : `
                <span class="validation-no-correction">
                  ${icon("circle-check")}
                  Aucune
                </span>
              `
          }
        </td>

        <td>
          <span class="validation-stage ${escapeHtml(item.stage.toLowerCase())}">
            ${escapeHtml(stageLabels[item.stage] || item.stage)}
          </span>
        </td>

        <td>
          <button
            class="mission-action"
            type="button"
            aria-label="Ouvrir"
          >
            ${icon("chevron-right")}
          </button>
        </td>
      </tr>
    `).join("");

    tbody
      .querySelectorAll("[data-fiche-id]")
      .forEach((row) => {
        const open = () => {
          location.hash =
            `#/validations/${row.dataset.ficheId}`;
        };

        row.addEventListener("click", open);

        row.addEventListener(
          "keydown",
          (event) => {
            if (event.key === "Enter") open();
          }
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
      "/api/v1/validations/workspace/filters"
    );

    fillSelect(
      $("#validationStage"),
      "Toutes les étapes",
      payload.stages
    );

    fillSelect(
      $("#validationDecision"),
      "Toutes les décisions",
      payload.decisions
    );
  }

  async function loadRegistry({
    button = null,
    message = "Chargement des validations",
  } = {}) {
    hideState();

    const task = async () => {
      const payload = await apiGet(
        `/api/v1/validations/workspace/registry?${queryString()}`
      );

      renderRows(payload);
    };

    try {
      if (window.HAUQE_ACTION_LOADER) {
        await window.HAUQE_ACTION_LOADER.run(task, {
          button,
          title: "Validation hiérarchisée",
          message,
          detail: "Lecture des contrôles FUCCS finalisés et décisions N1/N2.",
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

  function setStage(value) {
    filters.stage = value;
    $("#validationStage").value = value;

    document
      .querySelectorAll("[data-stage-tab]")
      .forEach((button) => {
        button.classList.toggle(
          "active",
          button.dataset.stageTab === value
        );
      });
  }

  function bind() {
    $("#validationSearch").addEventListener(
      "input",
      (event) => {
        clearTimeout(timer);

        timer = setTimeout(() => {
          filters.search =
            event.target.value.trim();

          offset = 0;

          loadRegistry({
            message: "Recherche des dossiers",
          });
        }, 350);
      }
    );

    $("#validationStage").addEventListener(
      "change",
      async (event) => {
        setStage(event.target.value);
        offset = 0;

        await loadRegistry({
          message: "Filtrage par étape",
        });
      }
    );

    $("#validationDecision").addEventListener(
      "change",
      async (event) => {
        filters.decision = event.target.value;
        offset = 0;

        await loadRegistry({
          message: "Filtrage par décision",
        });
      }
    );

    document
      .querySelectorAll("[data-stage-tab]")
      .forEach((button) => {
        button.addEventListener(
          "click",
          async () => {
            setStage(button.dataset.stageTab);
            offset = 0;

            await loadRegistry({
              message: "Changement de file",
            });
          }
        );
      });

    $("#resetValidations").addEventListener(
      "click",
      async (event) => {
        Object.assign(filters, {
          search: "",
          stage: "",
          decision: "",
        });

        offset = 0;

        $("#validationSearch").value = "";
        $("#validationDecision").value = "";

        setStage("");

        await loadRegistry({
          button: event.currentTarget,
          message: "Réinitialisation",
        });
      }
    );

    $("#validationPrev").addEventListener(
      "click",
      async (event) => {
        offset = Math.max(0, offset - PAGE_SIZE);

        await loadRegistry({
          button: event.currentTarget,
          message: "Page précédente",
        });
      }
    );

    $("#validationNext").addEventListener(
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
