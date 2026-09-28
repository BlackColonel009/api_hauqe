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
  let snccDraft = null;
  let publishTarget = null;
  let cloneSourceRule = null;
  let selectedCodificationRule = null;
  let editingCodificationRule = null;
  let cloneSourceCodificationRule = null;
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

  // La page reconstruit de nombreux boutons (règles, modèles, pondérations et
  // FUCCS) après recherche ou changement d'onglet. Chaque bouton est isolé du
  // chargeur global afin que son écouteur local réponde au premier clic.
  function stabilizeRuleButtons(root = document) {
    root.querySelectorAll(".rules-page button").forEach((button) => {
      button.setAttribute("data-no-action-loader", "true");
      button.classList.add("rules-action-button");
    });
  }

  // Même contrat que Gestion des campagnes : le bouton réel reçoit un seul
  // écouteur local et est explicitement ignoré du chargeur global. Le cloner
  // au moment du clic créait une fenêtre où l'action pouvait être perdue après
  // un rendu ou un changement d'onglet.
  function bindDirectRuleButtons(selector, handler, root = document) {
    root.querySelectorAll(selector).forEach((source) => {
      if (!(source instanceof HTMLButtonElement)) return;
      if (source.dataset.rulesDirectButton === "true") return;

      source.setAttribute("data-no-action-loader", "true");
      source.dataset.rulesDirectButton = "true";
      source.classList.add("rules-action-button");
      source.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation();
        void Promise.resolve(handler(source, event)).catch((error) => {
          console.error("[HAUQE Règles & codification] Action impossible", error);
          state(error?.message || "Opération impossible.", true);
        });
      });
    });
  }

  function icons() {
    stabilizeRuleButtons();
    window.lucide?.createIcons({ attrs: { "stroke-width": 1.8 } });
  }

  function createClientId(prefix = "item") {
    if (globalThis.crypto?.randomUUID) {
      return globalThis.crypto.randomUUID();
    }
    return [
      prefix,
      Date.now().toString(36),
      Math.random().toString(36).slice(2, 10),
    ].join("-");
  }

  function has(code) {
    return Array.isArray(user?.permissions) && user.permissions.includes(code);
  }

  function state(message, error = false) {
    const node = $("#institutionalApiState");

    if (!node) {
      console[error ? "error" : "info"](
        "[HAUQE Règles & codification]",
        message
      );
      return;
    }

    node.hidden = false;
    node.className =
      `dashboard-api-state ${error ? "error" : ""}`.trim();
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

    const codificationPublished = (objectType) => rules.find((item) =>
      String(item.logical_code || "").toUpperCase()
        === `CODIFICATION_BNEC_${objectType}`
      && String(item.statut || "").toUpperCase() === "PUBLIE"
    );
    const enterpriseCodeModel = codificationPublished("ENTREPRISE");
    const certificationCodeModel = codificationPublished("CERTIFICATION");
    const codificationReadiness = {
      ready: Boolean(enterpriseCodeModel && certificationCodeModel),
      version: enterpriseCodeModel && certificationCodeModel
        ? `${enterpriseCodeModel.version} · ${certificationCodeModel.version}`
        : null,
      approval_reference: enterpriseCodeModel && certificationCodeModel
        ? "Entreprise + certification publiées"
        : "Modèles entreprise et certification requis",
    };

    const cards = [
      ["clipboard-check", "COLLECTE_COMPLETUDE", readiness?.collecte_completude],
      ["fingerprint", "Codification BNEC", codificationReadiness],
      ["layout-grid", "Grille FUCCS", fuccsReadiness],
      ["building-2", "Classification entreprise", readiness?.classification_entreprise],
      ["badge-cent", "INFC", readiness?.infc],
      ["trophy", "Classement SNCC", readiness?.sncc],
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

    bindDirectRuleButtons("[data-remove-field]", (button) => {
        const index = fieldReqs.findIndex((x) => x.id === button.dataset.removeField);
        if (index >= 0) fieldReqs.splice(index, 1);
        renderRequirements();
    });

    bindDirectRuleButtons("[data-remove-count]", (button) => {
        const index = countReqs.findIndex((x) => x.id === button.dataset.removeCount);
        if (index >= 0) countReqs.splice(index, 1);
        renderRequirements();
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
      snccDraft = null;
      updateSnccPublishState();

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
      renderCodificationModels();
      restoreSnccDraft();
      renderSnccMatrixStatus();
      renderReadiness();
    } catch (error) {
      $("#businessRuleList").innerHTML = `<div class="priority-empty">${e(error?.message || "Règles indisponibles.")}</div>`;
    }
  }

  function renderRuleList() {
    const search = $("#ruleSearch")?.value.trim().toLowerCase() || "";
    const status = $("#ruleStatusFilter")?.value || "";
    const visible = rules.filter((item) => {
      const logicalCode = String(item.logical_code || "").toUpperCase();
      if (logicalCode.startsWith("CODIFICATION_BNEC_") || logicalCode === "SNCC_CLASSIFICATION_MATRIX") return false;
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

    bindDirectRuleButtons("[data-rule-id]", (button) => {
        selectedRule = rules.find((x) => String(x.id) === String(button.dataset.ruleId));
        renderRuleList();
        renderRuleDetail();
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

    bindDirectRuleButtons("#saveSelectedRule", async () => {
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

    bindDirectRuleButtons("#publishSelectedRule", () => openPublish("rule", selectedRule));
    bindDirectRuleButtons("#cloneSelectedRule", () => openRuleDialog(selectedRule));
    icons();
  }

  const rulePresets = {
    cert_expiration: {
      code: "CERTIFICATION_EXPIRATION_ALERTS",
      version: "1.0",
      family: "CERTIFICATIONS",
      label: "Alertes avant expiration d’une certification",
      description: "Génère des échéances et des alertes graduelles avant la date d’expiration d’une certification active.",
      params: {
        active: true,
        date_source: "date_expiration",
        thresholds_days: [180, 90, 30, 0],
        create_deadline: true,
        create_alert: true,
        notify_responsible: true,
      },
    },
    verification_delay: {
      code: "VERIFICATION_PROCESSING_DELAY",
      version: "1.0",
      family: "VERIFICATIONS",
      label: "Délai de traitement d’un dossier de vérification",
      description: "Crée une échéance et une alerte pour le vérificateur lorsque des dates de début et de fin sont renseignées sur l’affectation.",
      params: {
        active: true,
        start_date_field: "date_debut",
        due_date_field: "date_fin",
        reminder_days: [7, 3, 1],
        notify_assignee: true,
        channels: ["IN_APP", "EMAIL"],
      },
    },
    data_quality: {
      code: "DATA_COMPLETENESS_CONTROL",
      version: "1.0",
      family: "QUALITE_DONNEES",
      label: "Contrôle de complétude des données essentielles",
      description: "Signale les dossiers dont les informations obligatoires sont absentes ou incomplètes avant validation.",
      params: {
        active: true,
        minimum_completeness_percent: 80,
        blocking_fields: ["identifiant_national", "raison_sociale", "statut"],
        create_quality_issue: true,
        blocking: false,
      },
    },
    infc_validation: {
      code: "INFC_VALIDATION_THRESHOLD",
      version: "1.0",
      family: "INFC",
      label: "Seuil de validation d’un résultat INFC",
      description: "Détermine le seuil minimal indicatif permettant de présenter un calcul INFC à la validation de l’agent habilité.",
      params: {
        active: true,
        minimum_score: 70,
        maximum_score: 100,
        require_manual_validation: true,
        decision_code: "A_VALIDER",
      },
    },
  };

  function applyRulePreset(code) {
    const preset = rulePresets[code];
    if (!preset) return;
    $("#ruleCode").value = preset.code;
    $("#ruleVersion").value = preset.version;
    $("#ruleFamily").value = preset.family;
    $("#ruleLabel").value = preset.label;
    $("#ruleDescription").value = preset.description;
    $("#ruleParams").value = JSON.stringify(preset.params, null, 2);
  }

  function openRuleDialog(source = null) {
    cloneSourceRule = source;
    $("#ruleDialogTitle").textContent = source ? "Nouvelle version" : "Nouvelle règle";
    $("#ruleCode").value = source?.logical_code || "";
    $("#ruleCode").disabled = Boolean(source);
    $("#ruleVersion").value = source ? "" : "1.0";
    $("#ruleFamily").value = source?.famille || "";
    $("#ruleLabel").value = source?.libelle || "";
    $("#ruleDescription").value = source?.description || "";
    $("#ruleParams").value = JSON.stringify(source?.parametres || { active: true }, null, 2);
    $("#rulePreset").value = "";
    $("#rulePresetField").hidden = Boolean(source);
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

  const SNCC_TEMPLATE_ROWS = [
    { classe: "A+", label: "Très favorable", min: 90, max: 100, statut: "VA", risque: "R1" },
    { classe: "A", label: "Favorable", min: 75, max: 89.99, statut: "VA", risque: "R1" },
    { classe: "B", label: "À suivre", min: 60, max: 74.99, statut: "RE", risque: "R2" },
    { classe: "C", label: "Fragile", min: 40, max: 59.99, statut: "RE", risque: "R3" },
    { classe: "D", label: "Critique", min: 0, max: 39.99, statut: "RE", risque: "R5" },
  ];
  const SNCC_STATUS_OPTIONS = [
    ["VA", "VA — valide"], ["RE", "RE — réservé"],
  ];
  const SNCC_RISK_OPTIONS = [
    ["R1", "R1 — faible"], ["R2", "R2 — modéré"],
    ["R3", "R3 — significatif"], ["R4", "R4 — élevé"],
    ["R5", "R5 — critique"],
  ];

  function selectOptions(items, selected) {
    return items.map(([value, label]) => `<option value="${value}" ${value === selected ? "selected" : ""}>${label}</option>`).join("");
  }

  function renderSnccMatrix(rows = SNCC_TEMPLATE_ROWS) {
    const target = $("#snccMatrixRows");
    if (!target) return;
    target.innerHTML = rows.length ? rows.map((row) => `
      <tr data-sncc-class="${e(row.classe)}">
        <td><strong>${e(row.classe)}</strong></td>
        <td><small>${e(row.label)}</small></td>
        <td><input data-sncc-min type="number" min="0" max="100" step="0.01" value="${e(row.min)}" aria-label="Score minimum ${e(row.classe)}"></td>
        <td><input data-sncc-max type="number" min="0" max="100" step="0.01" value="${e(row.max)}" aria-label="Score maximum ${e(row.classe)}"></td>
        <td><select data-sncc-status aria-label="Statut normal ${e(row.classe)}">${selectOptions(SNCC_STATUS_OPTIONS, row.statut)}</select></td>
        <td><select data-sncc-risk aria-label="Risque ${e(row.classe)}">${selectOptions(SNCC_RISK_OPTIONS, row.risque)}</select></td>
      </tr>
    `).join("") : '<tr><td colspan="6" class="sncc-matrix-empty">Cliquez sur « Charger le préremplissage » pour voir les cinq classes proposées.</td></tr>';
    icons();
  }

  function updateSnccPrefillState(message, loaded = false) {
    const node = $("#snccPrefillState");
    if (!node) return;
    node.textContent = message;
    node.classList.toggle("loaded", loaded);
  }

  function updateSnccPublishState() {
    const button = $("#publishSnccMatrix");
    const guidance = $("#snccPublishGuidance");
    if (!button) return;
    const canPublish = has("GOUVERNANCE.ADMINISTRER_REGLES");
    button.hidden = false;
    button.disabled = !snccDraft?.id || !canPublish;
    button.title = !canPublish
      ? "Permission de publication requise"
      : snccDraft?.id
        ? "Publier le brouillon SNCC après approbation HAUQE"
        : "Enregistrez d’abord un brouillon SNCC";
    if (guidance) guidance.textContent = !canPublish
      ? "La publication est réservée à l’administration des règles."
      : snccDraft?.id
        ? `Brouillon v${snccDraft.version || "—"} prêt : la publication demandera une référence d’approbation.`
        : "Publication disponible après l’enregistrement du brouillon.";
  }

  function snccMatrixPayload() {
    const errors = [];
    const rows = $$("#snccMatrixRows tr").map((row) => {
      const minimum = Number(row.querySelector("[data-sncc-min]")?.value);
      const maximum = Number(row.querySelector("[data-sncc-max]")?.value);
      const classe = row.dataset.snccClass || "";
      const statut = row.querySelector("[data-sncc-status]")?.value || "";
      const risque = row.querySelector("[data-sncc-risk]")?.value || "";
      if (!Number.isFinite(minimum) || !Number.isFinite(maximum)) {
        errors.push(`Classe ${classe} : les deux bornes sont obligatoires.`);
      } else if (minimum < 0 || maximum > 100 || minimum > maximum) {
        errors.push(`Classe ${classe} : plage de score incohérente.`);
      }
      return { min: minimum, max: maximum, classe, statut_administratif: statut, niveau_risque: risque };
    });
    const ordered = [...rows].sort((a, b) => a.min - b.min);
    if (ordered.length !== 5) errors.push("Les cinq classes SNCC sont requises.");
    if (ordered.length && ordered[0].min !== 0) errors.push("La première plage doit commencer à 0.");
    if (ordered.length && ordered.at(-1).max !== 100) errors.push("La dernière plage doit se terminer à 100.");
    ordered.slice(1).forEach((current, index) => {
      const previous = ordered[index];
      if (current.min <= previous.max) errors.push("Les plages SNCC se chevauchent.");
      else {
        // Les scores sont administrés au centième. En JavaScript,
        // 75 - 74.99 peut devenir 0.010000000000005 ; arrondir le calcul
        // évite de déclarer à tort une lacune dans le préremplissage.
        const gap = Math.round((current.min - previous.max) * 100) / 100;
        if (gap > 0.01) errors.push("Les plages SNCC présentent un intervalle non couvert.");
      }
    });
    return { rows: ordered, errors: [...new Set(errors)] };
  }

  function snccScore(value) {
    const score = Number(value);
    return Number.isFinite(score)
      ? score.toLocaleString("fr-FR", { maximumFractionDigits: 2 })
      : "—";
  }

  function snccRowsSummary(rows = []) {
    if (!Array.isArray(rows) || !rows.length) return "";
    return `
      <div class="sncc-result-rows" aria-label="Résultat de la matrice SNCC">
        ${rows.map((row) => `
          <div class="sncc-result-row">
            <strong>${e(row.classe)}</strong>
            <span>${snccScore(row.min)} à ${snccScore(row.max)}</span>
            <small>${e(row.statut_administratif || row.statut || "—")} · ${e(row.niveau_risque || row.risque || "—")}</small>
          </div>
        `).join("")}
      </div>`;
  }

  function renderSnccValidation(result = null) {
    const node = $("#snccMatrixValidation");
    if (!node) return;
    if (!result) {
      node.innerHTML = `<div class="priority-empty compact">Cliquez sur « Vérifier la matrice » pour obtenir le résultat détaillé du contrôle.</div>`;
      return;
    }

    const { rows = [], errors = [] } = result;
    const matrixRows = snccRowsSummary(rows);
    node.innerHTML = errors.length
      ? `
        <div class="validation-summary invalid">
          <span><i data-lucide="triangle-alert"></i></span>
          <div><strong>Matrice à corriger</strong><small>${errors.length} point${errors.length > 1 ? "s" : ""} empêche${errors.length > 1 ? "nt" : ""} la création du brouillon.</small></div>
        </div>
        <ul class="validation-errors">${errors.map((item) => `<li>${e(item)}</li>`).join("")}</ul>
        ${matrixRows}`
      : `
        <div class="validation-summary valid">
          <span><i data-lucide="badge-check"></i></span>
          <div><strong>Matrice cohérente : brouillon prêt à créer</strong><small>Les cinq classes couvrent l’INFC de 0 à 100, sans chevauchement ni intervalle non couvert.</small></div>
        </div>
        ${matrixRows}
        <p class="sncc-validation-note">La matrice décide de la classe, du risque et du statut normal VA/RE. Les statuts EX, VE, SU et RT restent prioritaires lorsqu’ils sont imposés par la situation réelle du certificat.</p>`;
    icons();
  }

  function renderSnccDraftSummary(draft = null) {
    const node = $("#snccDraftSummary");
    if (!node) return;
    if (!draft) {
      node.hidden = true;
      node.innerHTML = "";
      return;
    }

    const rows = Array.isArray(draft.parametres?.rows) ? draft.parametres.rows : [];
    node.hidden = false;
    node.innerHTML = `
      <div class="sncc-draft-summary-head">
        <span><i data-lucide="file-check-2"></i></span>
        <div><strong>Brouillon SNCC enregistré</strong><small>Il est conservé comme brouillon et ne produit aucun classement tant qu’il n’est pas publié.</small></div>
      </div>
      <dl class="sncc-draft-details">
        <div><dt>Version</dt><dd>v${e(draft.version || "—")}</dd></div>
        <div><dt>Statut</dt><dd>Brouillon</dd></div>
        <div class="full"><dt>Libellé</dt><dd>${e(draft.libelle || "Matrice SNCC")}</dd></div>
      </dl>
      ${snccRowsSummary(rows)}
      <p class="sncc-draft-next"><i data-lucide="arrow-right"></i>Étape suivante : contrôlez les seuils, puis cliquez sur « Publier la matrice » après approbation HAUQE.</p>`;
    icons();
  }

  function renderSnccMatrixStatus() {
    const current = rules.find((item) => String(item.logical_code || "").toUpperCase() === "SNCC_CLASSIFICATION_MATRIX" && String(item.statut || "").toUpperCase() === "PUBLIE");
    const draft = rules.find((item) => String(item.logical_code || "").toUpperCase() === "SNCC_CLASSIFICATION_MATRIX" && String(item.statut || "").toUpperCase() === "BROUILLON");
    const node = $("#snccMatrixStatus");
    if (!node) return;
    node.textContent = current
      ? `Publiée · v${current.version || "—"}`
      : draft
        ? `Brouillon · v${draft.version || "—"}`
        : "Non publiée";
    node.className = `inst-status ${current ? "ready" : ""}`;
  }

  function restoreSnccDraft() {
    const draft = rules.find((item) =>
      String(item.logical_code || "").toUpperCase() === "SNCC_CLASSIFICATION_MATRIX"
      && String(item.statut || "").toUpperCase() === "BROUILLON"
    ) || null;
    const version = $("#snccMatrixVersion");
    const label = $("#snccMatrixLabel");
    const description = $("#snccMatrixDescription");
    const saveButton = $("#saveSnccMatrixDraft");
    const publishButton = $("#publishSnccMatrix");
    if (!version || !label || !description || !saveButton || !publishButton) return;

    snccDraft = draft;
    if (!draft) {
      version.disabled = false;
      saveButton.innerHTML = '<i data-lucide="save"></i>Créer le brouillon SNCC';
      updateSnccPublishState();
      renderSnccDraftSummary();
      return;
    }

    version.value = draft.version || version.value;
    version.disabled = true;
    version.title = "La version est fixée pour ce brouillon. Créez une nouvelle version après publication.";
    label.value = draft.libelle || label.value;
    description.value = draft.description || "";
    const rows = Array.isArray(draft.parametres?.rows) ? draft.parametres.rows : [];
    if (rows.length) renderSnccMatrix(rows);
    saveButton.innerHTML = '<i data-lucide="save"></i>Enregistrer le brouillon SNCC';
    updateSnccPublishState();
    updateSnccPrefillState(`Brouillon v${draft.version || "—"} chargé : cinq classes enregistrées.`, true);
    renderSnccDraftSummary(draft);
    icons();
  }

  async function validateSnccMatrix() {
    const payload = snccMatrixPayload();
    renderSnccValidation(payload);
    return payload;
  }

  async function saveSnccMatrixDraft() {
    const { rows, errors } = await validateSnccMatrix();
    if (errors.length) return;
    try {
      const draftPayload = {
        famille: "SNCC",
        libelle: $("#snccMatrixLabel").value.trim(),
        description: $("#snccMatrixDescription").value.trim() || null,
        parametres: { rows },
        date_debut_effet: null,
      };
      const isExistingDraft = Boolean(snccDraft?.id);
      snccDraft = await run(
        () => isExistingDraft
          ? api.apiPatch(`/api/v1/governance/rules/${snccDraft.id}`, draftPayload)
          : api.apiPost("/api/v1/governance/rules", {
            logical_code: "SNCC_CLASSIFICATION_MATRIX",
            ...draftPayload,
            version: $("#snccMatrixVersion").value.trim(),
          }),
        {
          button: $("#saveSnccMatrixDraft"),
          title: "Matrice SNCC",
          message: isExistingDraft ? "Enregistrement du brouillon" : "Création du brouillon",
        }
      );
      updateSnccPublishState();
      renderSnccValidation({ rows, errors: [] });
      renderSnccDraftSummary(snccDraft);
      state(
        isExistingDraft
          ? `Le brouillon SNCC v${snccDraft.version || "—"} est enregistré. Il peut maintenant être publié.`
          : `Le brouillon SNCC v${snccDraft.version || "—"} est créé. Vérifiez-le puis publiez la version approuvée.`
      );
      await Promise.all([loadRules(), loadReadiness()]);
      renderSnccMatrixStatus();
    } catch (error) {
      state(error?.message || "Création de la matrice SNCC impossible.", true);
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

    bindDirectRuleButtons("[data-model-id]", async (button) => {
        selectedModel = models.find((x) => String(x.id) === String(button.dataset.modelId));
        await loadSelectedModel();
        renderModelList();
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

    bindDirectRuleButtons("#saveModelRule", async () => {
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

    bindDirectRuleButtons("#publishModel", () => openPublish("model", selectedModel));
    bindDirectRuleButtons("#addWeight", () => {
      $("#weightDomain").value = "";
      $("#weightValue").value = "";
      $("#weightDialog").showModal();
      icons();
    });
    bindDirectRuleButtons("#loadInfcWeights", loadDocumentedInfcWeights);

    bindDirectRuleButtons("[data-deactivate-weight]", async (button) => {
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

  bindDirectRuleButtons("[data-fuccs-grid]", async (button) => {
      selectedFuccsGrid = fuccsGrids.find(
        (item) => String(item.id) === String(button.dataset.fuccsGrid)
      ) || null;

      renderFuccsGridList();
      await loadSelectedFuccsGrid();
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


${
  draft
  && canAdmin
  && Number(selectedFuccsGrid.rubriques_count || 0) === 0
  && Number(selectedFuccsGrid.criteres_count || 0) === 0
    ? `
      <section class="fuccs-historical-prefill">
        <span><i data-lucide="wand-sparkles"></i></span>

        <div>
          <strong>Modèle historique de recette disponible</strong>
          <small>Choisissez le modèle de recette adapté à la collecte actuelle.</small>
        </div>

        <div class="fuccs-prefill-actions">
          <div data-fuccs-prefill-action-slot="historical-24"></div>
          <div data-fuccs-prefill-action-slot="historical-22"></div>
        </div>
      </section>
    `
    : ""
}

      <div
        class="fuccs-grid-actions"
        data-fuccs-grid-action-slot
        data-fuccs-grid-draft="${draft}"
        data-fuccs-grid-published="${published}"
        data-fuccs-grid-admin="${canAdmin}"
      ></div>

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

          ${draft && canAdmin ? `<div data-new-fuccs-rubric-slot></div>` : ""}
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

  hydrateFuccsActionButtons(node);

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
              <div
                class="fuccs-inline-actions"
                data-fuccs-rubric-action-slot="${e(rubric.id)}"
              ></div>
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
                        <div
                          class="fuccs-inline-actions"
                          data-fuccs-criterion-action-slot="${e(criterion.id)}"
                        ></div>
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
              <div data-fuccs-add-criterion-slot="${e(rubric.id)}"></div>
            </footer>
          `
          : ""
      }
    </article>
  `;
}

// Les actions FUCCS sont volontairement créées après le rendu des données,
// comme les actions de Gestion des campagnes. Ainsi, aucune icône d'action ne
// dépend d'un bouton injecté par innerHTML ni d'un écouteur délégué.
function createFuccsActionButton({
  label,
  iconName,
  className = "btn btn-outline-secondary app-btn",
  iconOnly = false,
  handler,
}) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = className;
  button.setAttribute("aria-label", label);
  button.setAttribute("title", label);
  button.setAttribute("data-no-action-loader", "true");
  button.dataset.rulesDirectButton = "true";
  button.innerHTML = `<i data-lucide="${iconName}"></i>${iconOnly ? "" : label}`;
  button.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();
    void Promise.resolve(handler(button)).catch((error) => {
      console.error("[HAUQE FUCCS] Action impossible", error);
      state(error?.message || "Opération impossible.", true);
    });
  });
  return button;
}

function fuccsRubricById(id) {
  return fuccsRubrics.find((item) => String(item.id) === String(id)) || null;
}

function fuccsCriterionById(id) {
  return fuccsCriteria.find((item) => String(item.id) === String(id)) || null;
}

function hydrateFuccsActionButtons(root = document) {
  root.querySelectorAll("[data-fuccs-prefill-action-slot]").forEach((slot) => {
    const isSecondTemplate = slot.dataset.fuccsPrefillActionSlot === "historical-22";
    slot.replaceChildren(createFuccsActionButton({
      label: isSecondTemplate
        ? "Préremplissage 2 · sans RCCM/NIF"
        : "Préremplissage 1 · 24 critères",
      iconName: isSecondTemplate ? "list-minus" : "list-plus",
      className: isSecondTemplate
        ? "btn btn-outline-secondary app-btn"
        : "btn btn-primary app-btn",
      handler: (button) => (
        isSecondTemplate
          ? requestFuccsHistorical22NoLegalIdentifiers(button)
          : requestFuccsHistorical24(button)
      ),
    }));
  });

  root.querySelectorAll("[data-fuccs-grid-action-slot]").forEach((slot) => {
    const draft = slot.dataset.fuccsGridDraft === "true";
    const published = slot.dataset.fuccsGridPublished === "true";
    const canAdmin = slot.dataset.fuccsGridAdmin === "true";
    const actions = [];

    if (draft && canAdmin) {
      actions.push(createFuccsActionButton({
        label: "Modifier",
        iconName: "pencil",
        handler: () => openFuccsGridDialog(selectedFuccsGrid),
      }));
      actions.push(createFuccsActionButton({
        label: "Publier",
        iconName: "rocket",
        className: "btn btn-primary app-btn",
        handler: () => openPublish("fuccs", selectedFuccsGrid),
      }));
    }
    if (!draft && canAdmin) {
      actions.push(createFuccsActionButton({
        label: "Nouvelle version",
        iconName: "copy-plus",
        handler: openFuccsCloneDialog,
      }));
    }
    if (published && canAdmin) {
      actions.push(createFuccsActionButton({
        label: "Retirer",
        iconName: "archive",
        className: "btn btn-outline-danger app-btn",
        handler: () => {
          $("#fuccsRetireDate").value = new Date().toISOString().slice(0, 10);
          $("#fuccsRetireReason").value = "";
          $("#fuccsRetireDialog").showModal();
          icons();
        },
      }));
    }
    slot.replaceChildren(...actions);
  });

  root.querySelectorAll("[data-new-fuccs-rubric-slot]").forEach((slot) => {
    slot.replaceChildren(createFuccsActionButton({
      label: "Ajouter une rubrique",
      iconName: "folder-plus",
      className: "btn btn-primary app-btn",
      handler: () => openFuccsRubricDialog(),
    }));
  });

  root.querySelectorAll("[data-fuccs-rubric-action-slot]").forEach((slot) => {
    const rubric = fuccsRubricById(slot.dataset.fuccsRubricActionSlot);
    if (!rubric) return;
    slot.replaceChildren(
      createFuccsActionButton({
        label: "Modifier la rubrique",
        iconName: "pencil",
        className: "",
        iconOnly: true,
        handler: () => openFuccsRubricDialog(rubric),
      }),
      createFuccsActionButton({
        label: "Supprimer la rubrique",
        iconName: "trash-2",
        className: "",
        iconOnly: true,
        handler: () => openFuccsDeleteDialog("rubric", rubric),
      })
    );
  });

  root.querySelectorAll("[data-fuccs-criterion-action-slot]").forEach((slot) => {
    const criterion = fuccsCriterionById(slot.dataset.fuccsCriterionActionSlot);
    const rubric = fuccsRubricById(criterion?.rubrique_fuccs_id);
    if (!criterion || !rubric) return;
    slot.replaceChildren(
      createFuccsActionButton({
        label: "Modifier le critère",
        iconName: "pencil",
        className: "",
        iconOnly: true,
        handler: () => openFuccsCriterionDialog(rubric, criterion),
      }),
      createFuccsActionButton({
        label: "Supprimer le critère",
        iconName: "trash-2",
        className: "",
        iconOnly: true,
        handler: () => openFuccsDeleteDialog("criterion", criterion, rubric),
      })
    );
  });

  root.querySelectorAll("[data-fuccs-add-criterion-slot]").forEach((slot) => {
    const rubric = fuccsRubricById(slot.dataset.fuccsAddCriterionSlot);
    if (!rubric) return;
    slot.replaceChildren(createFuccsActionButton({
      label: "Ajouter un critère",
      iconName: "list-plus",
      handler: () => openFuccsCriterionDialog(rubric),
    }));
  });
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


function selectedFuccsCounts() {
  return {
    rubrics: Number(
      selectedFuccsGrid?.rubriques_count
      ?? fuccsRubrics.length
      ?? 0
    ),
    criteria: Number(
      selectedFuccsGrid?.criteres_count
      ?? fuccsCriteria.length
      ?? 0
    ),
  };
}

async function requestFuccsPrefill(variant, sourceButton = null) {

  try {
    if (!user) {
      user = await run(
        () => api.apiGet("/api/v1/me"),
        {
          button: sourceButton,
          title: "Grille FUCCS",
          message: "Vérification des habilitations",
          detail: "Patientez…",
        }
      );
    }

    if (!has("FUCCS.ADMINISTRER_GRILLE")) {
      state(
        "La permission FUCCS.ADMINISTRER_GRILLE est requise "
        + "pour préremplir la grille.",
        true
      );
      return;
    }

    if (!fuccsGrids.length) {
      await run(
        loadFuccsGrids,
        {
          button: sourceButton,
          title: "Grille FUCCS",
          message: "Chargement des grilles",
          detail: "Ce sera prêt…",
        }
      );
    }

    if (!selectedFuccsGrid) {
      const eligible = fuccsGrids.find((item) => (
        String(
          item.statut_publication || ""
        ).toUpperCase() === "BROUILLON"
        && Number(item.rubriques_count || 0) === 0
        && Number(item.criteres_count || 0) === 0
      ));

      if (!eligible) {
        state(
          "Aucune grille FUCCS brouillon vide n’est disponible. "
          + "Créez une nouvelle grille, sélectionnez-la, puis "
            + "relancez le préremplissage.",
          true
        );
        return;
      }

      selectedFuccsGrid = eligible;
      renderFuccsGridList();
      await loadSelectedFuccsGrid();
    }

    if (!fuccsGridIsDraft(selectedFuccsGrid)) {
      state(
        "La grille sélectionnée n’est pas un brouillon. "
        + "Créez une nouvelle version brouillon avant le "
        + "préremplissage.",
        true
      );
      return;
    }

    const counts = selectedFuccsCounts();

    if (counts.rubrics > 0 || counts.criteria > 0) {
      state(
        "La grille sélectionnée contient déjà des rubriques "
        + `ou des critères. ${variant.label} exige une `
        + "grille totalement vide.",
        true
      );
      return;
    }

    const confirmation = $(variant.confirmationSelector);
    const dialog = $(variant.dialogSelector);

    if (!confirmation || !dialog) {
      state(
        "Le formulaire de confirmation FUCCS n’est pas présent dans la page.",
        true
      );
      return;
    }

    confirmation.checked = false;

    if (dialog.open) {
      dialog.close();
    }

    dialog.showModal();

    requestAnimationFrame(() => {
      confirmation.focus({ preventScroll: true });
      icons();
    });
  } catch (error) {
    console.error(
      "[HAUQE FUCCS] Ouverture du préremplissage impossible",
      error
    );

    state(
      error?.message
      || "Impossible d’ouvrir le préremplissage FUCCS.",
      true
    );
  }
}

function requestFuccsHistorical24(sourceButton = null) {
  return requestFuccsPrefill({
    confirmationSelector: "#fuccsHistorical24Confirm",
    dialogSelector: "#fuccsHistorical24Dialog",
    label: "Le préremplissage historique",
  }, sourceButton);
}

function requestFuccsHistorical22NoLegalIdentifiers(sourceButton = null) {
  return requestFuccsPrefill({
    confirmationSelector: "#fuccsHistorical22Confirm",
    dialogSelector: "#fuccsHistorical22Dialog",
    label: "Le préremplissage 2",
  }, sourceButton);
}

async function prefillFuccsTemplate(event, variant) {
  event.preventDefault();

  if (!selectedFuccsGrid) return;

  if (!$(variant.confirmationSelector).checked) {
    state(
      `Confirmez l’utilisation de ${variant.label}.`,
      true
    );
    return;
  }

  try {
    await run(
        () => api.apiPost(
          `/api/v1/fuccs/grilles/${selectedFuccsGrid.id}`
          + variant.endpoint,
        {}
      ),
      {
        button: event.submitter,
        title: "Grille FUCCS",
        message: variant.progressMessage,
        detail: "Création transactionnelle des 6 rubriques.",
      }
    );

    $(variant.dialogSelector).close();
    await loadSelectedFuccsGrid();
    await loadFuccsGrids();

    state(
      `${variant.criteriaCount} critères ont été ajoutés. Vérifiez-les avant publication.`
    );
  } catch (error) {
    state(
      error?.message || "Préremplissage impossible.",
      true
    );
  }
}

function prefillFuccsHistorical24(event) {
  return prefillFuccsTemplate(event, {
    confirmationSelector: "#fuccsHistorical24Confirm",
    dialogSelector: "#fuccsHistorical24Dialog",
    endpoint: "/prefill-historical-24",
    label: "le modèle historique de recette",
    progressMessage: "Préremplissage des 24 critères",
    criteriaCount: 24,
  });
}

function prefillFuccsHistorical22NoLegalIdentifiers(event) {
  return prefillFuccsTemplate(event, {
    confirmationSelector: "#fuccsHistorical22Confirm",
    dialogSelector: "#fuccsHistorical22Dialog",
    endpoint: "/prefill-historical-22-no-legal-identifiers",
    label: "le préremplissage 2 sans RCCM/NIF",
    progressMessage: "Préremplissage des 22 critères",
    criteriaCount: 22,
  });
}



  /* ============================================================
     CODIFICATION BNEC
     - modèles versionnés dans regles_metier ;
     - code proposé dans l'intégration ;
     - séquence réservée par le système au moment de la transaction.
     ============================================================ */
  const CODIFICATION_PREFIX = "CODIFICATION_BNEC_";
  const CODIFICATION_TOKENS = [
    "HAUQE", "BNEC", "PAYS", "REGION", "ZONE", "ANNEE",
    "ANNEE2", "ANNEE4", "MOIS", "TYPE_OBJET", "CODE_ENTREPRISE",
    "ENTREPRISE", "CERTIF", "ORGANISME", "NORME", "SECTEUR",
    "SEQ3", "SEQ4", "SEQ5", "SEQUENCE",
  ];
  const CODIFICATION_SEQUENCE_TOKENS = new Set([
    "SEQ3", "SEQ4", "SEQ5", "SEQUENCE",
  ]);

  function codificationRules() {
    return rules.filter((item) =>
      String(item.logical_code || "").toUpperCase().startsWith(CODIFICATION_PREFIX)
    );
  }

  function codificationObjectFromRule(item) {
    return String(
      item?.parametres?.objet
      || item?.logical_code?.replace(CODIFICATION_PREFIX, "")
      || ""
    ).toUpperCase();
  }

  function codificationObjectLabel(value) {
    return String(value || "").toUpperCase() === "CERTIFICATION"
      ? "Certification"
      : "Entreprise BNEC";
  }

  function codificationDefaultLabel(objectType) {
    return objectType === "CERTIFICATION"
      ? "Modèle de codification des certifications"
      : "Modèle de codification des entreprises BNEC";
  }

  function codificationDefaultFormat(objectType) {
    return objectType === "CERTIFICATION"
      ? "{HAUQE}-{CERTIF}-{CODE_ENTREPRISE}-{NORME}-{ANNEE4}-{SEQ3}"
      : "{HAUQE}-{BNEC}-{PAYS}-{REGION}-{ANNEE4}-{SEQ4}";
  }

  function codificationDefaultScope(objectType) {
    return objectType === "CERTIFICATION"
      ? "ANNUELLE_PAR_ENTREPRISE"
      : "ANNUELLE";
  }

  function codificationDefaultLength(objectType) {
    return objectType === "CERTIFICATION" ? 3 : 4;
  }

  function normalizeCodificationSegment(value, fallback = "") {
    return String(value || fallback)
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toUpperCase()
      .replace(/[^A-Z0-9]+/g, "");
  }

  function extractCodificationTokens(format) {
    return [...String(format || "").toUpperCase().matchAll(/\{([A-Z0-9_]+)\}/g)]
      .map((match) => match[1]);
  }

  function codificationParametersFromForm() {
    return {
      objet: $("#codificationObject").value,
      format: $("#codificationFormat").value.trim().toUpperCase(),
      separateur: $("#codificationSeparator").value,
      sequence_longueur: Number($("#codificationSequenceLength").value || 4),
      sequence_portee: $("#codificationSequenceScope").value,
      sequence_reinitialisation: $("#codificationSequenceReset").value,
      constantes: {
        HAUQE: $("#codificationConstHauqe").value.trim(),
        BNEC: $("#codificationConstBnec").value.trim(),
        PAYS: $("#codificationConstCountry").value.trim(),
        CERTIF: $("#codificationConstCertif").value.trim(),
      },
      modele_par_defaut: true,
      libelle_modele: $("#codificationLabel").value.trim(),
    };
  }

  function validateCodificationForm() {
    const params = codificationParametersFromForm();
    const errors = [];
    const warnings = [];
    const tokens = extractCodificationTokens(params.format);
    const unknown = [...new Set(tokens.filter((token) =>
      !CODIFICATION_TOKENS.includes(token)
    ))];
    const sequences = tokens.filter((token) =>
      CODIFICATION_SEQUENCE_TOKENS.has(token)
    );

    if (!$("#codificationVersion").value.trim()) errors.push("Version obligatoire.");
    if (!$("#codificationLabel").value.trim()) errors.push("Nom du modèle obligatoire.");
    if (!params.format) errors.push("Format obligatoire.");
    if (unknown.length) errors.push(`Variables inconnues : ${unknown.map((x) => `{${x}}`).join(", ")}.`);
    if (sequences.length !== 1) errors.push("Le format doit contenir exactement une variable de séquence.");
    if (params.sequence_longueur < 2 || params.sequence_longueur > 12) {
      errors.push("La longueur de séquence doit être comprise entre 2 et 12.");
    }
    if (params.objet === "CERTIFICATION" && !tokens.includes("CODE_ENTREPRISE")) {
      warnings.push("Ajoutez {CODE_ENTREPRISE} pour rattacher visiblement le certificat à son entreprise.");
    }

    return { params, errors, warnings, tokens };
  }

  function codificationPreviewValue(validation) {
    const params = validation.params;
    const now = new Date();
    const length = Math.max(2, Math.min(12, Number(params.sequence_longueur || 4)));
    const constants = Object.fromEntries(
      Object.entries(params.constantes || {}).map(([key, value]) => [
        key,
        normalizeCodificationSegment(value),
      ])
    );
    const sample = {
      ...constants,
      REGION: "MARITIME",
      ZONE: "LOME",
      ANNEE: String(now.getFullYear()),
      ANNEE2: String(now.getFullYear()).slice(-2),
      ANNEE4: String(now.getFullYear()),
      MOIS: String(now.getMonth() + 1).padStart(2, "0"),
      TYPE_OBJET: params.objet,
      CODE_ENTREPRISE: `HAUQEBNECTGMAR${now.getFullYear()}0001`,
      ENTREPRISE: "AGROTOGO",
      CERTIF: normalizeCodificationSegment(params.constantes?.CERTIF, "CERT"),
      ORGANISME: "AFNOR",
      NORME: "ISO22000",
      SECTEUR: "AGROALIMENTAIRE",
      SEQUENCE: "1".padStart(length, "0"),
      SEQ3: "001",
      SEQ4: "0001",
      SEQ5: "00001",
    };

    let output = params.format || "";
    for (const token of extractCodificationTokens(output)) {
      output = output.replaceAll(`{${token}}`, sample[token] || `?${token}?`);
    }
    const separator = params.separateur || "-";
    output = output.replace(/[-/._]+/g, separator);
    return output.replace(new RegExp(`^[${separator.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}]|[${separator.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}]$`, "g"), "");
  }

  function updateCodificationPreview() {
    const validation = validateCodificationForm();
    const preview = codificationPreviewValue(validation) || "—";
    $("#codificationPreview").textContent = preview;

    const node = $("#codificationValidation");
    if (validation.errors.length) {
      node.className = "codification-validation-card invalid";
      node.innerHTML = `
        <span><i data-lucide="circle-x"></i></span>
        <div><strong>Configuration incomplète</strong><small>${e(validation.errors.join(" "))}</small></div>
      `;
    } else if (validation.warnings.length) {
      node.className = "codification-validation-card";
      node.innerHTML = `
        <span><i data-lucide="triangle-alert"></i></span>
        <div><strong>Configuration valide avec recommandation</strong><small>${e(validation.warnings.join(" "))}</small></div>
      `;
    } else {
      node.className = "codification-validation-card valid";
      node.innerHTML = `
        <span><i data-lucide="circle-check-big"></i></span>
        <div><strong>Configuration prête</strong><small>La validation institutionnelle sera confirmée par le backend lors de la publication.</small></div>
      `;
    }
    icons();
    return validation;
  }

  function renderCodificationTokens() {
    const labels = {
      HAUQE: "Constante HAUQE", BNEC: "Constante BNEC", PAYS: "Pays",
      REGION: "Région", ZONE: "Zone", ANNEE: "Année", ANNEE2: "Année 2 chiffres",
      ANNEE4: "Année 4 chiffres", MOIS: "Mois", TYPE_OBJET: "Type d’objet",
      CODE_ENTREPRISE: "Code entreprise", ENTREPRISE: "Entreprise", CERTIF: "Constante certificat",
      ORGANISME: "Organisme", NORME: "Norme", SECTEUR: "Secteur",
      SEQ3: "Séquence 3", SEQ4: "Séquence 4", SEQ5: "Séquence 5", SEQUENCE: "Séquence paramétrable",
    };
    $("#codificationTokens").innerHTML = CODIFICATION_TOKENS.map((token) => `
      <button class="codification-token" type="button" data-codification-token="${token}" title="${e(labels[token] || token)}">{${token}}</button>
    `).join("");
    bindDirectRuleButtons('[data-codification-token]', (button) => {
        const input = $("#codificationFormat");
        const token = `{${button.dataset.codificationToken}}`;
        const start = input.selectionStart ?? input.value.length;
        const end = input.selectionEnd ?? start;
        input.value = input.value.slice(0, start) + token + input.value.slice(end);
        input.focus();
        input.setSelectionRange(start + token.length, start + token.length);
        updateCodificationPreview();
    });
  }

  function renderCodificationModels() {
    const node = $("#codificationModelList");
    if (!node) return;
    const objectFilter = $("#codificationObjectFilter")?.value || "";
    const statusFilter = $("#codificationStatusFilter")?.value || "";
    const visible = codificationRules().filter((item) => {
      const objectType = codificationObjectFromRule(item);
      if (objectFilter && objectType !== objectFilter) return false;
      if (statusFilter && String(item.statut || "").toUpperCase() !== statusFilter) return false;
      return true;
    });

    node.innerHTML = visible.length ? visible.map((item) => {
      const objectType = codificationObjectFromRule(item);
      const format = item.parametres?.format || "—";
      return `
        <button class="institutional-list-row ${selectedCodificationRule?.id === item.id ? "active" : ""}" type="button" data-codification-rule="${e(item.id)}">
          <span class="rule-icon"><i data-lucide="fingerprint"></i></span>
          <div>
            <strong>${e(codificationObjectLabel(objectType))}</strong>
            <small>${e(item.libelle || item.logical_code)} · v${e(item.version || "—")}</small>
          </div>
          <div class="codification-list-meta">
            <span>${e(format)}</span>
            <b class="inst-status ${String(item.statut || "").toLowerCase()}">${e(item.statut || "—")}</b>
          </div>
          <i data-lucide="chevron-right"></i>
        </button>
      `;
    }).join("") : `<div class="priority-empty">Aucun modèle de codification.</div>`;

    bindDirectRuleButtons('[data-codification-rule]', (button) => {
        selectedCodificationRule = rules.find((item) =>
          String(item.id) === String(button.dataset.codificationRule)
        ) || null;
        renderCodificationModels();
        renderCodificationSummary();
    });
    icons();
  }

  function renderCodificationSummary() {
    const node = $("#codificationEditor");
    if (!node) return;
    const item = selectedCodificationRule;
    if (!item) {
      node.innerHTML = `<div class="priority-empty">Sélectionnez un modèle ou créez-en un nouveau.</div>`;
      return;
    }
    const params = item.parametres || {};
    const draft = String(item.statut || "").toUpperCase() === "BROUILLON";
    const published = String(item.statut || "").toUpperCase() === "PUBLIE";
    node.innerHTML = `
      <header>
        <div>
          <p class="eyebrow">${e(codificationObjectLabel(codificationObjectFromRule(item)))}</p>
          <h2>${e(item.libelle || item.logical_code)}</h2>
          <p>Version ${e(item.version || "—")}</p>
        </div>
        <span class="inst-status ${String(item.statut || "").toLowerCase()}">${e(item.statut || "—")}</span>
      </header>
      <div class="codification-summary">
        <div class="codification-summary-code">
          <small>Format institutionnel</small>
          <strong>${e(params.format || "—")}</strong>
        </div>
        <div class="codification-summary-grid">
          <article><small>Portée</small><strong>${e(params.sequence_portee || "—")}</strong></article>
          <article><small>Réinitialisation</small><strong>${e(params.sequence_reinitialisation || "—")}</strong></article>
          <article><small>Début d’effet</small><strong>${e(item.date_debut_effet || "—")}</strong></article>
          <article><small>Approbation</small><strong>${e(item.reference_approbation || "—")}</strong></article>
        </div>
        <div
          class="institutional-actions no-pad-actions"
          data-codification-action-slot
          data-codification-draft="${draft}"
          data-codification-published="${published}"
          data-codification-admin="${has("GOUVERNANCE.ADMINISTRER_REGLES")}"
        ></div>
      </div>
    `;
    hydrateCodificationActionButtons(node, item);
    icons();
  }

  function hydrateCodificationActionButtons(root, item) {
    root.querySelectorAll("[data-codification-action-slot]").forEach((slot) => {
      const draft = slot.dataset.codificationDraft === "true";
      const published = slot.dataset.codificationPublished === "true";
      const canAdmin = slot.dataset.codificationAdmin === "true";
      const actions = [];

      if (draft && canAdmin) {
        actions.push(createFuccsActionButton({
          label: "Modifier",
          iconName: "pencil",
          handler: () => openCodificationBuilder(item),
        }));
        actions.push(createFuccsActionButton({
          label: "Publier",
          iconName: "rocket",
          className: "btn btn-primary app-btn",
          handler: () => openPublish("rule", item),
        }));
      }
      if (published && canAdmin) {
        actions.push(createFuccsActionButton({
          label: "Nouvelle version",
          iconName: "copy-plus",
          handler: () => openCodificationBuilder(item, true),
        }));
      }
      slot.replaceChildren(...actions);
    });
  }

  function fillCodificationForm(objectType, source = null) {
    const params = source?.parametres || {};
    const objectValue = String(params.objet || objectType || "ENTREPRISE").toUpperCase();
    $("#codificationObject").value = objectValue;
    $("#codificationObject").dataset.previousObject = objectValue;
    $("#codificationVersion").value = cloneSourceCodificationRule ? "" : (source?.version || "1.0");
    $("#codificationLabel").value = source?.libelle || codificationDefaultLabel(objectValue);
    $("#codificationDescription").value = source?.description || "";
    $("#codificationFormat").value = params.format || codificationDefaultFormat(objectValue);
    $("#codificationSeparator").value = params.separateur || "-";
    $("#codificationSequenceLength").value = params.sequence_longueur || codificationDefaultLength(objectValue);
    $("#codificationSequenceScope").value = params.sequence_portee || codificationDefaultScope(objectValue);
    $("#codificationSequenceReset").value = params.sequence_reinitialisation || "JAMAIS";
    $("#codificationConstHauqe").value = params.constantes?.HAUQE || "HAUQE";
    $("#codificationConstBnec").value = params.constantes?.BNEC || "BNEC";
    $("#codificationConstCountry").value = params.constantes?.PAYS || "TG";
    $("#codificationConstCertif").value = params.constantes?.CERTIF || "CERT";
  }

  function openCodificationBuilder(source = null, clone = false) {
    editingCodificationRule = clone ? null : source;
    cloneSourceCodificationRule = clone ? source : null;
    const objectType = codificationObjectFromRule(source)
      || $("#codificationObjectFilter")?.value
      || "ENTREPRISE";
    fillCodificationForm(objectType, source);
    $("#codificationObject").disabled = Boolean(source);
    $("#codificationVersion").disabled = Boolean(source && !clone);
    $("#codificationBuilder").hidden = false;
    $("#codificationBuilderEyebrow").textContent = clone
      ? "Nouvelle version"
      : source
        ? "Modification du brouillon"
        : "Nouveau brouillon";
    $("#codificationBuilderTitle").textContent = clone
      ? `Nouvelle version — ${codificationObjectLabel(objectType)}`
      : source
        ? source.libelle
        : "Construire le modèle";
    $("#codificationBuilderStatus").textContent = clone ? "À CRÉER" : (source?.statut || "BROUILLON");
    $("#codificationBuilderStatus").className = `inst-status ${String(source?.statut || "").toLowerCase()}`;
    $("#cloneCodificationModel").hidden = true;
    $("#publishCodificationModel").hidden = !(source && String(source.statut).toUpperCase() === "BROUILLON");
    $("#saveCodificationModel").hidden = !has("GOUVERNANCE.ADMINISTRER_REGLES");
    renderCodificationTokens();
    updateCodificationPreview();
    $("#codificationBuilder").scrollIntoView({ behavior: "smooth", block: "start" });
    icons();
  }

  function closeCodificationBuilder() {
    editingCodificationRule = null;
    cloneSourceCodificationRule = null;
    $("#codificationBuilder").hidden = true;
    $("#codificationObject").disabled = false;
    $("#codificationVersion").disabled = false;
  }

  async function saveCodificationModel() {
    const validation = updateCodificationPreview();
    if (validation.errors.length) {
      state(validation.errors.join(" "), true);
      return;
    }
    const objectType = validation.params.objet;
    const logicalCode = `${CODIFICATION_PREFIX}${objectType}`;
    const payload = {
      famille: "CODIFICATION",
      libelle: $("#codificationLabel").value.trim(),
      description: $("#codificationDescription").value.trim() || null,
      parametres: validation.params,
    };

    try {
      let saved;
      if (cloneSourceCodificationRule) {
        saved = await api.apiPost(
          `/api/v1/governance/rules/${cloneSourceCodificationRule.id}/clone`,
          {
            version: $("#codificationVersion").value.trim(),
            libelle: payload.libelle,
            date_debut_effet: null,
          }
        );
        saved = await api.apiPatch(`/api/v1/governance/rules/${saved.id}`, payload);
      } else if (editingCodificationRule) {
        saved = await api.apiPatch(
          `/api/v1/governance/rules/${editingCodificationRule.id}`,
          payload
        );
      } else {
        saved = await api.apiPost("/api/v1/governance/rules", {
          logical_code: logicalCode,
          famille: payload.famille,
          libelle: payload.libelle,
          description: payload.description,
          version: $("#codificationVersion").value.trim(),
          parametres: payload.parametres,
          date_debut_effet: null,
        });
      }

      selectedCodificationRule = saved;
      editingCodificationRule = saved;
      cloneSourceCodificationRule = null;
      await loadRules();
      renderCodificationSummary();
      openCodificationBuilder(saved);
      state("Brouillon de codification enregistré.");
    } catch (error) {
      state(error?.message || "Enregistrement du modèle impossible.", true);
    }
  }

  async function copyCodificationPreview() {
    const value = $("#codificationPreview").textContent || "";
    try {
      if (navigator.clipboard?.writeText && window.isSecureContext) {
        await navigator.clipboard.writeText(value);
      } else {
        const area = document.createElement("textarea");
        area.value = value;
        area.style.position = "fixed";
        area.style.opacity = "0";
        document.body.appendChild(area);
        area.select();
        document.execCommand("copy");
        area.remove();
      }
      state("Aperçu copié.");
    } catch (error) {
      state("Copie automatique indisponible. Sélectionnez le code manuellement.", true);
    }
  }

  async function savePublicationDataRule() {
    const selected = $$("[data-public-field]:checked").map((node) => node.value);
    const nominal = $$("[data-public-field][data-nominal]:checked").map((node) => node.value);
    const reason = $("#publicationNominalReason").value.trim();
    if (!selected.length) return state("Sélectionnez au moins un champ à publier.", true);
    if (nominal.length && !reason) return state("Justifiez les données nominatives sélectionnées.", true);
    if (!$("#publicationPeriodStart").value || !$("#publicationPeriodEnd").value) return state("Renseignez la période couverte par la publication.", true);
    try {
      const item = await run(
        () => api.apiPost("/api/v1/governance/rules", {
          logical_code: "PUBLIC_DASHBOARD_INDICATORS",
          famille: "PUBLICATION",
          libelle: $("#publicationDataLabel").value.trim(),
          description: "Configuration contrôlée des données proposées au tableau de bord public.",
          version: $("#publicationDataVersion").value.trim(),
          parametres: {
            allowed_indicators: selected.filter((key) => !nominal.includes(key)),
            nominal_fields: nominal,
            nominal_justification: reason || null,
            minimum_aggregation: $("#publicationAggregation").value,
            period_start: $("#publicationPeriodStart").value,
            period_end: $("#publicationPeriodEnd").value,
            disclaimer: "Données publiées après approbation institutionnelle de la HAUQE.",
            direct_publication_forbidden: true,
          },
          date_debut_effet: null,
        }),
        { button: $("#savePublicationDataRule"), title: "Données à publier", message: "Création du brouillon contrôlé" }
      );
      state(`Brouillon ${item.code} créé. Publiez-le ensuite dans l’onglet Règles métier avant toute demande.`);
      await loadRules();
    } catch (error) { state(error?.message || "Création impossible.", true); }
  }

  function switchTab(tab) {
    $$("[data-inst-tab]").forEach((button) => {
      button.classList.toggle("active", button.dataset.instTab === tab);
    });
    $("#completenessTab").hidden = tab !== "completeness";
    $("#codificationTab").hidden = tab !== "codification";
    $("#rulesTab").hidden = tab !== "rules";
    $("#publicationDataTab").hidden = tab !== "publication-data";
    $("#scoringTab").hidden = tab !== "scoring";
    $("#snccTab").hidden = tab !== "sncc";
    $("#fuccsTab").hidden = tab !== "fuccs";

    if (tab === "codification") {
      renderCodificationModels();
      renderCodificationSummary();
    }
    if (tab === "fuccs") {
      loadFuccsGrids();
    }
    if (tab === "sncc") {
      renderSnccMatrixStatus();
    }
  }

  function bind() {
    bindDirectRuleButtons("#addFieldRequirement", () => {
      fieldReqs.push({ id: createClientId("field"), label: "", fields: [], match: "ALL" });
      renderRequirements();
    });
    bindDirectRuleButtons("#addCountRequirement", () => {
      countReqs.push({
        id: createClientId("count"),
        label: "",
        resource: catalog.count_resources?.[0]?.code || "DOCUMENTS",
        minimum: 1,
      });
      renderRequirements();
    });

    bindDirectRuleButtons("#validateCompleteness", validateCompleteness);
    bindDirectRuleButtons("#saveCompletenessDraft", createCompletenessDraft);
    bindDirectRuleButtons("#publishCompleteness", () => {
      if (completenessDraft) openPublish("rule", completenessDraft);
    });

    bindDirectRuleButtons("#newGenericRule", () => openRuleDialog());
    bindDirectRuleButtons("#savePublicationDataRule", savePublicationDataRule);
    bindDirectRuleButtons("#prefillSnccMatrix", () => {
      renderSnccMatrix();
      renderSnccValidation(snccMatrixPayload());
      updateSnccPrefillState("Préremplissage chargé : cinq classes visibles dans le tableau. Modifications non enregistrées.", true);
      $("#snccPrefillDialog").showModal();
      icons();
    });
    bindDirectRuleButtons("#validateSnccMatrix", validateSnccMatrix);
    bindDirectRuleButtons("#saveSnccMatrixDraft", saveSnccMatrixDraft);
    bindDirectRuleButtons("#publishSnccMatrix", () => {
      if (snccDraft) openPublish("rule", snccDraft);
    });
    $("#ruleForm").onsubmit = saveRuleDialog;
    $("#publishForm").onsubmit = publish;

    bindDirectRuleButtons("#newCodificationModel", () => openCodificationBuilder());
    $("#codificationObjectFilter").onchange = renderCodificationModels;
    $("#codificationStatusFilter").onchange = renderCodificationModels;
    bindDirectRuleButtons("#cancelCodificationEdit", closeCodificationBuilder);
    bindDirectRuleButtons("#saveCodificationModel", saveCodificationModel);
    bindDirectRuleButtons("#publishCodificationModel", () => {
      if (editingCodificationRule) openPublish("rule", editingCodificationRule);
    });
    bindDirectRuleButtons("#copyCodificationPreview", copyCodificationPreview);
    [
      "#codificationVersion", "#codificationLabel", "#codificationFormat",
      "#codificationSeparator", "#codificationSequenceLength",
      "#codificationSequenceScope", "#codificationSequenceReset",
      "#codificationConstHauqe", "#codificationConstBnec",
      "#codificationConstCountry", "#codificationConstCertif",
    ].forEach((selector) => {
      $(selector).addEventListener("input", updateCodificationPreview);
      $(selector).addEventListener("change", updateCodificationPreview);
    });
    $("#codificationObject").onchange = (event) => {
      const objectType = event.target.value;
      $("#codificationFormat").value = codificationDefaultFormat(objectType);
      $("#codificationSequenceLength").value = codificationDefaultLength(objectType);
      $("#codificationSequenceScope").value = codificationDefaultScope(objectType);
      if (!$("#codificationLabel").value.trim()) {
        $("#codificationLabel").value = objectType === "CERTIFICATION"
          ? "Modèle de codification des certifications"
          : "Modèle de codification des entreprises BNEC";
      }
      updateCodificationPreview();
    };

    bindDirectRuleButtons("#newScoringModel", () => openModelDialog(false));
    bindDirectRuleButtons("#prefillClassificationReference", () => openModelDialog(true));
    $("#modelForm").onsubmit = createModel;
    $("#weightForm").onsubmit = addWeight;

    $("#scoringObjectFilter").onchange = loadModels;
    $("#scoringStatusFilter").onchange = loadModels;
    $("#ruleStatusFilter").onchange = renderRuleList;

    bindDirectRuleButtons("#newFuccsGrid", () => openFuccsGridDialog());
    bindDirectRuleButtons("#openFuccsHistorical24", (button) => {
      return requestFuccsHistorical24(button);
    });
    bindDirectRuleButtons("#openFuccsHistorical22NoLegalIdentifiers", (button) => {
      return requestFuccsHistorical22NoLegalIdentifiers(button);
    });
    $("#fuccsGridForm").onsubmit = saveFuccsGrid;
    $("#fuccsCloneForm").onsubmit = cloneFuccsGrid;
    $("#fuccsRubricForm").onsubmit = saveFuccsRubric;
    $("#fuccsCriterionForm").onsubmit = saveFuccsCriterion;
    $("#fuccsRetireForm").onsubmit = retireFuccsGrid;
    $("#fuccsDeleteForm").onsubmit = deleteFuccsDraftItem;
    $("#fuccsHistorical24Form").onsubmit = prefillFuccsHistorical24;
    $("#fuccsHistorical22Form").onsubmit = prefillFuccsHistorical22NoLegalIdentifiers;

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
    bindDirectRuleButtons("#generateFuccsRubricCode", generateFuccsRubricCode);

    $("#fuccsCriterionOrder").oninput = () => {
      if (!editingFuccsCriterion) generateFuccsCriterionCode();
      else updateFuccsCriterionCodePreview();
    };
    $("#fuccsCriterionCode").oninput = (event) => {
      event.target.value = normalizeFuccsCode(event.target.value);
      updateFuccsCriterionCodePreview();
    };
    bindDirectRuleButtons("#generateFuccsCriterionCode", generateFuccsCriterionCode);

    $("#fuccsGridStatusFilter").onchange = renderFuccsGridList;
    $("#fuccsGridSearch").oninput = () => {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(renderFuccsGridList, 200);
    };
    $("#ruleSearch").oninput = () => {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(renderRuleList, 200);
    };
    $("#rulePreset").onchange = (event) => applyRulePreset(event.target.value);

    bindDirectRuleButtons("#refreshInstitutional", async (button) => {
      try {
        await run(
          () => Promise.all([
            loadReadiness(),
            loadRules(),
            loadModels(),
            loadFuccsGrids(),
          ]),
          { button, title: "Paramétrage institutionnel", message: "Actualisation" }
        );
      } catch (error) {
        state(error?.message || "Actualisation impossible.", true);
      }
    });

    bindDirectRuleButtons("[data-inst-tab]", (button) => switchTab(button.dataset.instTab));
    bindDirectRuleButtons("[data-close-inst-dialog]", (button) => document.getElementById(button.dataset.closeInstDialog)?.close());

    // Chaque fonction de rendu appelle bindDirectRuleButtons immédiatement
    // après son innerHTML. Aucun MutationObserver global n'est nécessaire :
    // il évite toute activité de fond qui pourrait donner une impression de
    // latence quand une grille FUCCS ou une liste est longue.
    window.__HAUQE_RULES_BUTTON_OBSERVER__?.disconnect?.();
    window.__HAUQE_RULES_BUTTON_OBSERVER__ = null;
    const page = $(".rules-page");
    if (page) stabilizeRuleButtons(page);
  }

  try {
    user = await api.apiGet("/api/v1/me");
    if (!has("GOUVERNANCE.LIRE")) {
      state("Le compte courant ne possède pas GOUVERNANCE.LIRE.", true);
      return;
    }

    bind();

    const requestedTab = sessionStorage.getItem("hauqe-institutional-tab");
    if (requestedTab) {
      sessionStorage.removeItem("hauqe-institutional-tab");
      switchTab(requestedTab);
    }

    const canGovernRules = has("GOUVERNANCE.ADMINISTRER_REGLES");
    const canAdminScoring = has("SCORING.ADMINISTRER_MODELE");
    const canAdminFuccs = has("FUCCS.ADMINISTRER_GRILLE");

    $("#newGenericRule").hidden = !canGovernRules;
    $("#newCodificationModel").hidden = !canGovernRules;
    $("#saveCodificationModel").hidden = !canGovernRules;
    $("#validateCompleteness").hidden = !canGovernRules;
    $("#saveCompletenessDraft").hidden = !canGovernRules;
    $("#addFieldRequirement").hidden = !canGovernRules;
    $("#addCountRequirement").hidden = !canGovernRules;
    $("#prefillSnccMatrix").hidden = !canGovernRules;
    $("#validateSnccMatrix").hidden = !canGovernRules;
    $("#saveSnccMatrixDraft").hidden = !canGovernRules;

    $("#newScoringModel").hidden = !canAdminScoring;
    $("#prefillClassificationReference").hidden = !canAdminScoring;
    $("#newFuccsGrid").hidden = !canAdminFuccs;

    const prefillToolbarButton =
      $("#openFuccsHistorical24");

    if (prefillToolbarButton) {
      prefillToolbarButton.disabled = false;
      prefillToolbarButton.setAttribute(
        "aria-disabled",
        String(!canAdminFuccs)
      );
      prefillToolbarButton.title = canAdminFuccs
        ? (
          "Sélectionnez une grille BROUILLON vide puis "
          + "préremplissez les 24 critères"
        )
        : "Permission FUCCS.ADMINISTRER_GRILLE requise";
    }

    const secondPrefillToolbarButton =
      $("#openFuccsHistorical22NoLegalIdentifiers");
    if (secondPrefillToolbarButton) {
      secondPrefillToolbarButton.disabled = false;
      secondPrefillToolbarButton.setAttribute(
        "aria-disabled",
        String(!canAdminFuccs)
      );
      secondPrefillToolbarButton.title = canAdminFuccs
        ? "Sélectionnez une grille BROUILLON vide puis préremplissez les 22 critères sans RCCM/NIF"
        : "Permission FUCCS.ADMINISTRER_GRILLE requise";
    }

    await Promise.all([
      loadReadiness(),
      loadCatalog(),
      loadRules(),
      loadModels(),
      loadFuccsGrids(),
    ]);

    renderRequirements();
    if (!snccDraft) renderSnccMatrix([]);
    renderSnccMatrixStatus();
  } catch (error) {
    state(error?.message || "Erreur de chargement.", true);
  }

  icons();
})();
