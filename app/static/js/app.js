(function () {
  "use strict";

  const $ = (selector) => document.querySelector(selector);

  const API = {
    filters: "/api/v1/dashboards/filters",
    definitions: "/api/v1/dashboards/indicator-definitions",
    operational: "/api/v1/dashboards/operational",
    operationalExport: "/api/v1/dashboards/operational/export",
  };

  const METRIC_LAYOUT = [
    {
      key: "enterprises_count",
      icon: "building-2",
      tone: "green",
      route: "entreprises",
    },
    {
      key: "active_certifications_count",
      icon: "badge-check",
      tone: "blue",
      route: "certifications",
    },
    {
      key: "new_certifications",
      icon: "sparkles",
      tone: "green",
      route: "certifications",
    },
    {
      key: "strategic_expiring_90d_enterprises",
      icon: "triangle-alert",
      tone: "orange",
      route: "echeances",
    },
    {
      key: "controls_to_plan",
      icon: "clipboard-check",
      tone: "purple",
      route: "controle",
    },
    {
      key: "active_alerts",
      icon: "bell-ring",
      tone: "red",
      route: "alertes",
    },
  ];

  const STATUS_COLORS = [
    "#178a60",
    "#3c72d9",
    "#dba33a",
    "#c95a55",
    "#7955b6",
    "#5b8d84",
    "#7b8883",
    "#2f9f8a",
  ];

  let apiGet = null;
  let apiBlob = null;
  let ApiError = null;
  let dashboardData = null;
  let definitions = new Map();
  let statusChart = null;
  let activityChart = null;
  let requestSequence = 0;
  let currentActionMenu = null;

  function icon(name) {
    return `<i data-lucide="${name}"></i>`;
  }

  function loader() {
    return window.HAUQE_ACTION_LOADER || null;
  }

  function formatNumber(value) {
    if (value === null || value === undefined || value === "") {
      return "—";
    }

    const number = Number(value);

    if (Number.isNaN(number)) {
      return String(value);
    }

    return new Intl.NumberFormat("fr-FR", {
      maximumFractionDigits: 2,
    }).format(number);
  }

  function formatDate(value, options = {}) {
    if (!value) return "—";

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return String(value);
    }

    return new Intl.DateTimeFormat("fr-FR", {
      day: "2-digit",
      month: "short",
      year: options.year === false ? undefined : "numeric",
      hour: options.time ? "2-digit" : undefined,
      minute: options.time ? "2-digit" : undefined,
    }).format(date);
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function initials(name) {
    const parts = String(name || "")
      .trim()
      .split(/\s+/)
      .filter(Boolean);

    if (!parts.length) return "—";

    return (
      `${parts[0]?.[0] || ""}${parts.at(-1)?.[0] || ""}`
      .toUpperCase()
    );
  }

  function go(route) {
    location.hash = `#/${route}`;
  }

  async function goWithLoader(route, message = "Ouverture") {
    const actionLoader = loader();

    if (!actionLoader) {
      go(route);
      return;
    }

    await actionLoader.run(
      async () => {
        await new Promise((resolve) => setTimeout(resolve, 160));
        go(route);
      },
      {
        title: "Navigation",
        message,
        detail: "Préparation de l'espace demandé.",
        minVisibleMs: 300,
      }
    );
  }

  function showState({
    title,
    message,
    tone = "",
    iconName = "info",
    retry = false,
  }) {
    const state = $("#dashboardApiState");

    if (!state) return;

    state.className = `dashboard-api-state ${tone}`.trim();
    state.hidden = false;
    state.innerHTML = `
      ${icon(iconName)}
      <div>
        <strong>${escapeHtml(title)}</strong>
        <span>${escapeHtml(message)}</span>
      </div>
      ${
        retry
          ? `<button class="btn btn-outline-secondary app-btn" id="dashboardRetry" type="button">
               ${icon("refresh-cw")}Réessayer
             </button>`
          : ""
      }
    `;

    $("#dashboardRetry")?.addEventListener("click", (event) => {
      loadOperationalDashboard({
        button: event.currentTarget,
        message: "Rechargement du tableau de bord",
      });
    });

    refreshIcons();
  }

  function hideState() {
    const state = $("#dashboardApiState");
    if (!state) return;
    state.hidden = true;
    state.innerHTML = "";
    state.className = "dashboard-api-state";
  }

  function refreshIcons() {
    if (window.lucide) {
      window.lucide.createIcons({
        attrs: { "stroke-width": 1.8 },
      });
    }
  }

  function kpiMap() {
    return new Map(
      (dashboardData?.kpis || []).map((item) => [item.key, item])
    );
  }

  function metricDefinition(key, fallback = "") {
    return (
      definitions.get(key)?.description
      || kpiMap().get(key)?.definition
      || fallback
      || ""
    );
  }

  function deltaBadge(kpi) {
    if (kpi?.delta === null || kpi?.delta === undefined) {
      return "";
    }

    const delta = Number(kpi.delta);

    if (Number.isNaN(delta)) return "";

    const tone = delta > 0 ? "up" : delta < 0 ? "down" : "neutral";
    const sign = delta > 0 ? "+" : "";

    return `<b class="${tone}">${sign}${formatNumber(delta)}</b>`;
  }

  function metricSubtitle(kpi, key) {
    const map = kpiMap();

    if (key === "active_alerts") {
      const critical = map.get("critical_alerts")?.value;
      if (critical !== undefined && critical !== null) {
        return `${formatNumber(critical)} alerte(s) critique(s)`;
      }
    }

    if (
      kpi?.previous_value !== null
      && kpi?.previous_value !== undefined
    ) {
      return `Période précédente : ${formatNumber(kpi.previous_value)}`;
    }

    return kpi?.unit || "Donnée calculée par le serveur";
  }

  function renderMetrics() {
    const container = $("#metricsGrid");
    const map = kpiMap();

    if (!container) return;

    container.innerHTML = METRIC_LAYOUT.map((meta) => {
      const kpi = map.get(meta.key) || {
        key: meta.key,
        label: meta.key,
        value: 0,
      };

      const definition = metricDefinition(meta.key);

      return `
        <article
          class="metric-card dashboard-clickable"
          data-metric-route="${escapeHtml(meta.route)}"
          data-tone="${escapeHtml(meta.tone)}"
          tabindex="0"
          role="button"
          aria-label="Ouvrir ${escapeHtml(kpi.label)}"
        >
          <div class="metric-icon ${escapeHtml(meta.tone)}">
            ${icon(meta.icon)}
          </div>

          <div class="metric-copy">
            <span>${escapeHtml(kpi.label)}</span>

            <div class="metric-value">
              <strong>${formatNumber(kpi.value)}</strong>
              ${deltaBadge(kpi)}
            </div>

            <small>${escapeHtml(metricSubtitle(kpi, meta.key))}</small>
          </div>

          ${
            definition
              ? `
                <button
                  class="metric-info"
                  type="button"
                  data-metric-definition="${escapeHtml(meta.key)}"
                  aria-label="Afficher la définition de l’indicateur"
                  title="Afficher la définition"
                >
                  ${icon("info")}
                </button>

                <div
                  class="metric-definition"
                  data-metric-definition-box="${escapeHtml(meta.key)}"
                  hidden
                >
                  ${escapeHtml(definition)}
                </div>
              `
              : ""
          }
        </article>
      `;
    }).join("");

    container
      .querySelectorAll("[data-metric-route]")
      .forEach((card) => {
        const open = async () => {
          await goWithLoader(
            card.dataset.metricRoute,
            "Ouverture du module"
          );
        };

        card.addEventListener("click", (event) => {
          if (event.target.closest(".metric-info")) return;
          open();
        });

        card.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            open();
          }
        });
      });

    container
      .querySelectorAll("[data-metric-definition]")
      .forEach((button) => {
        button.addEventListener("pointerup", (event) => {
          event.preventDefault();
          event.stopPropagation();

          const key = button.dataset.metricDefinition;
          const box = container.querySelector(
            `[data-metric-definition-box="${CSS.escape(key)}"]`
          );

          if (!box) return;

          container
            .querySelectorAll(".metric-definition")
            .forEach((item) => {
              if (item !== box) item.hidden = true;
            });

          box.hidden = !box.hidden;
          button.setAttribute("aria-expanded", String(!box.hidden));
        });
        button.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            button.dispatchEvent(new PointerEvent("pointerup", { bubbles: true }));
          }
        });
      });

    refreshIcons();
  }

  function statusTone(status) {
    const normalized = String(status || "").toUpperCase();

    if (
      normalized.includes("ACTIF")
      || normalized.includes("VALIDE")
      || normalized.includes("VE")
    ) {
      return "success";
    }

    if (
      normalized.includes("EXPIRE")
      || normalized.includes("REJET")
      || normalized.includes("RETIRE")
    ) {
      return "danger";
    }

    if (
      normalized.includes("SUSP")
      || normalized.includes("ATTENTE")
      || normalized.includes("RENOUVEL")
    ) {
      return "warning";
    }

    return "neutral";
  }

  function renderStatusChart() {
    const items = dashboardData?.certification_statuses || [];
    const canvas = $("#statusChart");
    const legend = $("#statusLegend");

    if (statusChart) {
      statusChart.destroy();
      statusChart = null;
    }

    if (!canvas || !legend) return;

    const total = items.reduce(
      (sum, item) => sum + Number(item.value || 0),
      0
    );

    legend.innerHTML = items.length
      ? items.map((item, index) => `
          <div>
            <span>
              <i style="background:${STATUS_COLORS[index % STATUS_COLORS.length]}"></i>
              ${escapeHtml(item.label)}
            </span>
            <strong>${formatNumber(item.value)}</strong>
            <small>
              ${
                item.percentage !== null && item.percentage !== undefined
                  ? `${formatNumber(item.percentage)} %`
                  : ""
              }
            </small>
          </div>
        `).join("")
      : `<div class="priority-empty">Aucun statut à afficher.</div>`;

    if (typeof Chart === "undefined" || !items.length) {
      return;
    }

    Chart.defaults.font.family = "DM Sans, sans-serif";
    Chart.defaults.color = "#667085";

    statusChart = new Chart(canvas, {
      type: "doughnut",
      data: {
        labels: items.map((item) => item.label),
        datasets: [{
          data: items.map((item) => Number(item.value || 0)),
          backgroundColor: items.map(
            (_, index) => STATUS_COLORS[index % STATUS_COLORS.length]
          ),
          borderWidth: 0,
          hoverOffset: 3,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "72%",
        plugins: {
          legend: { display: false },
          tooltip: {
            padding: 12,
            displayColors: true,
          },
        },
      },
      plugins: [{
        id: "dashboardCenterText",
        afterDraw(chart) {
          const { ctx, chartArea } = chart;
          const x = (chartArea.left + chartArea.right) / 2;
          const y = (chartArea.top + chartArea.bottom) / 2;
          const dark = document.documentElement.dataset.theme === "dark";

          ctx.save();
          ctx.textAlign = "center";
          ctx.fillStyle = dark ? "#edf7f3" : "#13251f";
          ctx.font = "800 28px Manrope";
          ctx.fillText(String(total), x, y - 2);
          ctx.fillStyle = dark ? "#a9beb7" : "#7b8883";
          ctx.font = "500 11px DM Sans";
          ctx.fillText("certifications", x, y + 18);
          ctx.restore();
        },
      }],
    });
  }

  function renderDeadlines() {
    const items = dashboardData?.deadline_buckets || [];
    const expiring = dashboardData?.expiring_certifications || [];
    const map = new Map(items.map((item) => [item.key, Number(item.value || 0)]));

    const expired = map.get("EXPIREE") || 0;
    const d30 = map.get("J30") || 0;
    const d90 = map.get("J90") || 0;
    const d180 = map.get("J180") || 0;
    const total = expired + d30 + d90 + d180;
    const within90 = d30 + d90;

    $("#deadline90Total").textContent = formatNumber(within90);

    const levels = [
      ["critical", "Expirés", expired],
      ["critical", "≤ 30 jours", d30],
      ["warning", "31 à 90 jours", d90],
      ["info", "91 à 180 jours", d180],
    ];

    $("#deadlineLevels").innerHTML = levels.map(
      ([tone, label, value]) => `
        <div>
          <span><i class="dot ${tone}"></i>${label}</span>
          <strong>${formatNumber(value)}</strong>
        </div>
      `
    ).join("");

    const ring = $("#deadlineRing");

    if (ring) {
      if (!total) {
        ring.style.background =
          "radial-gradient(circle,#fff 55%,transparent 56%), conic-gradient(#e7eeeb 0 100%)";
      } else {
        const p1 = (expired / total) * 100;
        const p2 = p1 + (d30 / total) * 100;
        const p3 = p2 + (d90 / total) * 100;

        ring.style.background = `
          radial-gradient(circle,#fff 55%,transparent 56%),
          conic-gradient(
            #c95a55 0 ${p1}%,
            #e9873e ${p1}% ${p2}%,
            #dba33a ${p2}% ${p3}%,
            #4b82d3 ${p3}% 100%
          )
        `;
      }
    }

    const list = $("#expiringCertificationList");

    if (!list) {
      refreshIcons();
      return;
    }

    if (!expiring.length) {
      list.innerHTML = `
        <div class="dashboard-empty-state">
          ${icon("calendar-check-2")}
          <strong>Aucun certificat à échéance dans les 180 jours</strong>
          <span>
            Aucune information fictive n'est affichée.
            Les prochaines expirations apparaîtront ici dès qu'elles existent dans la base.
          </span>
        </div>
      `;
      refreshIcons();
      return;
    }

    list.innerHTML = expiring.slice(0, 5).map((row, index) => {
      const days = Number(row.days_remaining ?? 0);
      const tone = days <= 30 ? "critical" : days <= 90 ? "warning" : "";

      return `
        <button
          class="dashboard-expiring-item"
          type="button"
          data-expiring-index="${index}"
        >
          <span class="dashboard-expiring-copy">
            <strong>${escapeHtml(row.enterprise_name || "Entreprise")}</strong>
            <span>
              ${escapeHtml(row.certification_code || "Certification")}
              ${row.norm ? ` · ${escapeHtml(row.norm)}` : ""}
            </span>
            <small>
              Expiration : ${escapeHtml(formatDate(row.expiration_date))}
              ${row.certification_body ? ` · ${escapeHtml(row.certification_body)}` : ""}
            </small>
          </span>

          <span class="dashboard-expiring-days ${tone}">
            ${days < 0 ? "Expiré" : `J-${days}`}
          </span>
        </button>
      `;
    }).join("");

    list
      .querySelectorAll("[data-expiring-index]")
      .forEach((button) => {
        button.addEventListener("click", async () => {
          const row = expiring[Number(button.dataset.expiringIndex)];

          if (!row?.certification_id) {
            await goWithLoader("echeances", "Ouverture des échéances");
            return;
          }

          await goWithLoader(
            `certifications/${row.certification_id}`,
            "Ouverture du certificat"
          );
        });
      });

    refreshIcons();
  }

  function priorityRoute(item) {
    const resourceType = String(item?.resource_type || "")
      .trim()
      .toUpperCase();
    const resourceId = item?.resource_id;

    if (resourceId) {
      if (["CERTIFICATION", "CERTIFICATIONS"].includes(resourceType)) {
        return `certifications/${resourceId}`;
      }

      if (["ENTREPRISE", "ENTREPRISES"].includes(resourceType)) {
        return `entreprises/${resourceId}`;
      }

      if (["ORGANISME", "ORGANISMES"].includes(resourceType)) {
        return `organismes/${resourceId}`;
      }
    }

    if (String(item?.type || "").toUpperCase() === "ALERTE") {
      return "alertes";
    }

    if (String(item?.type || "").toUpperCase() === "ECHEANCE") {
      return "echeances";
    }

    return "dashboard";
  }

  function renderPriorities() {
    const items = dashboardData?.priority_actions || [];
    const container = $("#priorityList");

    $("#priorityCount").textContent = String(items.length);

    if (!container) return;

    if (!items.length) {
      container.innerHTML = `
        <div class="priority-empty">
          Aucune action prioritaire remontée actuellement.
        </div>
      `;
      return;
    }

    container.innerHTML = items.slice(0, 6).map((item, index) => {
      const type = String(item.type || "").toUpperCase();
      const level = Number(item.level || 1);
      const isAlert = type === "ALERTE";

      return `
        <button
          class="priority-item"
          type="button"
          data-priority-index="${index}"
        >
          <span class="priority-icon level-${Math.min(4, Math.max(1, level))}">
            ${icon(isAlert ? "triangle-alert" : "calendar-clock")}
          </span>

          <span class="priority-meta">
            <strong>${escapeHtml(item.title || "Action prioritaire")}</strong>
            <small>
              ${
                item.due_date
                  ? `Échéance : ${escapeHtml(formatDate(item.due_date))}`
                  : isAlert
                    ? `Niveau ${level}`
                    : "À traiter"
              }
            </small>
          </span>

          ${icon("chevron-right")}
        </button>
      `;
    }).join("");

    container
      .querySelectorAll("[data-priority-index]")
      .forEach((button) => {
        button.addEventListener("click", async () => {
          const item = items[Number(button.dataset.priorityIndex)];

          await goWithLoader(
            priorityRoute(item),
            "Ouverture de l'action prioritaire"
          );
        });
      });

    refreshIcons();
  }

  function renderRecent() {
    const rows = dashboardData?.recent_certifications || [];
    const tbody = $("#recentTable");

    if (!tbody) return;

    if (!rows.length) {
      tbody.innerHTML = `
        <tr>
          <td colspan="7">
            <div class="dashboard-table-empty">
              Aucune certification récente à afficher.
            </div>
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = rows.map((row, index) => `
      <tr
        class="dashboard-clickable"
        data-recent="${index}"
        tabindex="0"
      >
        <td>
          <div class="company-cell">
            <span>${escapeHtml(initials(row.enterprise_name))}</span>
            <div>
              <strong>${escapeHtml(row.enterprise_name || "Entreprise")}</strong>
              <small>${escapeHtml(row.norm || "Norme non renseignée")}</small>
            </div>
          </div>
        </td>

        <td>
          <strong>${escapeHtml(row.certification_code || "—")}</strong>
          <small class="d-block text-muted">
            ${escapeHtml(row.norm || "")}
          </small>
        </td>

        <td>${escapeHtml(row.certification_body || "—")}</td>

        <td>
          <strong>${escapeHtml(formatDate(row.expiration_date))}</strong>
        </td>

        <td>
          <span class="status-badge ${statusTone(row.status)}">
            <i></i>${escapeHtml(row.status || "Non renseigné")}
          </span>
        </td>

        <td>
          <span class="recent-updated">
            ${escapeHtml(formatDate(row.updated_at, { time: true }))}
          </span>
        </td>

        <td>
          <button
            class="more-button"
            type="button"
            data-recent-menu="${index}"
            aria-label="Actions"
          >
            ${icon("ellipsis-vertical")}
          </button>
        </td>
      </tr>
    `).join("");

    tbody
      .querySelectorAll("[data-recent]")
      .forEach((rowElement) => {
        const open = async () => {
          const row = rows[Number(rowElement.dataset.recent)];

          if (!row?.certification_id) return;

          await goWithLoader(
            `certifications/${row.certification_id}`,
            "Ouverture du certificat"
          );
        };

        rowElement.addEventListener("click", (event) => {
          if (!event.target.closest("button")) open();
        });

        rowElement.addEventListener("keydown", (event) => {
          if (event.key === "Enter") open();
        });
      });

    tbody
      .querySelectorAll("[data-recent-menu]")
      .forEach((button) => {
        button.addEventListener("click", (event) => {
          event.stopPropagation();

          const row = rows[Number(button.dataset.recentMenu)];

          openActionMenu(button, [
            {
              icon: "eye",
              title: "Ouvrir le certificat",
              subtitle: row.certification_code || "Certification",
              action: () => goWithLoader(
                `certifications/${row.certification_id}`,
                "Ouverture du certificat"
              ),
            },
            {
              icon: "building-2",
              title: "Voir l’entreprise",
              subtitle: row.enterprise_name || "Entreprise",
              action: () => goWithLoader(
                `entreprises/${row.enterprise_id}`,
                "Ouverture de l'entreprise"
              ),
            },
            {
              icon: "calendar-clock",
              title: "Consulter les échéances",
              subtitle: formatDate(row.expiration_date),
              action: () => goWithLoader(
                "echeances",
                "Ouverture des échéances"
              ),
            },
          ]);
        });
      });

    refreshIcons();
  }

  function renderActivityChart() {
    const items = dashboardData?.activity_series || [];
    const canvas = $("#activityChart");

    if (activityChart) {
      activityChart.destroy();
      activityChart = null;
    }

    if (!canvas || typeof Chart === "undefined") {
      return;
    }

    Chart.defaults.font.family = "DM Sans, sans-serif";
    Chart.defaults.color = "#667085";

    activityChart = new Chart(canvas, {
      type: "line",
      data: {
        labels: items.map((item) => item.period),
        datasets: [{
          label: "Certifications",
          data: items.map((item) => Number(item.value || 0)),
          borderColor: "#178a60",
          backgroundColor: "rgba(23,138,96,.09)",
          fill: true,
          tension: .38,
          borderWidth: 2.5,
          pointRadius: 3,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          intersect: false,
          mode: "index",
        },
        scales: {
          x: {
            grid: { display: false },
          },
          y: {
            beginAtZero: true,
            grid: { color: "#edf1ef" },
            border: { display: false },
            ticks: {
              precision: 0,
            },
          },
        },
        plugins: {
          legend: {
            position: "bottom",
            align: "start",
            labels: {
              usePointStyle: true,
              boxWidth: 7,
              padding: 18,
            },
          },
        },
      },
    });
  }

  function renderMeta() {
    const generated = $("#dashboardGeneratedAt");
    const period = $("#dashboardPeriodLabel");
    const infc = $("#dashboardInfcBadge");

    if (generated) {
      generated.innerHTML = `
        ${icon("refresh-cw")}
        Synchronisé : ${escapeHtml(formatDate(
          dashboardData?.generated_at,
          { time: true }
        ))}
      `;
    }

    if (period) {
      period.innerHTML = `
        ${icon("calendar-range")}
        ${escapeHtml(dashboardData?.period?.label || "Période")}
      `;
    }

    if (
      infc
      && dashboardData?.infc_national_average !== null
      && dashboardData?.infc_national_average !== undefined
    ) {
      infc.hidden = false;
      infc.innerHTML = `
        ${icon("gauge")}
        INFC moyen : ${formatNumber(dashboardData.infc_national_average)}
      `;
    } else if (infc) {
      infc.hidden = true;
    }

    const activeAlerts = Number(kpiMap().get("active_alerts")?.value || 0);
    const navAlertBadge = $("#navAlertBadge");

    if (navAlertBadge) {
      navAlertBadge.textContent = String(activeAlerts);
      navAlertBadge.hidden = activeAlerts <= 0;
    }

    refreshIcons();
  }

  function renderAll() {
    hideState();
    renderMeta();
    renderMetrics();
    renderStatusChart();
    renderDeadlines();
    renderPriorities();
    renderRecent();
    renderActivityChart();
    refreshIcons();
  }

  function normalizeOperationalDays(value) {
    const parsed = Number.parseInt(String(value ?? "").trim(), 10);

    // Le backend /dashboards/operational accepte uniquement 1..90 jours.
    // Une ancienne valeur UI comme "Année 2026" ne doit jamais partir
    // telle quelle vers FastAPI.
    if (Number.isInteger(parsed) && parsed >= 1 && parsed <= 90) {
      return parsed;
    }

    console.warn(
      "Période opérationnelle invalide, fallback à 7 jours :",
      value
    );

    return 7;
  }

  function ensureOperationalPeriodFilter() {
    const select = $("#periodFilter");

    if (!select) return;

    const allowed = [
      ["7", "7 derniers jours"],
      ["30", "30 derniers jours"],
      ["60", "60 derniers jours"],
      ["90", "90 derniers jours"],
    ];

    const currentValues = Array.from(select.options).map(
      (option) => option.value
    );

    const valid =
      currentValues.length === allowed.length
      && allowed.every(([value], index) => currentValues[index] === value);

    if (valid) return;

    select.innerHTML = allowed
      .map(
        ([value, label]) =>
          `<option value="${value}">${label}</option>`
      )
      .join("");

    select.value = "7";
  }

  function queryString() {
    const params = new URLSearchParams();

    params.set(
      "days",
      String(
        normalizeOperationalDays(
          $("#periodFilter")?.value
        )
      )
    );

    const pairs = [
      ["zone_id", $("#regionFilter")?.value],
      ["sector", $("#sectorFilter")?.value],
      ["norm_id", $("#normFilter")?.value],
      ["organisme_id", $("#bodyFilter")?.value],
    ];

    pairs.forEach(([key, value]) => {
      if (value) params.set(key, value);
    });

    return params.toString();
  }

  async function loadOperationalDashboard({
    button = null,
    message = "Chargement du tableau de bord",
    initial = false,
  } = {}) {
    const currentRequest = ++requestSequence;
    const actionLoader = loader();

    const task = async () => {
      const payload = await apiGet(
        `${API.operational}?${queryString()}`
      );

      if (currentRequest !== requestSequence) {
        return;
      }

      dashboardData = payload;
      renderAll();
    };

    try {
      if (actionLoader) {
        await actionLoader.run(task, {
          button,
          title: initial
            ? "Tableau de bord"
            : "Actualisation",
          message,
          detail: initial
            ? "Récupération des indicateurs opérationnels."
            : "Application des filtres et actualisation des indicateurs.",
        });
      } else {
        await task();
      }
    } catch (error) {
      if (
        ApiError
        && error instanceof ApiError
        && error.status === 403
      ) {
        showState({
          title: "Accès au tableau de bord limité",
          message:
            "Votre compte ne possède pas la permission DASHBOARDS.OPERATIONNEL.",
          tone: "warning",
          iconName: "shield-alert",
        });
        return;
      }

      showState({
        title: "Impossible de charger les indicateurs",
        message:
          error?.message
          || "Le serveur n'a pas pu retourner le tableau de bord opérationnel.",
        tone: "error",
        iconName: "triangle-alert",
        retry: true,
      });
    }
  }

  function setFilterOptions(select, {
    allLabel,
    items = [],
    mapper,
  }) {
    if (!select) return;

    select.innerHTML = "";

    const allOption = document.createElement("option");
    allOption.value = "";
    allOption.textContent = allLabel;
    select.appendChild(allOption);

    items.forEach((item) => {
      const mapped = mapper(item);
      const option = document.createElement("option");
      option.value = mapped.value;
      option.textContent = mapped.label;
      select.appendChild(option);
    });

    select.disabled = false;
    select.removeAttribute("aria-busy");
  }

  function setFilterUnavailable(select, label) {
    if (!select) return;

    select.innerHTML = `<option value="">${escapeHtml(label)}</option>`;
    select.disabled = true;
    select.removeAttribute("aria-busy");
  }

  function populateFilters(payload) {
    const zones = Array.isArray(payload?.zones) ? payload.zones : [];
    const sectors = Array.isArray(payload?.sectors) ? payload.sectors : [];
    const norms = Array.isArray(payload?.norms) ? payload.norms : [];
    const bodies = Array.isArray(payload?.certification_bodies)
      ? payload.certification_bodies
      : [];

    setFilterOptions($("#regionFilter"), {
      allLabel: "Toutes les régions",
      items: zones,
      mapper: (item) => ({
        value: item.id,
        label: [
          item.name,
          item.type ? `(${item.type})` : "",
        ].filter(Boolean).join(" "),
      }),
    });

    setFilterOptions($("#sectorFilter"), {
      allLabel: "Tous les secteurs",
      items: sectors,
      mapper: (item) => ({
        value: item,
        label: item,
      }),
    });

    setFilterOptions($("#normFilter"), {
      allLabel: "Toutes les normes",
      items: norms,
      mapper: (item) => ({
        value: item.id,
        label: [
          item.code,
          item.version ? `v${item.version}` : "",
          item.name ? `— ${item.name}` : "",
        ].filter(Boolean).join(" "),
      }),
    });

    setFilterOptions($("#bodyFilter"), {
      allLabel: "Tous les organismes",
      items: bodies,
      mapper: (item) => ({
        value: item.id,
        label: [
          item.sigle || item.code,
          item.name,
        ].filter(Boolean).join(" — "),
      }),
    });

    const reset = $("#dashboardResetFilters");
    if (reset) reset.disabled = false;

  }

  async function loadMetadata() {
    const results = await Promise.allSettled([
      apiGet(API.filters),
      apiGet(API.definitions),
    ]);

    if (results[0].status === "fulfilled") {
      populateFilters(results[0].value);
    } else {
      console.warn("Filtres dashboard :", results[0].reason);

      setFilterUnavailable(
        $("#regionFilter"),
        "Régions indisponibles"
      );
      setFilterUnavailable(
        $("#sectorFilter"),
        "Secteurs indisponibles"
      );
      setFilterUnavailable(
        $("#normFilter"),
        "Normes indisponibles"
      );
      setFilterUnavailable(
        $("#bodyFilter"),
        "Organismes indisponibles"
      );

      const reset = $("#dashboardResetFilters");
      if (reset) reset.disabled = true;
    }

    if (results[1].status === "fulfilled") {
      definitions = new Map(
        (results[1].value?.items || []).map(
          (item) => [item.key, item]
        )
      );
    } else {
      console.warn(
        "Définitions indicateurs dashboard :",
        results[1].reason
      );
    }
  }

  async function applyFilters(event) {
    await loadOperationalDashboard({
      button: event?.currentTarget instanceof HTMLButtonElement
        ? event.currentTarget
        : null,
      message: "Application des filtres",
    });
  }

  async function resetFilters(event) {
    const period = $("#periodFilter");
    const region = $("#regionFilter");
    const sector = $("#sectorFilter");
    const norm = $("#normFilter");
    const body = $("#bodyFilter");

    if (period) period.value = "7";
    if (region) region.value = "";
    if (sector) sector.value = "";
    if (norm) norm.value = "";
    if (body) body.value = "";

    await loadOperationalDashboard({
      button: event?.currentTarget || null,
      message: "Réinitialisation des filtres",
    });
  }

  function closeActionMenu() {
    currentActionMenu?.remove();
    currentActionMenu = null;
  }

  function openActionMenu(anchor, items) {
    closeActionMenu();

    const box = document.createElement("div");
    box.id = "dashboardActionMenu";
    box.className = "dashboard-action-menu";

    box.innerHTML = items.map((item, index) => `
      <button type="button" data-menu-action="${index}">
        ${icon(item.icon)}
        <span>
          <strong>${escapeHtml(item.title)}</strong>
          <small>${escapeHtml(item.subtitle || "")}</small>
        </span>
      </button>
    `).join("");

    document.body.appendChild(box);
    currentActionMenu = box;

    const rect = anchor.getBoundingClientRect();

    box.style.top = `${
      Math.min(
        rect.bottom + 7,
        innerHeight - box.offsetHeight - 12
      )
    }px`;

    box.style.left = `${
      Math.max(
        12,
        Math.min(
          rect.right - box.offsetWidth,
          innerWidth - box.offsetWidth - 12
        )
      )
    }px`;

    box
      .querySelectorAll("[data-menu-action]")
      .forEach((button) => {
        button.addEventListener("click", async () => {
          const item = items[
            Number(button.dataset.menuAction)
          ];

          closeActionMenu();
          await item.action();
        });
      });

    refreshIcons();
  }

  async function exportDashboardCsv(event) {
    const actionLoader = loader();

    const task = async () => {
      const blob = await apiBlob(
        `${API.operationalExport}?${queryString()}`
      );

      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");

      link.href = url;
      link.download =
        `hauqe-dashboard-operationnel-${new Date().toISOString().slice(0, 10)}.csv`;

      document.body.appendChild(link);
      link.click();
      link.remove();

      setTimeout(() => URL.revokeObjectURL(url), 1000);
    };

    if (actionLoader) {
      await actionLoader.run(task, {
        button: event.currentTarget,
        title: "Export du tableau de bord",
        message: "Génération du fichier",
        detail:
          "Le serveur prépare l'export avec les filtres actuellement sélectionnés.",
      });
    } else {
      await task();
    }
  }

  async function exportStatusChart() {
    if (!statusChart) return;

    const actionLoader = loader();

    const task = async () => {
      const link = document.createElement("a");
      link.href = statusChart.toBase64Image(
        "image/png",
        1
      );
      link.download = `hauqe-statuts-certifications-${new Date().toISOString().slice(0, 10)}.png`;
      document.body.appendChild(link);
      link.click();
      link.remove();
    };

    if (actionLoader) {
      await actionLoader.run(task, {
        title: "Export du graphique",
        message: "Génération de l'image",
        detail: "Préparation du graphique des statuts.",
      });
    } else {
      await task();
    }
  }

  function bindActions() {
    $("#dashboardExport")?.addEventListener(
      "click",
      exportDashboardCsv
    );

    $("#dashboardNewCollection")?.addEventListener(
      "click",
      async (event) => {
        const actionLoader = loader();

        const task = async () => {
          await new Promise((resolve) => setTimeout(resolve, 160));
          go("collectes/nouveau");
        };

        if (actionLoader) {
          await actionLoader.run(task, {
            button: event.currentTarget,
            title: "Nouvelle collecte",
            message: "Ouverture du formulaire",
            detail: "Préparation de la fiche de collecte.",
          });
        } else {
          await task();
        }
      }
    );

    $("#dashboardResetFilters")?.addEventListener(
      "click",
      resetFilters
    );

    [
      "#periodFilter",
      "#regionFilter",
      "#sectorFilter",
      "#normFilter",
      "#bodyFilter",
    ].forEach((selector) => {
      $(selector)?.addEventListener("change", applyFilters);
    });

    $("#deadlineAllLink")?.addEventListener(
      "click",
      async (event) => {
        event.preventDefault();
        await goWithLoader(
          "echeances",
          "Ouverture des échéances"
        );
      }
    );


    $("#priorityCenterLink")?.addEventListener(
      "click",
      async (event) => {
        event.preventDefault();
        await goWithLoader(
          "alertes",
          "Ouverture du centre des alertes"
        );
      }
    );

    $("#certificationRegisterLink")?.addEventListener(
      "click",
      async (event) => {
        event.preventDefault();
        await goWithLoader(
          "certifications",
          "Ouverture du registre"
        );
      }
    );

    $("#statusChartMenu")?.addEventListener(
      "click",
      (event) => {
        openActionMenu(event.currentTarget, [
          {
            icon: "list",
            title: "Voir le registre",
            subtitle: "Toutes les certifications",
            action: () => goWithLoader(
              "certifications",
              "Ouverture du registre"
            ),
          },
          {
            icon: "download",
            title: "Exporter le graphique",
            subtitle: "Image PNG",
            action: exportStatusChart,
          },
        ]);
      }
    );

    document.addEventListener("click", (event) => {
      if (
        currentActionMenu
        && !event.target.closest(
          "#dashboardActionMenu,#statusChartMenu,[data-recent-menu]"
        )
      ) {
        closeActionMenu();
      }

      if (
        !event.target.closest(
          ".metric-info,.metric-definition"
        )
      ) {
        document
          .querySelectorAll(".metric-definition")
          .forEach((item) => {
            item.hidden = true;
          });
      }
    });

    window.addEventListener("hauqe:theme-change", () => {
      const dark =
        document.documentElement.dataset.theme === "dark";

      if (typeof Chart !== "undefined") {
        Chart.defaults.color = dark
          ? "#a9beb7"
          : "#667085";
      }

      if (activityChart) {
        activityChart.options.scales.y.grid.color = dark
          ? "#294a41"
          : "#edf1ef";
        activityChart.update();
      }

      statusChart?.draw();
    });
  }

  async function bootstrap() {
    try {
      const apiModule = await import(
        "/static/js/core/api.js"
      );

      apiGet = apiModule.apiGet;
      apiBlob = apiModule.apiBlob;
      ApiError = apiModule.ApiError;

      bindActions();
      ensureOperationalPeriodFilter();

      const actionLoader = loader();

      const task = async () => {
        await loadMetadata();

        const payload = await apiGet(
          `${API.operational}?${queryString()}`
        );

        dashboardData = payload;
        renderAll();
      };

      if (actionLoader) {
        await actionLoader.run(task, {
          title: "Tableau de bord",
          message: "Chargement des indicateurs",
          detail:
            "Récupération des filtres, définitions et données opérationnelles.",
          minVisibleMs: 420,
        });
      } else {
        await task();
      }
    } catch (error) {
      if (
        ApiError
        && error instanceof ApiError
        && error.status === 403
      ) {
        showState({
          title: "Accès au tableau de bord limité",
          message:
            "Les permissions Dashboard ne sont pas encore disponibles pour votre compte.",
          tone: "warning",
          iconName: "shield-alert",
        });
        return;
      }

      showState({
        title: "Impossible de charger le tableau de bord",
        message:
          error?.message
          || "Le serveur n'a pas pu retourner les données opérationnelles.",
        tone: "error",
        iconName: "triangle-alert",
        retry: true,
      });
    }
  }

  bootstrap();
})();
