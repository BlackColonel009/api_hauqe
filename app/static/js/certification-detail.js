(function () {
  "use strict";

  const $ = (selector) => document.querySelector(selector);
  const parts = location.hash.replace(/^#\//, "").split("/");
  const certificationId = parts[1];

  let apiGet;
  let apiPost;
  let apiBlob;
  let apiRequest;

  let cert = null;
  let context = null;
  let accreditation = null;
  let audits = [];
  let renewals = [];
  let documents = [];
  let history = [];
  let selectedRenewal = null;
  let alertPolicy = null;
  let statusAnalysis = null;
  let canManageAlertPolicy = false;
  let alertPolicyDays = [];

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
      month: "long",
      year: "numeric",
    }).format(date);
  }

  function formatDateTime(value) {
    if (!value) return "—";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);

    return new Intl.DateTimeFormat("fr-FR", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(date);
  }

  function statusClass(value, days) {
    const status = String(value || "").toUpperCase();

    if (status.includes("SUSPEND")) return "suspended";
    if (days !== null && days !== undefined && days < 0) return "expired";
    if (status.includes("VERIFIER")) return "verify";
    if (days !== null && days !== undefined && days <= 90) return "watch";
    if (["ACTIF", "ACTIVE", "VALIDE"].includes(status)) return "valid";
    return "verify";
  }

  function showState(message, { error = false } = {}) {
    const state = $("#certDetailState");
    state.hidden = false;
    state.className = `dashboard-api-state ${error ? "error" : ""}`.trim();
    state.innerHTML = `
      ${icon(error ? "triangle-alert" : "info")}
      <div>
        <strong>${error ? "Opération impossible" : "Information"}</strong>
        <span>${escapeHtml(message)}</span>
      </div>
    `;
    refreshIcons();
  }

  function hideState() {
    $("#certDetailState").hidden = true;
  }

  function renderHeader() {
    const standard = [
      context.norme_code,
      context.norme_version ? `v${context.norme_version}` : "",
    ].filter(Boolean).join(" ");

    $("#certBreadcrumb").textContent =
      `${standard || context.norme_name || "Certification"} · ${context.entreprise_name}`;

    $("#certLogo").textContent =
      (context.norme_code || "CERT").slice(0, 4).toUpperCase();

    $("#certTitle").textContent =
      standard || context.norme_name || "Certification";

    $("#certSubtitle").textContent =
      context.norme_name || "Certification officielle";

    const status = $("#certStatus");
    status.className =
      `cert-status ${statusClass(context.statut, context.days_remaining)}`;
    status.innerHTML =
      `<i></i>${escapeHtml(context.statut || "Non renseigné")}`;

    $("#certRefs").innerHTML = `
      <span>
        <b>N° original</b>
        ${escapeHtml(context.numero_certificat || "—")}
      </span>
      <span>
        <b>Code national</b>
        ${escapeHtml(context.identifiant_national)}
      </span>
    `;

    $("#certEdit").href =
      `#/certifications/modifier/${certificationId}`;

    $("#auditCount").textContent = String(audits.length);
    $("#renewalCount").textContent = String(renewals.length);
    $("#certDocumentCount").textContent = String(documents.length);
    $("#historyCount").textContent = String(history.length);

    let validity = "Sans échéance";
    if (context.days_remaining !== null) {
      if (context.days_remaining < 0) {
        validity = `Expirée depuis ${Math.abs(context.days_remaining)} j`;
      } else {
        validity = `${context.days_remaining} j restant(s)`;
      }
    }

    const openRenewals = renewals.filter(
      (item) => !item.date_decision
    ).length;

    const kpis = [
      [
        "red",
        "calendar-clock",
        "Expiration",
        formatDate(context.date_expiration),
        validity,
      ],
      [
        "green",
        "shield-check",
        "Authenticité",
        context.authenticite_verifiee ? "Vérifiée" : "À vérifier",
        `${documents.length} document(s)`,
      ],
      [
        "blue",
        "building-2",
        "Entreprise titulaire",
        context.entreprise_name,
        "Dossier BNEC",
      ],
      [
        "orange",
        "refresh-cw",
        "Renouvellement",
        openRenewals ? "En cours" : "Aucun ouvert",
        `${renewals.length} procédure(s)`,
      ],
    ];

    $("#certDetailKpis").innerHTML = kpis.map(
      ([tone, iconName, label, value, detail]) => `
        <article>
          <span class="${tone}">${icon(iconName)}</span>
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

  function renderOverview() {
    const statusFindings = statusAnalysis?.constats || [];
    const statusActions = [...new Map(
      statusFindings
        .filter((finding) => finding.action_tab && finding.action_label)
        .map((finding) => [finding.action_tab, finding])
    ).values()];
    $("#certTabContent").innerHTML = `
      <div class="cert-overview">
        <article class="panel">
          <div class="panel-heading">
            <div>
              <h2>Informations du certificat</h2>
              <p>Données officielles enregistrées dans la BNEC</p>
            </div>
          </div>

          <div class="cert-info-grid">
            ${[
              ["Référentiel", context.norme_code || context.norme_name],
              ["Version", context.norme_version],
              ["Date d’obtention", context.date_obtention],
              ["Date d’effet", context.date_effet],
              ["Date d’expiration", context.date_expiration],
              ["Statut", context.statut],
              ["Certification stratégique", context.certification_strategique ? "Oui" : "Non"],
              ["Authenticité", context.authenticite_verifiee ? "Vérifiée" : "À vérifier"],
            ].map(([label, value]) => `
              <div class="cert-info">
                <small>${escapeHtml(label)}</small>
                <strong>
                  ${escapeHtml(
                    label.startsWith("Date")
                      ? formatDate(value)
                      : value || "—"
                  )}
                </strong>
              </div>
            `).join("")}
          </div>

          <section class="cert-status-reasons" aria-label="Pourquoi ce statut">
            <div>
              <span>${icon("circle-help")}</span>
              <div>
                <strong>Pourquoi ce statut ?</strong>
                <small>
                  ${statusAnalysis
                    ? "Analyse automatique des données du dossier."
                    : "Analyse des manquements indisponible pour le moment."}
                </small>
              </div>
            </div>
            ${statusAnalysis?.statut_sncc_prioritaire
              ? `<p class="cert-status-priority">Priorité SNCC détectée : <strong>${escapeHtml(statusAnalysis.statut_sncc_prioritaire)}</strong></p>`
              : ""}
            <ul>${(statusFindings.length
              ? statusFindings.map((finding) => `
                <li class="status-finding-${escapeHtml(String(finding.niveau || "").toLowerCase())}">
                  <strong>${escapeHtml(finding.libelle)}</strong>
                  <span>${escapeHtml(finding.detail)}</span>
                </li>
              `)
              : ["Aucun détail disponible. Rechargez le dossier pour relancer l'analyse."]
                .map((reason) => `<li>${escapeHtml(reason)}</li>`)
            ).join("")}</ul>
            ${statusActions.length ? `
              <div class="cert-status-actions">
                ${statusActions.map((finding) => `
                  <button type="button" data-status-action-tab="${escapeHtml(finding.action_tab)}">
                    ${icon("arrow-up-right")}${escapeHtml(finding.action_label)}
                  </button>
                `).join("")}
              </div>
            ` : ""}
          </section>

          <div class="scope-box">
            <strong>Portée :</strong>
            ${escapeHtml(context.portee || "Aucune portée renseignée.")}
          </div>
        </article>

        <aside>
          <article class="panel cert-expiration-alerts-panel">
            <div class="panel-heading">
              <div>
                <h2>Alertes d’expiration</h2>
                <p>Jalons appliqués à ce certificat</p>
              </div>
              ${canManageAlertPolicy ? '<span id="configureCertificationAlertPolicySlot"></span>' : ""}
            </div>
            <div class="cert-expiration-alerts-content">
              <div class="cert-alert-days">
                ${(alertPolicy?.jours_avant || []).map((day) => `
                  <span class="${Number(day) === 0 ? "critical" : ""}">
                    ${Number(day) === 0 ? "Jour J" : `J-${escapeHtml(day)}`}
                  </span>
                `).join("") || "<small>Aucun jalon configuré.</small>"}
              </div>
              <small class="cert-alert-policy-source">
                ${alertPolicy?.source === "CERTIFICATION"
                  ? "Plan propre à cette certification"
                  : "Règle générale appliquée tant qu’aucun plan propre n’est enregistré"}
              </small>
            </div>
          </article>

          <article class="panel">
            <div class="panel-heading">
              <div>
                <h2>Parties concernées</h2>
                <p>Relations enregistrées</p>
              </div>
            </div>

            <div class="entity-card">
              <span>${icon("building-2")}</span>
              <div>
                <strong>${escapeHtml(context.entreprise_name)}</strong>
                <small>Entreprise titulaire</small>
              </div>
              <a href="#/entreprises/${escapeHtml(context.entreprise_id)}">
                Voir
              </a>
            </div>

            <div class="entity-card">
              <span>${icon("landmark")}</span>
              <div>
                <strong>${escapeHtml(context.organisme_name)}</strong>
                <small>${escapeHtml(context.organisme_sigle || "Organisme certificateur")}</small>
              </div>
              <a href="#/organismes/${escapeHtml(context.organisme_id)}">
                Voir
              </a>
            </div>

            <div class="entity-card">
              <span>${icon("shield-check")}</span>
              <div>
                <strong>${escapeHtml(accreditation?.accrediteur || context.accrediteur || "—")}</strong>
                <small>
                  ${
                    accreditation
                      ? `Accréditation ${escapeHtml(accreditation.numero || "sans numéro")}`
                      : "Aucune accréditation liée"
                  }
                </small>
              </div>
            </div>

            ${
              !context.date_expiration
                ? `
                  <div class="renewal-callout">
                    <strong>Certification sans date d’expiration</strong><br>
                    Elle doit rester à vérifier sauf si le référentiel
                    autorise explicitement une validité sans échéance.
                  </div>
                `
                : ""
            }
          </article>
        </aside>
      </div>
    `;

    hydrateCertificationAlertPolicyButtons();
    document.querySelectorAll("[data-status-action-tab]").forEach((button) => {
      button.addEventListener("click", () => showTab(button.dataset.statusActionTab));
    });

    refreshIcons();
  }

  function createCertificationAlertActionButton({
    label,
    iconName,
    className = "",
    handler,
  }) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = className;
    button.setAttribute("aria-label", label);
    button.setAttribute("title", label);
    button.setAttribute("data-no-action-loader", "true");
    button.setAttribute("data-certification-alert-action", "true");
    button.innerHTML = iconName ? `${icon(iconName)}${label}` : label;
    // L'affectation directe est volontaire : les boutons du plan sont
    // remplacés à chaque ouverture/rendu du modal. Ils ne doivent dépendre
    // ni d'une délégation sur le DOM, ni du chargeur global d'actions.
    button.onclick = (event) => {
      event.preventDefault();
      event.stopPropagation();
      handler();
    };
    return button;
  }

  function hydrateCertificationAlertPolicyButtons() {
    const configureSlot = $("#configureCertificationAlertPolicySlot");
    if (configureSlot) {
      configureSlot.replaceChildren(
        createCertificationAlertActionButton({
          label: "Paramétrer",
          iconName: "sliders-horizontal",
          className: "btn btn-outline-secondary app-btn cert-alert-policy-edit",
          handler: openCertificationAlertPolicy,
        })
      );
    }

    const addSlot = $("#addCertificationAlertDaySlot");
    if (addSlot) {
      addSlot.replaceChildren(
        createCertificationAlertActionButton({
          label: "Ajouter",
          iconName: "plus",
          className: "btn btn-outline-secondary app-btn",
          handler: addCertificationAlertDay,
        })
      );
    }
  }

  function renderCertificationAlertPolicyDays() {
    const container = $("#certificationAlertPolicyDays");
    container.innerHTML = alertPolicyDays.map((day) => `
      <span class="certification-alert-policy-day ${day === 0 ? "locked" : ""}">
        <strong>${day === 0 ? "Jour J" : `J-${escapeHtml(day)}`}</strong>
        <small>${day === 0 ? "expiration" : `${escapeHtml(day)} jours avant`}</small>
        ${day === 0 ? "" : `<span data-remove-certification-alert-day-slot="${escapeHtml(day)}"></span>`}
      </span>
    `).join("");
    container.querySelectorAll("[data-remove-certification-alert-day-slot]").forEach((slot) => {
      const day = Number(slot.dataset.removeCertificationAlertDaySlot);
      slot.replaceChildren(
        createCertificationAlertActionButton({
          label: `Retirer J-${day}`,
          iconName: "x",
          className: "certification-alert-policy-remove",
          handler: () => {
            alertPolicyDays = alertPolicyDays.filter((item) => item !== day);
            renderCertificationAlertPolicyDays();
          },
        })
      );
    });
    refreshIcons();
  }

  function addCertificationAlertDay() {
    const input = $("#certificationAlertDayInput");
    const day = Number(input.value);
    if (!Number.isInteger(day) || day < 1 || day > 3650) {
      showState("Indiquez un nombre entier compris entre 1 et 3 650 jours.", { error: true });
      input.focus();
      return;
    }
    if (alertPolicyDays.includes(day)) {
      showState(`Le jalon J-${day} existe déjà pour cette certification.`, { error: true });
      input.focus();
      return;
    }
    if (alertPolicyDays.length >= 12) {
      showState("Le plan peut contenir au maximum 12 jalons, jour J inclus.", { error: true });
      return;
    }
    alertPolicyDays = [...alertPolicyDays, day].sort((a, b) => b - a);
    input.value = "";
    renderCertificationAlertPolicyDays();
  }

  function openCertificationAlertPolicy() {
    alertPolicyDays = [...(alertPolicy?.jours_avant || [])]
      .map(Number)
      .filter(Number.isInteger)
      .sort((a, b) => b - a);
    if (!alertPolicyDays.includes(0)) alertPolicyDays.push(0);
    $("#certificationAlertDayInput").value = "";
    renderCertificationAlertPolicyDays();
    hydrateCertificationAlertPolicyButtons();
    $("#certificationAlertPolicyDialog").showModal();
    refreshIcons();
  }

  async function saveCertificationAlertPolicy(event) {
    event.preventDefault();
    const days = [...new Set(alertPolicyDays)].sort((a, b) => b - a);
    if (!days.includes(0)) {
      showState("Le jour J doit rester présent dans le plan d’alerte.", { error: true });
      return;
    }
    const task = async () => {
      alertPolicy = await apiRequest(
        `/api/v1/certifications/${certificationId}/expiration-alerts`,
        {
          method: "PATCH",
          body: JSON.stringify({ jours_avant: days }),
        }
      );
      cert = await apiGet(`/api/v1/certifications/${certificationId}`);
      $("#certificationAlertPolicyDialog").close();
      showTab("overview");
      showState("Le plan d’alerte est appliqué immédiatement à cette certification.");
    };
    try {
      if (window.HAUQE_ACTION_LOADER) {
        await window.HAUQE_ACTION_LOADER.run(task, {
          button: $("#saveCertificationAlertPolicy"),
          title: "Plan d’alerte de la certification",
          message: "Application des jalons",
          detail: "Les alertes automatiques actives sont recalculées.",
        });
      } else {
        await task();
      }
    } catch (error) {
      showState(error?.message || "Impossible d’enregistrer le plan d’alerte.", { error: true });
    }
  }

  function renderAudits() {
    const content = audits.length
      ? `
        <table class="audit-table">
          <thead>
            <tr>
              <th>Type</th>
              <th>Prévue</th>
              <th>Réalisée</th>
              <th>Auditeur</th>
              <th>Résultat</th>
              <th>Statut</th>
            </tr>
          </thead>
          <tbody>
            ${audits.map((item) => `
              <tr>
                <td><strong>${escapeHtml(item.type_audit || "Audit")}</strong></td>
                <td>${escapeHtml(formatDate(item.date_prevue))}</td>
                <td>${escapeHtml(formatDate(item.date_realisee))}</td>
                <td>${escapeHtml(item.auditeur || "—")}</td>
                <td>${escapeHtml(item.resultat || "—")}</td>
                <td><span class="audit-result">${escapeHtml(item.statut || "—")}</span></td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      `
      : `<div class="priority-empty">Aucun audit de certification enregistré.</div>`;

    $("#certTabContent").innerHTML = `
      <article class="panel mt-3">
        <div class="panel-heading">
          <div>
            <h2>Audits & surveillance</h2>
            <p>Audits liés au certificat</p>
          </div>
        </div>
        ${content}
      </article>
    `;
  }

  function renderRenewals() {
    const content = renewals.length
      ? `
        <table class="audit-table">
          <thead>
            <tr>
              <th>Ouverture</th>
              <th>Date limite</th>
              <th>Décision</th>
              <th>Résultat</th>
              <th>Statut</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            ${renewals.map((item) => `
              <tr>
                <td>${escapeHtml(formatDate(item.date_ouverture))}</td>
                <td>${escapeHtml(formatDate(item.date_limite))}</td>
                <td>${escapeHtml(item.decision || "En attente")}</td>
                <td>${escapeHtml(item.resultat || "—")}</td>
                <td><span class="audit-result">${escapeHtml(item.statut || "—")}</span></td>
                <td>
                  ${item.date_decision
                    ? `<span class="renewal-decided"><i data-lucide="circle-check"></i>Traité</span>`
                    : `<button class="btn btn-primary app-btn renewal-process-button" type="button" data-process-renewal="${escapeHtml(item.id)}"><i data-lucide="refresh-cw"></i>Traiter le renouvellement</button>`
                  }
                </td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      `
      : `
        <div class="renewal-empty-state">
          <span>${icon("calendar-plus-2")}</span>
          <div>
            <strong>Aucune procédure de renouvellement</strong>
            <small>Créez le cycle de renouvellement avant d’enregistrer sa décision.</small>
          </div>
          <button class="btn btn-primary app-btn" id="startRenewal" type="button">
            ${icon("plus")}Démarrer un renouvellement
          </button>
        </div>
      `;

    $("#certTabContent").innerHTML = `
      <article class="panel mt-3">
        <div class="panel-heading">
          <div>
            <h2>Renouvellements</h2>
            <p>Procédures officielles liées au certificat</p>
          </div>
          ${renewals.length && !renewals.some((item) => !item.date_decision)
            ? `<button class="btn btn-primary app-btn" id="startRenewal" type="button">${icon("plus")}Nouveau renouvellement</button>`
            : ""
          }
        </div>
        ${content}
      </article>
    `;

    $("#startRenewal")?.addEventListener("click", startRenewal);
    document.querySelectorAll("[data-process-renewal]").forEach((button) => {
      button.addEventListener("click", () => {
        selectedRenewal = renewals.find(
          (item) => String(item.id) === String(button.dataset.processRenewal)
        );
        openRenewalCompletion();
      });
    });
    refreshIcons();
  }

  async function startRenewal(event) {
    const today = dateIso(new Date());
    const deadline = context.date_expiration || addYears(today, 1);
    const task = async () => {
      const created = await apiPost(
        `/api/v1/certifications/${certificationId}/renewals`,
        {
          date_ouverture: today,
          date_limite: deadline,
          preuves: null,
          statut: "OUVERT",
        }
      );
      renewals = await apiGet(
        `/api/v1/certifications/${certificationId}/renewals`
      );
      selectedRenewal = renewals.find(
        (item) => String(item.id) === String(created.id)
      ) || created;
      renderHeader();
      renderRenewals();
      openRenewalCompletion();
    };

    try {
      if (window.HAUQE_ACTION_LOADER) {
        await window.HAUQE_ACTION_LOADER.run(task, {
          button: event.currentTarget,
          title: "Ouverture du renouvellement",
          message: "Création de la procédure",
          detail: "La procédure sera rattachée à cette certification.",
        });
      } else {
        await task();
      }
    } catch (error) {
      showState(
        error?.message || "Impossible de créer la procédure de renouvellement.",
        { error: true }
      );
    }
  }

  function dateIso(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  }

  function addYears(value, years) {
    const source = value ? new Date(`${value}T00:00:00`) : new Date();
    const target = new Date(
      source.getFullYear() + years,
      source.getMonth(),
      source.getDate()
    );
    if (target.getMonth() !== source.getMonth()) {
      target.setDate(0);
    }
    return dateIso(target);
  }

  function updateRenewalDecisionFields() {
    const renewed = $("#renewalDecision").value === "RENOUVELE";
    document.querySelectorAll("[data-renewed-field]").forEach((field) => {
      field.hidden = !renewed;
    });
    $("#renewalNewEffectiveDate").required = renewed;
    $("#renewalNewExpiryDate").required = renewed;
    $("#renewalEvidenceFiles").required = renewed;
    $("#renewalCompletionSubmit").innerHTML = renewed
      ? `${icon("badge-check")}Confirmer le renouvellement`
      : `${icon("shield-x")}Confirmer le refus`;
    $("#renewalImpactText").textContent = renewed
      ? "La certification, l’échéance, les alertes et le nouveau calendrier seront mis à jour ensemble."
      : "La certification passera à « Non renouvelée » et l’échéance ainsi que ses alertes seront clôturées.";
    refreshIcons();
  }

  function renderRenewalFiles() {
    const files = [...($("#renewalEvidenceFiles").files || [])];
    $("#renewalFileSelection").innerHTML = files.length
      ? files.map((file) => `
          <span>
            ${icon("file-check-2")}
            <strong>${escapeHtml(file.name)}</strong>
            <small>${Math.max(1, Math.round(file.size / 1024))} Ko</small>
          </span>
        `).join("")
      : "Aucun fichier sélectionné.";
    refreshIcons();
  }

  function openRenewalCompletion() {
    if (!selectedRenewal) return;
    const currentExpiry = context.date_expiration;
    const effective = currentExpiry
      ? dateIso(new Date(new Date(`${currentExpiry}T00:00:00`).getTime() + 86400000))
      : dateIso(new Date());

    $("#renewalCompletionForm").reset();
    renderRenewalFiles();
    $("#renewalDecision").value = "RENOUVELE";
    $("#renewalCompletionSubtitle").textContent =
      `Procédure ouverte le ${formatDate(selectedRenewal.date_ouverture)}`;
    $("#renewalCurrentCycle").textContent =
      `${formatDate(context.date_effet || context.date_obtention)} → ${formatDate(currentExpiry)}`;
    $("#renewalNewEffectiveDate").value = effective;
    $("#renewalNewExpiryDate").value = addYears(effective, 3);
    $("#renewalNewNumber").value = context.numero_certificat || "";
    updateRenewalDecisionFields();
    $("#renewalCompletionDialog").showModal();
    refreshIcons();
  }

  async function completeRenewal(event) {
    event.preventDefault();
    if (!selectedRenewal) return;
    const decision = $("#renewalDecision").value;
    const renewed = decision === "RENOUVELE";
    const payload = {
      decision,
      nouvelle_date_effet: renewed
        ? $("#renewalNewEffectiveDate").value || null
        : null,
      nouvelle_date_expiration: renewed
        ? $("#renewalNewExpiryDate").value || null
        : null,
      nouveau_numero_certificat: renewed
        ? $("#renewalNewNumber").value.trim() || null
        : null,
      reference_decision: $("#renewalDecisionReference").value.trim(),
      justification: $("#renewalJustification").value.trim(),
      justificatif_document_ids: [],
      preuves: $("#renewalEvidence").value.trim()
        ? { references: $("#renewalEvidence").value.trim() }
        : null,
    };

    if (
      !payload.reference_decision
      || !payload.justification
      || (renewed && (!payload.nouvelle_date_effet || !payload.nouvelle_date_expiration))
      || (renewed && !$("#renewalEvidenceFiles").files.length)
    ) {
      showState("Complétez tous les champs obligatoires du renouvellement.", {
        error: true,
      });
      return;
    }

    const task = async () => {
      for (const file of $("#renewalEvidenceFiles").files) {
        const documentForm = new FormData();
        documentForm.set("file", file);
        documentForm.set("type_document", "JUSTIFICATIF_RENOUVELLEMENT");
        documentForm.set("ressource_type", "RENOUVELLEMENT_CERTIFICATION");
        documentForm.set("ressource_id", selectedRenewal.id);
        documentForm.set("confidentialite", "INTERNE");
        documentForm.set("source", "INTERFACE_CERTIFICATION");
        const uploaded = await apiRequest("/api/v1/documents/upload", {
          method: "POST",
          body: documentForm,
        });
        payload.justificatif_document_ids.push(uploaded.id);
      }
      const result = await apiPost(
        `/api/v1/certifications/${certificationId}/renewals/${selectedRenewal.id}/complete`,
        payload
      );
      [cert, context, renewals, history, statusAnalysis] = await Promise.all([
        apiGet(`/api/v1/certifications/${certificationId}`),
        apiGet(`/api/v1/certifications/${certificationId}/context`),
        apiGet(`/api/v1/certifications/${certificationId}/renewals`),
        apiGet(`/api/v1/certifications/${certificationId}/history`),
        apiGet(`/api/v1/certifications/${certificationId}/status-analysis`).catch(() => null),
      ]);
      $("#renewalCompletionDialog").close();
      selectedRenewal = null;
      renderHeader();
      showTab("renewals");
      showState(
        decision === "RENOUVELE"
          ? `Renouvellement enregistré : ${result.echeances_terminees || 0} échéance(s) clôturée(s) et nouveau cycle planifié.`
          : "Refus de renouvellement enregistré et ancien cycle clôturé."
      );
      window.dispatchEvent(new CustomEvent("hauqe:page-ready"));
    };

    try {
      if (window.HAUQE_ACTION_LOADER) {
        await window.HAUQE_ACTION_LOADER.run(task, {
          button: $("#renewalCompletionSubmit"),
          title: renewed ? "Renouvellement du certificat" : "Refus du renouvellement",
          message: "Mise à jour coordonnée du dossier",
          detail: "Certification, échéances, alertes, historique et nouveau calendrier.",
        });
      } else {
        await task();
      }
    } catch (error) {
      showState(
        error?.message || "Le traitement du renouvellement a échoué.",
        { error: true }
      );
    }
  }

  function renderDocuments() {
    const content = documents.length
      ? documents.map((item) => `
          <button
            class="cert-doc-row"
            type="button"
            data-document-id="${escapeHtml(item.id)}"
          >
            <span>${icon("file-text")}</span>
            <div>
              <strong>${escapeHtml(item.nom_original || item.type_document || "Document")}</strong>
              <small>
                ${escapeHtml(item.type_document || "Document")}
                · ${escapeHtml(item.statut_verification || "Non vérifié")}
              </small>
            </div>
            <span class="more-button">${icon("download")}</span>
          </button>
        `).join("")
      : `<div class="priority-empty">Aucun document rattaché à cette certification.</div>`;

    $("#certTabContent").innerHTML = `
      <article class="panel mt-3">
        <div class="panel-heading">
          <div>
            <h2>Documents</h2>
            <p>Justificatifs et preuves documentaires. La présence d’un fichier ne confirme pas à elle seule son authenticité.</p>
          </div>
        </div>
        <div class="cert-proof-upload">
          <label for="certProofFile">1. Choisir une preuve propre à ce certificat</label>
          <input id="certProofFile" type="file" accept=".pdf,.png,.jpg,.jpeg,.webp" aria-describedby="certProofSelection" />
          <span id="certProofSelection" class="cert-proof-selection" aria-live="polite">Aucun fichier sélectionné.</span>
          <button class="btn btn-primary app-btn" id="certProofUpload" type="button">2. Déposer la preuve</button>
          <span id="certProofFeedback" class="cert-proof-feedback" role="alert" hidden></span>
          <small>Les pièces jointes seulement à la fiche de collecte doivent être déposées ici pour lever le manque documentaire de ce certificat.</small>
        </div>
        <div class="cert-doc-list">${content}</div>
      </article>
    `;

    const proofInput = $("#certProofFile");
    const proofSelection = $("#certProofSelection");
    const proofFeedback = $("#certProofFeedback");
    proofInput.addEventListener("change", () => {
      proofSelection.textContent = proofInput.files?.[0]?.name || "Aucun fichier sélectionné.";
      proofFeedback.hidden = true;
    });
    $("#certProofUpload").addEventListener("click", async (event) => {
      const file = proofInput.files?.[0];
      if (!file) {
        proofFeedback.textContent = "Choisissez d’abord un fichier ; la fenêtre de sélection va s’ouvrir.";
        proofFeedback.hidden = false;
        proofInput.click();
        return;
      }
      const task = async () => {
        const form = new FormData();
        form.set("file", file);
        form.set("type_document", "PREUVE_CERTIFICATION");
        form.set("ressource_type", "CERTIFICATION");
        form.set("ressource_id", certificationId);
        form.set("confidentialite", "INTERNE");
        form.set("source", "INTERFACE_CERTIFICATION");
        await apiRequest("/api/v1/documents/upload", { method: "POST", body: form });
        const response = await apiGet(`/api/v1/documents?ressource_type=CERTIFICATION&ressource_id=${encodeURIComponent(certificationId)}&limit=200&offset=0`);
        documents = Array.isArray(response?.items) ? response.items : [];
        statusAnalysis = await apiGet(`/api/v1/certifications/${certificationId}/status-analysis`).catch(() => statusAnalysis);
        showTab("documents");
        showState("Preuve déposée. L’authenticité reste à vérifier explicitement.");
      };
      try {
        if (window.HAUQE_ACTION_LOADER) await window.HAUQE_ACTION_LOADER.run(task, { button: event.currentTarget, title: "Preuve de certification", message: "Dépôt de la pièce", detail: "Rattachement au certificat sélectionné." });
        else await task();
      } catch (error) {
        proofFeedback.textContent = error?.message || "Dépôt impossible.";
        proofFeedback.hidden = false;
      }
    });

    document
      .querySelectorAll("[data-document-id]")
      .forEach((button) => {
        button.addEventListener("click", async () => {
          try {
            const blob = await apiBlob(
              `/api/v1/documents/${button.dataset.documentId}/download`
            );
            const url = URL.createObjectURL(blob);
            window.open(url, "_blank", "noopener");
            setTimeout(() => URL.revokeObjectURL(url), 30000);
          } catch (error) {
            showState(
              error?.message || "Téléchargement impossible.",
              { error: true }
            );
          }
        });
      });

    refreshIcons();
  }

  function renderHistory() {
    const content = history.length
      ? history.map((item) => `
          <div class="cert-history-row">
            <span class="history-mark"></span>
            <div>
              <strong>${escapeHtml(item.type_evenement || "Événement")}</strong>
              <small>
                ${escapeHtml(item.ancien_statut || "—")}
                →
                ${escapeHtml(item.nouveau_statut || "—")}
                ${item.motif ? ` · ${escapeHtml(item.motif)}` : ""}
              </small>
            </div>
            <time>${escapeHtml(formatDateTime(item.date_evenement || item.created_at))}</time>
          </div>
        `).join("")
      : `<div class="priority-empty">Aucun événement métier enregistré.</div>`;

    $("#certTabContent").innerHTML = `
      <article class="panel mt-3">
        <div class="panel-heading">
          <div>
            <h2>Historique de certification</h2>
            <p>Créations, changements de statut et vérifications</p>
          </div>
        </div>
        <div class="cert-history">${content}</div>
      </article>
    `;
  }

  function showTab(name) {
    document.querySelectorAll(".detail-tabs button").forEach((button) => {
      button.classList.toggle(
        "active",
        button.dataset.tab === name
      );
    });

    if (name === "audits") return renderAudits();
    if (name === "renewals") return renderRenewals();
    if (name === "documents") return renderDocuments();
    if (name === "history") return renderHistory();

    return renderOverview();
  }

  async function verify(event) {
    const authentic = window.confirm(
      "Confirmer que l’authenticité de cette certification a été vérifiée ?"
    );

    const motif = window.prompt(
      "Motif / référence de la vérification :"
    );

    if (!motif?.trim()) return;

    const task = async () => {
      cert = await apiPost(
        `/api/v1/certifications/${certificationId}/verification`,
        {
          authenticite_verifiee: authentic,
          motif: motif.trim(),
          source: "INTERFACE_CERTIFICATION",
        }
      );

      [context, statusAnalysis] = await Promise.all([
        apiGet(`/api/v1/certifications/${certificationId}/context`),
        apiGet(`/api/v1/certifications/${certificationId}/status-analysis`).catch(() => null),
      ]);

      renderHeader();
      showTab("overview");
    };

    try {
      if (window.HAUQE_ACTION_LOADER) {
        await window.HAUQE_ACTION_LOADER.run(task, {
          button: event.currentTarget,
          title: "Vérification de la certification",
          message: "Enregistrement de la vérification",
          detail: "Le backend contrôle notamment la présence d’un document actif.",
        });
      } else {
        await task();
      }
    } catch (error) {
      showState(
        error?.message || "Vérification impossible.",
        { error: true }
      );
    }
  }

  async function exportCurrent(event) {
    const motif = window.prompt(
      "Motif de l’export de cette certification :"
    );

    if (!motif?.trim()) return;

    const task = async () => {
      const params = new URLSearchParams({
        motif: motif.trim(),
      });

      const blob = await apiBlob(
        `/api/v1/certifications/${certificationId}/export?${params.toString()}`
      );

      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");

      link.href = url;
      link.download =
        `certification-${context.identifiant_national}.csv`;

      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    };

    try {
      if (window.HAUQE_ACTION_LOADER) {
        await window.HAUQE_ACTION_LOADER.run(task, {
          button: event.currentTarget,
          title: "Export de la certification",
          message: "Génération du fichier",
          detail: "Le motif d’export est enregistré dans l’audit.",
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
  }

  async function bootstrap() {
    if (!certificationId) {
      showState(
        "Identifiant certification absent.",
        { error: true }
      );
      return;
    }

    const api = await import("/static/js/core/api.js");
    const auth = await import("/static/js/core/auth.js");
    apiGet = api.apiGet;
    apiPost = api.apiPost;
    apiBlob = api.apiBlob;
    apiRequest = api.apiRequest;
    canManageAlertPolicy = auth.hasPermission("VEILLE.GERER");

    const task = async () => {
      [cert, context, audits, renewals, documents, history, alertPolicy, statusAnalysis] =
        await Promise.all([
          apiGet(`/api/v1/certifications/${certificationId}`),
          apiGet(`/api/v1/certifications/${certificationId}/context`),
          apiGet(`/api/v1/certifications/${certificationId}/audits`),
          apiGet(`/api/v1/certifications/${certificationId}/renewals`),
          apiGet(
            `/api/v1/documents?ressource_type=CERTIFICATION&ressource_id=${encodeURIComponent(certificationId)}&limit=100&offset=0`
          ).then((payload) => payload.items || []),
          apiGet(`/api/v1/certifications/${certificationId}/history`),
          apiGet(`/api/v1/certifications/${certificationId}/expiration-alerts`),
          apiGet(`/api/v1/certifications/${certificationId}/status-analysis`).catch(() => null),
        ]);

      if (context.accreditation_id) {
        try {
          accreditation = await apiGet(
            `/api/v1/organismes/${context.organisme_id}/accreditations/${context.accreditation_id}`
          );
        } catch {
          accreditation = null;
        }
      }

      hideState();
      renderHeader();
      showTab("overview");
    };

    try {
      if (window.HAUQE_ACTION_LOADER) {
        await window.HAUQE_ACTION_LOADER.run(task, {
          title: "Dossier certification",
          message: "Chargement du dossier",
          detail: "Certification, audits, renouvellements, documents et historique.",
          minVisibleMs: 360,
        });
      } else {
        await task();
      }
    } catch (error) {
      showState(
        error?.message || "Erreur de chargement.",
        { error: true }
      );
      return;
    }

    document.querySelectorAll(".detail-tabs button").forEach((button) => {
      button.addEventListener(
        "click",
        () => showTab(button.dataset.tab)
      );
    });

    $("#certVerify").addEventListener("click", verify);
    $("#certDetailExport").addEventListener("click", exportCurrent);
    $("#renewalDecision").addEventListener(
      "change",
      updateRenewalDecisionFields
    );
    $("#renewalCompletionForm").addEventListener(
      "submit",
      completeRenewal
    );
    $("#renewalEvidenceFiles").addEventListener(
      "change",
      renderRenewalFiles
    );
    $("#certificationAlertDayInput").addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        addCertificationAlertDay();
      }
    });
    $("#certificationAlertPolicyForm").addEventListener(
      "submit",
      saveCertificationAlertPolicy
    );
    document.querySelectorAll("[data-close-certification-alert-policy]").forEach((button) => {
      button.addEventListener("click", () => $("#certificationAlertPolicyDialog").close());
    });
    document.querySelectorAll("[data-close-renewal-dialog]").forEach((button) => {
      button.addEventListener("click", () => {
        $("#renewalCompletionDialog").close();
        selectedRenewal = null;
      });
    });

    refreshIcons();
  }

  bootstrap();
})();
