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
  let calendarScale = "month";
  let cursor = new Date();
  cursor.setDate(1);
  let loadSequence = 0;

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

  function calendarTitle(item) {
    const status = String(item.statut || "").toUpperCase();
    if (status === "TERMINEE") {
      return `Exécutée avec motif : ${item.motif_cloture || "motif consigné"}`;
    }
    if (status === "ANNULEE") {
      return `Annulée avec motif : ${item.motif_cloture || "motif consigné"}`;
    }
    return item.titre || item.type_echeance || "Échéance";
  }

  function params() {
    const p = new URLSearchParams({ limit: "300", offset: "0" });

    if (filters.type_echeance) p.set("type_echeance", filters.type_echeance);
    if (filters.statut) p.set("statut", filters.statut);

    const now = new Date();

    if (filters.range === "month") {
      let start = new Date(cursor.getFullYear(), cursor.getMonth(), 1);
      let end = new Date(cursor.getFullYear(), cursor.getMonth() + 1, 0);
      if (view === "macro" && calendarScale === "year") {
        start = new Date(cursor.getFullYear(), 0, 1);
        end = new Date(cursor.getFullYear(), 11, 31);
      } else if (view === "macro" && calendarScale === "decade") {
        const decade = Math.floor(cursor.getFullYear() / 10) * 10;
        start = new Date(decade, 0, 1);
        end = new Date(decade + 9, 11, 31);
      }
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

  function renderMonthCalendar() {
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
        <div class="calendar-day ${iso(new Date()) === key ? "today" : ""}" data-date="${key}">
          <span class="calendar-day-number">${day}</span>
          <div class="calendar-day-events">
            ${dayItems.slice(0, 3).map((item) => `
              <button class="deadline-calendar-event ${urgency(item)}" type="button" data-deadline="${e(item.id)}">
                <i></i><span>${e(calendarTitle(item))}</span>
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

  function renderYearCalendar() {
    const year = cursor.getFullYear();
    $("#monthTitle").textContent = `Année ${year}`;
    $("#calendarGrid").innerHTML = Array.from({ length: 12 }, (_, month) => {
      const monthItems = items.filter((item) => {
        if (!item.date_echeance) return false;
        const value = new Date(`${item.date_echeance}T00:00:00`);
        return value.getFullYear() === year && value.getMonth() === month;
      });
      const urgent = monthItems.filter((item) => {
        const tone = urgency(item);
        return ["expired", "critical", "warning"].includes(tone);
      }).length;
      return `
        <button class="calendar-period-card month-period-card" type="button" data-calendar-month="${month}">
          <span>${new Intl.DateTimeFormat("fr-FR", { month: "short" }).format(new Date(year, month, 1))}</span>
          <strong>${monthItems.length}</strong>
          <small>échéance(s)</small>
          <i style="--period-load:${Math.min(monthItems.length, 12)}"></i>
          ${urgent ? `<b>${urgent} prioritaire(s)</b>` : `<b class="quiet">Aucune urgence</b>`}
        </button>
      `;
    }).join("");
    document.querySelectorAll("[data-calendar-month]").forEach((button) => {
      button.onclick = async () => {
        cursor = new Date(year, Number(button.dataset.calendarMonth), 1);
        view = "calendar";
        calendarScale = "month";
        document.querySelectorAll("[data-view]").forEach((item) => {
          item.classList.toggle("active", item.dataset.view === "calendar");
        });
        await load();
      };
    });
  }

  function renderDecadeCalendar() {
    const startYear = Math.floor(cursor.getFullYear() / 10) * 10;
    $("#monthTitle").textContent = `${startYear} – ${startYear + 9}`;
    $("#calendarGrid").innerHTML = Array.from({ length: 10 }, (_, index) => {
      const year = startYear + index;
      const yearItems = items.filter(
        (item) => item.date_echeance?.startsWith(String(year))
      );
      const overdue = yearItems.filter((item) => urgency(item) === "expired").length;
      return `
        <button class="calendar-period-card year-period-card" type="button" data-calendar-year="${year}">
          <span>Année</span>
          <strong>${year}</strong>
          <small>${yearItems.length} échéance(s)</small>
          ${overdue ? `<b>${overdue} en retard</b>` : `<b class="quiet">Cycle suivi</b>`}
        </button>
      `;
    }).join("");
    document.querySelectorAll("[data-calendar-year]").forEach((button) => {
      button.onclick = async () => {
        cursor = new Date(Number(button.dataset.calendarYear), 0, 1);
        calendarScale = "year";
        await load();
      };
    });
  }

  function renderCalendar() {
    $("#calendarGrid").classList.toggle(
      "period-grid",
      view === "macro"
    );
    $(".weekday-row").hidden = view === "macro";
    if (view === "macro" && calendarScale === "decade") {
      renderDecadeCalendar();
    } else if (view === "macro") {
      renderYearCalendar();
    } else {
      renderMonthCalendar();
    }
    $("#calendarZoomControls").hidden = view !== "macro";
    $("#calendarZoomIn").disabled = calendarScale === "month";
    $("#calendarZoomOut").disabled = calendarScale === "decade";
    icons();
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

    $("#calendarView").hidden = !["calendar", "macro"].includes(view);
    $("#calendarView").classList.toggle("macro-view", view === "macro");
    $("#listView").hidden = view !== "list";
  }

  async function load() {
    const sequence = ++loadSequence;
    try {
      const payload = await api.apiGet(
        `/api/v1/veille/workspace/deadlines?${params()}`
      );
      if (sequence !== loadSequence) return;
      items = payload.items || [];
      renderKpis(payload.summary || {});
      render();
    } catch (error) {
      if (sequence !== loadSequence) return;
      state(error?.message || "Chargement impossible.", true);
    }
  }

  async function navigateMonth(delta) {
    if (view === "macro" && calendarScale === "decade") {
      cursor = new Date(cursor.getFullYear() + (delta * 10), 0, 1);
    } else if (view === "macro") {
      cursor = new Date(cursor.getFullYear() + delta, 0, 1);
    } else {
      cursor = new Date(
        cursor.getFullYear(),
        cursor.getMonth() + delta,
        1
      );
    }
    filters.range = "month";
    $("#deadlineRangeFilter").value = "month";
    renderCalendar();
    await load();
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

    const status = String(selected.statut || "PLANIFIEE").toUpperCase();
    const closed = ["TERMINEE","ANNULEE"].includes(status);
    const dueDate = selected.date_echeance
      ? new Date(`${String(selected.date_echeance).slice(0, 10)}T12:00:00`)
      : null;
    const day = dueDate && !Number.isNaN(dueDate.getTime())
      ? new Intl.DateTimeFormat("fr-FR", { day: "2-digit" }).format(dueDate)
      : "—";
    const monthYear = dueDate && !Number.isNaN(dueDate.getTime())
      ? new Intl.DateTimeFormat("fr-FR", { month: "long", year: "numeric" }).format(dueDate)
      : "Date non définie";
    const statusLabel = {
      PLANIFIEE: "Planifiée",
      EN_COURS: "En cours",
      TERMINEE: "Terminée",
      ANNULEE: "Annulée",
      EN_RETARD: "En retard",
    }[status] || status.replaceAll("_", " ");
    const priority = String(selected.priorite || "NORMALE").toUpperCase();
    const priorityLabel = {
      BASSE: "Basse",
      NORMALE: "Normale",
      MOYENNE: "Moyenne",
      HAUTE: "Haute",
      CRITIQUE: "Critique",
    }[priority] || priority.replaceAll("_", " ");
    const dialog = $("#deadlineDetailDialog");
    dialog.dataset.status = status;
    dialog.dataset.priority = priority;

    $("#deadlineDetailTitle").textContent = selected.titre || "Échéance";
    $("#deadlineDetailBody").innerHTML = `
      <section class="deadline-detail-overview">
        <div class="deadline-date-block" aria-label="Date prévue : ${e(dateLabel(selected.date_echeance))}">
          <span>${e(day)}</span>
          <strong>${e(monthYear)}</strong>
        </div>
        <div class="deadline-overview-copy">
          <small>Date prévue</small>
          <strong>${e(dateLabel(selected.date_echeance))}</strong>
          <span class="deadline-resource-line"><i data-lucide="building-2"></i>${e(selected.resource_label || selected.ressource_type || "Ressource non renseignée")}</span>
        </div>
        <span class="deadline-status-pill"><i data-lucide="${closed ? "check-circle-2" : "activity"}"></i>${e(statusLabel)}</span>
      </section>

      <div class="deadline-detail-layout">
        <main class="deadline-detail-main">
          <section class="deadline-description-panel">
            <div class="deadline-section-title"><span><i data-lucide="align-left"></i></span><div><small>Instruction</small><h3>Description de l’échéance</h3></div></div>
            <p>${e(selected.description || "Aucune instruction complémentaire n’a été renseignée pour cette échéance.")}</p>
          </section>
          ${closed ? `<section class="deadline-closure-note"><span><i data-lucide="file-check-2"></i></span><div><small>Décision enregistrée</small><strong>${e(selected.motif_cloture || "Le motif est consigné dans le journal d’audit.")}</strong></div></section>` : ""}
        </main>
        <aside class="deadline-detail-aside">
          <p class="deadline-aside-title">Repères</p>
          <div class="deadline-meta-row"><span><i data-lucide="tags"></i></span><div><small>Type d’échéance</small><strong>${e(selected.type_echeance || "Non renseigné")}</strong></div></div>
          <div class="deadline-meta-row"><span><i data-lucide="flag"></i></span><div><small>Niveau de priorité</small><strong class="deadline-priority-value">${e(priorityLabel)}</strong></div></div>
          <div class="deadline-meta-row"><span><i data-lucide="shield-check"></i></span><div><small>Traçabilité</small><strong>Journalisation active</strong></div></div>
        </aside>
      </div>`;
    $("#deadlineDetailActions").innerHTML = perm("ECHEANCES.GERER") && !closed
      ? `<button class="btn btn-outline-secondary app-btn" type="button" data-action="cancel"><i data-lucide="ban"></i>Annuler l’échéance</button>
         <button class="btn btn-primary app-btn" type="button" data-action="complete"><i data-lucide="circle-check"></i>Terminer l’échéance</button>`
      : `<button class="btn btn-outline-secondary app-btn" type="button" data-close-deadline-detail>Fermer</button>`;
    $("#deadlineDetailDialog").showModal();

    $$("[data-action]").forEach((button) => {
      button.onclick = () => {
        action = button.dataset.action;
        $("#deadlineDetailDialog").close();
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
      await navigateMonth(-1);
    };
    $("#nextMonth").onclick = async () => {
      await navigateMonth(1);
    };
    $("#todayButton").onclick = async () => {
      const today = new Date();
      cursor = new Date(today.getFullYear(), today.getMonth(), 1);
      filters.range = "month";
      $("#deadlineRangeFilter").value = "month";
      renderCalendar();
      await load();
      $("#calendarGrid .calendar-day.today")?.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
        inline: "center",
      });
    };

    $$("[data-view]").forEach((button) => {
      button.onclick = () => {
        view = button.dataset.view;
        if (view === "macro") calendarScale = "year";
        if (view === "calendar") calendarScale = "month";
        $$("[data-view]").forEach((x) => x.classList.toggle("active", x === button));
        load();
      };
    });

    $("#calendarZoomOut").onclick = async () => {
      if (calendarScale === "month") calendarScale = "year";
      else if (calendarScale === "year") calendarScale = "decade";
      view = "macro";
      await load();
    };
    $("#calendarZoomIn").onclick = async () => {
      if (calendarScale === "decade") calendarScale = "year";
      else if (calendarScale === "year") {
        calendarScale = "month";
        view = "calendar";
        $$("[data-view]").forEach((item) => {
          item.classList.toggle("active", item.dataset.view === "calendar");
        });
      }
      await load();
    };

    $$("[data-close-deadline-dialog]").forEach((b) => {
      b.onclick = () => $("#deadlineDialog").close();
    });
    $$("[data-close-deadline-action]").forEach((b) => {
      b.onclick = () => $("#deadlineActionDialog").close();
    });
    document.addEventListener("click", (event) => {
      if (event.target.closest("[data-close-deadline-detail]")) {
        $("#deadlineDetailDialog").close();
      }
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
