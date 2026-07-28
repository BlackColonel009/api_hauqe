(function () {
  "use strict";

  const $ = (selector) => document.querySelector(selector);

  const parts = location.hash.replace(/^#\//, "").split("/");
  const editMode = parts[1] === "modifier";
  const organismeId = editMode ? parts[2] : null;

  let apiGet;
  let apiPost;
  let apiPatch;

  let step = 1;
  let zones = [];
  let norms = [];
  let existingAccreditations = [];
  let pendingFiles = [];

  const state = {
    identifiant_national: "",
    nom_officiel: "",
    sigle: "",
    type_organisme: "",
    pays: "",
    numero_enregistrement: "",
    email: "",
    telephone: "",
    adresse: "",
    zone_id: "",
    site_web: "",
    statut: "A_VERIFIER",
    accreditations: [],
  };

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

  function showState(message, { error = false } = {}) {
    const node = $("#bodyFormState");
    node.hidden = false;
    node.className = `dashboard-api-state ${error ? "error" : ""}`.trim();
    node.innerHTML = `
      ${icon(error ? "triangle-alert" : "info")}
      <div>
        <strong>${error ? "Enregistrement impossible" : "Information"}</strong>
        <span>${escapeHtml(message)}</span>
      </div>
    `;
    refreshIcons();
  }

  function hideState() {
    $("#bodyFormState").hidden = true;
  }

  function input(name, label, {
    type = "text",
    required = false,
    value = state[name] || "",
  } = {}) {
    return `
      <div class="form-field">
        <label>${escapeHtml(label)}${required ? " <b>*</b>" : ""}</label>
        <input
          name="${escapeHtml(name)}"
          type="${escapeHtml(type)}"
          value="${escapeHtml(value)}"
          ${required ? "required" : ""}
        >
      </div>
    `;
  }

  function select(name, label, values, {
    required = false,
    current = state[name] || "",
    placeholder = "Sélectionner",
  } = {}) {
    return `
      <div class="form-field">
        <label>${escapeHtml(label)}${required ? " <b>*</b>" : ""}</label>
        <select name="${escapeHtml(name)}" ${required ? "required" : ""}>
          <option value="">${escapeHtml(placeholder)}</option>
          ${(values || []).map(([value, text]) => `
            <option
              value="${escapeHtml(value)}"
              ${String(value) === String(current) ? "selected" : ""}
            >
              ${escapeHtml(text)}
            </option>
          `).join("")}
        </select>
      </div>
    `;
  }

  function capture() {
    document.querySelectorAll("#bodyFormContent [name]").forEach((field) => {
      if (field.name.startsWith("acc_")) return;
      state[field.name] = field.value;
    });

    const accRows = Array.from(
      document.querySelectorAll("[data-accreditation-row]")
    );

    if (accRows.length) {
      state.accreditations = accRows.map((row) => ({
        id: row.dataset.id || null,
        accrediteur: row.querySelector('[name="acc_accrediteur"]')?.value || "",
        domaine_technique: row.querySelector('[name="acc_domaine"]')?.value || "",
        numero: row.querySelector('[name="acc_numero"]')?.value || "",
        date_delivrance: row.querySelector('[name="acc_delivrance"]')?.value || "",
        date_expiration: row.querySelector('[name="acc_expiration"]')?.value || "",
        statut: row.querySelector('[name="acc_statut"]')?.value || "A_VERIFIER",
        reference_officielle: row.querySelector('[name="acc_reference"]')?.value || "",
      }));
    }
  }

  function renderStep1() {
    return `
      <article class="panel form-card">
        <div class="panel-heading">
          <div>
            <h2>Identification officielle</h2>
            <p>Informations d'identité de l'organisme.</p>
          </div>
        </div>

        <div class="form-grid">
          ${input("nom_officiel", "Nom officiel", { required: true })}
          ${input("sigle", "Sigle")}
          ${input("identifiant_national", "Identifiant national HAUQE")}
          ${input("numero_enregistrement", "Numéro d’enregistrement")}
          ${input("type_organisme", "Type d’organisme")}
          ${select(
            "statut",
            "Statut",
            [
              ["A_VERIFIER", "À vérifier"],
              ["RECONNU", "Reconnu"],
              ["SUSPENDU", "Suspendu"],
              ["RETIRE", "Retiré"],
            ],
            { required: true }
          )}
        </div>
      </article>
    `;
  }

  function renderStep2() {
    const zoneValues = zones.map((zone) => [
      zone.id,
      `${zone.name}${zone.type ? ` (${zone.type})` : ""}`,
    ]);

    return `
      <article class="panel form-card">
        <div class="panel-heading">
          <div>
            <h2>Coordonnées</h2>
            <p>Siège, zone et contacts officiels.</p>
          </div>
        </div>

        <div class="form-grid">
          ${input("pays", "Pays", { required: true })}
          ${select(
            "zone_id",
            "Zone au Togo",
            zoneValues,
            { placeholder: "Non renseignée / représentation hors Togo" }
          )}
          ${input("adresse", "Adresse")}
          ${input("site_web", "Site web", { type: "url" })}
          ${input("email", "Email", { type: "email" })}
          ${input("telephone", "Téléphone", { type: "tel" })}
        </div>
      </article>
    `;
  }

  function accreditationRow(item = {}) {
    const domainOptions = norms.map((norm) => [
      norm.code || norm.id,
      [
        norm.code,
        norm.version ? `v${norm.version}` : "",
        norm.nom ? `— ${norm.nom}` : "",
      ].filter(Boolean).join(" "),
    ]);

    return `
      <div
        class="repeat-entry"
        data-accreditation-row
        ${item.id ? `data-id="${escapeHtml(item.id)}"` : ""}
      >
        ${input("acc_accrediteur", "Accréditeur", {
          value: item.accrediteur || "",
        })}

        ${select(
          "acc_domaine",
          "Domaine / référentiel",
          domainOptions,
          {
            current: item.domaine_technique || "",
            placeholder: "Sélectionner ou saisir ensuite",
          }
        )}

        ${input("acc_numero", "Numéro", {
          value: item.numero || "",
        })}

        ${input("acc_delivrance", "Date de délivrance", {
          type: "date",
          value: item.date_delivrance || "",
        })}

        ${input("acc_expiration", "Date d’expiration", {
          type: "date",
          value: item.date_expiration || "",
        })}

        ${select(
          "acc_statut",
          "Statut",
          [
            ["A_VERIFIER", "À vérifier"],
            ["ACTIF", "Actif"],
            ["SUSPENDU", "Suspendu"],
            ["EXPIRE", "Expiré"],
          ],
          {
            current: item.statut || "A_VERIFIER",
          }
        )}

        ${input("acc_reference", "Référence officielle", {
          value: item.reference_officielle || "",
        })}

        ${
          item.id
            ? `<span class="text-muted small">Accréditation existante — modification autorisée, suppression non exposée.</span>`
            : `<button class="remove-entry" type="button" data-remove-accreditation>
                 ${icon("trash-2")}
               </button>`
        }
      </div>
    `;
  }

  function renderStep3() {
    const rows = state.accreditations.length
      ? state.accreditations.map(accreditationRow).join("")
      : accreditationRow();

    return `
      <article class="panel form-card">
        <div class="panel-heading">
          <div>
            <h2>Accréditations</h2>
            <p>Ajoutez uniquement les informations réellement disponibles.</p>
          </div>
        </div>

        <div class="entry-list" id="accList">${rows}</div>

        <button
          type="button"
          class="btn btn-outline-secondary app-btn add-entry"
          id="addAcc"
        >
          ${icon("plus")}Ajouter une accréditation
        </button>
      </article>
    `;
  }

  function renderStep4() {
    return `
      <article class="panel form-card">
        <div class="panel-heading">
          <div>
            <h2>Documents</h2>
            <p>
              Les fichiers sont déposés dans le stockage privé après création
              ou mise à jour de l'organisme.
            </p>
          </div>
        </div>

        <div class="form-grid">
          <div class="form-field full">
            <label>Preuves documentaires</label>
            <input
              id="bodyDocuments"
              type="file"
              accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg"
              multiple
            >
            <small>PDF, PNG ou JPEG — les permissions Documents s’appliquent.</small>
          </div>

          <div class="form-field full">
            <div class="review-warning">
              ${icon("shield-check")}
              Aucun fichier n'est envoyé avant l'enregistrement de l'organisme.
            </div>
          </div>
        </div>
      </article>
    `;
  }

  function renderStep5() {
    return `
      <article class="panel form-card">
        <div class="panel-heading">
          <div>
            <h2>Vérification avant enregistrement</h2>
            <p>Résumé des données qui seront envoyées à FastAPI.</p>
          </div>
        </div>

        <div class="review-layout">
          <div class="review-card">
            <h3>Organisme</h3>
            <dl>
              <dt>Nom</dt><dd>${escapeHtml(state.nom_officiel || "—")}</dd>
              <dt>Sigle</dt><dd>${escapeHtml(state.sigle || "—")}</dd>
              <dt>Pays</dt><dd>${escapeHtml(state.pays || "—")}</dd>
              <dt>Statut</dt><dd>${escapeHtml(state.statut || "A_VERIFIER")}</dd>
            </dl>
          </div>

          <div class="review-card">
            <h3>Compléments</h3>
            <dl>
              <dt>Accréditations</dt><dd>${state.accreditations.length}</dd>
              <dt>Nouveaux documents</dt><dd>${pendingFiles.length}</dd>
              <dt>Email</dt><dd>${escapeHtml(state.email || "—")}</dd>
              <dt>Téléphone</dt><dd>${escapeHtml(state.telephone || "—")}</dd>
            </dl>
          </div>

          <div class="review-warning">
            ${icon("info")}
            L'enregistrement ne crée aucune certification automatiquement.
            Les certifications sont gérées dans leur propre module.
          </div>
        </div>
      </article>
    `;
  }

  const renderers = {
    1: renderStep1,
    2: renderStep2,
    3: renderStep3,
    4: renderStep4,
    5: renderStep5,
  };

  function bindStepContent() {
    $("#addAcc")?.addEventListener("click", () => {
      capture();
      state.accreditations.push({});
      render();
    });

    document
      .querySelectorAll("[data-remove-accreditation]")
      .forEach((button) => {
        button.addEventListener("click", () => {
          capture();
          const rows = Array.from(
            document.querySelectorAll("[data-accreditation-row]")
          );
          const index = rows.indexOf(button.closest("[data-accreditation-row]"));
          if (index >= 0) state.accreditations.splice(index, 1);
          render();
        });
      });

    $("#bodyDocuments")?.addEventListener("change", (event) => {
      pendingFiles = Array.from(event.target.files || []);
    });

    refreshIcons();
  }

  function render() {
    capture();

    $("#bodyFormContent").innerHTML = renderers[step]();
    $("#bodyProgress").textContent = `Étape ${step} sur 5`;
    $("#bodyPrevious").hidden = step === 1;
    $("#bodyNext").hidden = step === 5;

    document.querySelectorAll("#bodyStepper button").forEach((button) => {
      const number = Number(button.dataset.step);
      button.classList.toggle("active", number === step);
      button.classList.toggle("completed", number < step);
    });

    bindStepContent();
  }

  function validateCurrentStep() {
    capture();

    if (step === 1 && !state.nom_officiel.trim()) {
      showState("Le nom officiel est obligatoire.", { error: true });
      return false;
    }

    if (step === 2 && !state.pays.trim()) {
      showState("Le pays est obligatoire pour poursuivre.", { error: true });
      return false;
    }

    hideState();
    return true;
  }

  function organismePayload() {
    const payload = {
      identifiant_national: state.identifiant_national || null,
      nom_officiel: state.nom_officiel.trim(),
      sigle: state.sigle || null,
      type_organisme: state.type_organisme || null,
      pays: state.pays || null,
      numero_enregistrement: state.numero_enregistrement || null,
      email: state.email || null,
      telephone: state.telephone || null,
      adresse: state.adresse || null,
      zone_id: state.zone_id || null,
      site_web: state.site_web || null,
    };

    if (!editMode) {
      payload.statut = state.statut || "A_VERIFIER";
    }

    return payload;
  }

  function accreditationPayload(item) {
    return {
      numero: item.numero || null,
      accrediteur: item.accrediteur || null,
      domaine_technique: item.domaine_technique || null,
      date_delivrance: item.date_delivrance || null,
      date_expiration: item.date_expiration || null,
      statut: item.statut || "A_VERIFIER",
      reference_officielle: item.reference_officielle || null,
    };
  }

  async function uploadDocuments(id) {
    for (const file of pendingFiles) {
      const data = new FormData();
      data.append("file", file);
      data.append("type_document", "PREUVE_ORGANISME");
      data.append("ressource_type", "ORGANISME");
      data.append("ressource_id", id);
      data.append("confidentialite", "INTERNE");
      data.append("source", "FORMULAIRE_ORGANISME");

      await apiPost(
        "/api/v1/documents/upload",
        data
      );
    }
  }

  async function save(event) {
    capture();

    if (!state.nom_officiel.trim()) {
      step = 1;
      render();
      showState("Le nom officiel est obligatoire.", { error: true });
      return;
    }

    if (!state.pays.trim()) {
      step = 2;
      render();
      showState("Le pays est obligatoire.", { error: true });
      return;
    }

    const task = async () => {
      let saved;

      if (editMode) {
        saved = await apiPatch(
          `/api/v1/organismes/${organismeId}`,
          organismePayload()
        );
      } else {
        saved = await apiPost(
          "/api/v1/organismes",
          organismePayload()
        );
      }

      const currentId = saved.id;

      for (const item of state.accreditations) {
        const payload = accreditationPayload(item);

        const hasUsefulValue = [
          payload.numero,
          payload.accrediteur,
          payload.domaine_technique,
          payload.date_delivrance,
          payload.date_expiration,
          payload.reference_officielle,
        ].some(Boolean);

        if (!hasUsefulValue) continue;

        if (item.id) {
          await apiPatch(
            `/api/v1/organismes/${currentId}/accreditations/${item.id}`,
            payload
          );
        } else {
          await apiPost(
            `/api/v1/organismes/${currentId}/accreditations`,
            payload
          );
        }
      }

      await uploadDocuments(currentId);

      location.hash = `#/organismes/${currentId}`;
    };

    try {
      hideState();

      if (window.HAUQE_ACTION_LOADER) {
        await window.HAUQE_ACTION_LOADER.run(task, {
          button: event.currentTarget,
          title: editMode ? "Mise à jour de l’organisme" : "Création de l’organisme",
          message: "Enregistrement",
          detail: "Organisme, accréditations et documents sont traités par le backend.",
        });
      } else {
        await task();
      }
    } catch (error) {
      showState(error?.message || "Enregistrement impossible.", { error: true });
    }
  }

  async function loadEditData() {
    if (!editMode) return;

    const [org, accs] = await Promise.all([
      apiGet(`/api/v1/organismes/${organismeId}`),
      apiGet(`/api/v1/organismes/${organismeId}/accreditations`),
    ]);

    Object.assign(state, {
      identifiant_national: org.identifiant_national || "",
      nom_officiel: org.nom_officiel || "",
      sigle: org.sigle || "",
      type_organisme: org.type_organisme || "",
      pays: org.pays || "",
      numero_enregistrement: org.numero_enregistrement || "",
      email: org.email || "",
      telephone: org.telephone || "",
      adresse: org.adresse || "",
      zone_id: org.zone_id || "",
      site_web: org.site_web || "",
      statut: org.statut || "A_VERIFIER",
      accreditations: Array.isArray(accs) ? accs : [],
    });

    existingAccreditations = state.accreditations.slice();

    $("#bodyFormMode").textContent = "Modification";
    $("#bodyFormTitle").textContent =
      `Modifier ${org.nom_officiel || org.sigle || "l’organisme"}`;
  }

  async function bootstrap() {
    const api = await import("/static/js/core/api.js");
    apiGet = api.apiGet;
    apiPost = api.apiPost;
    apiPatch = api.apiPatch;

    const task = async () => {
      const [filterData, normData] = await Promise.all([
        apiGet("/api/v1/organismes/filters"),
        apiGet("/api/v1/normes"),
      ]);

      zones = Array.isArray(filterData?.zones) ? filterData.zones : [];
      norms = Array.isArray(normData) ? normData : [];

      await loadEditData();
      render();
    };

    try {
      if (window.HAUQE_ACTION_LOADER) {
        await window.HAUQE_ACTION_LOADER.run(task, {
          title: editMode ? "Modification organisme" : "Nouvel organisme",
          message: "Préparation du formulaire",
          detail: "Chargement des zones, normes et données existantes.",
          minVisibleMs: 320,
        });
      } else {
        await task();
      }
    } catch (error) {
      showState(error?.message || "Impossible de préparer le formulaire.", {
        error: true,
      });
      return;
    }

    $("#bodyNext").addEventListener("click", () => {
      if (!validateCurrentStep()) return;
      capture();
      step = Math.min(5, step + 1);
      render();
    });

    $("#bodyPrevious").addEventListener("click", () => {
      capture();
      step = Math.max(1, step - 1);
      render();
    });

    document.querySelectorAll("#bodyStepper button").forEach((button) => {
      button.addEventListener("click", () => {
        capture();
        step = Number(button.dataset.step);
        render();
      });
    });

    $("#submitBody").addEventListener("click", save);

    refreshIcons();
  }

  bootstrap();
})();
