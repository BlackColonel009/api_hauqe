(function () {
  "use strict";

  const $ = (selector) => document.querySelector(selector);
  const icon = (name) => `<i data-lucide="${name}"></i>`;

  let apiGet;
  let apiPost;
  let apiRequest;
  let apiBlob;
  let ApiError;
  let hasPermission;

  const state = {
    id: null,
    company: null,
    zone: null,
    contacts: [],
    sites: [],
    offers: [],
    certifications: [],
    certificationMeta: new Map(),
    classification: null,
    controls: [],
    documents: [],
    audit: [],
    restricted: new Set(),
    currentTab: "overview",
    menu: null,
  };

  function loader() {
    return window.HAUQE_ACTION_LOADER || null;
  }

  function refreshIcons() {
    if (window.lucide) {
      window.lucide.createIcons({ attrs: { "stroke-width": 1.8 } });
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

  function routeId() {
    const parts = location.hash.replace(/^#\/?/, "").split("/").filter(Boolean);
    return parts[0] === "entreprises" && parts[1] && parts[1] !== "modifier"
      ? parts[1]
      : null;
  }

  function displayName(company = state.company) {
    return company?.raison_sociale || company?.nom_commercial || company?.identifiant_national || "Entreprise";
  }

  function initials(value) {
    const parts = String(value || "Entreprise").trim().split(/\s+/).filter(Boolean);
    if (!parts.length) return "EN";
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return `${parts[0][0] || ""}${parts.at(-1)?.[0] || ""}`.toUpperCase();
  }

  function formatDate(value, { time = false } = {}) {
    if (!value) return "—";
    const date = new Date(value.length === 10 ? `${value}T00:00:00` : value);
    if (Number.isNaN(date.getTime())) return String(value);
    return new Intl.DateTimeFormat("fr-FR", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: time ? "2-digit" : undefined,
      minute: time ? "2-digit" : undefined,
    }).format(date);
  }

  function daysUntil(value) {
    if (!value) return null;
    const target = new Date(`${value}T00:00:00`);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    if (Number.isNaN(target.getTime())) return null;
    return Math.ceil((target - today) / 86400000);
  }

  function statusMeta(raw) {
    const key = String(raw || "").trim().toUpperCase();
    const map = {
      ACTIF: ["active", "Actif"],
      ACTIVE: ["active", "Active"],
      VALIDE: ["active", "Valide"],
      VALIDE_ACTIVE: ["active", "Valide"],
      CERTIFIEE_ACTIVE: ["active", "Certifiée active"],
      A_RISQUE: ["risk", "À risque"],
      A_SURVEILLER: ["risk", "À surveiller"],
      EN_ATTENTE_REGULARISATION: ["risk", "En attente de régularisation"],
      NON_CONFORME: ["noncompliant", "Non conforme"],
      A_VERIFIER: ["verify", "À vérifier"],
      ARCHIVE: ["verify", "Archivée"],
      EXPIRE: ["noncompliant", "Expirée"],
      EXPIREE: ["noncompliant", "Expirée"],
      INACTIF: ["verify", "Inactive"],
    };
    if (map[key]) return map[key];
    if (!key) return ["verify", "Non classée"];
    return ["verify", key.toLowerCase().replaceAll("_", " ").replace(/^./, (c) => c.toUpperCase())];
  }

  function statusBadge(raw) {
    const [tone, label] = statusMeta(raw);
    return `<span class="company-status ${tone}"><i></i>${escapeHtml(label)}</span>`;
  }

  function restrictedBox(label) {
    return `<div class="company-detail-restricted">${icon("shield-alert")}<div><strong>Accès limité</strong><span>${escapeHtml(label)}</span></div></div>`;
  }

  function emptyBox(title, message, iconName = "inbox") {
    return `<div class="company-detail-empty">${icon(iconName)}<strong>${escapeHtml(title)}</strong><span>${escapeHtml(message)}</span></div>`;
  }

  function showPageState(title, message, { error = false, retry = false } = {}) {
    const box = $("#companyDetailState");
    box.hidden = false;
    box.className = `company-detail-state ${error ? "error" : ""}`.trim();
    box.innerHTML = `${icon(error ? "triangle-alert" : "info")}<div><strong>${escapeHtml(title)}</strong><span>${escapeHtml(message)}</span></div>${retry ? `<button class="btn btn-outline-secondary app-btn" id="retryCompanyDetail" type="button">${icon("refresh-cw")}Réessayer</button>` : ""}`;
    $("#retryCompanyDetail")?.addEventListener("click", () => loadAll(true));
    refreshIcons();
  }

  function hidePageState() {
    const box = $("#companyDetailState");
    box.hidden = true;
    box.innerHTML = "";
  }

  function normalizeSettled(result, key, fallback) {
    if (result.status === "fulfilled") return result.value;
    const error = result.reason;
    if (error instanceof ApiError && (error.status === 403 || error.status === 404)) {
      if (error.status === 403) state.restricted.add(key);
      return fallback;
    }
    console.warn(`Dossier entreprise — ${key}:`, error);
    return fallback;
  }

  async function hydrateCertificationMeta(certifications) {
    const normIds = [...new Set(certifications.map((item) => item.norme_id).filter(Boolean))];
    const orgIds = [...new Set(certifications.map((item) => item.organisme_id).filter(Boolean))];

    const results = await Promise.allSettled([
      ...normIds.map((id) => apiGet(`/api/v1/normes/${id}`)),
      ...orgIds.map((id) => apiGet(`/api/v1/organismes/${id}`)),
    ]);

    let index = 0;
    normIds.forEach((id) => {
      const result = results[index++];
      if (result?.status === "fulfilled") state.certificationMeta.set(`norm:${id}`, result.value);
    });
    orgIds.forEach((id) => {
      const result = results[index++];
      if (result?.status === "fulfilled") state.certificationMeta.set(`org:${id}`, result.value);
    });
  }

  function renderHeader() {
    const company = state.company;
    const name = displayName(company);
    const zoneLabel = state.zone?.nom || "Zone non renseignée";

    $("#breadcrumbCompany").textContent = name;
    $("#companyInitials").textContent = initials(name);
    $("#companyName").textContent = name;
    $("#companyStatus").innerHTML = statusBadge(company.statut);
    $("#companySubtitle").textContent = [company.activite_principale, zoneLabel].filter(Boolean).join(" · ") || "Informations du registre";
    $("#companyNationalId").textContent = company.identifiant_national || "—";
    $("#companyRccm").textContent = company.rccm || "Non renseigné";
    $("#companyTaxId").textContent = company.nif || company.ifu || "—";

    const edit = $("#editCompanyButton");
    edit.href = `#/entreprises/modifier/${state.id}`;
    edit.hidden = !hasPermission("ENTREPRISES.MODIFIER") || String(company.statut || "").toUpperCase() === "ARCHIVE";

    $("#exportCompanyDossier").hidden = !hasPermission("ENTREPRISES.EXPORTER");
    $("#companyMoreActions").hidden = !hasPermission("ENTREPRISES.ARCHIVER");

    $("#companyProfile").hidden = false;
    $("#companyDetailTabs").hidden = false;
  }

  function renderKpis() {
    const activeStatuses = new Set(["ACTIVE", "ACTIF", "VALIDE", "VALIDE_ACTIVE"]);
    const activeCerts = state.certifications.filter((item) => activeStatuses.has(String(item.statut || "").toUpperCase()));
    const watched = state.certifications.filter((item) => {
      const d = daysUntil(item.date_expiration);
      return d !== null && d >= 0 && d <= 90;
    });
    const next = state.certifications
      .filter((item) => item.date_expiration)
      .map((item) => ({ item, days: daysUntil(item.date_expiration) }))
      .filter((item) => item.days !== null && item.days >= 0)
      .sort((a, b) => a.days - b.days)[0] || null;
    const latestControl = [...state.controls].sort((a, b) => String(b.date_fin || b.date_debut || "").localeCompare(String(a.date_fin || a.date_debut || "")))[0] || null;

    const cards = [
      ["green", "badge-check", "Certifications", state.restricted.has("certifications") ? "—" : state.certifications.length, state.restricted.has("certifications") ? "Accès limité" : `${activeCerts.length} active(s) · ${watched.length} à ≤ 90 j`],
      ["orange", "gauge", "Classification", state.restricted.has("classification") ? "—" : state.classification?.score ?? "—", state.restricted.has("classification") ? "Accès limité" : state.classification?.classe || "Non calculée"],
      ["red", "calendar-clock", "Prochaine échéance", state.restricted.has("certifications") ? "—" : next ? `${next.days} j` : "—", state.restricted.has("certifications") ? "Accès limité" : next ? formatDate(next.item.date_expiration) : "Aucune échéance"],
      ["blue", "clipboard-check", "Dernier contrôle FUCCS", state.restricted.has("controls") ? "—" : latestControl?.score_brut ?? "—", state.restricted.has("controls") ? "Accès limité" : latestControl ? `${latestControl.score_maximal ?? 56} max · ${formatDate(latestControl.date_fin || latestControl.date_debut)}` : "Aucun contrôle"],
    ];

    $("#companyDetailKpis").innerHTML = cards.map(([tone, iconName, label, value, sub]) => `<article><span class="${tone}">${icon(iconName)}</span><div><small>${escapeHtml(label)}</small><strong>${escapeHtml(value)}</strong><em>${escapeHtml(sub)}</em></div></article>`).join("");
    $("#companyDetailKpis").hidden = false;
    $("#certificationsCount").textContent = state.restricted.has("certifications") ? "—" : String(state.certifications.length);
    $("#documentsCount").textContent = state.restricted.has("documents") ? "—" : String(state.documents.length);
  }

  function infoItem(label, value) {
    return `<div class="info-item"><small>${escapeHtml(label)}</small><strong>${escapeHtml(value || "Non renseigné")}</strong></div>`;
  }

  function contactName(item) {
    return [item.prenoms, item.nom].filter(Boolean).join(" ") || item.nom || item.prenoms || "Contact";
  }

  function renderOverview() {
    const c = state.company;
    const markets = [...new Set(state.offers.flatMap((item) => item.marches_cibles || []))];
    const destinations = [...new Set(state.offers.flatMap((item) => item.destinations || []))];

    const contacts = state.contacts.length
      ? state.contacts.slice(0, 5).map((item) => `<div class="contact-row"><span class="contact-icon">${icon(item.contact_principal ? "user-round-check" : "user-round")}</span><div><strong>${escapeHtml(contactName(item))}</strong><small>${escapeHtml([item.fonction, item.telephone, item.email].filter(Boolean).join(" · ") || "Coordonnées non renseignées")}</small></div></div>`).join("")
      : emptyBox("Aucun contact", "Aucun contact actif n’est rattaché à cette entreprise.", "users");

    const sites = state.sites.length
      ? state.sites.slice(0, 5).map((item) => `<div class="contact-row"><span class="contact-icon">${icon("map-pin")}</span><div><strong>${escapeHtml(item.nom || item.type_site || "Site")}</strong><small>${escapeHtml([item.adresse, item.type_site].filter(Boolean).join(" · ") || "Adresse non renseignée")}</small></div></div>`).join("")
      : emptyBox("Aucun site", "Aucun site actif n’est enregistré.", "map-pin-off");

    return `<div class="tab-layout"><div>
      <article class="panel detail-section-panel"><div class="panel-heading"><div><h2>Informations générales</h2><p>Identité administrative et activité</p></div></div><div class="info-grid">
        ${infoItem("Identifiant national", c.identifiant_national)}
        ${infoItem("Raison sociale", c.raison_sociale)}
        ${infoItem("Nom commercial", c.nom_commercial)}
        ${infoItem("Forme juridique", c.forme_juridique)}
        ${infoItem("Date de création", formatDate(c.date_creation))}
        ${infoItem("Nationalité", c.nationalite)}
        ${infoItem("Effectif", c.effectif !== null && c.effectif !== undefined ? String(c.effectif) : null)}
        ${infoItem("Activité principale", c.activite_principale)}
        ${infoItem("Secteurs secondaires", (c.secteurs_secondaires || []).join(", "))}
        ${infoItem("Adresse du siège", c.adresse_siege)}
        ${infoItem("Zone administrative", state.zone?.nom)}
        ${infoItem("Site web", c.site_web)}
        ${infoItem("Téléphone principal", c.telephone_principal)}
        ${infoItem("Email principal", c.email_principal)}
        ${infoItem("Marchés", markets.join(", "))}
        ${infoItem("Destinations", destinations.join(", "))}
      </div></article>
      <article class="panel detail-section-panel mt-3"><div class="panel-heading"><div><h2>Offres enregistrées</h2><p>Produits et services rattachés</p></div></div><div class="company-offer-list">${state.offers.length ? state.offers.map((item) => `<div class="company-offer-row"><span>${icon(item.type_offre === "SERVICE" ? "briefcase" : "package")}</span><div><strong>${escapeHtml(item.nom || item.type_offre || "Offre")}</strong><small>${escapeHtml([item.categorie, item.unite && item.volume_annuel ? `${item.volume_annuel} ${item.unite}` : null].filter(Boolean).join(" · ") || "Détails non renseignés")}</small></div></div>`).join("") : emptyBox("Aucune offre", "Aucun produit ou service actif n’est enregistré.", "package-open")}</div></article>
    </div><aside>
      <article class="panel detail-section-panel"><div class="panel-heading"><div><h2>Contacts</h2><p>Interlocuteurs actifs</p></div></div><div class="contacts-list">${contacts}</div></article>
      <article class="panel detail-section-panel mt-3"><div class="panel-heading"><div><h2>Sites</h2><p>Implantations enregistrées</p></div></div><div class="contacts-list">${sites}</div></article>
    </aside></div>`;
  }

  function certLabel(item) {
    const norm = state.certificationMeta.get(`norm:${item.norme_id}`);
    return norm?.code || norm?.nom || item.identifiant_national || "Certification";
  }

  function orgLabel(item) {
    const org = state.certificationMeta.get(`org:${item.organisme_id}`);
    return org?.sigle || org?.nom_officiel || "Organisme non chargé";
  }

  function renderCertifications() {
    if (state.restricted.has("certifications")) return restrictedBox("Votre rôle ne possède pas CERTIFICATIONS.LIRE.");
    if (!state.certifications.length) return `<article class="panel detail-section-panel mt-3">${emptyBox("Aucune certification", "Aucun certificat officiel n’est rattaché à cette entreprise.", "badge-check")}</article>`;

    return `<article class="panel detail-section-panel mt-3"><div class="panel-heading"><div><h2>Certifications détenues</h2><p>Données officielles du registre des certifications</p></div>${hasPermission("CERTIFICATIONS.CREER") ? `<a href="#/certifications/nouveau" class="btn btn-primary app-btn">${icon("plus")}Ajouter</a>` : ""}</div><div class="certification-detail-list">${state.certifications.map((item) => {
      const days = daysUntil(item.date_expiration);
      return `<button class="cert-detail-row cert-detail-button" type="button" data-certification-id="${escapeHtml(item.id)}"><span class="cert-badge">${escapeHtml((certLabel(item) || "CER").slice(0, 3).toUpperCase())}</span><div><strong>${escapeHtml(certLabel(item))}</strong><small>${escapeHtml(orgLabel(item))} · ${escapeHtml(item.numero_certificat || item.identifiant_national)}</small></div><span class="stacked"><strong>${escapeHtml(formatDate(item.date_expiration))}</strong><small>${days === null ? "Sans échéance" : days < 0 ? "Échue" : `${days} jour(s) restant(s)`}</small></span>${statusBadge(item.statut)}</button>`;
    }).join("")}</div></article>`;
  }

  function renderControls() {
    const classification = state.restricted.has("classification")
      ? restrictedBox("Votre rôle ne possède pas CLASSIFICATION.LIRE.")
      : `<article class="panel detail-section-panel"><div class="panel-heading"><div><h2>Classification entreprise</h2><p>Dernier résultat validé disponible</p></div></div>${state.classification ? `<div class="score-breakdown"><div class="score-large"><strong>${escapeHtml(state.classification.score ?? "—")}</strong><span>/ 100</span></div><div class="classification-meta"><span>${statusBadge(state.classification.statut)}</span><strong>${escapeHtml(state.classification.classe || "Classe non renseignée")}</strong><small>Calcul : ${escapeHtml(formatDate(state.classification.date_calcul))} · Validation : ${escapeHtml(formatDate(state.classification.date_validation))}</small></div></div>` : emptyBox("Classification non calculée", "Aucun résultat de classification validé n’est disponible.", "gauge")}</article>`;

    let controls;
    if (state.restricted.has("controls")) {
      controls = restrictedBox("Votre rôle ne possède pas FUCCS.LIRE.");
    } else if (!state.controls.length) {
      controls = `<article class="panel detail-section-panel">${emptyBox("Aucun contrôle FUCCS", "Aucun contrôle n’est actuellement rattaché à cette entreprise.", "clipboard-check")}</article>`;
    } else {
      controls = `<article class="panel detail-section-panel"><div class="panel-heading"><div><h2>Contrôles FUCCS</h2><p>Contrôles rattachés via les fiches de collecte</p></div></div><div class="company-control-list">${state.controls.map((item) => `<div class="company-control-row"><span>${icon("clipboard-check")}</span><div><strong>${escapeHtml(formatDate(item.date_fin || item.date_debut))}</strong><small>${escapeHtml(item.statut || "Statut non renseigné")}${item.synthese ? ` · ${escapeHtml(item.synthese)}` : ""}</small></div><b>${escapeHtml(item.score_brut ?? "—")} / ${escapeHtml(item.score_maximal ?? "—")}</b></div>`).join("")}</div></article>`;
    }

    return `<div class="tab-layout">${controls}${classification}</div>`;
  }

  function documentSize(value) {
    const bytes = Number(value || 0);
    if (!bytes) return "—";
    if (bytes < 1024) return `${bytes} o`;
    if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} Ko`;
    return `${(bytes / 1024 / 1024).toFixed(1)} Mo`;
  }

  function renderDocuments() {
    if (state.restricted.has("documents")) return restrictedBox("Votre rôle ne possède pas DOCUMENTS.LIRE.");

    return `<article class="panel detail-section-panel mt-3"><div class="panel-heading"><div><h2>Documents du dossier</h2><p>Documents liés directement à l’entreprise</p></div>${hasPermission("DOCUMENTS.DEPOSER") ? `<button class="btn btn-primary app-btn" id="addCompanyDocument" type="button">${icon("upload")}Ajouter un document</button>` : ""}</div><div class="document-list">${state.documents.length ? state.documents.map((item) => `<div class="document-row"><span class="document-icon">${icon("file-text")}</span><div><strong>${escapeHtml(item.nom_original || item.nom_stockage || "Document")}</strong><small>${escapeHtml([item.type_document, item.format, documentSize(item.taille_octets)].filter(Boolean).join(" · "))}</small></div><div class="document-meta"><strong>${escapeHtml(formatDate(item.date_document || item.date_depot))}</strong><small>${escapeHtml(item.statut_verification || item.statut || "")}</small></div>${hasPermission("DOCUMENTS.TELECHARGER") ? `<button class="more-button" type="button" data-download-document="${escapeHtml(item.id)}" data-filename="${escapeHtml(item.nom_original || item.nom_stockage || "document")}">${icon("download")}</button>` : ""}</div>`).join("") : emptyBox("Aucun document", "Aucun document n’est directement rattaché à cette entreprise.", "files")}</div></article>`;
  }

  function auditLabel(item) {
    const action = String(item.action || "Événement").replaceAll("_", " ").toLowerCase();
    return action.replace(/^./, (c) => c.toUpperCase());
  }

  function renderHistory() {
    if (state.restricted.has("audit")) return restrictedBox("Votre rôle ne possède pas AUDIT.LIRE.");
    if (!state.audit.length) return `<article class="panel detail-section-panel mt-3">${emptyBox("Aucun événement d’audit", "Aucun événement n’a été trouvé pour cette entreprise.", "history")}</article>`;

    return `<article class="panel detail-section-panel mt-3"><div class="panel-heading"><div><h2>Historique du dossier</h2><p>Journal d’audit lié à l’entreprise</p></div></div><div class="timeline-list">${state.audit.map((item) => `<div class="timeline-row"><i class="timeline-dot"></i><div><strong>${escapeHtml(auditLabel(item))}</strong><small>${escapeHtml(item.resultat || item.categorie || "")}</small></div><span>${escapeHtml(formatDate(item.date_evenement || item.created_at, { time: true }))}</span></div>`).join("")}</div></article>`;
  }

  function renderTab(name) {
    state.currentTab = name;
    document.querySelectorAll("#companyDetailTabs button").forEach((button) => button.classList.toggle("active", button.dataset.tab === name));

    const renderers = {
      overview: renderOverview,
      certifications: renderCertifications,
      controls: renderControls,
      documents: renderDocuments,
      history: renderHistory,
    };

    $("#tabContent").innerHTML = (renderers[name] || renderOverview)();

    $("#addCompanyDocument")?.addEventListener("click", () => {
      $("#companyDocumentInput").value = "";
      $("#companyDocumentType").value = "JUSTIFICATIF_ENTREPRISE";
      $("#companyDocumentConfidentiality").value = "INTERNE";
      $("#companyDocumentDialog").showModal();
      refreshIcons();
    });
    document.querySelectorAll("[data-download-document]").forEach((button) => {
      button.addEventListener("click", () => downloadDocument(button));
    });
    document.querySelectorAll("[data-certification-id]").forEach((button) => {
      button.addEventListener("click", () => {
        location.hash = `#/certifications/${button.dataset.certificationId}`;
      });
    });
    refreshIcons();
  }

  function requestReason({ title, subtitle, label = "Motif", confirmLabel = "Confirmer", iconName = "info", danger = false }) {
    const dialog = $("#companyDetailDialog");
    const form = $("#companyDetailDialogForm");
    const reason = $("#companyDetailDialogReason");
    const confirm = $("#confirmCompanyDetailDialog");

    $("#companyDetailDialogTitle").textContent = title;
    $("#companyDetailDialogSubtitle").textContent = subtitle;
    $("#companyDetailDialogLabel").textContent = label;
    $("#companyDetailDialogIcon").innerHTML = icon(iconName);
    confirm.textContent = confirmLabel;
    confirm.classList.toggle("btn-danger", danger);
    confirm.classList.toggle("btn-primary", !danger);
    reason.value = "";
    refreshIcons();

    return new Promise((resolve) => {
      const finish = (value) => {
        form.removeEventListener("submit", submit);
        $("#cancelCompanyDetailDialog").removeEventListener("click", cancel);
        dialog.removeEventListener("cancel", cancel);
        dialog.close();
        resolve(value);
      };
      const submit = (event) => {
        event.preventDefault();
        const value = reason.value.trim();
        if (value.length < 3) {
          reason.classList.add("invalid");
          reason.focus();
          return;
        }
        finish(value);
      };
      const cancel = (event) => {
        event?.preventDefault?.();
        finish(null);
      };
      form.addEventListener("submit", submit);
      $("#cancelCompanyDetailDialog").addEventListener("click", cancel);
      dialog.addEventListener("cancel", cancel);
      dialog.showModal();
      setTimeout(() => reason.focus(), 0);
    });
  }

  async function exportDossier(button) {
    const motif = await requestReason({
      title: "Exporter le dossier",
      subtitle: displayName(),
      label: "Motif de l’export",
      confirmLabel: "Exporter",
      iconName: "download",
    });
    if (motif === null) return;

    const task = async () => {
      const blob = await apiBlob(`/api/v1/entreprises/${state.id}/export?motif=${encodeURIComponent(motif)}`);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `hauqe-entreprise-${state.company.identifiant_national || state.id}.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    };

    if (loader()) {
      await loader().run(task, { button, title: "Export du dossier", message: "Génération du fichier", detail: "Le serveur consolide les données du dossier entreprise." });
    } else {
      await task();
    }
  }

  async function archiveOrRestore(restore) {
    const motif = await requestReason({
      title: restore ? "Restaurer l’entreprise" : "Archiver l’entreprise",
      subtitle: displayName(),
      label: restore ? "Motif de restauration" : "Motif d’archivage",
      confirmLabel: restore ? "Restaurer" : "Archiver",
      iconName: restore ? "archive-restore" : "archive",
      danger: !restore,
    });
    if (motif === null) return;

    const task = async () => {
      await apiPost(`/api/v1/entreprises/${state.id}/${restore ? "restore" : "archive"}`, { motif });
      await loadAll(false);
    };

    try {
      if (loader()) {
        await loader().run(task, { title: restore ? "Restauration" : "Archivage", message: restore ? "Restauration de l’entreprise" : "Archivage de l’entreprise", detail: "L’opération est journalisée côté serveur." });
      } else {
        await task();
      }
    } catch (error) {
      showPageState("Opération impossible", error?.message || "L’opération n’a pas pu être exécutée.", { error: true });
    }
  }

  function closeMenu() {
    state.menu?.remove();
    state.menu = null;
  }

  function openMoreMenu(anchor) {
    closeMenu();
    const archived = String(state.company?.statut || "").toUpperCase() === "ARCHIVE";
    const menu = document.createElement("div");
    menu.className = "company-action-menu company-detail-action-menu";
    menu.innerHTML = `<button type="button" data-action="${archived ? "restore" : "archive"}" class="${archived ? "" : "danger"}">${icon(archived ? "archive-restore" : "archive")}<span><strong>${archived ? "Restaurer" : "Archiver"}</strong><small>${archived ? "Réintégrer au registre" : "Archivage logique audité"}</small></span></button>`;
    document.body.appendChild(menu);
    state.menu = menu;
    const rect = anchor.getBoundingClientRect();
    menu.style.left = `${Math.max(12, Math.min(rect.right - menu.offsetWidth, innerWidth - menu.offsetWidth - 12))}px`;
    menu.style.top = `${Math.max(12, Math.min(rect.bottom + 7, innerHeight - menu.offsetHeight - 12))}px`;
    menu.querySelector("button").addEventListener("click", () => {
      closeMenu();
      archiveOrRestore(archived);
    });
    refreshIcons();
  }

  async function downloadDocument(button) {
    const task = async () => {
      const blob = await apiBlob(`/api/v1/documents/${button.dataset.downloadDocument}/download`);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = button.dataset.filename || "document";
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    };

    try {
      if (loader()) await loader().run(task, { button, title: "Téléchargement", message: "Préparation du document", detail: "Accès au fichier privé sécurisé." });
      else await task();
    } catch (error) {
      showPageState("Téléchargement impossible", error?.message || "Le document n’a pas pu être téléchargé.", { error: true });
    }
  }

  async function uploadDocument(file, type, confidentiality) {
    if (!file || !String(type || "").trim()) return;

    const form = new FormData();
    form.append("file", file);
    form.append("type_document", String(type).trim());
    form.append("ressource_type", "ENTREPRISE");
    form.append("ressource_id", state.id);
    form.append("confidentialite", confidentiality || "INTERNE");
    form.append("source", "DOSSIER_ENTREPRISE");

    const task = async () => {
      await apiRequest("/api/v1/documents/upload", { method: "POST", body: form });
      const docs = await apiGet(`/api/v1/documents?ressource_type=ENTREPRISE&ressource_id=${state.id}&limit=100`);
      state.documents = docs.items || [];
      renderKpis();
      renderTab("documents");
    };

    try {
      if (loader()) await loader().run(task, { title: "Ajout du document", message: "Téléversement sécurisé", detail: "Le document sera rattaché à l’entreprise." });
      else await task();
    } catch (error) {
      showPageState("Ajout impossible", error?.message || "Le document n’a pas pu être ajouté.", { error: true });
    } finally {
      $("#companyDocumentInput").value = "";
    }
  }

  function bindStaticActions() {
    document.querySelectorAll("#companyDetailTabs button").forEach((button) => button.addEventListener("click", () => renderTab(button.dataset.tab)));
    $("#exportCompanyDossier").addEventListener("click", (event) => exportDossier(event.currentTarget));
    $("#companyMoreActions").addEventListener("click", (event) => {
      event.stopPropagation();
      openMoreMenu(event.currentTarget);
    });
    $("#companyDocumentForm").addEventListener("submit", async (event) => {
      event.preventDefault();
      const file = $("#companyDocumentInput").files?.[0];
      const type = $("#companyDocumentType").value.trim();
      if (!file || !type) return;
      $("#companyDocumentDialog").close();
      await uploadDocument(
        file,
        type,
        $("#companyDocumentConfidentiality").value
      );
    });
    $("#cancelCompanyDocument").addEventListener("click", () => {
      $("#companyDocumentDialog").close();
    });
    document.addEventListener("click", (event) => {
      if (state.menu && !event.target.closest(".company-detail-action-menu,#companyMoreActions")) closeMenu();
    });
  }

  async function loadAll(withLoader = true) {
    state.id = routeId();
    state.restricted.clear();

    if (!state.id) {
      showPageState("Entreprise introuvable", "L’URL ne contient aucun identifiant d’entreprise valide.", { error: true });
      return;
    }

    const task = async () => {
      const company = await apiGet(`/api/v1/entreprises/${state.id}`);
      state.company = company;

      const results = await Promise.allSettled([
        apiGet("/api/v1/entreprises/filters"),
        apiGet(`/api/v1/entreprises/${state.id}/contacts`),
        apiGet(`/api/v1/entreprises/${state.id}/sites`),
        apiGet(`/api/v1/entreprises/${state.id}/offres`),
        apiGet(`/api/v1/certifications?entreprise_id=${state.id}&limit=200`),
        apiGet(`/api/v1/entreprises/${state.id}/classifications/latest`),
        apiGet(`/api/v1/entreprises/${state.id}/controls-summary`),
        apiGet(`/api/v1/documents?ressource_type=ENTREPRISE&ressource_id=${state.id}&limit=100`),
        apiGet(`/api/v1/audit/events?ressource_type=entreprise&ressource_id=${state.id}&limit=100`),
      ]);

      const filters = normalizeSettled(results[0], "filters", { zones: [] });
      state.zone = (filters.zones || []).find((item) => String(item.id) === String(company.zone_siege_id)) || null;
      state.contacts = normalizeSettled(results[1], "contacts", []);
      state.sites = normalizeSettled(results[2], "sites", []);
      state.offers = normalizeSettled(results[3], "offers", []);
      const certPayload = normalizeSettled(results[4], "certifications", { items: [] });
      state.certifications = certPayload.items || [];
      state.classification = normalizeSettled(results[5], "classification", null);
      const controlsPayload = normalizeSettled(results[6], "controls", { items: [] });
      state.controls = controlsPayload.items || [];
      const docsPayload = normalizeSettled(results[7], "documents", { items: [] });
      state.documents = docsPayload.items || [];
      const auditPayload = normalizeSettled(results[8], "audit", { items: [] });
      state.audit = auditPayload.items || [];

      if (state.certifications.length) await hydrateCertificationMeta(state.certifications);

      hidePageState();
      renderHeader();
      renderKpis();
      renderTab(state.currentTab);
      refreshIcons();
    };

    try {
      if (withLoader && loader()) {
        await loader().run(task, { title: "Dossier entreprise", message: "Chargement du dossier", detail: "Récupération des données autorisées depuis PostgreSQL." });
      } else {
        await task();
      }
    } catch (error) {
      showPageState(
        error instanceof ApiError && error.status === 404 ? "Entreprise introuvable" : "Impossible de charger le dossier",
        error?.message || "Le serveur n’a pas pu charger cette entreprise.",
        { error: true, retry: !(error instanceof ApiError && error.status === 404) }
      );
    }
  }

  async function bootstrap() {
    const [api, auth] = await Promise.all([
      import("/static/js/core/api.js"),
      import("/static/js/core/auth.js"),
    ]);

    apiGet = api.apiGet;
    apiPost = api.apiPost;
    apiRequest = api.apiRequest;
    apiBlob = api.apiBlob;
    ApiError = api.ApiError;
    hasPermission = auth.hasPermission;

    bindStaticActions();
    await loadAll(true);
  }

  bootstrap();
})();
