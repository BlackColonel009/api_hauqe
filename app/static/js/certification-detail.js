(function () {
  "use strict";

  const $ = (selector) => document.querySelector(selector);
  const parts = location.hash.replace(/^#\//, "").split("/");
  const certificationId = parts[1];

  let apiGet;
  let apiPost;
  let apiBlob;

  let cert = null;
  let context = null;
  let accreditation = null;
  let audits = [];
  let renewals = [];
  let documents = [];
  let history = [];

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
              </tr>
            `).join("")}
          </tbody>
        </table>
      `
      : `<div class="priority-empty">Aucune procédure de renouvellement enregistrée.</div>`;

    $("#certTabContent").innerHTML = `
      <article class="panel mt-3">
        <div class="panel-heading">
          <div>
            <h2>Renouvellements</h2>
            <p>Procédures officielles liées au certificat</p>
          </div>
        </div>
        ${content}
      </article>
    `;
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

    refreshIcons();
  }

  bootstrap();
})();
