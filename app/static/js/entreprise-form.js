(function () {
  "use strict";

  const $ = (selector) => document.querySelector(selector);
  const icon = (name) => `<i data-lucide="${name}"></i>`;

  let apiGet;
  let apiPost;
  let apiPatch;
  let ApiError;
  let hasPermission;

  const state = {
    step: 1,
    editing: false,
    id: null,
    filters: { zones: [], sectors: [] },
    company: {
      identifiant_national: "",
      raison_sociale: "",
      nom_commercial: "",
      forme_juridique: "",
      rccm: "",
      nif: "",
      ifu: "",
      date_creation: "",
      nationalite: "Togolaise",
      capital_social: "",
      effectif: "",
      email_principal: "",
      telephone_principal: "",
      site_web: "",
      adresse_siege: "",
      zone_siege_id: "",
      activite_principale: "",
      secteurs_secondaires: [],
    },
    contacts: [],
    sites: [],
    offers: [],
    removed: {
      contacts: new Set(),
      sites: new Set(),
      offers: new Set(),
    },
    duplicateOk: false,
  };

  function loader() { return window.HAUQE_ACTION_LOADER || null; }
  function refreshIcons() { if (window.lucide) window.lucide.createIcons({ attrs: { "stroke-width": 1.8 } }); }
  function escapeHtml(value) { return String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;"); }
  function clean(value) { const text = String(value ?? "").trim(); return text || null; }
  function normalizedCode(value) { return clean(value)?.toUpperCase() || null; }
  function uuidFromHash() {
    const parts = location.hash.replace(/^#\/?/, "").split("/").filter(Boolean);
    if (parts[0] === "entreprises" && parts[1] === "modifier" && parts[2]) return parts[2];
    return null;
  }
  function toast(message) {
    $("#saveIndicator span").textContent = message;
    $("#saveIndicator").hidden = false;
    setTimeout(() => { $("#saveIndicator").hidden = true; }, 2200);
  }
  function showApiState(title, message, { error = false } = {}) {
    const box = $("#companyFormApiState");
    box.hidden = false;
    box.className = `company-form-api-state ${error ? "error" : ""}`.trim();
    box.innerHTML = `${icon(error ? "triangle-alert" : "info")}<div><strong>${escapeHtml(title)}</strong><span>${escapeHtml(message)}</span></div>`;
    refreshIcons();
  }
  function hideApiState() { $("#companyFormApiState").hidden = true; $("#companyFormApiState").innerHTML = ""; }

  function field(name, label, { required = false, type = "text", help = "", min = null, disabled = false } = {}) {
    const value = state.company[name] ?? "";
    return `<div class="form-field"><label>${escapeHtml(label)}${required ? " <b>*</b>" : ""}</label><input name="${escapeHtml(name)}" type="${escapeHtml(type)}" value="${escapeHtml(value)}" ${required ? "required" : ""} ${disabled ? "disabled" : ""} ${min !== null ? `min="${min}"` : ""}>${help ? `<small class="field-help">${escapeHtml(help)}</small>` : ""}</div>`;
  }

  function companySelect(name, label, options, { required = false, help = "" } = {}) {
    const value = String(state.company[name] ?? "");
    return `<div class="form-field"><label>${escapeHtml(label)}${required ? " <b>*</b>" : ""}</label><select name="${escapeHtml(name)}" ${required ? "required" : ""}><option value="">Sélectionner</option>${options.map((option) => `<option value="${escapeHtml(option.value)}" ${String(option.value) === value ? "selected" : ""}>${escapeHtml(option.label)}</option>`).join("")}</select>${help ? `<small class="field-help">${escapeHtml(help)}</small>` : ""}</div>`;
  }

  function head(title, text) { return `<div class="form-card-head"><h2>${escapeHtml(title)}</h2><p>${escapeHtml(text)}</p></div>`; }

  function zoneOptions() {
    const order = { REGION: 1, PREFECTURE: 2, COMMUNE: 3, LOCALITE: 4 };
    return [...(state.filters.zones || [])]
      .sort((a, b) => (order[String(a.type_zone || "").toUpperCase()] || 9) - (order[String(b.type_zone || "").toUpperCase()] || 9) || String(a.nom).localeCompare(String(b.nom), "fr"))
      .map((item) => ({ value: item.id, label: `${item.nom}${item.type_zone ? ` — ${item.type_zone}` : ""}` }));
  }

  function sectorOptions() {
    const base = state.filters.sectors || [];
    const current = clean(state.company.activite_principale);
    const values = [...new Set([...base, ...(current ? [current] : [])])];
    return values.map((value) => ({ value, label: value }));
  }

  function renderContactsEditor() {
    return `<div class="entry-list company-structured-list" id="contactList">${state.contacts.map((item, index) => `<div class="repeat-entry structured-contact" data-contact-index="${index}"><input type="hidden" data-field="id" value="${escapeHtml(item.id || "")}"><div class="form-field"><label>Prénoms / Nom</label><input data-field="name" value="${escapeHtml([item.prenoms, item.nom].filter(Boolean).join(" "))}"></div><div class="form-field"><label>Fonction</label><input data-field="fonction" value="${escapeHtml(item.fonction || "")}"></div><div class="form-field"><label>Téléphone</label><input data-field="telephone" type="tel" value="${escapeHtml(item.telephone || "")}"></div><div class="form-field"><label>Email</label><input data-field="email" type="email" value="${escapeHtml(item.email || "")}"></div><label class="structured-check"><input data-field="contact_principal" type="checkbox" ${item.contact_principal ? "checked" : ""}>Contact principal</label><button class="remove-entry" type="button" data-remove-contact="${index}">${icon("trash-2")}</button></div>`).join("")}</div><button type="button" class="btn btn-outline-secondary app-btn add-entry" id="addContact">${icon("plus")}Ajouter un contact</button>`;
  }

  function renderSitesEditor() {
    return `<div class="entry-list company-structured-list" id="siteList">${state.sites.map((item, index) => `<div class="repeat-entry structured-site" data-site-index="${index}"><input type="hidden" data-field="id" value="${escapeHtml(item.id || "")}"><div class="form-field"><label>Nom du site</label><input data-field="nom" value="${escapeHtml(item.nom || "")}"></div><div class="form-field"><label>Type</label><input data-field="type_site" value="${escapeHtml(item.type_site || "")}" placeholder="Siège, usine, entrepôt…"></div><div class="form-field"><label>Zone</label><select data-field="zone_id"><option value="">Sélectionner</option>${zoneOptions().map((option) => `<option value="${escapeHtml(option.value)}" ${String(item.zone_id || "") === String(option.value) ? "selected" : ""}>${escapeHtml(option.label)}</option>`).join("")}</select></div><div class="form-field"><label>Adresse</label><input data-field="adresse" value="${escapeHtml(item.adresse || "")}"></div><button class="remove-entry" type="button" data-remove-site="${index}">${icon("trash-2")}</button></div>`).join("")}</div><button type="button" class="btn btn-outline-secondary app-btn add-entry" id="addSite">${icon("plus")}Ajouter un site</button>`;
  }

  function renderOffersEditor() {
    return `<div class="entry-list company-structured-list" id="offerList">${state.offers.map((item, index) => `<div class="repeat-entry structured-offer" data-offer-index="${index}"><input type="hidden" data-field="id" value="${escapeHtml(item.id || "")}"><div class="form-field"><label>Type</label><select data-field="type_offre"><option value="PRODUIT" ${item.type_offre === "PRODUIT" ? "selected" : ""}>Produit</option><option value="SERVICE" ${item.type_offre === "SERVICE" ? "selected" : ""}>Service</option></select></div><div class="form-field"><label>Nom</label><input data-field="nom" value="${escapeHtml(item.nom || "")}"></div><div class="form-field"><label>Catégorie</label><input data-field="categorie" value="${escapeHtml(item.categorie || "")}"></div><div class="form-field"><label>Marchés (séparés par virgule)</label><input data-field="marches_cibles" value="${escapeHtml((item.marches_cibles || []).join(", "))}"></div><div class="form-field"><label>Destinations (séparées par virgule)</label><input data-field="destinations" value="${escapeHtml((item.destinations || []).join(", "))}"></div><button class="remove-entry" type="button" data-remove-offer="${index}">${icon("trash-2")}</button></div>`).join("")}</div><button type="button" class="btn btn-outline-secondary app-btn add-entry" id="addOffer">${icon("plus")}Ajouter un produit / service</button>`;
  }

  function reviewSection(title, rows) {
    return `<section class="review-section"><h3>${escapeHtml(title)}</h3>${rows.map(([label, value]) => `<div class="review-row"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value || "Non renseigné")}</strong></div>`).join("")}</section>`;
  }

  const views = {
    1: () => `<article class="panel form-card">${head("Identification de l’entreprise", "Données officielles du registre BNEC. Le RCCM reste facultatif pour les structures en attente de régularisation.")}<div class="form-grid">${field("identifiant_national", "Identifiant national", { required: !state.editing, disabled: state.editing, help: state.editing ? "L’identifiant national ne peut pas être modifié ici." : "Identifiant métier unique HAUQE/BNEC." })}${field("raison_sociale", "Raison sociale", { required: true })}${field("nom_commercial", "Nom commercial")}${companySelect("forme_juridique", "Forme juridique", ["SARL", "SA", "Entreprise individuelle", "Coopérative", "Association", "Autre"].map((x) => ({ value: x, label: x })))}<div class="form-field"><label>Numéro RCCM</label><div class="identifier-wrap"><input name="rccm" id="rccm" value="${escapeHtml(state.company.rccm || "")}"><button type="button" class="btn btn-outline-secondary app-btn" id="checkDuplicate">Vérifier</button></div><small class="field-help">RM-11 : unicité contrôlée par le serveur. L’absence de RCCM place le dossier en attente de régularisation.</small></div>${field("nif", "NIF")}${field("ifu", "IFU")}${field("date_creation", "Date de création", { type: "date" })}${field("nationalite", "Nationalité")}${field("capital_social", "Capital social", { type: "number", min: 0 })}${field("effectif", "Effectif", { type: "number", min: 0 })}</div><div class="duplicate-result" id="duplicateResult" hidden></div></article>`,
    2: () => `<article class="panel form-card">${head("Localisation et siège", "Sélectionnez la zone administrative la plus précise disponible.")}<div class="form-grid">${companySelect("zone_siege_id", "Zone administrative du siège", zoneOptions(), { required: true, help: "Région, préfecture, commune ou localité selon le référentiel disponible." })}${field("adresse_siege", "Adresse / localité", { required: true })}${field("site_web", "Site web", { type: "url" })}</div><div class="subresource-head"><div><h3>Sites de l’entreprise</h3><p>Les sites sont enregistrés dans le sous-module Sites entreprise.</p></div></div>${renderSitesEditor()}</article>`,
    3: () => `<article class="panel form-card">${head("Activités, produits et marchés", "L’activité principale alimente les filtres du registre. Les produits/services sont conservés comme offres structurées.")}<div class="form-grid">${companySelect("activite_principale", "Activité principale", sectorOptions(), { required: true })}<div class="form-field full"><label>Secteurs secondaires</label><input name="secteurs_secondaires_text" value="${escapeHtml((state.company.secteurs_secondaires || []).join(", "))}" placeholder="Séparer par des virgules"><small class="field-help">Liste optionnelle.</small></div></div><div class="subresource-head"><div><h3>Produits et services</h3><p>Marchés et destinations sont stockés de manière structurée.</p></div></div>${renderOffersEditor()}</article>`,
    4: () => `<article class="panel form-card">${head("Contacts et coordonnées", "RM-13 : au moins un téléphone ou un courriel est obligatoire pour l’entreprise.")}<div class="form-grid">${field("telephone_principal", "Téléphone principal", { type: "tel" })}${field("email_principal", "Email principal", { type: "email" })}</div><div class="subresource-head"><div><h3>Contacts rattachés</h3><p>Le premier contact peut être marqué principal.</p></div></div>${renderContactsEditor()}</article>`,
    5: () => `<article class="panel form-card">${head("Vérification avant enregistrement", "Le serveur reste souverain sur les contrôles d’unicité, les permissions et les règles métier.")}<div class="review-layout">${reviewSection("Identification", [["Identifiant national", state.company.identifiant_national], ["Raison sociale", state.company.raison_sociale], ["RCCM", state.company.rccm || "Non renseigné"], ["NIF / IFU", state.company.nif || state.company.ifu]])}${reviewSection("Localisation / activité", [["Zone", (state.filters.zones || []).find((z) => String(z.id) === String(state.company.zone_siege_id))?.nom], ["Adresse", state.company.adresse_siege], ["Activité", state.company.activite_principale], ["Effectif", state.company.effectif]])}${reviewSection("Coordonnées", [["Téléphone", state.company.telephone_principal], ["Email", state.company.email_principal], ["Contacts", String(state.contacts.length)], ["Sites", String(state.sites.length)]])}${reviewSection("Offres", [["Produits / services", String(state.offers.length)], ["Secteurs secondaires", (state.company.secteurs_secondaires || []).join(", ")]])}<div class="review-warning">${icon("info")}L’enregistrement d’une entreprise ne valide pas automatiquement ses certifications. Les certifications sont gérées dans leur module officiel.</div></div></article>`,
  };

  function captureCompanyFields() {
    document.querySelectorAll("#formStepContent [name]").forEach((input) => {
      if (input.name === "secteurs_secondaires_text") {
        state.company.secteurs_secondaires = String(input.value || "").split(",").map((x) => x.trim()).filter(Boolean);
        return;
      }
      state.company[input.name] = input.value;
    });
    captureStructured();
  }

  function splitName(value) {
    const parts = String(value || "").trim().split(/\s+/).filter(Boolean);
    if (!parts.length) return { prenoms: null, nom: null };
    if (parts.length === 1) return { prenoms: null, nom: parts[0] };
    return { prenoms: parts.slice(0, -1).join(" "), nom: parts.at(-1) };
  }

  function captureStructured() {
    document.querySelectorAll("[data-contact-index]").forEach((row) => {
      const index = Number(row.dataset.contactIndex);
      const current = state.contacts[index] || {};
      const name = splitName(row.querySelector('[data-field="name"]')?.value);
      state.contacts[index] = {
        ...current,
        ...name,
        fonction: clean(row.querySelector('[data-field="fonction"]')?.value),
        telephone: clean(row.querySelector('[data-field="telephone"]')?.value),
        email: clean(row.querySelector('[data-field="email"]')?.value),
        type_contact: current.type_contact || "ENTREPRISE",
        contact_principal: Boolean(row.querySelector('[data-field="contact_principal"]')?.checked),
      };
    });

    document.querySelectorAll("[data-site-index]").forEach((row) => {
      const index = Number(row.dataset.siteIndex);
      const current = state.sites[index] || {};
      state.sites[index] = {
        ...current,
        nom: clean(row.querySelector('[data-field="nom"]')?.value),
        type_site: clean(row.querySelector('[data-field="type_site"]')?.value),
        zone_id: clean(row.querySelector('[data-field="zone_id"]')?.value),
        adresse: clean(row.querySelector('[data-field="adresse"]')?.value),
      };
    });

    document.querySelectorAll("[data-offer-index]").forEach((row) => {
      const index = Number(row.dataset.offerIndex);
      const current = state.offers[index] || {};
      state.offers[index] = {
        ...current,
        type_offre: row.querySelector('[data-field="type_offre"]')?.value || "PRODUIT",
        nom: clean(row.querySelector('[data-field="nom"]')?.value),
        categorie: clean(row.querySelector('[data-field="categorie"]')?.value),
        marches_cibles: String(row.querySelector('[data-field="marches_cibles"]')?.value || "").split(",").map((x) => x.trim()).filter(Boolean),
        destinations: String(row.querySelector('[data-field="destinations"]')?.value || "").split(",").map((x) => x.trim()).filter(Boolean),
      };
    });
  }

  function bindStructured() {
    $("#addContact")?.addEventListener("click", () => { captureCompanyFields(); state.contacts.push({ contact_principal: state.contacts.length === 0 }); renderStep(); });
    $("#addSite")?.addEventListener("click", () => { captureCompanyFields(); state.sites.push({ zone_id: state.company.zone_siege_id || "" }); renderStep(); });
    $("#addOffer")?.addEventListener("click", () => { captureCompanyFields(); state.offers.push({ type_offre: "PRODUIT", marches_cibles: [], destinations: [] }); renderStep(); });

    document.querySelectorAll("[data-remove-contact]").forEach((button) => button.addEventListener("click", () => {
      captureCompanyFields();
      const item = state.contacts[Number(button.dataset.removeContact)];
      if (item?.id) state.removed.contacts.add(String(item.id));
      state.contacts.splice(Number(button.dataset.removeContact), 1);
      renderStep();
    }));
    document.querySelectorAll("[data-remove-site]").forEach((button) => button.addEventListener("click", () => {
      captureCompanyFields();
      const item = state.sites[Number(button.dataset.removeSite)];
      if (item?.id) state.removed.sites.add(String(item.id));
      state.sites.splice(Number(button.dataset.removeSite), 1);
      renderStep();
    }));
    document.querySelectorAll("[data-remove-offer]").forEach((button) => button.addEventListener("click", () => {
      captureCompanyFields();
      const item = state.offers[Number(button.dataset.removeOffer)];
      if (item?.id) state.removed.offers.add(String(item.id));
      state.offers.splice(Number(button.dataset.removeOffer), 1);
      renderStep();
    }));
  }

  async function checkDuplicate(button = null) {
    const input = $("#rccm");
    const box = $("#duplicateResult");
    const value = normalizedCode(input?.value);
    state.company.rccm = input?.value || "";

    if (!value) {
      state.duplicateOk = true;
      box.hidden = false;
      box.className = "duplicate-result ok";
      box.innerHTML = `${icon("info")}<div><strong>RCCM non renseigné</strong><small>Le serveur enregistrera l’entreprise en attente de régularisation conformément à RM-12.</small></div>`;
      refreshIcons();
      return true;
    }

    const task = async () => {
      const payload = await apiGet(`/api/v1/entreprises?search=${encodeURIComponent(value)}&include_archived=true&limit=50`);
      const duplicate = (payload.items || []).find((item) => normalizedCode(item.rccm) === value && String(item.id) !== String(state.id || ""));
      box.hidden = false;
      if (duplicate) {
        state.duplicateOk = false;
        box.className = "duplicate-result";
        box.innerHTML = `${icon("triangle-alert")}<div><strong>RCCM déjà utilisé</strong><small>${escapeHtml(duplicate.raison_sociale || duplicate.identifiant_national)} possède déjà ce RCCM. Le serveur bloquera l’enregistrement.</small></div>`;
        return false;
      }
      state.duplicateOk = true;
      box.className = "duplicate-result ok";
      box.innerHTML = `${icon("circle-check")}<div><strong>Aucun doublon RCCM trouvé</strong><small>La vérification serveur définitive sera répétée à l’enregistrement.</small></div>`;
      return true;
    };

    if (loader()) return loader().run(task, { button, title: "Contrôle du RCCM", message: "Recherche de doublon", detail: "Vérification dans le registre entreprises." });
    return task();
  }

  function bindStep() {
    bindStructured();
    $("#checkDuplicate")?.addEventListener("click", (event) => checkDuplicate(event.currentTarget));
    refreshIcons();
  }

  function renderStep() {
    captureCompanyFields();
    $("#formStepContent").innerHTML = views[state.step]();
    $("#formProgress").textContent = `Étape ${state.step} sur 5`;
    $("#previousStep").hidden = state.step === 1;
    $("#nextStep").hidden = state.step === 5;
    document.querySelectorAll("#companyStepper button").forEach((button) => {
      const number = Number(button.dataset.step);
      button.classList.toggle("active", number === state.step);
      button.classList.toggle("completed", number < state.step);
    });
    bindStep();
  }

  function validCurrentStep() {
    let ok = true;
    document.querySelectorAll("#formStepContent [required]").forEach((input) => {
      const missing = !String(input.value || "").trim();
      input.classList.toggle("invalid", missing);
      if (missing) ok = false;
    });
    if (!ok) showApiState("Informations manquantes", "Complétez les champs obligatoires de cette étape.", { error: true });
    return ok;
  }

  function validateAll() {
    captureCompanyFields();
    const errors = [];
    if (!clean(state.company.identifiant_national)) errors.push("Identifiant national obligatoire.");
    if (!clean(state.company.raison_sociale)) errors.push("Raison sociale obligatoire.");
    if (!clean(state.company.zone_siege_id)) errors.push("Zone administrative obligatoire.");
    if (!clean(state.company.adresse_siege)) errors.push("Adresse / localité obligatoire.");
    if (!clean(state.company.activite_principale)) errors.push("Activité principale obligatoire.");
    if (!clean(state.company.telephone_principal) && !clean(state.company.email_principal)) errors.push("Téléphone principal ou email principal obligatoire.");
    if (errors.length) {
      showApiState("Enregistrement impossible", errors.join(" "), { error: true });
      return false;
    }
    return true;
  }

  function companyPayload() {
    const c = state.company;
    const payload = {
      raison_sociale: clean(c.raison_sociale),
      nom_commercial: clean(c.nom_commercial),
      forme_juridique: clean(c.forme_juridique),
      rccm: clean(c.rccm),
      nif: clean(c.nif),
      ifu: clean(c.ifu),
      date_creation: clean(c.date_creation),
      nationalite: clean(c.nationalite),
      capital_social: clean(c.capital_social) === null ? null : Number(c.capital_social),
      effectif: clean(c.effectif) === null ? null : Number(c.effectif),
      email_principal: clean(c.email_principal),
      telephone_principal: clean(c.telephone_principal),
      site_web: clean(c.site_web),
      adresse_siege: clean(c.adresse_siege),
      zone_siege_id: c.zone_siege_id,
      activite_principale: clean(c.activite_principale),
      secteurs_secondaires: c.secteurs_secondaires || [],
    };
    if (!state.editing) payload.identifiant_national = clean(c.identifiant_national);
    return payload;
  }

  function contactPayload(item) {
    return {
      nom: clean(item.nom), prenoms: clean(item.prenoms), fonction: clean(item.fonction),
      telephone: clean(item.telephone), email: clean(item.email),
      type_contact: clean(item.type_contact) || "ENTREPRISE",
      contact_principal: Boolean(item.contact_principal),
    };
  }
  function sitePayload(item) {
    return { nom: clean(item.nom), type_site: clean(item.type_site), adresse: clean(item.adresse), zone_id: item.zone_id || state.company.zone_siege_id };
  }
  function offerPayload(item) {
    return { type_offre: item.type_offre || "PRODUIT", nom: clean(item.nom), categorie: clean(item.categorie), marches_cibles: item.marches_cibles || [], destinations: item.destinations || [] };
  }

  async function syncSubresources(companyId) {
    for (let index = 0; index < state.contacts.length; index += 1) {
      const item = state.contacts[index];
      if (!(clean(item.nom) || clean(item.prenoms) || clean(item.telephone) || clean(item.email))) continue;

      const saved = item.id
        ? await apiPatch(`/api/v1/entreprises/${companyId}/contacts/${item.id}`, contactPayload(item))
        : await apiPost(`/api/v1/entreprises/${companyId}/contacts`, contactPayload(item));

      state.contacts[index] = { ...item, ...saved };
    }

    for (let index = 0; index < state.sites.length; index += 1) {
      const item = state.sites[index];
      if (!(clean(item.nom) || clean(item.adresse))) continue;

      const saved = item.id
        ? await apiPatch(`/api/v1/entreprises/${companyId}/sites/${item.id}`, sitePayload(item))
        : await apiPost(`/api/v1/entreprises/${companyId}/sites`, sitePayload(item));

      state.sites[index] = { ...item, ...saved };
    }

    for (let index = 0; index < state.offers.length; index += 1) {
      const item = state.offers[index];
      if (!clean(item.nom)) continue;

      const saved = item.id
        ? await apiPatch(`/api/v1/entreprises/${companyId}/offres/${item.id}`, offerPayload(item))
        : await apiPost(`/api/v1/entreprises/${companyId}/offres`, offerPayload(item));

      state.offers[index] = { ...item, ...saved };
    }

    for (const id of [...state.removed.contacts]) {
      await apiPost(`/api/v1/entreprises/${companyId}/contacts/${id}/deactivate`, {
        motif: "Retiré depuis le formulaire entreprise",
      });
      state.removed.contacts.delete(id);
    }

    for (const id of [...state.removed.sites]) {
      await apiPost(`/api/v1/entreprises/${companyId}/sites/${id}/deactivate`, {
        motif: "Retiré depuis le formulaire entreprise",
      });
      state.removed.sites.delete(id);
    }

    for (const id of [...state.removed.offers]) {
      await apiPost(`/api/v1/entreprises/${companyId}/offres/${id}/deactivate`, {
        motif: "Retiré depuis le formulaire entreprise",
      });
      state.removed.offers.delete(id);
    }
  }

  async function submit() {
    if (!validateAll()) {
      state.step = 5;
      renderStep();
      return;
    }

    const task = async () => {
      let company;
      if (state.editing) {
        company = await apiPatch(`/api/v1/entreprises/${state.id}`, companyPayload());
      } else {
        company = await apiPost("/api/v1/entreprises", companyPayload());
        state.id = company.id;
        // Si une sous-ressource échoue ensuite, un nouveau clic doit
        // reprendre par PATCH et non recréer l'entreprise.
        state.editing = true;
      }

      await syncSubresources(company.id);
      location.hash = `#/entreprises/${company.id}`;
    };

    try {
      hideApiState();
      if (loader()) {
        await loader().run(task, { button: $("#submitCompany"), title: state.editing ? "Modification de l’entreprise" : "Création de l’entreprise", message: state.editing ? "Enregistrement des modifications" : "Enregistrement dans la BNEC", detail: "Entreprise, contacts, sites et offres sont synchronisés avec l’API." });
      } else {
        await task();
      }
    } catch (error) {
      showApiState("Enregistrement incomplet", error?.message || "Le serveur a refusé l’enregistrement.", { error: true });
    }
  }

  function bindStatic() {
    $("#nextStep").addEventListener("click", () => {
      captureCompanyFields();
      if (!validCurrentStep()) return;
      state.step = Math.min(5, state.step + 1);
      hideApiState();
      renderStep();
    });
    $("#previousStep").addEventListener("click", () => {
      captureCompanyFields();
      state.step = Math.max(1, state.step - 1);
      renderStep();
    });
    document.querySelectorAll("#companyStepper button").forEach((button) => button.addEventListener("click", () => {
      captureCompanyFields();
      state.step = Number(button.dataset.step);
      renderStep();
    }));
    $("#submitCompany").addEventListener("click", async () => {
      captureCompanyFields();
      if (state.step !== 5) {
        state.step = 5;
        renderStep();
        return;
      }
      await submit();
    });
  }

  async function load() {
    const [api, auth] = await Promise.all([
      import("/static/js/core/api.js"),
      import("/static/js/core/auth.js"),
    ]);
    apiGet = api.apiGet;
    apiPost = api.apiPost;
    apiPatch = api.apiPatch;
    ApiError = api.ApiError;
    hasPermission = auth.hasPermission;

    state.id = uuidFromHash();
    state.editing = Boolean(state.id);

    if (state.editing && !hasPermission("ENTREPRISES.MODIFIER")) {
      showApiState("Modification non autorisée", "Votre rôle ne possède pas ENTREPRISES.MODIFIER.", { error: true });
      $("#submitCompany").hidden = true;
    }
    if (!state.editing && !hasPermission("ENTREPRISES.CREER")) {
      showApiState("Création non autorisée", "Votre rôle ne possède pas ENTREPRISES.CREER.", { error: true });
      $("#submitCompany").hidden = true;
    }

    const task = async () => {
      const filtersPromise = apiGet("/api/v1/entreprises/filters");
      const companyPromise = state.editing ? apiGet(`/api/v1/entreprises/${state.id}`) : Promise.resolve(null);
      const contactsPromise = state.editing ? apiGet(`/api/v1/entreprises/${state.id}/contacts?include_inactive=true`) : Promise.resolve([]);
      const sitesPromise = state.editing ? apiGet(`/api/v1/entreprises/${state.id}/sites?include_inactive=true`) : Promise.resolve([]);
      const offersPromise = state.editing ? apiGet(`/api/v1/entreprises/${state.id}/offres?include_inactive=true`) : Promise.resolve([]);

      const [filters, company, contacts, sites, offers] = await Promise.all([filtersPromise, companyPromise, contactsPromise, sitesPromise, offersPromise]);
      state.filters = filters || { zones: [], sectors: [] };

      if (company) {
        Object.keys(state.company).forEach((key) => {
          if (key in company && company[key] !== null && company[key] !== undefined) state.company[key] = company[key];
        });
        state.company.date_creation = company.date_creation || "";
        state.company.capital_social = company.capital_social ?? "";
        state.company.effectif = company.effectif ?? "";
        state.contacts = (contacts || []).filter((item) => String(item.statut || "ACTIF").toUpperCase() !== "INACTIF");
        state.sites = (sites || []).filter((item) => String(item.statut || "ACTIF").toUpperCase() !== "INACTIF");
        state.offers = (offers || []).filter((item) => String(item.statut || "ACTIF").toUpperCase() !== "INACTIF");
        $("#companyFormTitle").textContent = `Modifier ${company.raison_sociale || company.identifiant_national}`;
        $("#formModeLabel").textContent = "Modification";
        $("#companyFormSubtitle").textContent = "Modifiez les informations autorisées ; l’identifiant national reste immuable dans cette route.";
      } else {
        if (!state.contacts.length) state.contacts.push({ contact_principal: true });
        if (!state.sites.length) state.sites.push({ zone_id: "" });
        if (!state.offers.length) state.offers.push({ type_offre: "PRODUIT", marches_cibles: [], destinations: [] });
      }

      hideApiState();
      renderStep();
    };

    try {
      if (loader()) await loader().run(task, { title: state.editing ? "Entreprise" : "Nouvelle entreprise", message: state.editing ? "Chargement de la fiche" : "Chargement des référentiels", detail: "Récupération des zones, secteurs et données autorisées." });
      else await task();
    } catch (error) {
      showApiState("Impossible de charger le formulaire", error?.message || "Une erreur API empêche l’ouverture de la fiche.", { error: true });
    }
  }

  bindStatic();
  load();
})();
