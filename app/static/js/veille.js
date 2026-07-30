(async function () {
  "use strict";

  const api = await import("/static/js/core/api.js");
  const $ = (s) => document.querySelector(s);
  const $$ = (s) => [...document.querySelectorAll(s)];

  let user = null;
  let cases = [];
  let selected = null;
  let selectedFollowup = null;
  let selectedReport = null;
  let options = null;
  let timer = null;

  const filters = {
    search: "",
    statut: "",
    priorite: "",
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
    const node = $("#watchApiState");
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
    const d = new Date(v);
    if (Number.isNaN(d.getTime())) return String(v);

    return new Intl.DateTimeFormat("fr-FR", {
      dateStyle: "medium",
      ...(String(v).includes("T") ? { timeStyle: "short" } : {}),
    }).format(d);
  }

  function renderDashboard(data) {
    const cards = [
      ["green","folder-open","Dossiers ouverts",data.open_watch_cases,"File de veille"],
      ["red","calendar-x-2","Échéances en retard",data.overdue_deadlines,"À traiter"],
      ["orange","bell-ring","Alertes actives",data.active_alerts,`${data.critical_alerts} critique(s)`],
      ["purple","send","Relances en attente",data.pending_followups,"Réponse attendue"],
      ["blue","bell","Notifications non lues",data.unread_notifications,"Compte connecté"],
    ];

    $("#watchDashboardKpis").innerHTML = cards.map(([tone,icon,label,value,detail]) => `
      <article class="gov-kpi watch-kpi ${tone}">
        <span><i data-lucide="${icon}"></i></span>
        <div><small>${e(label)}</small><strong>${e(value ?? 0)}</strong><em>${e(detail)}</em></div>
      </article>
    `).join("");
    icons();
  }

  async function loadDashboard() {
    renderDashboard(await api.apiGet("/api/v1/veille/dashboard"));
  }

  function visible(item) {
    if (!filters.search) return true;
    const needle = filters.search.toLowerCase();

    return [
      item.certification_identifier,
      item.certificate_number,
      item.enterprise_name,
      item.standard_code,
      item.type_evenement,
      item.responsable_name,
    ].filter(Boolean).join(" ").toLowerCase().includes(needle);
  }

  function renderCases() {
    const rows = cases.filter(visible);
    $("#watchCaseCount").textContent = `${rows.length} dossier${rows.length > 1 ? "s" : ""}`;

    $("#watchCaseList").innerHTML = rows.length
      ? rows.map((item) => `
          <button class="watch-case-row ${selected?.id === item.id ? "active" : ""}" type="button" data-case="${e(item.id)}">
            <span class="watch-case-icon"><i data-lucide="folder-search-2"></i></span>
            <div><strong>${e(item.enterprise_name || "Entreprise")}</strong><small>${e(item.certification_identifier || "Certification")} · ${e(item.type_evenement || "Événement")}</small></div>
            <div class="watch-case-meta"><strong>${e(item.responsable_name || "—")}</strong><small>${e(item.relances_en_attente_count || 0)} relance(s) en attente</small></div>
            <span class="gov-status">${e(item.statut || "—")}</span>
            <i data-lucide="chevron-right"></i>
          </button>
        `).join("")
      : `<div class="priority-empty">Aucun dossier de veille.</div>`;

    $$("#watchCaseList [data-case]").forEach((button) => {
      button.onclick = async () => {
        selected = cases.find((x) => String(x.id) === String(button.dataset.case));
        renderCases();
        await renderDetail();
      };
    });

    icons();
  }

  async function renderDetail() {
    const node = $("#watchCaseDetail");

    if (!selected) {
      node.innerHTML = `<div class="priority-empty">Sélectionnez un dossier.</div>`;
      return;
    }

    let followups = [];
    try {
      followups = await api.apiGet(`/api/v1/veille/dossiers/${selected.id}/relances`);
    } catch {}

    node.innerHTML = `
      <header>
        <div>
          <h2>${e(selected.enterprise_name || "Entreprise")}</h2>
          <p>${e(selected.certification_identifier || "Certification")} · ${e(selected.standard_code || "Norme")}</p>
        </div>
        <span class="gov-status">${e(selected.statut || "—")}</span>
      </header>

      <div class="watch-case-detail-body">
        <div class="cert-info-grid">
          <div class="cert-info"><small>Événement</small><strong>${e(selected.type_evenement || "—")}</strong></div>
          <div class="cert-info"><small>Responsable</small><strong>${e(selected.responsable_name || "—")}</strong></div>
          <div class="cert-info"><small>Priorité</small><strong>${e(selected.priorite || "—")}</strong></div>
          <div class="cert-info"><small>Ouverture</small><strong>${e(dateLabel(selected.date_ouverture))}</strong></div>
          <div class="cert-info"><small>Prochaine action</small><strong>${e(dateLabel(selected.prochaine_action_at))}</strong></div>
          <div class="cert-info"><small>Expiration certificat</small><strong>${e(dateLabel(selected.expiry_date))}</strong></div>
        </div>

        <div class="watch-followup-head">
          <div><strong>Relances</strong><small>${followups.length} entrée(s)</small></div>
          ${
            perm("VEILLE.RELANCER") && String(selected.statut || "").toUpperCase() !== "CLOTURE"
              ? `<button class="btn btn-outline-secondary app-btn" id="newFollowup" type="button"><i data-lucide="send"></i>Nouvelle relance</button>`
              : ""
          }
        </div>

        <div class="watch-followup-list">
          ${
            followups.length
              ? followups.map((item) => `
                  <article class="watch-followup-row">
                    <span><i data-lucide="${item.date_reponse ? "message-circle-reply" : "send"}"></i></span>
                    <div>
                      <strong>${e(item.objet || "Relance")}</strong>
                      <small>${e(item.destinataire || "—")} · ${e(item.canal || "—")} · ${e(item.statut || "—")}</small>
                      ${item.reponse ? `<p><b>Réponse :</b> ${e(item.reponse)}</p>` : ""}
                    </div>
                    ${
                      perm("VEILLE.RELANCER") && !item.date_reponse
                        ? `<button class="btn btn-outline-secondary app-btn" type="button" data-response="${e(item.id)}">Réponse</button>`
                        : ""
                    }
                  </article>
                `).join("")
              : `<div class="priority-empty">Aucune relance.</div>`
          }
        </div>

        <footer class="watch-case-actions">
          <a href="#/certifications/${e(selected.certification_id)}" class="btn btn-outline-secondary app-btn">
            <i data-lucide="badge-check"></i>Certification
          </a>

          ${
            perm("VEILLE.CLOTURER") && String(selected.statut || "").toUpperCase() !== "CLOTURE"
              ? `<button class="btn btn-primary app-btn" id="closeWatchCase" type="button"><i data-lucide="lock"></i>Clôturer</button>`
              : ""
          }
        </footer>
      </div>
    `;

    $("#newFollowup")?.addEventListener("click", () => {
      ["followupRecipient","followupEmail","followupChannel","followupSubject","followupMessage","followupSendDate","followupDueDate"]
        .forEach((id) => $(`#${id}`).value = "");
      $("#followupChannel").value = "EMAIL";
      $("#followupDialog").showModal();
      icons();
    });

    $("#closeWatchCase")?.addEventListener("click", () => {
      $("#closeWatchReason").value = "";
      $("#closeWatchCaseDialog").showModal();
      icons();
    });

    node.querySelectorAll("[data-response]").forEach((button) => {
      button.onclick = () => {
        selectedFollowup = followups.find((x) => String(x.id) === String(button.dataset.response));
        $("#followupResponseDate").value = "";
        $("#followupResponseText").value = "";
        $("#followupResult").value = "";
        $("#followupResponseDialog").showModal();
        icons();
      };
    });

    icons();
  }

  function params() {
    const p = new URLSearchParams({ limit:"200", offset:"0" });
    if (filters.statut) p.set("statut", filters.statut);
    if (filters.priorite) p.set("priorite", filters.priorite);
    return p;
  }

  async function loadCases() {
    try {
      const payload = await api.apiGet(`/api/v1/veille/workspace/cases?${params()}`);
      cases = payload.items || [];
      if (selected && !cases.some((x) => x.id === selected.id)) selected = null;
      renderCases();
      await renderDetail();
    } catch (error) {
      state(error?.message || "Dossiers indisponibles.", true);
    }
  }

  function fill(node, label, values) {
    node.innerHTML = `<option value="">${e(label)}</option>`
      + (values || []).map((v) => `<option value="${e(v)}">${e(v)}</option>`).join("");
    node.disabled = false;
  }

  async function loadFilters() {
    const data = await api.apiGet("/api/v1/veille/workspace/filters");
    fill($("#watchStatus"), "Tous les statuts", data.watch_case_statuses);
    fill($("#watchPriority"), "Toutes les priorités", data.watch_case_priorities);
    $("#watchEventTypeOptions").innerHTML = (data.watch_case_event_types || [])
      .map((value) => `<option value="${e(value)}"></option>`).join("");
    $("#watchCasePriorityOptions").innerHTML = (data.watch_case_priorities || [])
      .map((value) => `<option value="${e(value)}"></option>`).join("");
  }

  async function ensureOptions() {
    if (!options) options = await api.apiGet("/api/v1/veille/workspace/watch-options");
    return options;
  }

  async function openCase() {
    try {
      await ensureOptions();

      $("#watchCertification").innerHTML = options.certifications
        .map((x) => `<option value="${e(x.id)}">${e(x.label)}</option>`).join("");
      $("#watchResponsible").innerHTML = options.users
        .map((x) => `<option value="${e(x.id)}">${e(x.label)}</option>`).join("");

      $("#watchEventType").value = "";
      $("#watchCasePriority").value = "";
      $("#watchNextAction").value = "";

      $("#watchCaseDialog").showModal();
      icons();
    } catch (error) {
      state(error?.message || "Options indisponibles.", true);
    }
  }

  async function createCase(event) {
    event.preventDefault();

    try {
      const nextAction = $("#watchNextAction").value;

      await api.apiPost("/api/v1/veille/dossiers", {
        certification_id: $("#watchCertification").value,
        type_evenement: $("#watchEventType").value.trim(),
        priorite: $("#watchCasePriority").value.trim() || null,
        responsable_id: $("#watchResponsible").value,
        prochaine_action_at: nextAction ? new Date(nextAction).toISOString() : null,
      });

      $("#watchCaseDialog").close();
      await Promise.all([loadDashboard(), loadCases()]);
      state("Dossier de veille ouvert.");
    } catch (error) {
      state(error?.message || "Création impossible.", true);
    }
  }

  async function createFollowup(event) {
    event.preventDefault();
    if (!selected) return;

    try {
      await api.apiPost(`/api/v1/veille/dossiers/${selected.id}/relances`, {
        destinataire: $("#followupRecipient").value.trim(),
        adresse_email: $("#followupEmail").value.trim(),
        canal: $("#followupChannel").value.trim(),
        objet: $("#followupSubject").value.trim(),
        contenu: $("#followupMessage").value.trim(),
        date_envoi: $("#followupSendDate").value || null,
        date_echeance: $("#followupDueDate").value || null,
      });

      $("#followupDialog").close();
      await Promise.all([loadDashboard(), loadCases()]);
      state("Relance enregistrée.");
    } catch (error) {
      state(error?.message || "Relance impossible.", true);
    }
  }

  async function saveResponse(event) {
    event.preventDefault();
    if (!selected || !selectedFollowup) return;

    try {
      await api.apiPost(
        `/api/v1/veille/dossiers/${selected.id}/relances/${selectedFollowup.id}/response`,
        {
          date_reponse: $("#followupResponseDate").value || null,
          reponse: $("#followupResponseText").value.trim(),
          resultat: $("#followupResult").value.trim() || null,
        }
      );

      $("#followupResponseDialog").close();
      selectedFollowup = null;

      await Promise.all([loadDashboard(), loadCases()]);
      state("Réponse enregistrée.");
    } catch (error) {
      state(error?.message || "Réponse impossible.", true);
    }
  }

  async function closeCase(event) {
    event.preventDefault();
    if (!selected) return;

    try {
      await api.apiPost(`/api/v1/veille/dossiers/${selected.id}/close`, {
        motif: $("#closeWatchReason").value.trim(),
      });

      $("#closeWatchCaseDialog").close();
      selected = null;

      await Promise.all([loadDashboard(), loadCases()]);
      state("Dossier clôturé.");
    } catch (error) {
      state(error?.message || "Clôture impossible.", true);
    }
  }

  async function scan() {
    try {
      const result = await api.apiPost("/api/v1/veille/scans/daily", {});
      await Promise.all([loadDashboard(), loadCases()]);
      state(`Scan ${result.scan_date} : ${result.deadlines_created} échéance(s), ${result.alerts_created} alerte(s) créées.`);
    } catch (error) {
      state(error?.message || "Scan impossible.", true);
    }
  }

  async function loadReports() {
    const node = $("#watchReportList");

    try {
      const payload = await api.apiGet("/api/v1/veille/workspace/reports?limit=100&offset=0");
      const rows = payload.items || [];

      node.innerHTML = rows.length
        ? rows.map((item) => `
            <article class="watch-report-row">
              <span><i data-lucide="file-chart-column"></i></span>
              <div>
                <strong>${e(item.type_rapport || "Rapport")}</strong>
                <small>${e(item.periode_debut || "—")} → ${e(item.periode_fin || "—")} · préparé par ${e(item.prepare_par_name || "—")}</small>
              </div>
              <div class="watch-report-metrics">
                <span><b>${e(item.nombre_certifications_suivies || 0)}</b>certifications</span>
                <span><b>${e(item.nombre_alertes || 0)}</b>alertes</span>
              </div>
              <span class="gov-status">${e(item.statut || "—")}</span>
              ${
                String(item.statut || "").toUpperCase() !== "VALIDE" && perm("VEILLE.VALIDER_RAPPORT")
                  ? `<button class="btn btn-primary app-btn" type="button" data-validate="${e(item.id)}">Valider</button>`
                  : ""
              }
            </article>
          `).join("")
        : `<div class="priority-empty">Aucun rapport de veille.</div>`;

      node.querySelectorAll("[data-validate]").forEach((button) => {
        button.onclick = () => {
          selectedReport = rows.find((x) => String(x.id) === String(button.dataset.validate));
          $("#watchReportValidationComment").value = "";
          $("#validateWatchReportDialog").showModal();
          icons();
        };
      });

      icons();
    } catch (error) {
      node.innerHTML = `<div class="priority-empty">${e(error?.message || "Rapports indisponibles.")}</div>`;
    }
  }

  async function generateReport(event) {
    event.preventDefault();

    try {
      await api.apiPost("/api/v1/veille/rapports/generate", {
        type_rapport: $("#watchReportType").value.trim(),
        periode_debut: $("#watchReportStart").value,
        periode_fin: $("#watchReportEnd").value,
      });

      $("#watchReportDialog").close();
      await loadReports();
      state("Rapport de veille généré.");
    } catch (error) {
      state(error?.message || "Génération impossible.", true);
    }
  }

  async function validateReport(event) {
    event.preventDefault();
    if (!selectedReport) return;

    try {
      await api.apiPost(`/api/v1/veille/rapports/${selectedReport.id}/validate`, {
        commentaire: $("#watchReportValidationComment").value.trim() || null,
      });

      $("#validateWatchReportDialog").close();
      selectedReport = null;
      await loadReports();
      state("Rapport de veille validé.");
    } catch (error) {
      state(error?.message || "Validation impossible.", true);
    }
  }

  function switchTab(name) {
    $$("[data-watch-tab]").forEach((button) => {
      button.classList.toggle("active", button.dataset.watchTab === name);
    });
    $("#watchCasesTab").hidden = name !== "cases";
    $("#watchReportsTab").hidden = name !== "reports";
    if (name === "reports") loadReports();
  }

  function bind() {
    $("#watchScan").hidden = !perm("VEILLE.SCANNER");
    $("#newWatchCase").hidden = !perm("VEILLE.GERER");
    $("#generateWatchReport").hidden = !perm("VEILLE.RAPPORTER");

    $("#watchScan").onclick = scan;
    $("#newWatchCase").onclick = openCase;
    $("#generateWatchReport").onclick = () => {
      $("#watchReportType").value = "";
      $("#watchReportStart").value = "";
      $("#watchReportEnd").value = "";
      $("#watchReportDialog").showModal();
      icons();
    };

    $("#watchSearch").oninput = (event) => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        filters.search = event.target.value.trim();
        renderCases();
      }, 250);
    };

    $("#watchStatus").onchange = async (event) => {
      filters.statut = event.target.value; await loadCases();
    };
    $("#watchPriority").onchange = async (event) => {
      filters.priorite = event.target.value; await loadCases();
    };
    $("#watchReset").onclick = async () => {
      Object.assign(filters, { search:"", statut:"", priorite:"" });
      $("#watchSearch").value = "";
      $("#watchStatus").value = "";
      $("#watchPriority").value = "";
      await loadCases();
    };

    $("#watchCaseForm").onsubmit = createCase;
    $("#followupForm").onsubmit = createFollowup;
    $("#followupResponseForm").onsubmit = saveResponse;
    $("#closeWatchCaseForm").onsubmit = closeCase;
    $("#watchReportForm").onsubmit = generateReport;
    $("#validateWatchReportForm").onsubmit = validateReport;

    $$("[data-watch-tab]").forEach((button) => {
      button.onclick = () => switchTab(button.dataset.watchTab);
    });

    $$("[data-close-watch-dialog]").forEach((button) => {
      button.onclick = () => document.getElementById(
        button.dataset.closeWatchDialog
      )?.close();
    });
  }

  try {
    user = await api.apiGet("/api/v1/me");
    bind();

    await Promise.all([
      loadDashboard(),
      loadFilters(),
      loadCases(),
      loadReports(),
    ]);
  } catch (error) {
    state(error?.message || "Erreur de chargement.", true);
  }

  icons();
})();
