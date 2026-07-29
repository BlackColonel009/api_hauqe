(async function () {
  "use strict";

  const api = await import("/static/js/core/api.js");
  const $ = (s) => document.querySelector(s);
  const $$ = (s) => [...document.querySelectorAll(s)];

  let user = null;
  let alerts = [];
  let selected = null;
  let options = null;
  let timer = null;

  const filters = {
    search: "",
    niveau: "",
    type_alerte: "",
    statut: "",
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
    const node = $("#alertApiState");
    node.hidden = false;
    node.className = `dashboard-api-state ${error ? "error" : ""}`.trim();
    node.innerHTML = `
      <i data-lucide="${error ? "triangle-alert" : "info"}"></i>
      <div><strong>${error ? "Opération impossible" : "Information"}</strong><span>${e(message)}</span></div>
    `;
    icons();
  }

  function dateLabel(v) {
    if (!v) return "—";
    return new Intl.DateTimeFormat("fr-FR", {
      day: "2-digit", month: "short", year: "numeric",
    }).format(new Date(`${v}T00:00:00`));
  }

  function levelClass(level) {
    return Number(level) === 4
      ? "critical"
      : Number(level) >= 2
        ? "warning"
        : "info";
  }

  function renderKpis(s) {
    const cards = [
      ["all","bell-ring","Actives",s.active,"À traiter",""],
      ["info","info","Niveau 1",s.level_1,"Information","1"],
      ["warning","eye","Niveau 2",s.level_2,"Surveillance","2"],
      ["warning","clock-alert","Niveau 3",s.level_3,"Urgence","3"],
      ["critical","triangle-alert","Niveau 4",s.level_4,"Critique","4"],
    ];

    $("#alertKpis").innerHTML = cards.map(([tone,icon,label,value,detail,level]) => `
      <button class="alert-stat ${tone}" type="button" data-kpi-level="${level}">
        <span class="alert-stat-icon ${tone}"><i data-lucide="${icon}"></i></span>
        <div><small>${e(label)}</small><strong>${e(value ?? 0)}</strong><em>${e(detail)}</em></div>
      </button>
    `).join("");

    $$("#alertKpis [data-kpi-level]").forEach((button) => {
      button.onclick = async () => {
        filters.niveau = button.dataset.kpiLevel;
        $("#alertLevel").value = filters.niveau;
        await loadAlerts();
      };
    });

    icons();
  }

  function params() {
    const p = new URLSearchParams({ limit: "200", offset: "0" });
    if (filters.niveau) p.set("niveau", filters.niveau);
    if (filters.type_alerte) p.set("type_alerte", filters.type_alerte);
    if (filters.statut) p.set("statut", filters.statut);
    return p;
  }

  function visible() {
    if (!filters.search) return alerts;
    const needle = filters.search.toLowerCase();

    return alerts.filter((x) =>
      [x.titre,x.message,x.resource_label,x.resource_subtitle,x.type_alerte]
        .filter(Boolean).join(" ").toLowerCase().includes(needle)
    );
  }

  function renderList() {
    const rows = visible();
    $("#alertCount").textContent = `${rows.length} alerte${rows.length > 1 ? "s" : ""}`;
    $("#emptyAlerts").hidden = rows.length > 0;

    $("#alertsList").innerHTML = rows.map((item) => `
      <button class="alert-row ${selected?.id === item.id ? "selected" : ""}" type="button" data-alert="${e(item.id)}">
        <span class="row-level-icon ${levelClass(item.niveau)}">
          <i data-lucide="${Number(item.niveau) === 4 ? "triangle-alert" : Number(item.niveau) >= 2 ? "clock-alert" : "info"}"></i>
        </span>
        <div class="alert-row-copy">
          <strong>${e(item.titre || "Alerte")}</strong>
          <span>${e(item.resource_label || item.ressource_type || "Ressource")}</span>
          <small>${e(item.level_label || `Niveau ${item.niveau || "—"}`)} · ${e(dateLabel(item.date_detection))}</small>
        </div>
        <div class="alert-owner">
          <span class="owner-avatar">${e((item.responsable_name || "?").split(/\s+/).slice(0,2).map((p) => p[0] || "").join("").toUpperCase())}</span>
          <span>${e(item.responsable_name || "Non affectée")}</span>
        </div>
        <span class="alert-state">${e(item.statut || "—")}</span>
        <i data-lucide="chevron-right"></i>
      </button>
    `).join("");

    $$("#alertsList [data-alert]").forEach((button) => {
      button.onclick = () => {
        selected = alerts.find((x) => String(x.id) === String(button.dataset.alert));
        renderList();
        renderDetail();
      };
    });

    icons();
  }

  function renderDetail() {
    const container = $("#alertDetail");
    if (!selected) {
      container.innerHTML = `<div class="priority-empty">Sélectionnez une alerte.</div>`;
      return;
    }

    const resolved = String(selected.statut || "").toUpperCase() === "RESOLUE";

    container.innerHTML = `
      <div class="detail-head">
        <div class="detail-head-top">
          <span class="level-pill ${levelClass(selected.niveau)}">
            N${e(selected.niveau || "—")} · ${e(selected.level_label || "Alerte")}
          </span>
        </div>
        <h2>${e(selected.titre || "Alerte")}</h2>
        <p>${e(selected.resource_label || selected.ressource_type || "Ressource")}</p>
      </div>

      <div class="detail-body">
        <section class="detail-section">
          <h3>Informations</h3>
          <div class="detail-grid">
            <div><small>Type</small><strong>${e(selected.type_alerte || "—")}</strong></div>
            <div><small>Statut</small><strong>${e(selected.statut || "—")}</strong></div>
            <div><small>Responsable</small><strong>${e(selected.responsable_name || "Non affectée")}</strong></div>
            <div><small>Détection</small><strong>${e(dateLabel(selected.date_detection))}</strong></div>
          </div>
        </section>

        <section class="detail-section">
          <h3>Message</h3>
          <div class="detail-note">${e(selected.message || "—")}</div>
        </section>

        <section class="detail-section">
          <h3>Traçabilité</h3>
          <div class="detail-grid">
            <div><small>Règle</small><strong>${e(selected.regle_notification || "Aucune")}</strong></div>
            <div><small>Notifications</small><strong>${e(selected.notifications_count || 0)}</strong></div>
            <div><small>Échéance liée</small><strong>${selected.echeance_id ? "Oui" : "Non"}</strong></div>
            <div><small>Résolution</small><strong>${e(dateLabel(selected.date_resolution))}</strong></div>
          </div>
        </section>

        ${selected.resource_route ? `<a class="btn btn-outline-secondary app-btn" href="${e(selected.resource_route)}"><i data-lucide="arrow-up-right"></i>Ouvrir la ressource</a>` : ""}
      </div>

      <div class="detail-actions">
        ${perm("ALERTES.AFFECTER") && !resolved ? `<button class="btn btn-outline-secondary app-btn" id="assignAlert" type="button"><i data-lucide="user-round-plus"></i>Affecter</button>` : ""}
        ${perm("NOTIFICATIONS.CREER") && !resolved ? `<button class="btn btn-outline-secondary app-btn" id="notifyAlert" type="button"><i data-lucide="send"></i>Notifier</button>` : ""}
        ${perm("ALERTES.RESOUDRE") && !resolved ? `<button class="btn btn-primary app-btn" id="resolveAlert" type="button"><i data-lucide="circle-check"></i>Résoudre</button>` : ""}
      </div>
    `;

    $("#assignAlert")?.addEventListener("click", openAssign);
    $("#notifyAlert")?.addEventListener("click", openNotify);
    $("#resolveAlert")?.addEventListener("click", () => {
      $("#alertResolution").value = "";
      $("#closeAlertAfterResolution").checked = true;
      $("#resolveAlertDialog").showModal();
      icons();
    });

    icons();
  }

  async function loadAlerts() {
    try {
      const payload = await api.apiGet(`/api/v1/veille/workspace/alerts?${params()}`);
      alerts = payload.items || [];
      renderKpis(payload.summary || {});

      if (selected && !alerts.some((x) => x.id === selected.id)) selected = null;

      renderList();
      renderDetail();
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
    const data = await api.apiGet("/api/v1/veille/workspace/alert-filters");
    fill($("#alertType"), "Tous les types", data.alert_types);
    fill($("#alertStatus"), "Tous les statuts", data.alert_statuses);
  }

  async function ensureOptions() {
    if (!options) {
      options = await api.apiGet("/api/v1/veille/workspace/alert-options");
    }
    return options;
  }

  function userOptions(selectedId = "") {
    return (options?.users || []).map((x) => `
      <option value="${e(x.id)}" ${String(x.id) === String(selectedId) ? "selected" : ""}>
        ${e(x.label)}
      </option>
    `).join("");
  }

  async function openAssign() {
    try {
      await ensureOptions();
      $("#assignAlertResponsible").innerHTML = userOptions(selected?.responsable_id);
      $("#assignAlertComment").value = "";
      $("#assignAlertDialog").showModal();
      icons();
    } catch (error) {
      state(error?.message || "Responsables indisponibles.", true);
    }
  }

  async function assign(event) {
    event.preventDefault();
    if (!selected) return;

    try {
      await api.apiPost(`/api/v1/alertes/${selected.id}/assign`, {
        responsable_id: $("#assignAlertResponsible").value,
        commentaire: $("#assignAlertComment").value.trim() || null,
      });
      $("#assignAlertDialog").close();
      await loadAlerts();
      state("Alerte affectée.");
    } catch (error) {
      state(error?.message || "Affectation impossible.", true);
    }
  }

  async function resolve(event) {
    event.preventDefault();
    if (!selected) return;

    try {
      await api.apiPost(`/api/v1/alertes/${selected.id}/resolve`, {
        resolution: $("#alertResolution").value.trim(),
        cloturer: $("#closeAlertAfterResolution").checked,
      });
      $("#resolveAlertDialog").close();
      selected = null;
      await loadAlerts();
      state("Résolution enregistrée.");
    } catch (error) {
      state(error?.message || "Résolution impossible.", true);
    }
  }

  function recipientMode() {
    const email = $("#alertNotificationChannel").value === "EMAIL";
    $("#internalRecipientField").hidden = email;
    $("#externalRecipientField").hidden = !email;
    $("#alertNotificationUser").required = !email;
    $("#alertNotificationEmail").required = email;
  }

  async function openNotify() {
    try {
      await ensureOptions();

      $("#alertNotificationUser").innerHTML = userOptions();
      $("#alertNotificationChannel").value = "IN_APP";
      $("#alertNotificationSubject").value = selected?.titre || "";
      $("#alertNotificationContent").value = selected?.message || "";
      $("#alertNotificationEmail").value = "";
      recipientMode();
      $("#notifyAlertDialog").showModal();
      icons();
    } catch (error) {
      state(error?.message || "Options de notification indisponibles.", true);
    }
  }

  async function notify(event) {
    event.preventDefault();
    if (!selected) return;

    const channel = $("#alertNotificationChannel").value;
    const recipient = channel === "EMAIL"
      ? {
          destinataire_utilisateur_id: null,
          adresse_externe: $("#alertNotificationEmail").value.trim(),
          canal: channel,
        }
      : {
          destinataire_utilisateur_id: $("#alertNotificationUser").value,
          adresse_externe: null,
          canal: channel,
        };

    try {
      const rows = await api.apiPost(`/api/v1/alertes/${selected.id}/notifications`, {
        objet: $("#alertNotificationSubject").value.trim(),
        contenu: $("#alertNotificationContent").value.trim(),
        destinataires: [recipient],
      });

      $("#notifyAlertDialog").close();
      await loadAlerts();
      state(`${rows.length} notification(s) créée(s).`);
    } catch (error) {
      state(error?.message || "Notification impossible.", true);
    }
  }

  async function openSpecial() {
    try {
      await ensureOptions();

      $("#specialAlertCertification").innerHTML = options.certifications
        .map((x) => `<option value="${e(x.id)}">${e(x.label)}</option>`).join("");

      $("#specialAlertResponsible").innerHTML = `<option value="">Non affectée</option>`
        + userOptions();

      $("#specialAlertType").value = "";
      $("#specialAlertLevel").value = "2";
      $("#specialAlertResponsible").value = "";
      $("#specialAlertTitle").value = "";
      $("#specialAlertMessage").value = "";
      $("#specialAlertRule").value = "";

      $("#specialAlertDialog").showModal();
      icons();
    } catch (error) {
      state(error?.message || "Options indisponibles.", true);
    }
  }

  async function createSpecial(event) {
    event.preventDefault();

    try {
      await api.apiPost("/api/v1/alertes", {
        echeance_id: null,
        type_alerte: $("#specialAlertType").value.trim(),
        niveau: Number($("#specialAlertLevel").value),
        titre: $("#specialAlertTitle").value.trim(),
        message: $("#specialAlertMessage").value.trim(),
        ressource_type: "CERTIFICATION",
        ressource_id: $("#specialAlertCertification").value,
        responsable_id: $("#specialAlertResponsible").value || null,
        regle_notification: $("#specialAlertRule").value.trim() || null,
      });

      $("#specialAlertDialog").close();
      await loadAlerts();
      state("Alerte spéciale créée.");
    } catch (error) {
      state(error?.message || "Création impossible.", true);
    }
  }

  function notificationTime(v) {
    if (!v) return "—";
    const d = new Date(v);
    if (Number.isNaN(d.getTime())) return String(v);
    return new Intl.DateTimeFormat("fr-FR", {
      dateStyle: "short", timeStyle: "short",
    }).format(d);
  }

  async function loadNotifications() {
    const container = $("#notificationCenterList");

    try {
      const payload = await api.apiGet("/api/v1/notifications?limit=100&offset=0");
      $("#notificationUnreadBadge").textContent = String(payload.unread_count || 0);

      const items = payload.items || [];
      container.innerHTML = items.length
        ? items.map((item) => `
            <article class="notification-center-row ${item.date_lecture ? "" : "unread"}">
              <span><i data-lucide="${item.canal === "EMAIL" ? "mail" : "bell-ring"}"></i></span>
              <div>
                <strong>${e(item.objet || "Notification")}</strong>
                <p>${e(item.contenu || "")}</p>
                <small>${e(item.canal || "—")} · ${e(notificationTime(item.created_at))} · ${e(item.statut || "—")}</small>
              </div>
              ${!item.date_lecture ? `<button class="btn btn-outline-secondary app-btn" type="button" data-read="${e(item.id)}">Marquer lue</button>` : ""}
            </article>
          `).join("")
        : `<div class="priority-empty">Aucune notification.</div>`;

      container.querySelectorAll("[data-read]").forEach((button) => {
        button.onclick = async () => {
          try {
            await api.apiPost(`/api/v1/notifications/${button.dataset.read}/read`, {});
            await loadNotifications();
          } catch (error) {
            state(error?.message || "Lecture impossible.", true);
          }
        };
      });

      icons();
    } catch (error) {
      container.innerHTML = `<div class="priority-empty">${e(error?.message || "Notifications indisponibles.")}</div>`;
    }
  }

  function switchTab(name) {
    $$("[data-alert-tab]").forEach((button) => {
      button.classList.toggle("active", button.dataset.alertTab === name);
    });
    $("#alertsTab").hidden = name !== "alerts";
    $("#notificationsTab").hidden = name !== "notifications";
    if (name === "notifications") loadNotifications();
  }

  function bind() {
    $("#newSpecialAlert").hidden = !perm("ALERTES.CREER");
    $("#newSpecialAlert").onclick = openSpecial;

    $("#alertSearch").oninput = (event) => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        filters.search = event.target.value.trim();
        renderList();
      }, 250);
    };

    $("#alertLevel").onchange = async (event) => {
      filters.niveau = event.target.value; await loadAlerts();
    };
    $("#alertType").onchange = async (event) => {
      filters.type_alerte = event.target.value; await loadAlerts();
    };
    $("#alertStatus").onchange = async (event) => {
      filters.statut = event.target.value; await loadAlerts();
    };

    $("#resetAlerts").onclick = async () => {
      Object.assign(filters, { search:"", niveau:"", type_alerte:"", statut:"" });
      $("#alertSearch").value = "";
      $("#alertLevel").value = "";
      $("#alertType").value = "";
      $("#alertStatus").value = "";
      await loadAlerts();
    };

    $("#assignAlertForm").onsubmit = assign;
    $("#resolveAlertForm").onsubmit = resolve;
    $("#notifyAlertForm").onsubmit = notify;
    $("#specialAlertForm").onsubmit = createSpecial;

    $("#alertNotificationChannel").onchange = recipientMode;

    $("#markAllNotificationsRead").onclick = async () => {
      try {
        await api.apiPost("/api/v1/notifications/read-all", {});
        await loadNotifications();
      } catch (error) {
        state(error?.message || "Action impossible.", true);
      }
    };

    $$("[data-alert-tab]").forEach((button) => {
      button.onclick = () => switchTab(button.dataset.alertTab);
    });

    $$("[data-close-alert-dialog]").forEach((button) => {
      button.onclick = () => document.getElementById(
        button.dataset.closeAlertDialog
      )?.close();
    });
  }

  try {
    user = await api.apiGet("/api/v1/me");
    bind();
    await loadFilters();
    await Promise.all([loadAlerts(), loadNotifications()]);
  } catch (error) {
    state(error?.message || "Erreur de chargement.", true);
  }

  icons();
})();
