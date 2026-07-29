(async function () {
  "use strict";

  const api = await import("/static/js/core/api.js");
  const $ = (s) => document.querySelector(s);
  const $$ = (s) => [...document.querySelectorAll(s)];

  let user = null;
  let readiness = null;
  let catalog = { fields: [], count_resources: [] };
  let rules = [];
  let models = [];
  let selectedRule = null;
  let selectedModel = null;
  let selectedWeights = [];
  let completenessDraft = null;
  let publishTarget = null;
  let cloneSourceRule = null;
  let searchTimer = null;

  let fuccsGrids = [];
  let fuccsActiveGrid = null;
  let fuccsAccessDenied = false;
  let selectedFuccsGrid = null;
  let fuccsRubrics = [];
  let fuccsCriteria = [];
  let editingFuccsGrid = null;
  let editingFuccsRubric = null;
  let editingFuccsCriterion = null;
  let activeFuccsRubric = null;
  let fuccsDeleteTarget = null;

  const fieldReqs = [];
  const countReqs = [];

  function e(v) {
    return String(v ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function icons() {
    window.lucide?.createIcons({ attrs: { "stroke-width": 1.8 } });
  }

  function has(code) {
    return Array.isArray(user?.permissions) && user.permissions.includes(code);
  }

  function state(message, error = false) {
    const node = $("#institutionalApiState");
    node.hidden = false;
    node.className = `dashboard-api-state ${error ? "error" : ""}`.trim();
    node.innerHTML = `
      <i data-lucide="${error ? "triangle-alert" : "info"}"></i>
      <div>
        <strong>${error ? "Opération impossible" : "Information"}</strong>
        <span>${e(message)}</span>
      </div>
    `;
    icons();
  }

  async function run(task, options = {}) {
    if (window.HAUQE_ACTION_LOADER) {
      return window.HAUQE_ACTION_LOADER.run(task, options);
    }
    return task();
  }

  function renderReadiness() {
    const fuccsReadiness = {
      ready: Boolean(fuccsActiveGrid),
      version: fuccsActiveGrid?.version || null,
      approval_reference:
        fuccsActiveGrid?.reference_approbation
        || (fuccsAccessDenied
          ? "Permission FUCCS.LIRE requise"
          : "Aucune grille active publiée"),
    };

    const cards = [
      ["clipboard-check", "COLLECTE_COMPLETUDE", readiness?.collecte_completude],
      ["layout-grid", "Grille FUCCS", fuccsReadiness],
      ["building-2", "Classification entreprise", readiness?.classification_entreprise],
      ["badge-cent", "INFC", readiness?.infc],
    ];

    $("#institutionalReadiness").innerHTML = cards.map(([icon, label, item]) => `
      <article class="readiness-card ${item?.ready ? "ready" : "blocked"}">
        <span><i data-lucide="${icon}"></i></span>
        <div>
          <small>${e(label)}</small>
          <strong>${item?.version ? `v${e(item.version)}` : "Non publié"}</strong>
          <em>${e(item?.approval_reference || item?.calculation_mode || "Paramétrage requis")}</em>
        </div>
        <b>${item?.ready ? "PRÊT" : "BLOQUÉ"}</b>
      </article>
    `).join("");

    const active = readiness?.collecte_completude;
    $("#activeCompletenessStatus").textContent = active?.ready
      ? `Publiée · v${active.version}`
      : "Non publiée";
    $("#activeCompletenessStatus").className = `inst-status ${active?.ready ? "ready" : ""}`;
    icons();
  }

  async function loadReadiness() {
    readiness = await api.apiGet("/api/v1/governance/setup/readiness");
    renderReadiness();
  }

  async function loadCatalog() {
    catalog = await api.apiGet(
      "/api/v1/governance/setup/collecte-completeness/catalog"
    );
  }

  function fieldOptions(selected = []) {
    return catalog.fields.map((field) => `
      <option value="${e(field.name)}" ${selected.includes(field.name) ? "selected" : ""}>
        ${e(field.label)} · ${e(field.name)}
      </option>
    `).join("");
  }

  function countOptions(selected = "") {
    return catalog.count_resources.map((item) => `
      <option value="${e(item.code)}" ${item.code === selected ? "selected" : ""}>
        ${e(item.label)}
      </option>
    `).join("");
  }

  function renderRequirements() {
    $("#fieldRequirements").innerHTML = fieldReqs.length
      ? fieldReqs.map((item) => `
          <article class="requirement-row" data-field-id="${e(item.id)}">
            <label><span>Libellé</span><input data-field-prop="label" value="${e(item.label)}"></label>
            <label class="requirement-fields">
              <span>Champ(s)</span>
              <select data-field-prop="fields" multiple size="4">${fieldOptions(item.fields)}</select>
            </label>
            <label>
              <span>Condition</span>
              <select data-field-prop="match">
                <option value="ALL" ${item.match === "ALL" ? "selected" : ""}>Tous requis</option>
                <option value="ANY" ${item.match === "ANY" ? "selected" : ""}>Au moins un</option>
              </select>
            </label>
            <button class="remove-requirement" type="button" data-remove-field="${e(item.id)}"><i data-lucide="trash-2"></i></button>
          </article>
        `).join("")
      : `<div class="priority-empty compact">Aucune exigence de champ.</div>`;

    $("#countRequirements").innerHTML = countReqs.length
      ? countReqs.map((item) => `
          <article class="requirement-row count" data-count-id="${e(item.id)}">
            <label><span>Libellé</span><input data-count-prop="label" value="${e(item.label)}"></label>
            <label><span>Ressource</span><select data-count-prop="resource">${countOptions(item.resource)}</select></label>
            <label><span>Minimum</span><input data-count-prop="minimum" type="number" min="1" value="${e(item.minimum)}"></label>
            <button class="remove-requirement" type="button" data-remove-count="${e(item.id)}"><i data-lucide="trash-2"></i></button>
          </article>
        `).join("")
      : `<div class="priority-empty compact">Aucune exigence relationnelle.</div>`;

    $$("[data-field-prop]").forEach((node) => {
      node.onchange = () => {
        const row = node.closest("[data-field-id]");
        const item = fieldReqs.find((x) => x.id === row.dataset.fieldId);
        if (!item) return;
        const prop = node.dataset.fieldProp;
        item[prop] = prop === "fields"
          ? [...node.selectedOptions].map((option) => option.value)
          : node.value;
      };
    });

    $$("[data-count-prop]").forEach((node) => {
      node.onchange = () => {
        const row = node.closest("[data-count-id]");
        const item = countReqs.find((x) => x.id === row.dataset.countId);
        if (!item) return;
        item[node.dataset.countProp] = node.dataset.countProp === "minimum"
          ? Number(node.value)
          : node.value;
      };
    });

    $$("[data-remove-field]").forEach((button) => {
      button.onclick = () => {
        const index = fieldReqs.findIndex((x) => x.id === button.dataset.removeField);
        if (index >= 0) fieldReqs.splice(index, 1);
        renderRequirements();
      };
    });

    $$("[data-remove-count]").forEach((button) => {
      button.onclick = () => {
        const index = countReqs.findIndex((x) => x.id === button.dataset.removeCount);
        if (index >= 0) countReqs.splice(index, 1);
        renderRequirements();
      };
    });

    icons();
  }

  function completenessParams() {
    return {
      requirements: [
        ...fieldReqs.map((item) => ({
          type: "FIELD",
          label: item.label.trim() || item.fields.join(" / ") || "Champ obligatoire",
          fields: item.fields,
          match: item.match,
        })),
        ...countReqs.map((item) => ({
          type: "COUNT",
          label: item.label.trim() || item.resource,
          resource: item.resource,
          minimum: Number(item.minimum || 1),
        })),
      ],
      minimum_submission_rate: Number($("#completenessMinimum").value),
    };
  }

  function renderValidation(result) {
    $("#completenessValidationReport").innerHTML = `
      <div class="validation-summary ${result.valid ? "valid" : "invalid"}">
        <span><i data-lucide="${result.valid ? "circle-check-big" : "circle-x"}"></i></span>
        <div>
          <strong>${result.valid ? "Configuration valide" : "Configuration invalide"}</strong>
          <small>${result.valid ? "Prête à être enregistrée en brouillon." : "Corrigez les erreurs avant publication."}</small>
        </div>
      </div>
      ${result.errors?.length ? `<ul class="validation-errors">${result.errors.map((x) => `<li>${e(x)}</li>`).join("")}</ul>` : ""}
      ${result.warnings?.length ? `<ul class="validation-warnings">${result.warnings.map((x) => `<li>${e(x)}</li>`).join("")}</ul>` : ""}
      <details class="normalized-rule"><summary>Paramètres normalisés</summary><pre>${e(JSON.stringify(result.normalized, null, 2))}</pre></details>
    `;
    icons();
  }

  async function validateCompleteness() {
    try {
      const result = await api.apiPost(
        "/api/v1/governance/setup/collecte-completeness/validate",
        { parametres: completenessParams() }
      );
      renderValidation(result);
      return result;
    } catch (error) {
      state(error?.message || "Validation impossible.", true);
      return null;
    }
  }

  async function createCompletenessDraft() {
    const validation = await validateCompleteness();
    if (!validation?.valid) return;

    try {
      completenessDraft = await run(
        () => api.apiPost("/api/v1/governance/rules", {
          logical_code: "COLLECTE_COMPLETUDE",
          famille: $("#completenessFamily").value.trim() || null,
          libelle: $("#completenessLabel").value.trim(),
          description: $("#completenessDescription").value.trim() || null,
          version: $("#completenessVersion").value.trim(),
          parametres: validation.normalized,
          date_debut_effet: null,
        }),
        {
          button: $("#saveCompletenessDraft"),
          title: "COLLECTE_COMPLETUDE",
          message: "Création du brouillon",
        }
      );

      $("#publishCompleteness").hidden = false;
      state(`Brouillon ${completenessDraft.code} créé.`);
      await Promise.all([loadRules(), loadReadiness()]);
    } catch (error) {
      state(error?.message || "Création impossible.", true);
    }
  }

  function openPublish(kind, item) {
    publishTarget = { kind, item };

    const label = kind === "rule"
      ? item.logical_code
      : item.code;

    $("#publishDialogTitle").textContent =
      `Publier ${label} v${item.version}`;

    $("#publishApprovalReference").value = "";
    $("#publishEffectiveDate").value =
      item.date_effet || new Date().toISOString().slice(0, 10);
    $("#publishComment").value = "";
    $("#publishCommentField").hidden =
      ["model", "fuccs"].includes(kind);

    $("#publishDialog").showModal();
    icons();
  }

  async function publish(event) {
    event.preventDefault();
    if (!publishTarget) return;

    try {
      if (publishTarget.kind === "rule") {
        await api.apiPost(
          `/api/v1/governance/rules/${publishTarget.item.id}/publish`,
          {
            reference_approbation: $("#publishApprovalReference").value.trim(),
            date_debut_effet: $("#publishEffectiveDate").value,
            commentaire: $("#publishComment").value.trim() || null,
          }
        );
      } else if (publishTarget.kind === "model") {
        await api.apiPost(
          `/api/v1/scoring/models/${publishTarget.item.id}/publish`,
          {
            reference_approbation:
              $("#publishApprovalReference").value.trim(),
            date_debut_validite: $("#publishEffectiveDate").value,
          }
        );
      } else if (publishTarget.kind === "fuccs") {
        await api.apiPost(
          `/api/v1/fuccs/grilles/${publishTarget.item.id}/publish`,
          {
            reference_approbation:
              $("#publishApprovalReference").value.trim(),
            date_effet: $("#publishEffectiveDate").value,
          }
        );
      }

      $("#publishDialog").close();
      publishTarget = null;
      completenessDraft = null;
      $("#publishCompleteness").hidden = true;

      await Promise.all([
        loadReadiness(),
        loadRules(),
        loadModels(),
        loadFuccsGrids(),
      ]);

      state("Version publiée et journalisée.");
    } catch (error) {
      state(error?.message || "Publication impossible.", true);
    }
  }

  async function loadRules() {
    try {
      rules = await api.apiGet("/api/v1/governance/rules");
      renderRuleList();
    } catch (error) {
      $("#businessRuleList").innerHTML = `<div class="priority-empty">${e(error?.message || "Règles indisponibles.")}</div>`;
    }
  }

  function renderRuleList() {
    const search = $("#ruleSearch")?.value.trim().toLowerCase() || "";
    const status = $("#ruleStatusFilter")?.value || "";
    const visible = rules.filter((item) => {
      if (status && String(item.statut || "").toUpperCase() !== status) return false;
      if (!search) return true;
      return [item.logical_code, item.libelle, item.famille, item.version]
        .filter(Boolean).join(" ").toLowerCase().includes(search);
    });

    $("#businessRuleList").innerHTML = visible.length
      ? visible.map((item) => `
          <button class="institutional-list-row ${selectedRule?.id === item.id ? "active" : ""}" type="button" data-rule-id="${e(item.id)}">
            <span class="rule-icon"><i data-lucide="braces"></i></span>
            <div><strong>${e(item.logical_code)}</strong><small>${e(item.libelle || "—")} · v${e(item.version || "—")}</small></div>
            <span class="inst-status ${String(item.statut || "").toLowerCase()}">${e(item.statut || "—")}</span>
            <i data-lucide="chevron-right"></i>
          </button>
        `).join("")
      : `<div class="priority-empty">Aucune règle.</div>`;

    $$("[data-rule-id]").forEach((button) => {
      button.onclick = () => {
        selectedRule = rules.find((x) => String(x.id) === String(button.dataset.ruleId));
        renderRuleList();
        renderRuleDetail();
      };
    });
    icons();
  }

  function renderRuleDetail() {
    const node = $("#businessRuleDetail");
    if (!selectedRule) {
      node.innerHTML = `<div class="priority-empty">Sélectionnez une version de règle.</div>`;
      return;
    }

    const draft = String(selectedRule.statut || "").toUpperCase() === "BROUILLON";
    const published = String(selectedRule.statut || "").toUpperCase() === "PUBLIE";

    node.innerHTML = `
      <header>
        <div><p class="eyebrow">${e(selectedRule.famille || "RÈGLE")}</p><h2>${e(selectedRule.logical_code)}</h2><p>${e(selectedRule.libelle || "—")}</p></div>
        <span class="inst-status ${String(selectedRule.statut || "").toLowerCase()}">${e(selectedRule.statut || "—")}</span>
      </header>
      <div class="rule-detail-body">
        <div class="cert-info-grid">
          <div class="cert-info"><small>Version</small><strong>${e(selectedRule.version || "—")}</strong></div>
          <div class="cert-info"><small>Code physique</small><strong>${e(selectedRule.code || "—")}</strong></div>
          <div class="cert-info"><small>Début d’effet</small><strong>${e(selectedRule.date_debut_effet || "—")}</strong></div>
          <div class="cert-info"><small>Approbation</small><strong>${e(selectedRule.reference_approbation || "—")}</strong></div>
        </div>
        <label class="json-editor"><span>Paramètres JSON</span><textarea id="selectedRuleJson" rows="14" ${draft ? "" : "readonly"}>${e(JSON.stringify(selectedRule.parametres || {}, null, 2))}</textarea></label>
        <div class="institutional-actions no-pad-actions">
          ${draft && has("GOUVERNANCE.ADMINISTRER_REGLES") ? `<button class="btn btn-outline-secondary app-btn" id="saveSelectedRule" type="button"><i data-lucide="save"></i>Enregistrer</button><button class="btn btn-primary app-btn" id="publishSelectedRule" type="button"><i data-lucide="rocket"></i>Publier</button>` : ""}
          ${published && has("GOUVERNANCE.ADMINISTRER_REGLES") ? `<button class="btn btn-outline-secondary app-btn" id="cloneSelectedRule" type="button"><i data-lucide="copy-plus"></i>Nouvelle version</button>` : ""}
        </div>
      </div>
    `;

    $("#saveSelectedRule")?.addEventListener("click", async () => {
      try {
        const params = JSON.parse($("#selectedRuleJson").value);
        selectedRule = await api.apiPatch(
          `/api/v1/governance/rules/${selectedRule.id}`,
          { parametres: params }
        );
        await loadRules();
        state("Brouillon mis à jour.");
      } catch (error) {
        state(error?.message || "Mise à jour impossible.", true);
      }
    });

    $("#publishSelectedRule")?.addEventListener("click", () => openPublish("rule", selectedRule));
    $("#cloneSelectedRule")?.addEventListener("click", () => openRuleDialog(selectedRule));
    icons();
  }

  function openRuleDialog(source = null) {
    cloneSourceRule = source;
    $("#ruleDialogTitle").textContent = source ? "Nouvelle version" : "Nouvelle règle";
    $("#ruleCode").value = source?.logical_code || "";
    $("#ruleCode").disabled = Boolean(source);
    $("#ruleVersion").value = "";
    $("#ruleFamily").value = source?.famille || "";
    $("#ruleLabel").value = source?.libelle || "";
    $("#ruleDescription").value = source?.description || "";
    $("#ruleParams").value = JSON.stringify(source?.parametres || {}, null, 2);
    $("#ruleDialog").showModal();
    icons();
  }

  async function saveRuleDialog(event) {
    event.preventDefault();
    try {
      let created;
      if (cloneSourceRule) {
        created = await api.apiPost(
          `/api/v1/governance/rules/${cloneSourceRule.id}/clone`,
          {
            version: $("#ruleVersion").value.trim(),
            libelle: $("#ruleLabel").value.trim() || null,
            date_debut_effet: null,
          }
        );
        created = await api.apiPatch(
          `/api/v1/governance/rules/${created.id}`,
          {
            famille: $("#ruleFamily").value.trim() || null,
            description: $("#ruleDescription").value.trim() || null,
            parametres: JSON.parse($("#ruleParams").value || "{}"),
          }
        );
      } else {
        created = await api.apiPost("/api/v1/governance/rules", {
          logical_code: $("#ruleCode").value.trim(),
          famille: $("#ruleFamily").value.trim() || null,
          libelle: $("#ruleLabel").value.trim(),
          description: $("#ruleDescription").value.trim() || null,
          version: $("#ruleVersion").value.trim(),
          parametres: JSON.parse($("#ruleParams").value || "{}"),
          date_debut_effet: null,
        });
      }

      $("#ruleDialog").close();
      $("#ruleCode").disabled = false;
      cloneSourceRule = null;
      selectedRule = created;
      await loadRules();
      renderRuleDetail();
      state("Brouillon de règle créé.");
    } catch (error) {
      state(error?.message || "Création impossible.", true);
    }
  }

  async function loadModels() {
    try {
      const p = new URLSearchParams();
      if ($("#scoringObjectFilter")?.value) p.set("objet_evalue", $("#scoringObjectFilter").value);
      if ($("#scoringStatusFilter")?.value) p.set("statut", $("#scoringStatusFilter").value);
      models = await api.apiGet(`/api/v1/scoring/models${p.toString() ? `?${p}` : ""}`);
      renderModelList();
    } catch (error) {
      $("#scoringModelList").innerHTML = `<div class="priority-empty">${e(error?.message || "Modèles indisponibles.")}</div>`;
    }
  }

  function renderModelList() {
    $("#scoringModelList").innerHTML = models.length
      ? models.map((item) => `
          <button class="institutional-list-row ${selectedModel?.id === item.id ? "active" : ""}" type="button" data-model-id="${e(item.id)}">
            <span class="rule-icon"><i data-lucide="calculator"></i></span>
            <div><strong>${e(item.code || "Modèle")}</strong><small>${e(item.objet_evalue || "—")} · v${e(item.version || "—")}</small></div>
            <span class="inst-status ${String(item.statut || "").toLowerCase()}">${e(item.statut || "—")}</span>
            <i data-lucide="chevron-right"></i>
          </button>
        `).join("")
      : `<div class="priority-empty">Aucun modèle.</div>`;

    $$("[data-model-id]").forEach((button) => {
      button.onclick = async () => {
        selectedModel = models.find((x) => String(x.id) === String(button.dataset.modelId));
        await loadSelectedModel();
        renderModelList();
      };
    });
    icons();
  }

  async function loadSelectedModel() {
    if (!selectedModel) return;
    try {
      selectedModel = await api.apiGet(`/api/v1/scoring/models/${selectedModel.id}`);
      selectedWeights = await api.apiGet(`/api/v1/scoring/models/${selectedModel.id}/weights`);
      renderModelDetail();
    } catch (error) {
      state(error?.message || "Modèle indisponible.", true);
    }
  }

  function renderModelDetail() {
    const node = $("#scoringModelDetail");
    if (!selectedModel) {
      node.innerHTML = `<div class="priority-empty">Sélectionnez ou créez un modèle.</div>`;
      return;
    }

    const draft = String(selectedModel.statut || "").toUpperCase() === "BROUILLON";
    const infcDraft = draft && selectedModel.objet_evalue === "INFC";

    node.innerHTML = `
      <header>
        <div><p class="eyebrow">${e(selectedModel.objet_evalue || "SCORING")}</p><h2>${e(selectedModel.code || "Modèle")}</h2><p>${e(selectedModel.libelle || "—")}</p></div>
        <span class="inst-status ${String(selectedModel.statut || "").toLowerCase()}">${e(selectedModel.statut || "—")}</span>
      </header>
      <div class="rule-detail-body">
        <div class="cert-info-grid">
          <div class="cert-info"><small>Version</small><strong>${e(selectedModel.version || "—")}</strong></div>
          <div class="cert-info"><small>Mode</small><strong>${e(selectedModel.regle_calcul?.calculation_mode || "—")}</strong></div>
          <div class="cert-info"><small>Pondérations</small><strong>${e(selectedModel.ponderations_count || 0)}</strong></div>
          <div class="cert-info"><small>Total</small><strong>${e(selectedModel.total_ponderation || 0)}</strong></div>
        </div>

        <label class="json-editor"><span>Règle de calcul JSON</span><textarea id="selectedModelRule" rows="13" ${draft ? "" : "readonly"}>${e(JSON.stringify(selectedModel.regle_calcul || {}, null, 2))}</textarea></label>

        <section class="weights-admin">
          <div class="weights-admin-head">
            <div><strong>Pondérations / domaines</strong><small>Modifiables sur brouillon.</small></div>
            <div class="weights-buttons">
              ${infcDraft && has("SCORING.ADMINISTRER_MODELE") ? `<button class="btn btn-outline-secondary app-btn" id="loadInfcWeights" type="button"><i data-lucide="layers-3"></i>6 domaines INFC</button>` : ""}
              ${draft && has("SCORING.ADMINISTRER_MODELE") ? `<button class="btn btn-outline-secondary app-btn" id="addWeight" type="button"><i data-lucide="plus"></i>Ajouter</button>` : ""}
            </div>
          </div>
          <div class="weights-list">
            ${selectedWeights.length ? selectedWeights.map((w) => `
              <article class="weight-real-row">
                <div><strong>${e(w.domaine || "Domaine")}</strong><small>${e(w.statut || "—")}</small></div>
                <b>${e(w.valeur ?? "—")}</b>
                ${draft && String(w.statut || "").toUpperCase() !== "INACTIF" ? `<button class="remove-requirement" type="button" data-deactivate-weight="${e(w.id)}"><i data-lucide="ban"></i></button>` : ""}
              </article>
            `).join("") : `<div class="priority-empty compact">Aucune pondération.</div>`}
          </div>
        </section>

        <div class="institutional-actions no-pad-actions">
          ${draft && has("SCORING.ADMINISTRER_MODELE") ? `<button class="btn btn-outline-secondary app-btn" id="saveModelRule" type="button"><i data-lucide="save"></i>Enregistrer</button><button class="btn btn-primary app-btn" id="publishModel" type="button"><i data-lucide="rocket"></i>Publier</button>` : ""}
        </div>
      </div>
    `;

    $("#saveModelRule")?.addEventListener("click", async () => {
      try {
        selectedModel = await api.apiPatch(
          `/api/v1/scoring/models/${selectedModel.id}`,
          { regle_calcul: JSON.parse($("#selectedModelRule").value) }
        );
        await loadModels();
        renderModelDetail();
        state("Règle de calcul mise à jour.");
      } catch (error) {
        state(error?.message || "Mise à jour impossible.", true);
      }
    });

    $("#publishModel")?.addEventListener("click", () => openPublish("model", selectedModel));
    $("#addWeight")?.addEventListener("click", () => {
      $("#weightDomain").value = "";
      $("#weightValue").value = "";
      $("#weightDialog").showModal();
      icons();
    });
    $("#loadInfcWeights")?.addEventListener("click", loadDocumentedInfcWeights);

    $$("[data-deactivate-weight]").forEach((button) => {
      button.onclick = async () => {
        try {
          await api.apiPost(
            `/api/v1/scoring/models/${selectedModel.id}/weights/${button.dataset.deactivateWeight}/deactivate`,
            {}
          );
          await loadSelectedModel();
          state("Pondération désactivée.");
        } catch (error) {
          state(error?.message || "Désactivation impossible.", true);
        }
      };
    });
    icons();
  }

  function openModelDialog(classificationPreset = false) {
    $("#modelObject").value = "CLASSIFICATION_ENTREPRISE";
    $("#modelCode").value = classificationPreset ? "CLASSIFICATION_ENTREPRISE" : "";
    $("#modelVersion").value = "1.0";
    $("#modelLabel").value = classificationPreset ? "Classification globale des entreprises" : "";
    $("#modelDescription").value = classificationPreset
      ? "Référentiel RM-22 à RM-24 : Conforme, À surveiller, Non conforme."
      : "";
    $("#modelMode").value = "DIRECT_SCORE";
    $("#modelRounding").value = "2";
    $("#modelScoreMin").value = "0";
    $("#modelScoreMax").value = "100";
    $("#modelIntervals").value = classificationPreset
      ? JSON.stringify([
          { code: "CONFORME", min: 85 },
          { code: "A_SURVEILLER", min: 60 },
          { code: "NON_CONFORME", default: true },
        ], null, 2)
      : "[]";
    $("#modelDialog").showModal();
    icons();
  }

  async function createModel(event) {
    event.preventDefault();
    try {
      const objectType = $("#modelObject").value;
      const mode = $("#modelMode").value;
      const intervals = JSON.parse($("#modelIntervals").value || "[]");
      const rule = {
        calculation_mode: mode,
        rounding: Number($("#modelRounding").value || 2),
        score_min: Number($("#modelScoreMin").value || 0),
        score_max: Number($("#modelScoreMax").value || 100),
      };
      if (mode !== "DIRECT_SCORE") rule.missing_policy = "REJECT";
      if (objectType === "CLASSIFICATION_ENTREPRISE") rule.classes = intervals;
      else if (intervals.length) rule.levels = intervals;

      selectedModel = await api.apiPost("/api/v1/scoring/models", {
        code: $("#modelCode").value.trim(),
        libelle: $("#modelLabel").value.trim(),
        version: $("#modelVersion").value.trim(),
        objet_evalue: objectType,
        description: $("#modelDescription").value.trim() || null,
        date_debut_validite: null,
        date_fin_validite: null,
        regle_calcul: rule,
      });

      $("#modelDialog").close();
      await loadModels();
      await loadSelectedModel();
      state("Brouillon de modèle créé.");
    } catch (error) {
      state(error?.message || "Création impossible.", true);
    }
  }

  async function addWeight(event) {
    event.preventDefault();
    if (!selectedModel) return;
    try {
      await api.apiPost(`/api/v1/scoring/models/${selectedModel.id}/weights`, {
        domaine: $("#weightDomain").value.trim(),
        valeur: Number($("#weightValue").value),
        periode_debut: null,
        periode_fin: null,
        statut: "ACTIF",
      });
      $("#weightDialog").close();
      await loadSelectedModel();
      state("Pondération ajoutée.");
    } catch (error) {
      state(error?.message || "Ajout impossible.", true);
    }
  }

  async function loadDocumentedInfcWeights() {
    const values = [
      ["AUTHENTICITE", 20],
      ["VALIDITE", 20],
      ["MAINTIEN", 20],
      ["MAITRISE_DOCUMENTAIRE", 15],
      ["TRACABILITE_MAITRISE_OPERATIONNELLE", 15],
      ["SUIVI_RENOUVELLEMENT", 10],
    ];
    const existing = new Set(
      selectedWeights
        .filter((x) => String(x.statut || "").toUpperCase() !== "INACTIF")
        .map((x) => String(x.domaine || "").toUpperCase())
    );

    try {
      for (const [domaine, valeur] of values) {
        if (existing.has(domaine)) continue;
        await api.apiPost(`/api/v1/scoring/models/${selectedModel.id}/weights`, {
          domaine,
          valeur,
          periode_debut: null,
          periode_fin: null,
          statut: "ACTIF",
        });
      }
      await loadSelectedModel();
      state("Six domaines INFC documentés ajoutés au brouillon. La formule et le mapping numérique des niveaux restent à approuver avant publication définitive.");
    } catch (error) {
      state(error?.message || "Chargement impossible.", true);
    }
  }


/* ============================================================
   GRILLES FUCCS
   Le backend existant reste souverain :
   - brouillon modifiable ;
   - version publiée immuable ;
   - clone pour toute nouvelle version ;
   - grille utilisée conservée dans chaque contrôle.
   ============================================================ */

function normalizeFuccsCode(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toUpperCase()
    .replace(/[^A-Z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .replace(/_+/g, "_");
}

function validateFuccsCode(value, label = "Code") {
  const normalized = normalizeFuccsCode(value);

  if (!normalized) {
    throw new Error(`${label} obligatoire.`);
  }

  if (!/^[A-Z][A-Z0-9_]*$/.test(normalized)) {
    throw new Error(
      `${label} invalide : utilisez des majuscules, chiffres et tirets bas.`
    );
  }

  return normalized;
}

function padCode(value) {
  return String(Math.max(1, Number(value) || 1)).padStart(2, "0");
}

function rubricCodeFor(order) {
  const gridCode = normalizeFuccsCode(
    selectedFuccsGrid?.code || $("#fuccsGridCode")?.value || "FUCCS"
  ) || "FUCCS";

  return `${gridCode}_R${padCode(order)}`;
}

function criterionCodeFor(rubric, order) {
  const rubricCode = normalizeFuccsCode(
    rubric?.code || rubricCodeFor(rubric?.ordre_affichage || 1)
  );

  return `${rubricCode}_C${padCode(order)}`;
}

function nextRubricOrder() {
  return Math.max(
    0,
    ...fuccsRubrics.map((item) => Number(item.ordre_affichage) || 0)
  ) + 1;
}

function criteriaForRubric(rubricId) {
  return fuccsCriteria.filter(
    (item) => String(item.rubrique_fuccs_id) === String(rubricId)
  );
}

function nextCriterionOrder(rubricId) {
  return Math.max(
    0,
    ...criteriaForRubric(rubricId).map(
      (item) => Number(item.ordre_affichage) || 0
    )
  ) + 1;
}

function fuccsGridIsDraft(item = selectedFuccsGrid) {
  return String(item?.statut_publication || "").toUpperCase()
    === "BROUILLON";
}

function fuccsGridIsPublished(item = selectedFuccsGrid) {
  return String(item?.statut_publication || "").toUpperCase()
    === "PUBLIE";
}

function fuccsStatusClass(value) {
  return String(value || "").toLowerCase();
}

function totalFuccsWeight() {
  return fuccsCriteria.reduce(
    (sum, item) => sum + Number(item.poids || 0),
    0
  );
}

async function loadFuccsActiveGrid() {
  fuccsAccessDenied = false;

  try {
    fuccsActiveGrid = await api.apiGet("/api/v1/fuccs/grilles/active");
  } catch (error) {
    if (error?.status === 404) {
      fuccsActiveGrid = null;
      return;
    }

    if (error?.status === 403) {
      fuccsAccessDenied = true;
      fuccsActiveGrid = null;
      return;
    }

    throw error;
  }
}

async function loadFuccsGrids() {
  if (!has("FUCCS.LIRE")) {
    fuccsAccessDenied = true;
    fuccsGrids = [];
    fuccsActiveGrid = null;

    $("#fuccsGridList").innerHTML = `
      <div class="priority-empty">
        Permission FUCCS.LIRE requise.
      </div>
    `;

    $("#fuccsGridDetail").innerHTML = `
      <div class="priority-empty">
        Ce compte ne peut pas consulter le référentiel FUCCS.
      </div>
    `;

    renderReadiness();
    return;
  }

  try {
    const [grids] = await Promise.all([
      api.apiGet("/api/v1/fuccs/grilles"),
      loadFuccsActiveGrid(),
    ]);

    fuccsGrids = Array.isArray(grids) ? grids : [];

    if (
      selectedFuccsGrid
      && !fuccsGrids.some(
        (item) => String(item.id) === String(selectedFuccsGrid.id)
      )
    ) {
      selectedFuccsGrid = null;
      fuccsRubrics = [];
      fuccsCriteria = [];
    }

    renderFuccsGridList();

    if (selectedFuccsGrid) {
      selectedFuccsGrid = fuccsGrids.find(
        (item) => String(item.id) === String(selectedFuccsGrid.id)
      ) || null;

      await loadSelectedFuccsGrid();
    } else {
      renderFuccsGridDetail();
    }

    renderReadiness();
  } catch (error) {
    $("#fuccsGridList").innerHTML = `
      <div class="priority-empty">
        ${e(error?.message || "Grilles FUCCS indisponibles.")}
      </div>
    `;
  }
}

function renderFuccsGridList() {
  const search =
    $("#fuccsGridSearch")?.value.trim().toLowerCase() || "";
  const status = $("#fuccsGridStatusFilter")?.value || "";

  const visible = fuccsGrids.filter((item) => {
    if (
      status
      && String(item.statut_publication || "").toUpperCase() !== status
    ) {
      return false;
    }

    if (!search) return true;

    return [
      item.code,
      item.libelle,
      item.version,
      item.reference_approbation,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase()
      .includes(search);
  });

  $("#fuccsGridList").innerHTML = visible.length
    ? visible.map((item) => `
        <button
          class="institutional-list-row fuccs-grid-row
            ${selectedFuccsGrid?.id === item.id ? "active" : ""}"
          type="button"
          data-fuccs-grid="${e(item.id)}"
        >
          <span class="rule-icon">
            <i data-lucide="layout-grid"></i>
          </span>

          <div>
            <strong>${e(item.code || "FUCCS")}</strong>
            <small>
              ${e(item.libelle || "—")} · v${e(item.version || "—")}
            </small>
          </div>

          <div class="fuccs-list-metrics">
            <span>${e(item.rubriques_count || 0)} R</span>
            <span>${e(item.criteres_count || 0)} C</span>
            <b>${e(item.score_maximal_calcule || 0)} pts</b>
          </div>

          <span class="inst-status ${fuccsStatusClass(item.statut_publication)}">
            ${e(item.statut_publication || "—")}
          </span>

          <i data-lucide="chevron-right"></i>
        </button>
      `).join("")
    : `<div class="priority-empty">Aucune version de grille FUCCS.</div>`;

  $$("[data-fuccs-grid]").forEach((button) => {
    button.onclick = async () => {
      selectedFuccsGrid = fuccsGrids.find(
        (item) => String(item.id) === String(button.dataset.fuccsGrid)
      ) || null;

      renderFuccsGridList();
      await loadSelectedFuccsGrid();
    };
  });

  icons();
}

async function loadSelectedFuccsGrid() {
  if (!selectedFuccsGrid) {
    renderFuccsGridDetail();
    return;
  }

  try {
    const [grid, rubrics, criteria] = await Promise.all([
      api.apiGet(`/api/v1/fuccs/grilles/${selectedFuccsGrid.id}`),
      api.apiGet(
        `/api/v1/fuccs/grilles/${selectedFuccsGrid.id}/rubriques`
      ),
      api.apiGet(
        `/api/v1/fuccs/grilles/${selectedFuccsGrid.id}/criteres`
      ),
    ]);

    selectedFuccsGrid = grid;
    fuccsRubrics = Array.isArray(rubrics) ? rubrics : [];
    fuccsCriteria = Array.isArray(criteria) ? criteria : [];

    renderFuccsGridList();
    renderFuccsGridDetail();
  } catch (error) {
    state(
      error?.message || "Impossible de charger la grille FUCCS.",
      true
    );
  }
}

function renderFuccsGridDetail() {
  const node = $("#fuccsGridDetail");

  if (!selectedFuccsGrid) {
    node.innerHTML = `
      <div class="priority-empty">
        Sélectionnez une version de grille FUCCS.
      </div>
    `;
    return;
  }

  const draft = fuccsGridIsDraft();
  const published = fuccsGridIsPublished();
  const canAdmin = has("FUCCS.ADMINISTRER_GRILLE");
  const totalWeight = totalFuccsWeight();

  node.innerHTML = `
    <header class="fuccs-detail-header">
      <div>
        <p class="eyebrow">Référentiel FUCCS</p>
        <h2>
          ${e(selectedFuccsGrid.code || "FUCCS")}
          <span>v${e(selectedFuccsGrid.version || "—")}</span>
        </h2>
        <p>${e(selectedFuccsGrid.libelle || "—")}</p>
      </div>

      <span class="inst-status ${fuccsStatusClass(selectedFuccsGrid.statut_publication)}">
        ${e(selectedFuccsGrid.statut_publication || "—")}
      </span>
    </header>

    <div class="fuccs-detail-body">
      <section class="fuccs-grid-summary">
        <article>
          <span><i data-lucide="folders"></i></span>
          <div>
            <small>Rubriques</small>
            <strong>${e(selectedFuccsGrid.rubriques_count || 0)}</strong>
          </div>
        </article>

        <article>
          <span><i data-lucide="list-checks"></i></span>
          <div>
            <small>Critères</small>
            <strong>${e(selectedFuccsGrid.criteres_count || 0)}</strong>
          </div>
        </article>

        <article>
          <span><i data-lucide="sigma"></i></span>
          <div>
            <small>Score maximal</small>
            <strong>${e(selectedFuccsGrid.score_maximal_calcule || 0)}</strong>
          </div>
        </article>

        <article>
          <span><i data-lucide="weight"></i></span>
          <div>
            <small>Poids renseignés</small>
            <strong>${e(totalWeight.toFixed(2))}</strong>
          </div>
        </article>
      </section>

      <section class="fuccs-version-meta">
        <div>
          <small>Date d’effet</small>
          <strong>${e(selectedFuccsGrid.date_effet || "—")}</strong>
        </div>
        <div>
          <small>Date de fin</small>
          <strong>${e(selectedFuccsGrid.date_fin || "—")}</strong>
        </div>
        <div>
          <small>Référence d’approbation</small>
          <strong>${e(selectedFuccsGrid.reference_approbation || "—")}</strong>
        </div>
      </section>

      <section class="fuccs-codification-card">
        <div class="fuccs-codification-heading">
          <span><i data-lucide="binary"></i></span>
          <div>
            <strong>Schéma de codification appliqué</strong>
            <small>
              La version reste séparée afin de préserver les mêmes codes
              lors du clonage.
            </small>
          </div>
        </div>

        <div class="fuccs-code-chain">
          <code>${e(selectedFuccsGrid.code || "FUCCS")}</code>
          <i data-lucide="arrow-right"></i>
          <code>${e(selectedFuccsGrid.code || "FUCCS")}_R01</code>
          <i data-lucide="arrow-right"></i>
          <code>${e(selectedFuccsGrid.code || "FUCCS")}_R01_C01</code>
        </div>

        <ul>
          <li>Le code de grille reste stable entre les versions.</li>
          <li>Les codes retirés ne doivent pas être réutilisés.</li>
          <li>L’ordre d’affichage reste un champ distinct du code.</li>
        </ul>
      </section>

      <div class="fuccs-grid-actions">
        ${
          draft && canAdmin
            ? `
              <button class="btn btn-outline-secondary app-btn" id="editFuccsGrid" type="button">
                <i data-lucide="pencil"></i>
                Modifier
              </button>

              <button class="btn btn-primary app-btn" id="publishFuccsGrid" type="button">
                <i data-lucide="rocket"></i>
                Publier
              </button>
            `
            : ""
        }

        ${
          !draft && canAdmin
            ? `
              <button class="btn btn-outline-secondary app-btn" id="cloneFuccsGrid" type="button">
                <i data-lucide="copy-plus"></i>
                Nouvelle version
              </button>
            `
            : ""
        }

        ${
          published && canAdmin
            ? `
              <button class="btn btn-outline-danger app-btn" id="retireFuccsGrid" type="button">
                <i data-lucide="archive"></i>
                Retirer
              </button>
            `
            : ""
        }
      </div>

      <section class="fuccs-structure">
        <div class="fuccs-structure-heading">
          <div>
            <h3>Rubriques et critères</h3>
            <p>
              ${
                draft
                  ? "La structure peut encore être modifiée."
                  : "Cette version est verrouillée et consultable en lecture seule."
              }
            </p>
          </div>

          ${
            draft && canAdmin
              ? `
                <button class="btn btn-primary app-btn" id="newFuccsRubric" type="button">
                  <i data-lucide="folder-plus"></i>
                  Ajouter une rubrique
                </button>
              `
              : ""
          }
        </div>

        <div class="fuccs-rubric-list">
          ${
            fuccsRubrics.length
              ? fuccsRubrics.map((rubric) =>
                  renderFuccsRubric(rubric, draft, canAdmin)
                ).join("")
              : `
                <div class="priority-empty compact">
                  Aucune rubrique dans cette version.
                </div>
              `
          }
        </div>
      </section>
    </div>
  `;

  $("#editFuccsGrid")?.addEventListener(
    "click",
    () => openFuccsGridDialog(selectedFuccsGrid)
  );

  $("#publishFuccsGrid")?.addEventListener(
    "click",
    () => openPublish("fuccs", selectedFuccsGrid)
  );

  $("#cloneFuccsGrid")?.addEventListener(
    "click",
    openFuccsCloneDialog
  );

  $("#retireFuccsGrid")?.addEventListener("click", () => {
    $("#fuccsRetireDate").value =
      new Date().toISOString().slice(0, 10);
    $("#fuccsRetireReason").value = "";
    $("#fuccsRetireDialog").showModal();
    icons();
  });

  $("#newFuccsRubric")?.addEventListener(
    "click",
    () => openFuccsRubricDialog()
  );

  $$("[data-edit-fuccs-rubric]").forEach((button) => {
    button.onclick = () => {
      const rubric = fuccsRubrics.find(
        (item) => String(item.id)
          === String(button.dataset.editFuccsRubric)
      );

      openFuccsRubricDialog(rubric);
    };
  });

  $$("[data-delete-fuccs-rubric]").forEach((button) => {
    button.onclick = () => {
      const rubric = fuccsRubrics.find(
        (item) => String(item.id)
          === String(button.dataset.deleteFuccsRubric)
      );

      openFuccsDeleteDialog("rubric", rubric);
    };
  });

  $$("[data-add-fuccs-criterion]").forEach((button) => {
    button.onclick = () => {
      const rubric = fuccsRubrics.find(
        (item) => String(item.id)
          === String(button.dataset.addFuccsCriterion)
      );

      openFuccsCriterionDialog(rubric);
    };
  });

  $$("[data-edit-fuccs-criterion]").forEach((button) => {
    button.onclick = () => {
      const criterion = fuccsCriteria.find(
        (item) => String(item.id)
          === String(button.dataset.editFuccsCriterion)
      );

      const rubric = fuccsRubrics.find(
        (item) => String(item.id)
          === String(criterion?.rubrique_fuccs_id)
      );

      openFuccsCriterionDialog(rubric, criterion);
    };
  });

  $$("[data-delete-fuccs-criterion]").forEach((button) => {
    button.onclick = () => {
      const criterion = fuccsCriteria.find(
        (item) => String(item.id)
          === String(button.dataset.deleteFuccsCriterion)
      );

      const rubric = fuccsRubrics.find(
        (item) => String(item.id)
          === String(criterion?.rubrique_fuccs_id)
      );

      openFuccsDeleteDialog("criterion", criterion, rubric);
    };
  });

  icons();
}

function renderFuccsRubric(rubric, draft, canAdmin) {
  const criteria = criteriaForRubric(rubric.id);

  return `
    <article class="fuccs-rubric-card">
      <header>
        <span class="fuccs-rubric-order">
          ${e(padCode(rubric.ordre_affichage || 1))}
        </span>

        <div>
          <strong>${e(rubric.code || "RUBRIQUE")}</strong>
          <h4>${e(rubric.libelle || "Rubrique sans libellé")}</h4>
          <small>${e(rubric.description || "Aucune description.")}</small>
        </div>

        <div class="fuccs-rubric-count">
          <b>${criteria.length}</b>
          <small>critère(s)</small>
        </div>

        ${
          draft && canAdmin
            ? `
              <div class="fuccs-inline-actions">
                <button
                  type="button"
                  title="Modifier la rubrique"
                  data-edit-fuccs-rubric="${e(rubric.id)}"
                >
                  <i data-lucide="pencil"></i>
                </button>

                <button
                  type="button"
                  title="Supprimer la rubrique"
                  data-delete-fuccs-rubric="${e(rubric.id)}"
                >
                  <i data-lucide="trash-2"></i>
                </button>
              </div>
            `
            : ""
        }
      </header>

      <div class="fuccs-criteria-table">
        <div class="fuccs-criteria-head">
          <span>Code / critère</span>
          <span>Score</span>
          <span>Poids</span>
          <span>Exigences</span>
          <span></span>
        </div>

        ${
          criteria.length
            ? criteria.map((criterion) => `
                <article class="fuccs-criterion-row">
                  <div>
                    <code>${e(criterion.code || "—")}</code>
                    <strong>${e(criterion.libelle || "Critère")}</strong>
                    <small>${e(criterion.description || "")}</small>
                  </div>

                  <b>${e(criterion.score_maximal || 0)}</b>
                  <span>${e(criterion.poids ?? "—")}</span>

                  <div class="fuccs-obligation-tags">
                    ${
                      criterion.commentaire_obligatoire
                        ? `<em><i data-lucide="message-square-text"></i> Commentaire</em>`
                        : ""
                    }
                    ${
                      criterion.preuve_obligatoire
                        ? `<em><i data-lucide="paperclip"></i> Preuve</em>`
                        : ""
                    }
                    ${
                      !criterion.commentaire_obligatoire
                      && !criterion.preuve_obligatoire
                        ? `<small>Aucune</small>`
                        : ""
                    }
                  </div>

                  ${
                    draft && canAdmin
                      ? `
                        <div class="fuccs-inline-actions">
                          <button
                            type="button"
                            title="Modifier le critère"
                            data-edit-fuccs-criterion="${e(criterion.id)}"
                          >
                            <i data-lucide="pencil"></i>
                          </button>

                          <button
                            type="button"
                            title="Supprimer le critère"
                            data-delete-fuccs-criterion="${e(criterion.id)}"
                          >
                            <i data-lucide="trash-2"></i>
                          </button>
                        </div>
                      `
                      : ""
                  }
                </article>
              `).join("")
            : `
              <div class="priority-empty compact">
                Aucun critère dans cette rubrique.
              </div>
            `
        }
      </div>

      ${
        draft && canAdmin
          ? `
            <footer>
              <button
                class="btn btn-outline-secondary app-btn"
                type="button"
                data-add-fuccs-criterion="${e(rubric.id)}"
              >
                <i data-lucide="list-plus"></i>
                Ajouter un critère
              </button>
            </footer>
          `
          : ""
      }
    </article>
  `;
}

function updateFuccsGridCodePreview() {
  const code = normalizeFuccsCode($("#fuccsGridCode").value) || "FUCCS";
  const version = $("#fuccsGridVersion").value.trim() || "1.0";

  $("#fuccsGridCodePreview").textContent =
    `${code} · v${version}`;
}

function openFuccsGridDialog(source = null) {
  editingFuccsGrid = source;

  $("#fuccsGridDialogTitle").textContent =
    source ? "Modifier le brouillon" : "Nouvelle grille";

  $("#fuccsGridCode").value = source?.code || "FUCCS";
  $("#fuccsGridCode").disabled = Boolean(source);
  $("#fuccsGridVersion").value = source?.version || "1.0";
  $("#fuccsGridLabel").value = source?.libelle || "";
  $("#fuccsGridEffectiveDate").value = source?.date_effet || "";

  updateFuccsGridCodePreview();
  $("#fuccsGridDialog").showModal();
  icons();
}

async function saveFuccsGrid(event) {
  event.preventDefault();

  try {
    const code = validateFuccsCode(
      $("#fuccsGridCode").value,
      "Code de grille"
    );

    const payload = {
      libelle: $("#fuccsGridLabel").value.trim(),
      version: $("#fuccsGridVersion").value.trim(),
      date_effet: $("#fuccsGridEffectiveDate").value || null,
    };

    if (editingFuccsGrid) {
      selectedFuccsGrid = await api.apiPatch(
        `/api/v1/fuccs/grilles/${editingFuccsGrid.id}`,
        payload
      );
    } else {
      selectedFuccsGrid = await api.apiPost(
        "/api/v1/fuccs/grilles",
        {
          code,
          ...payload,
        }
      );
    }

    $("#fuccsGridDialog").close();
    editingFuccsGrid = null;

    await loadFuccsGrids();
    state("Brouillon de grille FUCCS enregistré.");
  } catch (error) {
    state(error?.message || "Enregistrement impossible.", true);
  }
}

function suggestNextVersion(value) {
  const parts = String(value || "1.0").split(".");
  const major = Number(parts[0]) || 1;
  const minor = Number(parts[1]) || 0;

  return `${major}.${minor + 1}`;
}

function openFuccsCloneDialog() {
  if (!selectedFuccsGrid) return;

  $("#fuccsCloneCode").value =
    normalizeFuccsCode(selectedFuccsGrid.code || "FUCCS");
  $("#fuccsCloneVersion").value =
    suggestNextVersion(selectedFuccsGrid.version);
  $("#fuccsCloneLabel").value =
    selectedFuccsGrid.libelle || "";
  $("#fuccsCloneEffectiveDate").value = "";

  $("#fuccsCloneDialog").showModal();
  icons();
}

async function cloneFuccsGrid(event) {
  event.preventDefault();
  if (!selectedFuccsGrid) return;

  try {
    selectedFuccsGrid = await api.apiPost(
      `/api/v1/fuccs/grilles/${selectedFuccsGrid.id}/clone`,
      {
        code: validateFuccsCode(
          $("#fuccsCloneCode").value,
          "Code de grille"
        ),
        libelle: $("#fuccsCloneLabel").value.trim(),
        version: $("#fuccsCloneVersion").value.trim(),
        date_effet: $("#fuccsCloneEffectiveDate").value || null,
      }
    );

    $("#fuccsCloneDialog").close();
    await loadFuccsGrids();
    state(
      "Nouvelle version brouillon créée avec les mêmes codes de rubriques et critères."
    );
  } catch (error) {
    state(error?.message || "Clonage impossible.", true);
  }
}

function updateFuccsRubricCodePreview() {
  const code = normalizeFuccsCode($("#fuccsRubricCode").value)
    || rubricCodeFor($("#fuccsRubricOrder").value);

  $("#fuccsRubricCodePreview").textContent = code;
}

function generateFuccsRubricCode() {
  $("#fuccsRubricCode").value =
    rubricCodeFor($("#fuccsRubricOrder").value);

  updateFuccsRubricCodePreview();
}

function openFuccsRubricDialog(source = null) {
  editingFuccsRubric = source;

  $("#fuccsRubricDialogTitle").textContent =
    source ? "Modifier la rubrique" : "Nouvelle rubrique";

  $("#fuccsRubricOrder").value =
    source?.ordre_affichage || nextRubricOrder();
  $("#fuccsRubricCode").value =
    source?.code || rubricCodeFor($("#fuccsRubricOrder").value);
  $("#fuccsRubricLabel").value = source?.libelle || "";
  $("#fuccsRubricDescription").value =
    source?.description || "";

  updateFuccsRubricCodePreview();
  $("#fuccsRubricDialog").showModal();
  icons();
}

async function saveFuccsRubric(event) {
  event.preventDefault();
  if (!selectedFuccsGrid) return;

  try {
    const code = validateFuccsCode(
      $("#fuccsRubricCode").value,
      "Code de rubrique"
    );

    const duplicate = fuccsRubrics.some(
      (item) =>
        normalizeFuccsCode(item.code) === code
        && String(item.id) !== String(editingFuccsRubric?.id || "")
    );

    if (duplicate) {
      throw new Error(
        `Le code de rubrique ${code} existe déjà dans cette grille.`
      );
    }

    const payload = {
      code,
      libelle: $("#fuccsRubricLabel").value.trim(),
      description:
        $("#fuccsRubricDescription").value.trim() || null,
      ordre_affichage: Number($("#fuccsRubricOrder").value),
    };

    if (editingFuccsRubric) {
      await api.apiPatch(
        `/api/v1/fuccs/grilles/${selectedFuccsGrid.id}`
        + `/rubriques/${editingFuccsRubric.id}`,
        payload
      );
    } else {
      await api.apiPost(
        `/api/v1/fuccs/grilles/${selectedFuccsGrid.id}/rubriques`,
        payload
      );
    }

    $("#fuccsRubricDialog").close();
    editingFuccsRubric = null;
    await loadSelectedFuccsGrid();
    state("Rubrique FUCCS enregistrée.");
  } catch (error) {
    state(error?.message || "Enregistrement impossible.", true);
  }
}

function updateFuccsCriterionCodePreview() {
  const code = normalizeFuccsCode($("#fuccsCriterionCode").value)
    || criterionCodeFor(
      activeFuccsRubric,
      $("#fuccsCriterionOrder").value
    );

  $("#fuccsCriterionCodePreview").textContent = code;
}

function generateFuccsCriterionCode() {
  if (!activeFuccsRubric) return;

  $("#fuccsCriterionCode").value =
    criterionCodeFor(
      activeFuccsRubric,
      $("#fuccsCriterionOrder").value
    );

  updateFuccsCriterionCodePreview();
}

function openFuccsCriterionDialog(rubric, source = null) {
  if (!rubric) return;

  activeFuccsRubric = rubric;
  editingFuccsCriterion = source;

  $("#fuccsCriterionDialogTitle").textContent =
    source ? "Modifier le critère" : "Nouveau critère";

  $("#fuccsCriterionRubricLabel").value =
    `${rubric.code || "RUBRIQUE"} · ${rubric.libelle || ""}`;

  $("#fuccsCriterionOrder").value =
    source?.ordre_affichage || nextCriterionOrder(rubric.id);

  $("#fuccsCriterionCode").value =
    source?.code
    || criterionCodeFor(
      rubric,
      $("#fuccsCriterionOrder").value
    );

  $("#fuccsCriterionLabel").value = source?.libelle || "";
  $("#fuccsCriterionDescription").value =
    source?.description || "";
  $("#fuccsCriterionMaxScore").value =
    source?.score_maximal ?? "";
  $("#fuccsCriterionWeight").value =
    source?.poids ?? "";
  $("#fuccsCriterionCommentRequired").checked =
    Boolean(source?.commentaire_obligatoire);
  $("#fuccsCriterionProofRequired").checked =
    Boolean(source?.preuve_obligatoire);

  updateFuccsCriterionCodePreview();
  $("#fuccsCriterionDialog").showModal();
  icons();
}

async function saveFuccsCriterion(event) {
  event.preventDefault();

  if (!selectedFuccsGrid || !activeFuccsRubric) return;

  try {
    const code = validateFuccsCode(
      $("#fuccsCriterionCode").value,
      "Code de critère"
    );

    const duplicate = fuccsCriteria.some(
      (item) =>
        normalizeFuccsCode(item.code) === code
        && String(item.id) !== String(editingFuccsCriterion?.id || "")
    );

    if (duplicate) {
      throw new Error(
        `Le code de critère ${code} existe déjà dans cette grille.`
      );
    }

    const weightValue =
      $("#fuccsCriterionWeight").value.trim();

    const payload = {
      code,
      libelle: $("#fuccsCriterionLabel").value.trim(),
      description:
        $("#fuccsCriterionDescription").value.trim() || null,
      score_maximal: Number($("#fuccsCriterionMaxScore").value),
      poids: weightValue === "" ? null : Number(weightValue),
      ordre_affichage:
        Number($("#fuccsCriterionOrder").value),
      commentaire_obligatoire:
        $("#fuccsCriterionCommentRequired").checked,
      preuve_obligatoire:
        $("#fuccsCriterionProofRequired").checked,
    };

    const base =
      `/api/v1/fuccs/grilles/${selectedFuccsGrid.id}`
      + `/rubriques/${activeFuccsRubric.id}/criteres`;

    if (editingFuccsCriterion) {
      await api.apiPatch(
        `${base}/${editingFuccsCriterion.id}`,
        payload
      );
    } else {
      await api.apiPost(base, payload);
    }

    $("#fuccsCriterionDialog").close();
    editingFuccsCriterion = null;
    activeFuccsRubric = null;

    await loadSelectedFuccsGrid();
    state("Critère FUCCS enregistré.");
  } catch (error) {
    state(error?.message || "Enregistrement impossible.", true);
  }
}

function openFuccsDeleteDialog(kind, item, rubric = null) {
  if (!item) return;

  fuccsDeleteTarget = { kind, item, rubric };

  $("#fuccsDeleteTitle").textContent =
    kind === "rubric"
      ? "Supprimer la rubrique"
      : "Supprimer le critère";

  $("#fuccsDeleteLabel").textContent =
    `${item.code || "—"} · ${item.libelle || "—"}`;

  $("#fuccsDeleteMessage").textContent =
    kind === "rubric"
      ? "Les critères contenus dans cette rubrique seront également supprimés du brouillon."
      : "Le critère sera supprimé uniquement de cette version brouillon.";

  $("#fuccsDeleteDialog").showModal();
  icons();
}

async function deleteFuccsDraftItem(event) {
  event.preventDefault();

  if (!selectedFuccsGrid || !fuccsDeleteTarget) return;

  const { kind, item, rubric } = fuccsDeleteTarget;

  try {
    if (kind === "rubric") {
      await api.apiDelete(
        `/api/v1/fuccs/grilles/${selectedFuccsGrid.id}`
        + `/rubriques/${item.id}`
      );
    } else {
      await api.apiDelete(
        `/api/v1/fuccs/grilles/${selectedFuccsGrid.id}`
        + `/rubriques/${rubric.id}/criteres/${item.id}`
      );
    }

    $("#fuccsDeleteDialog").close();
    fuccsDeleteTarget = null;

    await loadSelectedFuccsGrid();
    state(
      kind === "rubric"
        ? "Rubrique supprimée du brouillon."
        : "Critère supprimé du brouillon."
    );
  } catch (error) {
    state(error?.message || "Suppression impossible.", true);
  }
}

async function retireFuccsGrid(event) {
  event.preventDefault();
  if (!selectedFuccsGrid) return;

  try {
    await api.apiPost(
      `/api/v1/fuccs/grilles/${selectedFuccsGrid.id}/retire`,
      {
        date_fin: $("#fuccsRetireDate").value,
        motif: $("#fuccsRetireReason").value.trim(),
      }
    );

    $("#fuccsRetireDialog").close();
    await loadFuccsGrids();
    state("Grille FUCCS retirée et conservée dans l’historique.");
  } catch (error) {
    state(error?.message || "Retrait impossible.", true);
  }
}

  function switchTab(tab) {
    $$("[data-inst-tab]").forEach((button) => {
      button.classList.toggle("active", button.dataset.instTab === tab);
    });
    $("#completenessTab").hidden = tab !== "completeness";
    $("#rulesTab").hidden = tab !== "rules";
    $("#scoringTab").hidden = tab !== "scoring";
    $("#fuccsTab").hidden = tab !== "fuccs";

    if (tab === "fuccs") {
      loadFuccsGrids();
    }
  }

  function bind() {
    $("#addFieldRequirement").onclick = () => {
      fieldReqs.push({ id: crypto.randomUUID(), label: "", fields: [], match: "ALL" });
      renderRequirements();
    };
    $("#addCountRequirement").onclick = () => {
      countReqs.push({
        id: crypto.randomUUID(),
        label: "",
        resource: catalog.count_resources?.[0]?.code || "DOCUMENTS",
        minimum: 1,
      });
      renderRequirements();
    };

    $("#validateCompleteness").onclick = validateCompleteness;
    $("#saveCompletenessDraft").onclick = createCompletenessDraft;
    $("#publishCompleteness").onclick = () => {
      if (completenessDraft) openPublish("rule", completenessDraft);
    };

    $("#newGenericRule").onclick = () => openRuleDialog();
    $("#ruleForm").onsubmit = saveRuleDialog;
    $("#publishForm").onsubmit = publish;

    $("#newScoringModel").onclick = () => openModelDialog(false);
    $("#prefillClassificationReference").onclick = () => openModelDialog(true);
    $("#modelForm").onsubmit = createModel;
    $("#weightForm").onsubmit = addWeight;

    $("#scoringObjectFilter").onchange = loadModels;
    $("#scoringStatusFilter").onchange = loadModels;
    $("#ruleStatusFilter").onchange = renderRuleList;

    $("#newFuccsGrid").onclick = () => openFuccsGridDialog();
    $("#fuccsGridForm").onsubmit = saveFuccsGrid;
    $("#fuccsCloneForm").onsubmit = cloneFuccsGrid;
    $("#fuccsRubricForm").onsubmit = saveFuccsRubric;
    $("#fuccsCriterionForm").onsubmit = saveFuccsCriterion;
    $("#fuccsRetireForm").onsubmit = retireFuccsGrid;
    $("#fuccsDeleteForm").onsubmit = deleteFuccsDraftItem;

    $("#fuccsGridCode").oninput = (event) => {
      event.target.value = normalizeFuccsCode(event.target.value);
      updateFuccsGridCodePreview();
    };
    $("#fuccsGridVersion").oninput = updateFuccsGridCodePreview;

    $("#fuccsRubricOrder").oninput = () => {
      if (!editingFuccsRubric) generateFuccsRubricCode();
      else updateFuccsRubricCodePreview();
    };
    $("#fuccsRubricCode").oninput = (event) => {
      event.target.value = normalizeFuccsCode(event.target.value);
      updateFuccsRubricCodePreview();
    };
    $("#generateFuccsRubricCode").onclick =
      generateFuccsRubricCode;

    $("#fuccsCriterionOrder").oninput = () => {
      if (!editingFuccsCriterion) generateFuccsCriterionCode();
      else updateFuccsCriterionCodePreview();
    };
    $("#fuccsCriterionCode").oninput = (event) => {
      event.target.value = normalizeFuccsCode(event.target.value);
      updateFuccsCriterionCodePreview();
    };
    $("#generateFuccsCriterionCode").onclick =
      generateFuccsCriterionCode;

    $("#fuccsGridStatusFilter").onchange = renderFuccsGridList;
    $("#fuccsGridSearch").oninput = () => {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(renderFuccsGridList, 200);
    };
    $("#ruleSearch").oninput = () => {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(renderRuleList, 200);
    };

    $("#refreshInstitutional").onclick = async (event) => {
      try {
        await run(
          () => Promise.all([
            loadReadiness(),
            loadRules(),
            loadModels(),
            loadFuccsGrids(),
          ]),
          { button: event.currentTarget, title: "Paramétrage institutionnel", message: "Actualisation" }
        );
      } catch (error) {
        state(error?.message || "Actualisation impossible.", true);
      }
    };

    $$("[data-inst-tab]").forEach((button) => {
      button.onclick = () => switchTab(button.dataset.instTab);
    });

    $$("[data-close-inst-dialog]").forEach((button) => {
      button.onclick = () => document.getElementById(button.dataset.closeInstDialog)?.close();
    });
  }

  try {
    user = await api.apiGet("/api/v1/me");
    if (!has("GOUVERNANCE.LIRE")) {
      state("Le compte courant ne possède pas GOUVERNANCE.LIRE.", true);
      return;
    }

    bind();

    const canGovernRules = has("GOUVERNANCE.ADMINISTRER_REGLES");
    const canAdminScoring = has("SCORING.ADMINISTRER_MODELE");
    const canAdminFuccs = has("FUCCS.ADMINISTRER_GRILLE");

    $("#newGenericRule").hidden = !canGovernRules;
    $("#validateCompleteness").hidden = !canGovernRules;
    $("#saveCompletenessDraft").hidden = !canGovernRules;
    $("#addFieldRequirement").hidden = !canGovernRules;
    $("#addCountRequirement").hidden = !canGovernRules;

    $("#newScoringModel").hidden = !canAdminScoring;
    $("#prefillClassificationReference").hidden = !canAdminScoring;
    $("#newFuccsGrid").hidden = !canAdminFuccs;

    await Promise.all([
      loadReadiness(),
      loadCatalog(),
      loadRules(),
      loadModels(),
      loadFuccsGrids(),
    ]);

    renderRequirements();
  } catch (error) {
    state(error?.message || "Erreur de chargement.", true);
  }

  icons();
})();
