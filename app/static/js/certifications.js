(function () {
  "use strict";

  const $ = (selector) => document.querySelector(selector);
  const PAGE_SIZE = 25;

  let apiGet;
  let apiBlob;

  let offset = 0;
  let total = 0;
  let timer = null;

  const filters = {
    search: "",
    statut: "",
    norme_id: "",
    organisme_id: "",
    deadline: "",
    verification: "",
    sort: "deadline",
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

  function normalizedStatus(value) {
    return String(value || "").trim().toUpperCase();
  }

  function statusClass(value, days) {
    const status = normalizedStatus(value);

    if (status.includes("SUSPEND")) return "suspended";
    if (days !== null && days < 0) return "expired";
    if (
      status.includes("VERIFIER")
      || status.includes("À VERIFIER")
    ) {
      return "verify";
    }
    if (days !== null && days <= 90) return "watch";
    if (["ACTIF", "ACTIVE", "VALIDE"].includes(status)) return "valid";

    return "verify";
  }

  function showState(message, { error = false } = {}) {
    const state = $("#certApiState");
    state.hidden = false;
    state.className = `dashboard-api-state ${error ? "error" : ""}`.trim();
    state.innerHTML = `
      ${icon(error ? "triangle-alert" : "info")}
      <div>
        <strong>${error ? "Impossible de charger le registre" : "Information"}</strong>
        <span>${escapeHtml(message)}</span>
      </div>
    `;
    refreshIcons();
  }

  function hideState() {
    $("#certApiState").hidden = true;
  }

  function fillSelect(select, allLabel, items, mapper) {
    select.innerHTML = `<option value="">${escapeHtml(allLabel)}</option>`
      + (items || []).map((item) => {
        const mapped = mapper(item);
        return `
          <option value="${escapeHtml(mapped.value)}">
            ${escapeHtml(mapped.label)}
          </option>
        `;
      }).join("");

    select.disabled = false;
  }

  function renderKpis(summary) {
    const data = [
      [
        "green",
        "badge-check",
        "Statut actif",
        summary?.active_status ?? 0,
        "Valeur enregistrée",
      ],
      [
        "blue",
        "shield-check",
        "Authentifiées",
        summary?.verified ?? 0,
        "Authenticité vérifiée",
      ],
      [
        "orange",
        "calendar-clock",
        "≤ 30 jours",
        summary?.expiring_30 ?? 0,
        "Alerte RM-07",
      ],
      [
        "red",
        "badge-x",
        "Expirées",
        summary?.expired ?? 0,
        "Traitement prioritaire",
      ],
      [
        "gray",
        "search-check",
        "À vérifier",
        summary?.to_verify ?? 0,
        `${summary?.renewals_open ?? 0} renouvellement(s) ouvert(s)`,
      ],
    ];

    $("#certKpis").innerHTML = data.map(
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

    $("#certCount").textContent =
      `${total} certification${total > 1 ? "s" : ""}`;

    const start = total ? offset + 1 : 0;
    const end = Math.min(offset + items.length, total);

    $("#certRange").textContent = total
      ? `${start}–${end} sur ${total}`
      : "Aucune donnée enregistrée";

    $("#certPagination").textContent = total
      ? `Affichage ${start} à ${end}`
      : "0 résultat";

    $("#certPrev").disabled = offset <= 0;
    $("#certNextPage").disabled = offset + PAGE_SIZE >= total;

    const tbody = $("#certRows");
    const empty = $("#certEmpty");

    if (!items.length) {
      tbody.innerHTML = "";
      empty.hidden = false;
      refreshIcons();
      return;
    }

    empty.hidden = true;

    tbody.innerHTML = items.map((item) => {
      const days = item.days_remaining;
      let dayText = "Sans échéance";

      if (days !== null && days !== undefined) {
        if (days < 0) {
          dayText = `Expirée depuis ${Math.abs(days)} j`;
        } else if (days === 0) {
          dayText = "Expire aujourd’hui";
        } else {
          dayText = `${days} jour${days > 1 ? "s" : ""}`;
        }
      }

      const standard = [
        item.norme_code,
        item.norme_version ? `v${item.norme_version}` : "",
      ].filter(Boolean).join(" ");

      return `
        <tr data-id="${escapeHtml(item.id)}" tabindex="0">
          <td>
            <div class="cert-main">
              <span class="cert-logo">
                ${escapeHtml((item.norme_code || "CERT").slice(0, 4))}
              </span>
              <div>
                <strong>${escapeHtml(standard || item.norme_name || "Certification")}</strong>
                <small>
                  ${escapeHtml(item.numero_certificat || "Sans numéro")}
                  <br>${escapeHtml(item.identifiant_national)}
                </small>
              </div>
            </div>
          </td>

          <td>
            <div class="cert-stack">
              <strong>${escapeHtml(item.entreprise_name)}</strong>
              <small>Entreprise titulaire</small>
            </div>
          </td>

          <td>
            <div class="cert-stack">
              <strong>${escapeHtml(item.organisme_sigle || item.organisme_name)}</strong>
              <small>${escapeHtml(item.organisme_name)}</small>
            </div>
          </td>

          <td>
            <div class="cert-stack">
              <strong>${escapeHtml(item.portee || "—")}</strong>
              <small>${item.certification_strategique ? "Stratégique" : "Portée enregistrée"}</small>
            </div>
          </td>

          <td>
            <div class="cert-stack">
              <strong>${escapeHtml(formatDate(item.date_expiration))}</strong>
              <small class="${days !== null && days <= 30 ? "text-danger" : ""}">
                ${escapeHtml(dayText)}
              </small>
            </div>
          </td>

          <td>
            <span class="verification ${item.authenticite_verifiee ? "checked" : "pending"}">
              ${icon(item.authenticite_verifiee ? "badge-check" : "clock-3")}
              ${item.authenticite_verifiee ? "Vérifiée" : "En attente"}
            </span>
          </td>

          <td>
            <span class="cert-status ${statusClass(item.statut, days)}">
              <i></i>${escapeHtml(item.statut || "Non renseigné")}
            </span>
          </td>

          <td>
            <button class="more-button" type="button" aria-label="Ouvrir">
              ${icon("chevron-right")}
            </button>
          </td>
        </tr>
      `;
    }).join("");

    tbody.querySelectorAll("tr[data-id]").forEach((row) => {
      const open = () => {
        location.hash = `#/certifications/${row.dataset.id}`;
      };

      row.addEventListener("click", open);
      row.addEventListener("keydown", (event) => {
        if (event.key === "Enter") open();
      });
    });

    refreshIcons();
  }

  function queryString({ paging = true } = {}) {
    const params = new URLSearchParams();

    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.set(key, value);
    });

    if (paging) {
      params.set("limit", String(PAGE_SIZE));
      params.set("offset", String(offset));
    }

    return params.toString();
  }

  async function loadFilters() {
    const payload = await apiGet(
      "/api/v1/certifications/filters"
    );

    fillSelect(
      $("#certStatus"),
      "Tous les statuts",
      payload.statuses,
      (value) => ({ value, label: value })
    );

    fillSelect(
      $("#certStandard"),
      "Tous les référentiels",
      payload.norms,
      (item) => ({ value: item.id, label: item.label })
    );

    fillSelect(
      $("#certBody"),
      "Tous les organismes",
      payload.organisms,
      (item) => ({ value: item.id, label: item.label })
    );
  }

  async function loadRegistry({
    button = null,
    message = "Chargement des certifications",
  } = {}) {
    hideState();

    const task = async () => {
      const payload = await apiGet(
        `/api/v1/certifications/registry?${queryString()}`
      );
      renderRows(payload);
    };

    try {
      if (window.HAUQE_ACTION_LOADER) {
        await window.HAUQE_ACTION_LOADER.run(task, {
          button,
          title: "Registre des certifications",
          message,
          detail: "Lecture des données officielles de la BNEC.",
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
    $("#certSearch").addEventListener("input", (event) => {
      clearTimeout(timer);

      timer = setTimeout(() => {
        filters.search = event.target.value.trim();
        offset = 0;
        loadRegistry({ message: "Recherche des certifications" });
      }, 350);
    });

    [
      ["#certStatus", "statut"],
      ["#certStandard", "norme_id"],
      ["#certBody", "organisme_id"],
      ["#certDeadline", "deadline"],
      ["#certVerification", "verification"],
      ["#certSort", "sort"],
    ].forEach(([selector, key]) => {
      $(selector).addEventListener("change", (event) => {
        filters[key] = event.target.value;
        offset = 0;
        loadRegistry({ message: "Application des filtres" });
      });
    });

    $("#resetCerts").addEventListener("click", async (event) => {
      Object.assign(filters, {
        search: "",
        statut: "",
        norme_id: "",
        organisme_id: "",
        deadline: "",
        verification: "",
        sort: "deadline",
      });

      offset = 0;

      $("#certSearch").value = "";
      $("#certStatus").value = "";
      $("#certStandard").value = "";
      $("#certBody").value = "";
      $("#certDeadline").value = "";
      $("#certVerification").value = "";
      $("#certSort").value = "deadline";

      await loadRegistry({
        button: event.currentTarget,
        message: "Réinitialisation du registre",
      });
    });

    $("#certPrev").addEventListener("click", async (event) => {
      offset = Math.max(0, offset - PAGE_SIZE);

      await loadRegistry({
        button: event.currentTarget,
        message: "Page précédente",
      });
    });

    $("#certNextPage").addEventListener("click", async (event) => {
      offset += PAGE_SIZE;

      await loadRegistry({
        button: event.currentTarget,
        message: "Page suivante",
      });
    });

    $("#certExport").addEventListener("click", async (event) => {
      const motif = window.prompt(
        "Motif de l’export du registre des certifications :"
      );

      if (!motif?.trim()) return;

      const task = async () => {
        const params = new URLSearchParams(
          queryString({ paging: false })
        );
        params.set("motif", motif.trim());

        const blob = await apiBlob(
          `/api/v1/certifications/export?${params.toString()}`
        );

        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");

        link.href = url;
        link.download =
          `hauqe-certifications-${new Date().toISOString().slice(0, 10)}.csv`;

        document.body.appendChild(link);
        link.click();
        link.remove();

        setTimeout(() => URL.revokeObjectURL(url), 1000);
      };

      try {
        if (window.HAUQE_ACTION_LOADER) {
          await window.HAUQE_ACTION_LOADER.run(task, {
            button: event.currentTarget,
            title: "Export des certifications",
            message: "Génération du fichier",
            detail: "Le motif et les filtres sont tracés côté serveur.",
          });
        } else {
          await task();
        }
      } catch (error) {
        showState(
          error?.message || "Export impossible.",
          { error: true }
        );
      }
    });
  }

  async function bootstrap() {
    const api = await import("/static/js/core/api.js");

    apiGet = api.apiGet;
    apiBlob = api.apiBlob;

    bind();

    try {
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
