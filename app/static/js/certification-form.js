(function () {
  "use strict";

  const $ = (selector) => document.querySelector(selector);

  const parts = location.hash.replace(/^#\//, "").split("/");
  const editMode = parts[1] === "modifier";
  const certificationId = editMode ? parts[2] : null;

  let apiGet;
  let apiPost;
  let apiPatch;

  let step = 1;
  let enterprises = [];
  let organisms = [];
  let norms = [];
  let accreditations = [];
  let pendingFiles = [];

  const state = {
    identifiant_national: "",
    entreprise_id: "",
    norme_id: "",
    numero_certificat: "",
    organisme_id: "",
    accreditation_id: "",
    portee: "",
    issue: "",
    effect: "",
    expiry: "",
    certification_strategique: false,
    source_donnee: "SAISIE_HAUQE",
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
    const node = $("#certFormState");
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
    $("#certFormState").hidden = true;
  }

  function input(name, label, {
    type = "text",
    required = false,
    value = state[name] ?? "",
    disabled = false,
    placeholder = "",
  } = {}) {
    return `
      <div class="form-field">
        <label>
          ${escapeHtml(label)}
          ${required ? " <b>*</b>" : ""}
        </label>
        <input
          name="${escapeHtml(name)}"
          type="${escapeHtml(type)}"
          value="${escapeHtml(value)}"
          placeholder="${escapeHtml(placeholder)}"
          ${required ? "required" : ""}
          ${disabled ? "disabled" : ""}
        >
      </div>
    `;
  }

  function select(name, label, values, {
    required = false,
    current = state[name] || "",
    disabled = false,
    placeholder = "Sélectionner",
  } = {}) {
    return `
      <div class="form-field">
        <label>
          ${escapeHtml(label)}
          ${required ? " <b>*</b>" : ""}
        </label>
        <select
          name="${escapeHtml(name)}"
          ${required ? "required" : ""}
          ${disabled ? "disabled" : ""}
        >
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
    document.querySelectorAll("#certFormContent [name]").forEach((field) => {
      if (field.type === "checkbox") {
        state[field.name] = field.checked;
      } else {
        state[field.name] = field.value;
      }
    });
  }

  async function loadAccreditations(organismeId) {
    if (!organismeId) {
      accreditations = [];
      return;
    }

    accreditations = await apiGet(
      `/api/v1/organismes/${organismeId}/accreditations`
    );
  }

  function renderStep1() {
    const enterpriseOptions = enterprises.map((item) => [
      item.id,
      item.raison_sociale
        || item.nom_commercial
        || item.identifiant_national,
    ]);

    const normOptions = norms.map((item) => [
      item.id,
      [
        item.code,
        item.version ? `v${item.version}` : "",
        item.nom ? `— ${item.nom}` : "",
      ].filter(Boolean).join(" "),
    ]);

    return `
      <article class="panel form-card">
        <div class="panel-heading">
          <div>
            <h2>Identification</h2>
            <p>Titulaire, référentiel et identifiants du certificat.</p>
          </div>
        </div>

        <div class="form-grid">
          ${input(
            "identifiant_national",
            "Identifiant national",
            {
              required: true,
              disabled: editMode,
              placeholder: "Identifiant officiel HAUQE",
            }
          )}

          ${input(
            "numero_certificat",
            "Numéro du certificat",
            {
              placeholder: "Numéro original du certificateur",
            }
          )}

          ${select(
            "entreprise_id",
            "Entreprise titulaire",
            enterpriseOptions,
            {
              required: true,
              disabled: editMode,
            }
          )}

          ${select(
            "norme_id",
            "Référentiel / norme",
            normOptions,
            {
              required: true,
              disabled: editMode,
            }
          )}
        </div>

        ${
          editMode
            ? `
              <div class="review-warning">
                ${icon("lock-keyhole")}
                L’identifiant national, l’entreprise et la norme ne sont pas
                modifiables par la route de mise à jour actuelle.
              </div>
            `
            : ""
        }
      </article>
    `;
  }

  function renderStep2() {
    const organismOptions = organisms.map((item) => [
      item.id,
      [
        item.sigle || item.identifiant_national,
        item.nom_officiel,
      ].filter(Boolean).join(" — "),
    ]);

    const accreditationOptions = accreditations.map((item) => [
      item.id,
      [
        item.numero,
        item.accrediteur,
        item.domaine_technique,
      ].filter(Boolean).join(" — "),
    ]);

    return `
      <article class="panel form-card">
        <div class="panel-heading">
          <div>
            <h2>Organisme certificateur</h2>
            <p>Organisme ayant délivré le certificat et accréditation éventuelle.</p>
          </div>
        </div>

        <div class="form-grid">
          ${select(
            "organisme_id",
            "Organisme certificateur",
            organismOptions,
            {
              required: true,
              disabled: editMode,
            }
          )}

          ${select(
            "accreditation_id",
            "Accréditation liée",
            accreditationOptions,
            {
              disabled: editMode,
              placeholder: "Aucune / non renseignée",
            }
          )}
        </div>

        <div class="review-warning">
          ${icon("shield-alert")}
          Un organisme peut être enregistré sans accréditation active.
          L’authenticité et la conformité du certificat restent contrôlées
          séparément.
        </div>
      </article>
    `;
  }

  function renderStep3() {
    return `
      <article class="panel form-card">
        <div class="panel-heading">
          <div>
            <h2>Portée & dates</h2>
            <p>Validité et périmètre de la certification.</p>
          </div>
        </div>

        <div class="form-grid">
          <div class="form-field full">
            <label>Portée</label>
            <textarea
              name="portee"
              rows="4"
              placeholder="Produits, services, sites ou activités couverts"
            >${escapeHtml(state.portee || "")}</textarea>
          </div>

          ${input(
            "issue",
            "Date d’obtention",
            {
              type: "date",
              required: true,
              value: state.issue,
            }
          )}

          ${input(
            "effect",
            "Date d’effet",
            {
              type: "date",
              value: state.effect,
            }
          )}

          ${input(
            "expiry",
            "Date d’expiration",
            {
              type: "date",
              value: state.expiry,
            }
          )}

          <div class="form-field">
            <label>Certification stratégique</label>
            <label class="rule-check">
              <input
                name="certification_strategique"
                type="checkbox"
                ${state.certification_strategique ? "checked" : ""}
              >
              Cette certification est stratégique pour l’entreprise
            </label>
          </div>

          ${input(
            "source_donnee",
            "Source de la donnée",
            {
              value: state.source_donnee,
              placeholder: "SAISIE_HAUQE, IMPORT, COLLECTE…",
            }
          )}
        </div>

        <div class="review-warning" id="dateWarning" hidden>
          ${icon("triangle-alert")}
          Les dates ne sont pas chronologiquement cohérentes.
        </div>
      </article>
    `;
  }

  function renderStep4() {
    return `
      <article class="panel form-card">
        <div class="panel-heading">
          <div>
            <h2>Documents</h2>
            <p>Justificatifs qui seront stockés dans l’espace documentaire privé.</p>
          </div>
        </div>

        <div class="form-grid">
          <div class="form-field full">
            <label>
              ${editMode ? "Nouveau justificatif principal" : "Certificat principal"}
              ${editMode ? "" : " <b>*</b>"}
            </label>
            <input
              id="certDocuments"
              type="file"
              accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg"
              multiple
            >
            <small class="field-help">
              PDF, PNG ou JPEG. L’authenticité positive exige au moins
              un document actif.
            </small>
          </div>
        </div>
      </article>
    `;
  }

  function renderStep5() {
    const enterprise = enterprises.find(
      (item) => String(item.id) === String(state.entreprise_id)
    );

    const organism = organisms.find(
      (item) => String(item.id) === String(state.organisme_id)
    );

    const norm = norms.find(
      (item) => String(item.id) === String(state.norme_id)
    );

    return `
      <article class="panel form-card">
        <div class="panel-heading">
          <div>
            <h2>Vérification avant enregistrement</h2>
            <p>Les données ci-dessous seront envoyées à FastAPI.</p>
          </div>
        </div>

        <div class="review-layout">
          <div class="review-card">
            <h3>Certification</h3>
            <dl>
              <dt>Identifiant</dt>
              <dd>${escapeHtml(state.identifiant_national || "—")}</dd>

              <dt>Numéro</dt>
              <dd>${escapeHtml(state.numero_certificat || "—")}</dd>

              <dt>Référentiel</dt>
              <dd>${escapeHtml(norm?.code || norm?.nom || "—")}</dd>

              <dt>Entreprise</dt>
              <dd>${escapeHtml(
                enterprise?.raison_sociale
                || enterprise?.nom_commercial
                || "—"
              )}</dd>
            </dl>
          </div>

          <div class="review-card">
            <h3>Certificateur & validité</h3>
            <dl>
              <dt>Organisme</dt>
              <dd>${escapeHtml(organism?.nom_officiel || "—")}</dd>

              <dt>Obtention</dt>
              <dd>${escapeHtml(state.issue || "—")}</dd>

              <dt>Expiration</dt>
              <dd>${escapeHtml(state.expiry || "Sans échéance")}</dd>

              <dt>Nouveaux documents</dt>
              <dd>${pendingFiles.length}</dd>
            </dl>
          </div>

          <div class="review-warning">
            ${icon("info")}
            Une nouvelle certification est créée « À vérifier ».
            La vérification d’authenticité s’effectue ensuite dans son dossier.
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

  function bindContent() {
    const organismSelect = document.querySelector(
      '[name="organisme_id"]'
    );

    if (organismSelect && !editMode) {
      organismSelect.addEventListener("change", async (event) => {
        capture();

        try {
          await loadAccreditations(event.target.value);
          state.accreditation_id = "";
          render();
        } catch (error) {
          showState(
            error?.message || "Impossible de charger les accréditations.",
            { error: true }
          );
        }
      });
    }

    $("#certDocuments")?.addEventListener("change", (event) => {
      pendingFiles = Array.from(event.target.files || []);
    });

    refreshIcons();
  }

  function render() {
    capture();

    $("#certFormContent").innerHTML = renderers[step]();
    $("#certProgress").textContent = `Étape ${step} sur 5`;
    $("#certPrevious").hidden = step === 1;
    $("#certNext").hidden = step === 5;

    document.querySelectorAll("#certStepper button").forEach((button) => {
      const number = Number(button.dataset.step);
      button.classList.toggle("active", number === step);
      button.classList.toggle("completed", number < step);
    });

    bindContent();
  }

  function validateStep() {
    capture();
    hideState();

    if (step === 1) {
      if (!state.identifiant_national.trim()) {
        showState(
          "L’identifiant national est obligatoire.",
          { error: true }
        );
        return false;
      }

      if (!state.entreprise_id || !state.norme_id) {
        showState(
          "L’entreprise et le référentiel sont obligatoires.",
          { error: true }
        );
        return false;
      }
    }

    if (step === 2 && !state.organisme_id) {
      showState(
        "L’organisme certificateur est obligatoire.",
        { error: true }
      );
      return false;
    }

    if (step === 3) {
      if (!state.issue) {
        showState(
          "La date d’obtention est obligatoire.",
          { error: true }
        );
        return false;
      }

      const today = new Date().toISOString().slice(0, 10);

      if (state.issue > today) {
        showState(
          "La date d’obtention ne peut pas être future.",
          { error: true }
        );
        return false;
      }

      const reference = state.effect || state.issue;

      if (state.effect && state.effect < state.issue) {
        $("#dateWarning").hidden = false;
        return false;
      }

      if (state.expiry && state.expiry < reference) {
        $("#dateWarning").hidden = false;
        return false;
      }
    }

    if (
      step === 4
      && !editMode
      && pendingFiles.length === 0
    ) {
      showState(
        "Ajoutez au moins un justificatif avant l’enregistrement.",
        { error: true }
      );
      return false;
    }

    return true;
  }

  function createPayload() {
    return {
      identifiant_national: state.identifiant_national.trim(),
      entreprise_id: state.entreprise_id,
      organisme_id: state.organisme_id,
      accreditation_id: state.accreditation_id || null,
      norme_id: state.norme_id,
      numero_certificat: state.numero_certificat || null,
      portee: state.portee || null,
      date_obtention: state.issue || null,
      date_effet: state.effect || null,
      date_expiration: state.expiry || null,
      statut: "A_VERIFIER",
      certification_strategique:
        Boolean(state.certification_strategique),
      source_donnee: state.source_donnee || "SAISIE_HAUQE",
    };
  }

  function updatePayload() {
    return {
      numero_certificat: state.numero_certificat || null,
      portee: state.portee || null,
      date_obtention: state.issue || null,
      date_effet: state.effect || null,
      date_expiration: state.expiry || null,
      certification_strategique:
        Boolean(state.certification_strategique),
      source_donnee: state.source_donnee || null,
    };
  }

  async function uploadDocuments(id) {
    for (const file of pendingFiles) {
      const body = new FormData();

      body.append("file", file);
      body.append("type_document", "CERTIFICAT");
      body.append("ressource_type", "CERTIFICATION");
      body.append("ressource_id", id);
      body.append("confidentialite", "INTERNE");
      body.append("source", "FORMULAIRE_CERTIFICATION");

      await apiPost(
        "/api/v1/documents/upload",
        body
      );
    }
  }

  async function save(event) {
    capture();

    for (const targetStep of [1, 2, 3, 4]) {
      const previousStep = step;
      step = targetStep;
      render();

      if (!validateStep()) {
        return;
      }

      step = previousStep;
    }

    step = 5;
    render();

    const task = async () => {
      let saved;

      if (editMode) {
        saved = await apiPatch(
          `/api/v1/certifications/${certificationId}`,
          updatePayload()
        );
      } else {
        saved = await apiPost(
          "/api/v1/certifications",
          createPayload()
        );
      }

      await uploadDocuments(saved.id);

      location.hash = `#/certifications/${saved.id}`;
    };

    try {
      if (window.HAUQE_ACTION_LOADER) {
        await window.HAUQE_ACTION_LOADER.run(task, {
          button: event.currentTarget,
          title: editMode
            ? "Mise à jour de la certification"
            : "Création de la certification",
          message: "Enregistrement",
          detail: "Certification et justificatifs sont traités par le backend.",
        });
      } else {
        await task();
      }
    } catch (error) {
      showState(
        error?.message || "Enregistrement impossible.",
        { error: true }
      );
    }
  }

  async function loadEditData() {
    if (!editMode) return;

    const cert = await apiGet(
      `/api/v1/certifications/${certificationId}`
    );

    Object.assign(state, {
      identifiant_national: cert.identifiant_national || "",
      entreprise_id: cert.entreprise_id || "",
      organisme_id: cert.organisme_id || "",
      accreditation_id: cert.accreditation_id || "",
      norme_id: cert.norme_id || "",
      numero_certificat: cert.numero_certificat || "",
      portee: cert.portee || "",
      issue: cert.date_obtention || "",
      effect: cert.date_effet || "",
      expiry: cert.date_expiration || "",
      certification_strategique:
        Boolean(cert.certification_strategique),
      source_donnee: cert.source_donnee || "",
    });

    await loadAccreditations(state.organisme_id);

    $("#certFormMode").textContent = "Modification";
    $("#certFormTitle").textContent =
      `Modifier ${cert.identifiant_national}`;
  }

  async function bootstrap() {
    const api = await import("/static/js/core/api.js");

    apiGet = api.apiGet;
    apiPost = api.apiPost;
    apiPatch = api.apiPatch;

    const task = async () => {
      const [enterpriseData, organismData, normData] =
        await Promise.all([
          apiGet(
            "/api/v1/entreprises?limit=200&offset=0"
          ),
          apiGet(
            "/api/v1/organismes?limit=200&offset=0"
          ),
          apiGet("/api/v1/normes"),
        ]);

      enterprises = enterpriseData.items || [];
      organisms = Array.isArray(organismData)
        ? organismData
        : (organismData.items || []);
      norms = Array.isArray(normData) ? normData : [];

      await loadEditData();

      if (!editMode && state.organisme_id) {
        await loadAccreditations(state.organisme_id);
      }

      render();
    };

    try {
      if (window.HAUQE_ACTION_LOADER) {
        await window.HAUQE_ACTION_LOADER.run(task, {
          title: editMode
            ? "Modification certification"
            : "Nouvelle certification",
          message: "Préparation du formulaire",
          detail: "Chargement des entreprises, organismes et référentiels.",
          minVisibleMs: 320,
        });
      } else {
        await task();
      }
    } catch (error) {
      showState(
        error?.message || "Impossible de préparer le formulaire.",
        { error: true }
      );
      return;
    }

    $("#certNext").addEventListener("click", () => {
      if (!validateStep()) return;

      capture();
      step = Math.min(5, step + 1);
      render();
    });

    $("#certPrevious").addEventListener("click", () => {
      capture();
      step = Math.max(1, step - 1);
      render();
    });

    document.querySelectorAll("#certStepper button").forEach((button) => {
      button.addEventListener("click", () => {
        capture();
        step = Number(button.dataset.step);
        render();
      });
    });

    $("#submitCert").addEventListener("click", save);

    refreshIcons();
  }

  bootstrap();
})();
