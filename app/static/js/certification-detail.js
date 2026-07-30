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
        <strong>${error ? "Impossible de charger le dossier" : "Information"}</strong>
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

          <div class="scope-box">
            <strong>Portée :</strong>
            ${escapeHtml(context.portee || "Aucune portée renseignée.")}
          </div>
        </article>

        <aside>
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

    refreshIcons();
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
      [cert, context, renewals, history] = await Promise.all([
        apiGet(`/api/v1/certifications/${certificationId}`),
        apiGet(`/api/v1/certifications/${certificationId}/context`),
        apiGet(`/api/v1/certifications/${certificationId}/renewals`),
        apiGet(`/api/v1/certifications/${certificationId}/history`),
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
            <p>Justificatifs et preuves documentaires</p>
          </div>
        </div>
        <div class="cert-doc-list">${content}</div>
      </article>
    `;

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

      context = await apiGet(
        `/api/v1/certifications/${certificationId}/context`
      );

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
    apiGet = api.apiGet;
    apiPost = api.apiPost;
    apiBlob = api.apiBlob;
    apiRequest = api.apiRequest;

    const task = async () => {
      [cert, context, audits, renewals, documents, history] =
        await Promise.all([
          apiGet(`/api/v1/certifications/${certificationId}`),
          apiGet(`/api/v1/certifications/${certificationId}/context`),
          apiGet(`/api/v1/certifications/${certificationId}/audits`),
          apiGet(`/api/v1/certifications/${certificationId}/renewals`),
          apiGet(
            `/api/v1/documents?ressource_type=CERTIFICATION&ressource_id=${encodeURIComponent(certificationId)}&limit=100&offset=0`
          ).then((payload) => payload.items || []),
          apiGet(`/api/v1/certifications/${certificationId}/history`),
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
