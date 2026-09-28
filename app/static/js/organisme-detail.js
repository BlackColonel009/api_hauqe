(function () {
  "use strict";

  const $ = (selector) => document.querySelector(selector);
  const hashParts = location.hash.replace(/^#\//, "").split("/");
  const organismeId = hashParts[1];

  let apiGet;
  let apiPost;
  let apiBlob;

  let organisme = null;
  let accreditations = [];
  let certifications = [];
  let documents = [];

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

  function statusClass(value) {
    const status = String(value || "").toUpperCase();
    if (["RECONNU", "VALIDE", "ACTIF"].includes(status)) return "valid";
    if (status.includes("SUSPEND")) return "suspended";
    if (status.includes("RETIR") || status.includes("INACTIF")) return "expired";
    return "verify";
  }

  function showState(message, { error = false } = {}) {
    const state = $("#bodyDetailState");
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
    $("#bodyDetailState").hidden = true;
  }

  function nextAccreditationExpiry() {
    return accreditations
      .map((item) => item.date_expiration)
      .filter(Boolean)
      .sort()[0] || null;
  }

  function renderHeader() {
    $("#bodyBreadcrumb").textContent =
      organisme.nom_officiel || organisme.sigle || "Organisme";

    $("#bodyLogo").textContent =
      (organisme.sigle || organisme.nom_officiel || "OC")
        .slice(0, 4)
        .toUpperCase();

    $("#bodyName").textContent =
      organisme.nom_officiel || "Organisme sans nom";

    const status = $("#bodyStatus");
    status.className = `cert-status ${statusClass(organisme.statut)}`;
    status.innerHTML = `<i></i>${escapeHtml(organisme.statut || "Non renseigné")}`;

    $("#bodyType").textContent =
      organisme.type_organisme || "Organisme certificateur";

    $("#bodyRefs").innerHTML = `
      <span><b>Pays</b> ${escapeHtml(organisme.pays || "—")}</span>
      <span><b>Identifiant</b> ${escapeHtml(organisme.identifiant_national || "—")}</span>
      <span><b>Enregistrement</b> ${escapeHtml(organisme.numero_enregistrement || "—")}</span>
    `;

    $("#bodyEdit").href = `#/organismes/modifier/${organisme.id}`;

    $("#accreditationCount").textContent = String(accreditations.length);
    $("#certificateCount").textContent = String(certifications.length);
    $("#documentCount").textContent = String(documents.length);

    const nextExpiry = nextAccreditationExpiry();

    const cards = [
      ["green", "badge-check", "Certificats délivrés", certifications.length, "Registre officiel"],
      ["blue", "shield-check", "Accréditations", accreditations.length, "Enregistrées"],
      ["orange", "calendar-clock", "Prochaine échéance", formatDate(nextExpiry), nextExpiry ? "Accréditation" : "Aucune date"],
      ["green", "search-check", "Dernière vérification", formatDate(organisme.date_derniere_verification), "HAUQE"],
    ];

    $("#bodyDetailKpis").innerHTML = cards.map(
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
    $("#bodyTabContent").innerHTML = `
      <div class="cert-overview">
        <article class="panel">
          <div class="panel-heading">
            <div>
              <h2>Informations générales</h2>
              <p>Identité et coordonnées enregistrées</p>
            </div>
          </div>

          <div class="cert-info-grid">
            ${[
              ["Nom officiel", organisme.nom_officiel],
              ["Sigle", organisme.sigle],
              ["Type d’organisme", organisme.type_organisme],
              ["Pays", organisme.pays],
              ["Adresse", organisme.adresse],
              ["Email", organisme.email],
              ["Téléphone", organisme.telephone],
              ["Site web", organisme.site_web],
            ].map(([label, value]) => `
              <div class="cert-info">
                <small>${escapeHtml(label)}</small>
                <strong>${escapeHtml(value || "—")}</strong>
              </div>
            `).join("")}
          </div>
        </article>

        <article class="panel">
          <div class="panel-heading">
            <div>
              <h2>Situation HAUQE</h2>
              <p>Éléments de contrôle disponibles dans le registre</p>
            </div>
          </div>

          <div class="verification-checks">
            <div class="verification-check">
              <span>${icon("shield-check")}</span>
              <div>
                <strong>${escapeHtml(organisme.statut || "Non renseigné")}</strong>
                <small>Statut courant de l’organisme</small>
              </div>
            </div>

            <div class="verification-check">
              <span>${icon("calendar-check-2")}</span>
              <div>
                <strong>${escapeHtml(formatDate(organisme.date_derniere_verification))}</strong>
                <small>Dernière vérification enregistrée</small>
              </div>
            </div>

            <div class="verification-check">
              <span>${icon("file-check-2")}</span>
              <div>
                <strong>${documents.length}</strong>
                <small>Document(s) directement rattaché(s)</small>
              </div>
            </div>
          </div>
        </article>
      </div>
    `;
    refreshIcons();
  }

  function renderAccreditations() {
    const content = accreditations.length
      ? `
        <table class="audit-table">
          <thead>
            <tr>
              <th>Accréditeur</th>
              <th>Domaine</th>
              <th>Numéro</th>
              <th>Délivrance</th>
              <th>Expiration</th>
              <th>Statut</th>
              <th>Décision HAUQE</th>
            </tr>
          </thead>
          <tbody>
            ${accreditations.map((item) => `
              <tr>
                <td><strong>${escapeHtml(item.accrediteur || "—")}</strong></td>
                <td>${escapeHtml(item.domaine_technique || "—")}</td>
                <td>${escapeHtml(item.numero || "—")}</td>
                <td>${escapeHtml(formatDate(item.date_delivrance))}</td>
                <td>${escapeHtml(formatDate(item.date_expiration))}</td>
                <td>
                  <span class="audit-result">
                    ${escapeHtml(item.statut || "Non renseigné")}
                  </span>
                </td>
                <td>${escapeHtml(item.decision_hauqe || "—")}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      `
      : `<div class="priority-empty">Aucune accréditation enregistrée.</div>`;

    $("#bodyTabContent").innerHTML = `
      <article class="panel mt-3">
        <div class="panel-heading">
          <div>
            <h2>Accréditations</h2>
            <p>Portées, périodes et décisions enregistrées</p>
          </div>
        </div>
        ${content}
      </article>
    `;
  }

  function renderCertificates() {
    const content = certifications.length
      ? certifications.map((item) => `
          <button
            class="cert-doc-row"
            type="button"
            data-cert-id="${escapeHtml(item.id)}"
          >
            <span>${icon("badge-check")}</span>
            <div>
              <strong>${escapeHtml(item.identifiant_national || item.numero_certificat || "Certification")}</strong>
              <small>
                Statut ${escapeHtml(item.statut || "—")}
                · expiration ${escapeHtml(formatDate(item.date_expiration))}
              </small>
            </div>
            <span class="more-button">${icon("chevron-right")}</span>
          </button>
        `).join("")
      : `<div class="priority-empty">Aucune certification liée à cet organisme.</div>`;

    $("#bodyTabContent").innerHTML = `
      <article class="panel mt-3">
        <div class="panel-heading">
          <div>
            <h2>Certificats délivrés</h2>
            <p>Certifications officielles liées dans la BNEC</p>
          </div>
        </div>
        <div class="cert-doc-list">${content}</div>
      </article>
    `;

    document
      .querySelectorAll("[data-cert-id]")
      .forEach((button) => {
        button.addEventListener("click", () => {
          location.hash =
            `#/certifications/${button.dataset.certId}`;
        });
      });

    refreshIcons();
  }

  function renderDocuments() {
    const owned = documents.filter((item) => !item.certification_id);
    const certificateProofs = documents.filter((item) => item.certification_id);
    const documentedCertifications = new Set(certificateProofs.map((item) => String(item.certification_id)));
    const missing = certifications.filter((item) => !documentedCertifications.has(String(item.id)));
    const documentRow = (entry) => {
      const item = entry.document;
      return `
        <div class="cert-doc-row organisme-document-row">
          <span>${icon("file-text")}</span>
          <div>
            <strong>${escapeHtml(item.nom_original || item.type_document || "Document")}</strong>
            <small>${escapeHtml(item.type_document || "Document")} · ${escapeHtml(item.statut_verification || "Non vérifié")}</small>
            ${entry.certification_id ? `<small>${escapeHtml(entry.entreprise_name || "Entreprise")} · ${escapeHtml(entry.certification_code || "Certification")}</small>` : ""}
          </div>
          ${entry.certification_id ? `<a class="btn btn-outline-secondary app-btn" href="#/certifications/${escapeHtml(entry.certification_id)}">Voir le certificat</a>` : ""}
          <button class="btn btn-outline-secondary app-btn" type="button" data-document-id="${escapeHtml(item.id)}" aria-label="Télécharger ${escapeHtml(item.nom_original || "le document")}">${icon("download")}</button>
        </div>`;
    };

    $("#bodyTabContent").innerHTML = `
      <article class="panel mt-3">
        <div class="panel-heading">
          <div>
            <h2>Documents</h2>
            <p>Preuves et pièces enregistrées</p>
          </div>
        </div>
        <div class="organisme-document-group">
          <h3>Pièces propres à l’organisme</h3>
          <div class="cert-doc-list">${owned.length ? owned.map(documentRow).join("") : '<div class="priority-empty">Aucune pièce propre à l’organisme.</div>'}</div>
        </div>
        <div class="organisme-document-group">
          <h3>Preuves des certifications délivrées</h3>
          <p>Ces fichiers restent liés à chaque certification : ils ne sont ni copiés ni déplacés.</p>
          <div class="cert-doc-list">${certificateProofs.length ? certificateProofs.map(documentRow).join("") : '<div class="priority-empty">Aucune preuve de certification liée pour le moment.</div>'}</div>
          ${missing.length ? `<div class="organisme-document-missing"><strong>${missing.length} certification(s) sans preuve liée</strong>${missing.map((item) => `<a href="#/certifications/${escapeHtml(item.id)}">${escapeHtml(item.identifiant_national || item.numero_certificat || "Voir la certification")}</a>`).join("")}</div>` : ""}
        </div>
      </article>
    `;

    document
      .querySelectorAll("[data-document-id]")
      .forEach((button) => {
        button.addEventListener("click", async () => {
          const task = async () => {
            const blob = await apiBlob(
              `/api/v1/documents/${button.dataset.documentId}/download`
            );
            const url = URL.createObjectURL(blob);
            window.open(url, "_blank", "noopener");
            setTimeout(() => URL.revokeObjectURL(url), 30000);
          };

          if (window.HAUQE_ACTION_LOADER) {
            await window.HAUQE_ACTION_LOADER.run(task, {
              button,
              title: "Document",
              message: "Téléchargement",
              detail: "Contrôle des droits et récupération du fichier.",
            });
          } else {
            await task();
          }
        });
      });

    refreshIcons();
  }

  function showTab(name) {
    document.querySelectorAll(".detail-tabs button").forEach((button) => {
      button.classList.toggle("active", button.dataset.tab === name);
    });

    if (name === "accreditations") return renderAccreditations();
    if (name === "certificates") return renderCertificates();
    if (name === "documents") return renderDocuments();
    return renderOverview();
  }

  async function verifyCurrent(event) {
    event.preventDefault();
    if (!organisme || !apiPost) {
      showState("Le dossier est encore en cours de chargement.");
      return;
    }
    const dialog = $("#organismeVerificationDialog");
    $("#organismeVerificationStatus").value = organisme?.statut === "RECONNU" ? "RECONNU" : "A_VERIFIER";
    $("#organismeVerificationReason").value = "";
    $("#organismeVerificationError").hidden = true;
    dialog.showModal();
  }

  async function saveVerification(event) {
    event.preventDefault();
    const status = $("#organismeVerificationStatus").value;
    const motif = $("#organismeVerificationReason").value.trim();
    const errorNode = $("#organismeVerificationError");
    if (motif.length < 3) {
      errorNode.textContent = "Précisez le motif du contrôle (au moins trois caractères).";
      errorNode.hidden = false;
      return;
    }

    const task = async () => {
      organisme = await apiPost(
        `/api/v1/organismes/${organisme.id}/verification`,
        {
          statut: status,
          motif,
        }
      );
      renderHeader();
      showTab("overview");
      $("#organismeVerificationDialog").close();
    };

    try {
      if (window.HAUQE_ACTION_LOADER) {
        await window.HAUQE_ACTION_LOADER.run(task, {
          button: $("#organismeVerificationSave"),
          title: "Vérification de l’organisme",
          message: "Enregistrement de la décision",
          detail: "La date de vérification et l’audit seront mis à jour.",
        });
      } else {
        await task();
      }
    } catch (error) {
      errorNode.textContent = error?.message || "Vérification impossible.";
      errorNode.hidden = false;
    }
  }

  async function bootstrap() {
    if (!organismeId) {
      showState("Identifiant organisme absent.", { error: true });
      return;
    }

    document.querySelectorAll(".detail-tabs button").forEach((button) => {
      button.addEventListener("click", () => showTab(button.dataset.tab));
    });
    $("#bodyVerify").addEventListener("click", verifyCurrent);
    $("#organismeVerificationForm").addEventListener("submit", saveVerification);
    $("#organismeVerificationClose").addEventListener("click", () => $("#organismeVerificationDialog").close());
    $("#organismeVerificationCancel").addEventListener("click", () => $("#organismeVerificationDialog").close());

    const api = await import("/static/js/core/api.js");
    apiGet = api.apiGet;
    apiPost = api.apiPost;
    apiBlob = api.apiBlob;

    const task = async () => {
      const [org, accs, certs, docs] = await Promise.all([
        apiGet(`/api/v1/organismes/${organismeId}`),
        apiGet(`/api/v1/organismes/${organismeId}/accreditations`),
        apiGet(`/api/v1/certifications?organisme_id=${encodeURIComponent(organismeId)}&limit=200&offset=0`),
        apiGet(`/api/v1/organismes/${encodeURIComponent(organismeId)}/documents`),
      ]);

      organisme = org;
      accreditations = Array.isArray(accs) ? accs : [];
      certifications = Array.isArray(certs?.items) ? certs.items : [];
      documents = Array.isArray(docs?.items) ? docs.items : [];

      hideState();
      renderHeader();
      showTab("overview");
    };

    try {
      if (window.HAUQE_ACTION_LOADER) {
        await window.HAUQE_ACTION_LOADER.run(task, {
          title: "Dossier organisme",
          message: "Chargement du dossier",
          detail: "Organisme, accréditations, certifications et documents.",
          minVisibleMs: 360,
        });
      } else {
        await task();
      }
    } catch (error) {
      showState(error?.message || "Erreur de chargement.", { error: true });
      return;
    }

    refreshIcons();
  }

  bootstrap();
})();
