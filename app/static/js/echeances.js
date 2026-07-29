(async function () {
  "use strict";

  const api = await import("/static/js/core/api.js");
  const $ = (s) => document.querySelector(s);
  const $$ = (s) => [...document.querySelectorAll(s)];

  let user = null;
  let options = null;
  let items = [];
  let selected = null;
  let action = null;
  let view = "calendar";
  let cursor = new Date();
  cursor.setDate(1);

  const filters = {
    type_echeance: "",
    statut: "",
    range: "month",
  };

  function e(v) {
    return String(v ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function perm(code) {
    return Array.isArray(user?.permissions)
      && user.permissions.includes(code);
  }

  function icons() {
    window.lucide?.createIcons({ attrs: { "stroke-width": 1.8 } });
  }

  function state(message, error = false) {
    const node = $("#deadlineApiState");
    node.hidden = false;
    node.className = `dashboard-api-state ${error ? "error" : ""}`.trim();
    node.innerHTML = `
      <i data-lucide="${error ? "triangle-alert" : "info"}"></i>
      <div><strong>${error ? "Opération impossible" : "Information"}</strong><span>${e(message)}</span></div>
    `;
    icons();
  }

  function iso(date) {
    return date.toISOString().slice(0, 10);
  }

  function dateLabel(value) {
    if (!value) return "—";
    return new Intl.DateTimeFormat("fr-FR", {
      day: "2-digit", month: "short", year: "numeric",
    }).format(new Date(`${value}T00:00:00`));
  }

  function urgency(item) {
    const d = item.jours_restants;
    if (d == null) return "neutral";
    if (d < 0) return "expired";
    if (d <= 30) return "critical";
    if (d <= 90) return "warning";
    if (d <= 180) return "info";
    return "neutral";
  }

  function remaining(item) {
    const d = item.jours_restants;
    if (d == null) return "—";
    if (d < 0) return `${Math.abs(d)} j de retard`;
    if (d === 0) return "Aujourd’hui";
    return `J-${d}`;
  }

  function params() {
    const p = new URLSearchParams({ limit: "300", offset: "0" });

    if (filters.type_echeance) p.set("type_echeance", filters.type_echeance);
    if (filters.statut) p.set("statut", filters.statut);

    const now = new Date();

    if (filters.range === "month") {
      const start = new Date(cursor.getFullYear(), cursor.getMonth(), 1);
      const end = new Date(cursor.getFullYear(), cursor.getMonth() + 1, 0);
      p.set("start_date", iso(start));
      p.set("end_date", iso(end));
    } else if (["30", "90", "180"].includes(filters.range)) {
      const end = new Date(now);
      end.setDate(end.getDate() + Number(filters.range));
      p.set("start_date", iso(now));
      p.set("end_date", iso(end));
    } else if (filters.range === "overdue") {
      p.set("overdue_only", "true");
    }

    return p;
  }

  function renderKpis(s) {
    const cards = [
      ["blue","calendar-clock","Total",s.total,"Toutes les échéances"],
      ["green","activity","Actives",s.active,"Non clôturées"],
      ["red","triangle-alert","En retard",s.overdue,"Date dépassée"],
      ["orange","clock-3","≤ 30 jours",s.due_30,"Priorité temporelle"],
      ["purple","calendar-check-2","Terminées",s.completed,"Historique conservé"],
    ];

    $("#deadlineKpis").innerHTML = cards.map(([tone,icon,label,value,detail]) => `
      <article class="deadline-kpi ${tone}">
        <span><i data-lucide="${icon}"></i></span>
        <div><small>${e(label)}</small><strong>${e(value ?? 0)}</strong><em>${e(detail)}</em></div>
      </article>
    `).join("");
    icons();
  }

  function renderCalendar() {
    const title = new Intl.DateTimeFormat("fr-FR", {
      month: "long", year: "numeric",
    }).format(cursor);
    $("#monthTitle").textContent = title[0].toUpperCase() + title.slice(1);

    const first = new Date(cursor.getFullYear(), cursor.getMonth(), 1);
    const last = new Date(cursor.getFullYear(), cursor.getMonth() + 1, 0);
    const offset = (first.getDay() + 6) % 7;
    const cells = Array.from({ length: offset }, () => `<div class="calendar-day muted"></div>`);

    for (let day = 1; day <= last.getDate(); day += 1) {
      const key = iso(new Date(cursor.getFullYear(), cursor.getMonth(), day));
      const dayItems = items.filter((item) => item.date_echeance === key);

      cells.push(`
        <div class="calendar-day ${iso(new Date()) === key ? "today" : ""}">
          <span class="calendar-day-number">${day}</span>
          <div class="calendar-day-events">
            ${dayItems.slice(0, 3).map((item) => `
              <button class="deadline-calendar-event ${urgency(item)}" type="button" data-deadline="${e(item.id)}">
                <i></i><span>${e(item.titre || item.type_echeance || "Échéance")}</span>
              </button>
            `).join("")}
            ${dayItems.length > 3 ? `<small>+${dayItems.length - 3} autre(s)</small>` : ""}
          </div>
        </div>
      `);
    }

    $("#calendarGrid").innerHTML = cells.join("");

    $$("#calendarGrid [data-deadline]").forEach((button) => {
      button.onclick = () => {
        selected = items.find((x) => String(x.id) === String(button.dataset.deadline));
        showDetail();
      };
    });
  }

  function renderList() {
    $("#deadlineList").innerHTML = items.length
      ? items.map((item) => `
          <article class="deadline-real-row">
            <span class="deadline-date-box ${urgency(item)}">
              <strong>${e(item.date_echeance?.slice(8, 10) || "—")}</strong>
              <small>${e(item.date_echeance ? new Intl.DateTimeFormat("fr-FR",{month:"short"}).format(new Date(`${item.date_echeance}T00:00:00`)) : "")}</small>
            </span>
            <div><strong>${e(item.titre || "Échéance")}</strong><small>${e(item.resource_label || item.ressource_type || "Ressource")} · ${e(item.type_echeance || "—")}</small></div>
            <div class="deadline-row-meta"><strong>${e(remaining(item))}</strong><small>${e(item.responsable_name || "Non affectée")}</small></div>
            <span class="deadline-status-pill">${e(item.statut || "—")}</span>
            <button class="more-button" type="button" data-deadline="${e(item.id)}"><i data-lucide="chevron-right"></i></button>
          </article>
        `).join("")
      : `<div class="priority-empty">Aucune échéance dans la période.</div>`;

    $$("#deadlineList [data-deadline]").forEach((button) => {
      button.onclick = () => {
        selected = items.find((x) => String(x.id) === String(button.dataset.deadline));
        showDetail();
      };
    });
    icons();
  }

  function renderSecondary() {
    const active = items
      .filter((x) => !["TERMINEE","ANNULEE"].includes(String(x.statut || "").toUpperCase()))
      .sort((a,b) => String(a.date_echeance || "").localeCompare(String(b.date_echeance || "")))
      .slice(0, 6);

    $("#upcomingList").innerHTML = active.length
      ? active.map((item) => `
          <button class="upcoming-deadline-row" type="button" data-deadline="${e(item.id)}">
            <span class="${urgency(item)}"><i data-lucide="calendar-clock"></i></span>
            <div><strong>${e(item.titre || "Échéance")}</strong><small>${e(item.resource_label || "Ressource")}</small></div>
            <em>${e(remaining(item))}</em>
          </button>
        `).join("")
      : `<div class="priority-empty">Aucune échéance prioritaire.</div>`;

    $$("#upcomingList [data-deadline]").forEach((button) => {
      button.onclick = () => {
        selected = items.find((x) => String(x.id) === String(button.dataset.deadline));
        showDetail();
      };
    });

    const counts = new Map();
    items
      .filter((x) => !["TERMINEE","ANNULEE"].includes(String(x.statut || "").toUpperCase()))
      .forEach((x) => {
        const name = x.responsable_name || "Non affectée";
        counts.set(name, (counts.get(name) || 0) + 1);
      });

    $("#deadlineWorkload").innerHTML = [...counts.entries()]
      .sort((a,b) => b[1] - a[1])
      .map(([name,count]) => `
        <div class="workload-real-row">
          <span><i data-lucide="user-round"></i></span>
          <div><strong>${e(name)}</strong><small>${count} échéance(s)</small></div>
          <b>${count}</b>
        </div>
      `).join("") || `<div class="priority-empty">Aucune charge visible.</div>`;

    icons();
  }

  function render() {
    renderCalendar();
    renderList();
    renderSecondary();

    $("#calendarView").hidden = view !== "calendar";
    $("#listView").hidden = view !== "list";
  }

  async function load() {
    try {
      const payload = await api.apiGet(
        `/api/v1/veille/workspace/deadlines?${params()}`
      );
      items = payload.items || [];
      renderKpis(payload.summary || {});
      render();
    } catch (error) {
      state(error?.message || "Chargement impossible.", true);
    }
  }

  function fill(node, label, values) {
    node.innerHTML = `<option value="">${e(label)}</option>`
      + (values || []).map((v) => `<option value="${e(v)}">${e(v)}</option>`).join("");
    node.disabled = false;
  }

  async function loadFilters() {
    const data = await api.apiGet("/api/v1/veille/workspace/deadline-filters");
    fill($("#deadlineTypeFilter"), "Tous les types", data.deadline_types);
    fill($("#deadlineStatusFilter"), "Tous les statuts", data.deadline_statuses);
  }

  async function openCreate() {
    try {
      options ||= await api.apiGet("/api/v1/veille/workspace/deadline-options");

      $("#deadlineCertification").innerHTML = options.certifications
        .map((x) => `<option value="${e(x.id)}">${e(x.label)}</option>`).join("");

      $("#deadlineResponsible").innerHTML = `<option value="">Non affectée</option>`
        + options.users.map((x) => `<option value="${e(x.id)}">${e(x.label)}</option>`).join("");

      ["deadlineType","deadlineTitle","deadlineDate","deadlinePriority","deadlineDescription"]
        .forEach((id) => $(`#${id}`).value = "");

      $("#deadlineResponsible").value = "";
      $("#deadlineDialog").showModal();
      icons();
    } catch (error) {
      state(error?.message || "Options indisponibles.", true);
    }
  }

  async function create(event) {
    event.preventDefault();

    try {
      await api.apiPost("/api/v1/echeances", {
        ressource_type: "CERTIFICATION",
        ressource_id: $("#deadlineCertification").value,
        type_echeance: $("#deadlineType").value.trim(),
        titre: $("#deadlineTitle").value.trim(),
        description: $("#deadlineDescription").value.trim() || null,
        date_echeance: $("#deadlineDate").value,
        responsable_id: $("#deadlineResponsible").value || null,
        priorite: $("#deadlinePriority").value.trim() || null,
      });

      $("#deadlineDialog").close();
      await load();
      state("Échéance créée et auditée.");
    } catch (error) {
      state(error?.message || "Création impossible.", true);
    }
  }

  function showDetail() {
    if (!selected) return;

    const closed = ["TERMINEE","ANNULEE"].includes(
      String(selected.statut || "").toUpperCase()
    );

    const node = $("#deadlineApiState");
    node.hidden = false;
    node.className = "dashboard-api-state";
    node.innerHTML = `
      <i data-lucide="calendar-clock"></i>
      <div class="deadline-inline-detail">
        <strong>${e(selected.titre || "Échéance")}</strong>
        <span>${e(selected.resource_label || selected.ressource_type || "Ressource")} · ${e(dateLabel(selected.date_echeance))} · ${e(selected.statut || "—")} · ${e(selected.responsable_name || "Non affectée")}</span>
        ${
          perm("ECHEANCES.GERER") && !closed
            ? `<div class="deadline-detail-actions">
                <button class="btn btn-primary app-btn" type="button" data-action="complete"><i data-lucide="circle-check"></i>Terminer</button>
                <button class="btn btn-outline-secondary app-btn" type="button" data-action="cancel"><i data-lucide="ban"></i>Annuler</button>
              </div>`
            : ""
        }
      </div>
    `;

    $$("[data-action]").forEach((button) => {
      button.onclick = () => {
        action = button.dataset.action;
        $("#deadlineActionTitle").textContent =
          action === "complete" ? "Terminer l’échéance" : "Annuler l’échéance";
        $("#deadlineActionReason").value = "";
        $("#deadlineActionDialog").showModal();
        icons();
      };
    });

    icons();
  }

  async function submitAction(event) {
    event.preventDefault();
    if (!selected || !action) return;

    const endpoint = action === "complete"
      ? `/api/v1/echeances/${selected.id}/complete`
      : `/api/v1/echeances/${selected.id}/cancel`;

    try {
      await api.apiPost(endpoint, {
        motif: $("#deadlineActionReason").value.trim(),
      });

      $("#deadlineActionDialog").close();
      selected = null;
      action = null;
      await load();
      state("Échéance mise à jour.");
    } catch (error) {
      state(error?.message || "Action impossible.", true);
    }
  }

  async function scan() {
    try {
      const result = await api.apiPost("/api/v1/veille/scans/daily", {});
      await load();
      state(`Scan ${result.scan_date} : ${result.deadlines_created} échéance(s), ${result.alerts_created} alerte(s) créées.`);
    } catch (error) {
      state(error?.message || "Scan impossible.", true);
    }
  }

  function bind() {
    $("#newDeadline").hidden = !perm("ECHEANCES.GERER");
    $("#runWatchScanFromDeadlines").hidden = !perm("VEILLE.SCANNER");

    $("#newDeadline").onclick = openCreate;
    $("#runWatchScanFromDeadlines").onclick = scan;
    $("#deadlineForm").onsubmit = create;
    $("#deadlineActionForm").onsubmit = submitAction;

    $("#deadlineTypeFilter").onchange = async (ev) => {
      filters.type_echeance = ev.target.value; await load();
    };
    $("#deadlineStatusFilter").onchange = async (ev) => {
      filters.statut = ev.target.value; await load();
    };
    $("#deadlineRangeFilter").onchange = async (ev) => {
      filters.range = ev.target.value; await load();
    };

    $("#resetDeadlines").onclick = async () => {
      filters.type_echeance = "";
      filters.statut = "";
      filters.range = "month";
      $("#deadlineTypeFilter").value = "";
      $("#deadlineStatusFilter").value = "";
      $("#deadlineRangeFilter").value = "month";
      cursor = new Date(); cursor.setDate(1);
      await load();
    };

    $("#prevMonth").onclick = async () => {
      cursor.setMonth(cursor.getMonth() - 1);
      filters.range = "month";
      $("#deadlineRangeFilter").value = "month";
      await load();
    };
    $("#nextMonth").onclick = async () => {
      cursor.setMonth(cursor.getMonth() + 1);
      filters.range = "month";
      $("#deadlineRangeFilter").value = "month";
      await load();
    };
    $("#todayButton").onclick = async () => {
      cursor = new Date(); cursor.setDate(1);
      filters.range = "month";
      $("#deadlineRangeFilter").value = "month";
      await load();
    };

    $$("[data-view]").forEach((button) => {
      button.onclick = () => {
        view = button.dataset.view;
        $$("[data-view]").forEach((x) => x.classList.toggle("active", x === button));
        render();
      };
    });

    $$("[data-close-deadline-dialog]").forEach((b) => {
      b.onclick = () => $("#deadlineDialog").close();
    });
    $$("[data-close-deadline-action]").forEach((b) => {
      b.onclick = () => $("#deadlineActionDialog").close();
    });
  }

  try {
    user = await api.apiGet("/api/v1/me");
    bind();
    await loadFilters();
    await load();
  } catch (error) {
    state(error?.message || "Erreur de chargement.", true);
  }

  icons();
})();
