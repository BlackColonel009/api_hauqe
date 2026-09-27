(function () {
  "use strict";

  const $ = (selector) => document.querySelector(selector);

  const hashParts = location.hash.replace(/^#\//, "").split("/");
  const editMode = hashParts[1] === "modifier";

  // Une nouvelle collecte peut être ouverte depuis une mission précise. Cela
  // n'ouvre jamais la fiche d'une autre entreprise de cette mission.
  let missionId = editMode
    ? hashParts[2]
    : (hashParts[1] === "nouveau" ? hashParts[2] || null : null);
  let ficheId = editMode ? hashParts[3] : null;
  let campagneId = null;
  let fiche = null;
  let mission = null;
  let campaign = null;

  let apiGet;
  let apiPost;
  let apiPatch;
  let apiRequest;

  let currentUser = null;
  let workspace = {
    campaigns: [],
    zones: [],
    collectors: [],
    missions: [],
  };

  let assignments = [];
  let offers = [];
  let declaredCertifications = [];
  let documents = [];
  let ficheHistory = [];
  let selectedEnterprise = null;
  let saveOffersPromise = null;
  let saveCertificationsPromise = null;
  let pendingFiles = [];

  let step = 1;
  let enterpriseSearchTimer = null;

  const state = {
    campaign_id: "",
    new_campaign_code: "",
    new_campaign_name: "",
    new_campaign_start: "",
    new_campaign_end: "",

    mission_code: "",
    mission_object: "",
    zone_id: "",
    planned_start: "",
    planned_end: "",
    priority: "",
    assigned_user_id: "",

    entreprise_id: "",
    version_formulaire: "HAUQE-COLLECTE-SIMPLIFIEE-V1",
    consentement_obtenu: false,
    nom_declarant: "",
    fonction_declarant: "",
    telephone_declarant: "",
    email_declarant: "",
    signature_declarant: "",
    observations: "",
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

  function formatDate(value) {
    if (!value) return "—";

    const date = new Date(`${value}T00:00:00`);
    if (Number.isNaN(date.getTime())) return String(value);

    return new Intl.DateTimeFormat("fr-FR", {
      day: "2-digit",
      month: "short",
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

  function formatFileSize(bytes) {
    const size = Number(bytes || 0);
    if (size < 1024) return `${size} o`;
    if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} Ko`;
    return `${(size / (1024 * 1024)).toFixed(1)} Mo`;
  }

  function hasPermission(code) {
    return Array.isArray(currentUser?.permissions)
      && currentUser.permissions.includes(code);
  }

  function isDraft() {
    return !fiche
      || String(fiche.statut || "").toUpperCase() === "BROUILLON";
  }

  function showState(message, { error = false } = {}) {
    const node = $("#collectFormState");
    node.hidden = false;
    node.className =
      `dashboard-api-state ${error ? "error" : ""}`.trim();

    node.innerHTML = `
      ${icon(error ? "triangle-alert" : "info")}
      <div>
        <strong>
          ${error ? "Opération impossible" : "Information"}
        </strong>
        <span>${escapeHtml(message)}</span>
      </div>
    `;

    refreshIcons();
  }

  function hideState() {
    $("#collectFormState").hidden = true;
  }

  function input(
    name,
    label,
    {
      type = "text",
      value = state[name] ?? "",
      required = false,
      placeholder = "",
      disabled = false,
      className = "",
    } = {}
  ) {
    return `
      <div class="form-field${className ? ` ${escapeHtml(className)}` : ""}">
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

  function select(
    name,
    label,
    values,
    {
      current = state[name] || "",
      required = false,
      disabled = false,
      placeholder = "Sélectionner",
      className = "",
    } = {}
  ) {
    return `
      <div class="form-field${className ? ` ${escapeHtml(className)}` : ""}">
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

          ${(values || []).map(([value, label]) => `
            <option
              value="${escapeHtml(value)}"
              ${String(value) === String(current) ? "selected" : ""}
            >
              ${escapeHtml(label)}
            </option>
          `).join("")}
        </select>
      </div>
    `;
  }

  function capture() {
    document.querySelectorAll(
      "#collectFormContent [name]"
    ).forEach((field) => {
      if (field.type === "checkbox") {
        state[field.name] = field.checked;
      } else {
        state[field.name] = field.value;
      }
    });

    const offerRows = Array.from(
      document.querySelectorAll("[data-offer-row]")
    );

    if (offerRows.length) {
      offers = offerRows.map((row) => ({
        id: row.dataset.id || null,
        type_offre:
          row.querySelector('[name="offer_type"]')?.value || "",
        nom:
          row.querySelector('[name="offer_name"]')?.value || "",
        description:
          row.querySelector('[name="offer_description"]')?.value || "",
        categorie:
          row.querySelector('[name="offer_category"]')?.value || "",
        volume:
          row.querySelector('[name="offer_volume"]')?.value || "",
        unite:
          row.querySelector('[name="offer_unit"]')?.value || "",
        capacite:
          row.querySelector('[name="offer_capacity"]')?.value || "",
        marches_vises:
          row.querySelector('[name="offer_markets"]')?.value || "",
        statut: row.dataset.status || "ACTIF",
      }));
    }

    const certRows = Array.from(
      document.querySelectorAll("[data-declared-cert-row]")
    );

    if (certRows.length) {
      declaredCertifications = certRows.map((row) => ({
        id: row.dataset.id || null,
        nom_certification:
          row.querySelector('[name="decl_cert_name"]')?.value || "",
        numero:
          row.querySelector('[name="decl_cert_number"]')?.value || "",
        organisme_declare:
          row.querySelector('[name="decl_cert_body"]')?.value || "",
        norme_declaree:
          row.querySelector('[name="decl_cert_standard"]')?.value || "",
        portee:
          row.querySelector('[name="decl_cert_scope"]')?.value || "",
        date_obtention:
          row.querySelector('[name="decl_cert_issue"]')?.value || "",
        date_expiration:
          row.querySelector('[name="decl_cert_expiry"]')?.value || "",
        copie_disponible:
          row.querySelector('[name="decl_cert_copy"]')?.value || "",
        situation_declaree:
          row.querySelector('[name="decl_cert_situation"]')?.value || "",
        certification_officielle_id:
          row.dataset.officialId || null,
        statut_rapprochement:
          row.dataset.matchStatus || null,
      }));
    }
  }

  function uniqueOffers(items) {
    const seenIds = new Set();
    const seenBusinessKeys = new Set();
    const seenFallbackKeys = new Set();
    return (items || []).filter((item) => {
      const normalize = (value) => String(value ?? "").trim().toUpperCase();
      const businessKey = [
        item.type_offre, item.nom, item.categorie,
      ].map(normalize).join("|");
      const fallbackKey = [
        businessKey, item.description, item.unite, item.marches_vises,
      ].map(normalize).join("|");
      const id = String(item.id || "").trim();
      if (id && seenIds.has(id)) return false;
      if (id) seenIds.add(id);
      if (normalize(item.nom) && seenBusinessKeys.has(businessKey)) return false;
      if (normalize(item.nom)) seenBusinessKeys.add(businessKey);
      if (!normalize(item.nom) && seenFallbackKeys.has(fallbackKey)) return false;
      if (!normalize(item.nom)) seenFallbackKeys.add(fallbackKey);
      return true;
    });
  }

  function uniqueDeclaredCertifications(items) {
    const seenIds = new Set();
    const seenContent = new Set();
    return (items || []).filter((item) => {
      const id = String(item.id || "").trim();
      const key = [
        item.nom_certification, item.numero, item.organisme_declare,
        item.norme_declaree, item.portee, item.date_obtention,
        item.date_expiration,
      ].map((value) => String(value ?? "").trim().toUpperCase()).join("|");
      if (id && seenIds.has(id)) return false;
      if (id) seenIds.add(id);
      if (key && seenContent.has(key)) return false;
      if (key) seenContent.add(key);
      return true;
    });
  }

  function campaignOptions() {
    const values = (workspace.campaigns || []).map((item) => [
      item.id,
      item.label,
    ]);

    if (!editMode && hasPermission("COLLECTE.AFFECTER")) {
      values.unshift([
        "__new__",
        "Créer une nouvelle campagne…",
      ]);
    }

    return values;
  }

  function zoneOptions() {
    return (workspace.zones || []).map((item) => [
      item.id,
      item.label,
    ]);
  }

  function collectorOptions() {
    return (workspace.collectors || []).map((item) => [
      item.id,
      item.label,
    ]);
  }

  function missionOptions() {
    return (workspace.missions || []).map((item) => [
      item.id,
      [item.code || "Mission sans référence", item.objet].filter(Boolean).join(" — "),
    ]);
  }

  function renderStep1() {
    if (!editMode && !fiche) {
      const selected = missionId
        ? (workspace.missions || []).find((item) => String(item.id) === String(missionId))
        : null;
      return `
        <article class="panel form-card">
          <div class="form-card-head">
            <h2>Choisir la mission de collecte</h2>
            <p>Sélectionnez une mission à laquelle vous êtes affecté. La campagne et ses données sont consultées ici, sans être modifiées.</p>
          </div>
          <div class="form-grid">
            ${select("selected_mission_id", "Mission affectée", missionOptions(), { current: missionId || "", required: true, placeholder: "Sélectionnez une mission" })}
          </div>
          ${selected ? `
            <div class="review-section mission-readonly-summary">
              <h3>${escapeHtml(selected.code || "Mission sélectionnée")}</h3>
              <div class="review-row"><span>Campagne</span><strong>${escapeHtml(campaign?.code || campaign?.nom || "—")}</strong></div>
              <div class="review-row"><span>Objet</span><strong>${escapeHtml(selected.objet || "Non renseigné")}</strong></div>
              <div class="review-row"><span>Zone administrative</span><strong>${escapeHtml((workspace.zones || []).find((zone) => String(zone.id) === String(selected.zone_id))?.label || "—")}</strong></div>
              <div class="review-row"><span>Période prévue</span><strong>${escapeHtml([formatDate(selected.date_debut_prevue), formatDate(selected.date_fin_prevue)].filter((value) => value !== "—").join(" → ") || "Non renseignée")}</strong></div>
            </div>
          ` : `<div class="review-warning"><i data-lucide="circle-info"></i><span>La liste contient les missions auxquelles votre compte est affecté. Demandez à l’administrateur HAUQE de vous affecter si la mission n’apparaît pas.</span></div>`}
        </article>
      `;
    }
    const canPlan = hasPermission("COLLECTE.AFFECTER");
    const newCampaign = state.campaign_id === "__new__";

    return `
      <article class="panel form-card">
        <div class="form-card-head">
          <h2>Mission de collecte</h2>
          <p>
            La campagne et la zone structurent la mission.
            L’affectation ne vaut pas validation de la fiche.
          </p>
        </div>

        <div class="form-grid">
          ${select(
            "campaign_id",
            "Campagne",
            campaignOptions(),
            {
              required: true,
              disabled: !canPlan || !isDraft(),
            }
          )}

          ${input(
            "mission_code",
            "Référence mission",
            {
              placeholder: "Peut rester vide si votre procédure le permet",
              disabled: !canPlan,
            }
          )}

          <div class="form-field full zone-picker-field">
            <label>Zone administrative <b>*</b></label>
            <input type="hidden" name="zone_id" value="${escapeHtml(state.zone_id || "")}">
            <div class="zone-picker-control">
              ${icon("search")}
              <input id="collectZoneSearch" type="search" value="${escapeHtml((workspace.zones || []).find(z => String(z.id) === String(state.zone_id))?.label || "")}" placeholder="Rechercher une région, préfecture, commune ou localité…" autocomplete="off" ${!canPlan ? "disabled" : ""}>
              ${canPlan ? `<button type="button" id="openQuickZone" class="btn btn-outline-secondary app-btn"><i data-lucide="map-pin-plus"></i>Créer</button>` : ""}
            </div>
            <div class="zone-picker-results" id="collectZoneResults"></div>
          </div>

          ${select(
            "priority",
            "Priorité",
            [
              ["NORMALE", "Normale"],
              ["HAUTE", "Haute"],
              ["URGENTE", "Urgente"],
            ],
            {
              disabled: !canPlan,
              placeholder: "Non renseignée",
            }
          )}

          ${input(
            "planned_start",
            "Date de début prévue",
            {
              type: "date",
              disabled: !canPlan,
            }
          )}

          ${input(
            "planned_end",
            "Date de fin prévue",
            {
              type: "date",
              disabled: !canPlan,
            }
          )}

          <div class="form-field full">
            <label>Objet de la mission</label>
            <textarea
              name="mission_object"
              rows="3"
              ${!canPlan ? "disabled" : ""}
            >${escapeHtml(state.mission_object || "")}</textarea>
          </div>

          ${select(
            "assigned_user_id",
            "Nouvelle affectation",
            collectorOptions(),
            {
              disabled: !canPlan,
              placeholder: "Aucune nouvelle affectation",
            }
          )}
        </div>

        ${
          newCampaign
            ? `
              <div class="form-subsection">
                <h3>Nouvelle campagne</h3>
                <p>
                  Le compte connecté sera enregistré comme responsable
                  initial de la campagne.
                </p>

                <div class="form-grid">
                  ${input(
                    "new_campaign_code",
                    "Code campagne",
                    {
                      required: true,
                    }
                  )}

                  ${input(
                    "new_campaign_name",
                    "Nom de la campagne"
                  )}

                  ${input(
                    "new_campaign_start",
                    "Début",
                    { type: "date" }
                  )}

                  ${input(
                    "new_campaign_end",
                    "Fin",
                    { type: "date" }
                  )}
                </div>
              </div>
            `
            : ""
        }

        ${
          assignments.length
            ? `
              <div class="review-section">
                <h3>Affectations actuelles</h3>
                ${assignments.map((item) => {
                  const collector = workspace.collectors.find(
                    (user) => String(user.id) === String(item.utilisateur_id)
                  );

                  return `
                    <div class="review-row">
                      <span>
                        ${escapeHtml(
                          collector?.label || item.utilisateur_id
                        )}
                      </span>
                      <strong>
                        ${escapeHtml(item.role_mission || "Agent")}
                        · ${escapeHtml(item.statut || "—")}
                      </strong>
                    </div>
                  `;
                }).join("")}
              </div>
            `
            : ""
        }
      </article>
    `;
  }

  function renderEnterpriseSelection() {
    if (selectedEnterprise) {
      return `
        <div class="existing-company">
          <div>
            ${icon("building-2")}
            <span>
              <strong>
                ${escapeHtml(
                  selectedEnterprise.raison_sociale
                  || selectedEnterprise.nom_commercial
                  || selectedEnterprise.identifiant_national
                )}
              </strong>
              <small>
                ${escapeHtml(
                  selectedEnterprise.identifiant_national || ""
                )}
              </small>
            </span>
          </div>

          ${
            isDraft()
              ? `
                <button
                  type="button"
                  class="btn btn-outline-secondary app-btn"
                  id="changeEnterprise"
                >
                  Changer
                </button>
              `
              : ""
          }
        </div>
      `;
    }

    return `
      <div class="form-field full">
        <label>Rechercher une entreprise du registre</label>

        <div class="collecte-search">
          ${icon("search")}
          <input
            id="enterpriseSearch"
            type="search"
            placeholder="Raison sociale, identifiant ou IFU…"
            autocomplete="off"
          >
        </div>

        <div
          class="enterprise-search-results"
          id="enterpriseSearchResults"
        >
          <div class="document-placeholder">
            Saisissez au moins 2 caractères.
          </div>
        </div>
      </div>
    `;
  }

  function renderStep2() {
    return `
      <article class="panel form-card">
        <div class="form-card-head">
          <h2>Entreprise & déclarant</h2>
          <p>
            La collecte référence l’entreprise du registre au lieu
            de recopier toute sa fiche d’identité.
          </p>
        </div>

        <div class="form-grid">
          <div class="full">
            ${renderEnterpriseSelection()}
          </div>

          ${input(
            "nom_declarant",
            "Nom du déclarant"
          )}

          ${input(
            "fonction_declarant",
            "Fonction du déclarant"
          )}

          ${input(
            "telephone_declarant",
            "Téléphone",
            { type: "tel" }
          )}

          ${input(
            "email_declarant",
            "Email",
            { type: "email" }
          )}

          <div class="form-field">
            <label>Consentement obtenu</label>
            <label class="rule-check">
              <input
                type="checkbox"
                name="consentement_obtenu"
                ${state.consentement_obtenu ? "checked" : ""}
              >
              Le consentement de traitement des données a été recueilli
            </label>
          </div>

          ${input(
            "signature_declarant",
            "Référence / mention de signature",
            {
              placeholder: "Ex. Recueillie sur fiche terrain",
            }
          )}
        </div>

        ${
          hasPermission("COLLECTE.CREER")
            ? `
              <div class="review-warning quick-enterprise-cta">
                ${icon("info")}
                <span>Entreprise absente du registre ? Précréez son dossier incomplet sans quitter la collecte.</span>
                <button class="btn btn-outline-secondary app-btn" id="openQuickEnterprise" type="button"><i data-lucide="building-2"></i>Précréer</button>
              </div>
            `
            : ""
        }
      </article>
    `;
  }

  function offerRow(item = {}) {
    return `
      <div
        class="repeat-entry collect-offer-entry"
        data-offer-row
        ${item.id ? `data-id="${escapeHtml(item.id)}"` : ""}
        data-status="${escapeHtml(item.statut || "ACTIF")}"
      >
        ${select(
          "offer_type",
          "Type",
          [
            ["PRODUIT", "Produit"],
            ["SERVICE", "Service"],
            ["AUTRE", "Autre"],
          ],
          {
            current: item.type_offre || "",
            placeholder: "Non renseigné",
            className: "collect-field-type",
          }
        )}

        ${input(
          "offer_name",
          "Nom",
          {
            value: item.nom || "",
            className: "collect-field-name",
          }
        )}

        ${input(
          "offer_category",
          "Catégorie",
          {
            value: item.categorie || "",
            className: "collect-field-category",
          }
        )}

        ${input(
          "offer_volume",
          "Volume",
          {
            type: "number",
            value: item.volume ?? "",
            className: "collect-field-volume",
          }
        )}

        ${input(
          "offer_unit",
          "Unité",
          {
            value: item.unite || "",
            className: "collect-field-unit",
          }
        )}

        ${input(
          "offer_capacity",
          "Capacité",
          {
            type: "number",
            value: item.capacite ?? "",
            className: "collect-field-capacity",
          }
        )}

        <div class="form-field full">
          <label>Description</label>
          <textarea
            name="offer_description"
            rows="2"
          >${escapeHtml(item.description || "")}</textarea>
        </div>

        <div class="form-field full">
          <label>Marchés visés</label>
          <input
            name="offer_markets"
            value="${escapeHtml(item.marches_vises || "")}"
            placeholder="Ex. marché national, CEDEAO…"
          >
        </div>

        <span data-remove-new-offer-slot></span>
      </div>
    `;
  }

  function renderStep3() {
    const rows = offers.length
      ? offers.map(offerRow).join("")
      : `<div class="entry-list-empty">Aucune offre ajoutée. Utilisez « Ajouter une offre » pour commencer.</div>`;

    return `
      <article class="panel form-card">
        <div class="form-card-head">
          <h2>Produits & services déclarés</h2>
          <p>
            Chaque offre est stockée séparément dans la fiche courante.
          </p>
        </div>

        <div class="entry-list" id="offerList">
          ${rows}
        </div>

        <span id="addOfferSlot"></span>
      </article>
    `;
  }

  function declaredCertificationRow(item = {}) {
    const copyValue = (
      item.copie_disponible === true
        ? "true"
        : item.copie_disponible === false
          ? "false"
          : ""
    );

    return `
      <div
        class="repeat-entry collect-declared-cert-entry"
        data-declared-cert-row
        ${item.id ? `data-id="${escapeHtml(item.id)}"` : ""}
        ${item.certification_officielle_id
          ? `data-official-id="${escapeHtml(item.certification_officielle_id)}"`
          : ""}
        ${item.statut_rapprochement
          ? `data-match-status="${escapeHtml(item.statut_rapprochement)}"`
          : ""}
      >
        ${input(
          "decl_cert_name",
          "Nom de la certification",
          {
            value: item.nom_certification || "",
            className: "collect-field-cert-name",
          }
        )}

        ${input(
          "decl_cert_number",
          "Numéro du certificat",
          {
            value: item.numero || "",
            className: "collect-field-cert-number",
          }
        )}

        ${input(
          "decl_cert_body",
          "Organisme certificateur",
          {
            value: item.organisme_declare || "",
            className: "collect-field-cert-body",
          }
        )}

        ${input(
          "decl_cert_standard",
          "Norme / référentiel du certificat",
          {
            value: item.norme_declaree || "",
            className: "collect-field-cert-standard",
          }
        )}

        <div class="form-field full">
          <label>Portée déclarée</label>
          <textarea
            name="decl_cert_scope"
            rows="2"
          >${escapeHtml(item.portee || "")}</textarea>
        </div>

        ${input(
          "decl_cert_issue",
          "Date d’obtention",
          {
            type: "date",
            value: item.date_obtention || "",
            className: "collect-field-cert-date",
          }
        )}

        ${input(
          "decl_cert_expiry",
          "Date d’expiration",
          {
            type: "date",
            value: item.date_expiration || "",
            className: "collect-field-cert-date",
          }
        )}

        ${select(
          "decl_cert_situation",
          "Situation actuelle déclarée",
          [
            ["PRESENTE", "1 — Présente"],
            ["ABSENTE", "2 — Absente"],
            ["AUDIT_SURVEILLANCE_1", "3 — Audit de surveillance 1"],
            ["AUDIT_SURVEILLANCE_2", "4 — Audit de surveillance 2"],
            ["AUDIT_SURVEILLANCE_3", "5 — Audit de surveillance 3"],
            ["RENOUVELLEMENT", "6 — Renouvellement"],
            ["EXPIREE", "7 — Expirée"],
            ["AUDIT_INITIAL", "8 — Audit initial"],
          ],
          {
            current: item.situation_declaree || "",
            placeholder: "Sélectionner la situation",
            className: "collect-field-cert-situation",
          }
        )}

        ${select(
          "decl_cert_copy",
          "Copie disponible",
          [
            ["true", "Oui"],
            ["false", "Non"],
          ],
          {
            current: copyValue,
            placeholder: "Non renseigné",
            className: "collect-field-cert-copy",
          }
        )}

        ${
          item.certification_officielle_id
            ? `
              <div class="review-warning full">
                ${icon("link")}
                Rapprochée à une certification officielle :
                ${escapeHtml(item.statut_rapprochement || "LIÉE")}
              </div>
            `
            : ""
        }

        <span data-remove-new-cert-slot></span>
      </div>
    `;
  }

  function renderStep4() {
    const rows = declaredCertifications.length
      ? declaredCertifications
          .map(declaredCertificationRow)
          .join("")
      : `<div class="entry-list-empty">Aucune certification déclarée. Utilisez « Ajouter une certification déclarée » pour commencer.</div>`;

    return `
      <article class="panel form-card">
        <div class="form-card-head">
          <h2>Certifications déclarées</h2>
          <p>
            Il s’agit de déclarations de terrain.
            Elles ne deviennent pas automatiquement des certifications BNEC.
          </p>
        </div>

        <div class="entry-list" id="declaredCertList">
          ${rows}
        </div>

        <span id="addDeclaredCertSlot"></span>
      </article>
    `;
  }

  function renderStep5() {
    const savedDocuments = documents.map((item) => `
          <div class="uploaded-file">
            ${icon("file-check")}
            <span>
              <strong>
                ${escapeHtml(item.nom_original || item.type_document)}
              </strong>
              <small>
                ${escapeHtml(item.statut_verification || "Non vérifié")}
              </small>
            </span>
          </div>
        `).join("");
    const selectedDocuments = pendingFiles.map((file, index) => `
          <div class="uploaded-file pending-upload">
            ${icon("file-up")}
            <span>
              <strong>${escapeHtml(file.name)}</strong>
              <small>Sélectionné - ${escapeHtml(formatFileSize(file.size))}</small>
            </span>
            <span data-remove-pending-file-slot="${index}"></span>
          </div>
        `).join("");
    const documentList = savedDocuments || selectedDocuments
      ? `${savedDocuments}${selectedDocuments}`
      : `
        <div class="document-placeholder">
          Aucun document enregistré ou sélectionné.
        </div>
      `;

    return `
      <article class="panel form-card">
        <div class="form-card-head">
          <h2>Preuves & observations</h2>
          <p>
            Les documents sont déposés dans le stockage privé
            et rattachés à la fiche de collecte.
          </p>
        </div>

        ${
          hasPermission("DOCUMENTS.DEPOSER") && isDraft()
            ? `
              <div class="document-drop">
                ${icon("cloud-upload")}
                <strong>Ajouter des justificatifs</strong>
                <span>PDF, PNG ou JPEG</span>
                <input
                  id="collectFiles"
                  type="file"
                  multiple
                  accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg"
                >
              </div>
            `
            : ""
        }

        <div class="uploaded-files" id="uploadedFiles">
          ${documentList}
        </div>

        <div class="form-grid">
          <div class="form-field full">
            <label>Observations de collecte</label>
            <textarea
              name="observations"
              rows="5"
            >${escapeHtml(state.observations || "")}</textarea>
          </div>
        </div>
      </article>
    `;
  }

  function renderStep6() {
    const completeness = (
      fiche?.taux_completude === null
      || fiche?.taux_completude === undefined
    )
      ? "Non calculée"
      : `${Number(fiche.taux_completude).toFixed(2)} %`;

    return `
      <article class="panel form-card">
        <div class="form-card-head">
          <h2>Contrôle & soumission</h2>
          <p>
            Le taux et le seuil de soumission sont déterminés
            par la règle métier publiée côté serveur.
          </p>
        </div>

        <div class="completion-banner">
          <span>${icon("gauge")}</span>
          <div>
            <strong>Complétude backend</strong>
            <small>
              Le frontend ne recalcule pas un taux parallèle.
            </small>
          </div>
          <b>${escapeHtml(completeness)}</b>
        </div>

        <div class="review-layout">
          <section class="review-section">
            <h3>Mission</h3>
            <div class="review-row">
              <span>Référence</span>
              <strong>${escapeHtml(state.mission_code || "—")}</strong>
            </div>
            <div class="review-row">
              <span>Zone</span>
              <strong>
                ${escapeHtml(
                  workspace.zones.find(
                    (item) => String(item.id) === String(state.zone_id)
                  )?.label || "—"
                )}
              </strong>
            </div>
          </section>

          <section class="review-section">
            <h3>Entreprise</h3>
            <div class="review-row">
              <span>Titulaire</span>
              <strong>
                ${escapeHtml(
                  selectedEnterprise?.raison_sociale
                  || selectedEnterprise?.nom_commercial
                  || "Non renseignée"
                )}
              </strong>
            </div>
            <div class="review-row">
              <span>Consentement</span>
              <strong>
                ${state.consentement_obtenu ? "Oui" : "Non"}
              </strong>
            </div>
          </section>

          <section class="review-section">
            <h3>Déclarations</h3>
            <div class="review-row">
              <span>Offres</span>
              <strong>${offers.filter(item => item.nom || item.type_offre).length}</strong>
            </div>
            <div class="review-row">
              <span>Certifications déclarées</span>
              <strong>
                ${declaredCertifications.filter(
                  item => item.nom_certification
                    || item.numero
                    || item.norme_declaree
                ).length}
              </strong>
            </div>
            <div class="review-row">
              <span>Documents</span>
              <strong>${documents.length + pendingFiles.length}</strong>
            </div>
          </section>

          <section class="review-section">
            <h3>Fiche</h3>
            <div class="review-row">
              <span>Révision</span>
              <strong>${escapeHtml(fiche?.numero_revision || "—")}</strong>
            </div>
            <div class="review-row">
              <span>Statut</span>
              <strong>${escapeHtml(fiche?.statut || "BROUILLON")}</strong>
            </div>
            <div class="review-row">
              <span>Dernière collecte</span>
              <strong>${escapeHtml(formatDateTime(fiche?.collecte_at))}</strong>
            </div>
          </section>
        </div>

        <div class="review-warning">
          ${icon("shield-check")}
          La soumission sera refusée par FastAPI si aucune règle
          COLLECTE_COMPLETUDE active n’existe ou si le seuil publié
          n’est pas atteint.
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
    6: renderStep6,
  };

  function applyReadOnlyState() {
    if (isDraft()) return;

    document.querySelectorAll(
      "#collectFormContent input,"
      + "#collectFormContent select,"
      + "#collectFormContent textarea,"
      + "#collectFormContent .add-entry,"
      + "#collectFormContent .remove-entry"
    ).forEach((node) => {
      node.disabled = true;
    });
  }

  function applySelectedCampaign(selectedCampaign, campaignMission = null) {
    campaign = selectedCampaign;
    const keepCurrentDraft = Boolean(missionId && fiche && isDraft());
    if (!keepCurrentDraft) {
      mission = null;
      missionId = null;
      fiche = null;
    }
    campagneId = selectedCampaign.id || state.campaign_id;

    Object.assign(state, {
      campaign_id: campagneId,
      mission_code: selectedCampaign.code || "",
      mission_object: selectedCampaign.objet || selectedCampaign.objectif || campaignMission?.objet || selectedCampaign.nom || "",
      zone_id: campaignMission?.zone_id || "",
      planned_start: selectedCampaign.date_debut || "",
      planned_end: selectedCampaign.date_fin || "",
      priority: campaignMission?.priorite || "",
    });
  }

  async function selectExistingCampaign(campaignId) {
    const [selectedCampaign, missionsResponse] = await Promise.all([
      apiGet(`/api/v1/campagnes/${encodeURIComponent(campaignId)}`),
      apiGet(`/api/v1/campagnes/${encodeURIComponent(campaignId)}/missions?limit=200`),
    ]);
    const missions = Array.isArray(missionsResponse) ? missionsResponse : (missionsResponse.items || []);
    const campaignMission = missions.find((item) => item.zone_id || item.priorite || item.objet) || null;
    applySelectedCampaign(selectedCampaign, campaignMission);
    render(false);
    showState("Informations de la campagne reprises. Complétez ce premier formulaire avant de poursuivre.");
  }

  function createDirectEntryButton({ label, iconName, className, onClick, title = "" }) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = className;
    button.setAttribute("data-no-action-loader", "true");
    if (title) button.title = title;
    button.setAttribute("aria-label", title || label);
    button.innerHTML = `${icon(iconName)}${label ? `<span>${escapeHtml(label)}</span>` : ""}`;
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      onClick(button);
    });
    return button;
  }

  async function removeNewEntry(button, rowSelector, getEntries, endpointFor) {
    // L'index est calculé à partir des lignes réellement affichées, après
    // capture des saisies : plusieurs ajouts et suppressions restent fiables.
    capture();
    const entries = getEntries();
    const rows = Array.from(document.querySelectorAll(rowSelector));
    const index = rows.indexOf(button.closest(rowSelector));
    if (index < 0 || !entries[index]) return;
    try {
      if (entries[index].id) {
        if (!fiche || !isDraft()) {
          showState("Seules les lignes d’une fiche brouillon peuvent être retirées.", { error: true });
          return;
        }
        await apiRequest(endpointFor(entries[index].id), { method: "DELETE" });
      }
      entries.splice(index, 1);
      render(false);
    } catch (error) {
      showState(error?.message || "Suppression impossible.", { error: true });
    }
  }

  function hydrateCollectionEntryActions() {
    const offerSlot = $("#addOfferSlot");
    if (offerSlot) {
      offerSlot.replaceChildren(createDirectEntryButton({
        label: "Ajouter une offre",
        iconName: "plus",
        className: "btn btn-outline-secondary app-btn add-entry",
        onClick: () => { capture(); offers.push({}); render(false); },
      }));
    }
    document.querySelectorAll("[data-remove-new-offer-slot]").forEach((slot) => {
      slot.replaceChildren(createDirectEntryButton({
        label: "", iconName: "trash-2", className: "remove-entry",
        title: "Retirer cette offre",
        onClick: (button) => removeNewEntry(
          button, "[data-offer-row]", () => offers,
          (id) => `/api/v1/missions/${missionId}/fiches/${fiche.id}/offres/${id}`,
        ),
      }));
    });

    const certificationSlot = $("#addDeclaredCertSlot");
    if (certificationSlot) {
      certificationSlot.replaceChildren(createDirectEntryButton({
        label: "Ajouter une certification déclarée",
        iconName: "plus",
        className: "btn btn-outline-secondary app-btn add-entry",
        onClick: () => { capture(); declaredCertifications.push({}); render(false); },
      }));
    }
    document.querySelectorAll("[data-remove-new-cert-slot]").forEach((slot) => {
      slot.replaceChildren(createDirectEntryButton({
        label: "", iconName: "trash-2", className: "remove-entry",
        title: "Retirer cette certification déclarée",
        onClick: (button) => removeNewEntry(
          button, "[data-declared-cert-row]", () => declaredCertifications,
          (id) => `/api/v1/missions/${missionId}/fiches/${fiche.id}/certifications/${id}`,
        ),
      }));
    });

    document.querySelectorAll("[data-remove-pending-file-slot]").forEach((slot) => {
      const index = Number(slot.dataset.removePendingFileSlot);
      slot.replaceChildren(createDirectEntryButton({
        label: "", iconName: "x", className: "pending-file-remove",
        title: "Retirer ce fichier sélectionné",
        onClick: () => {
          pendingFiles.splice(index, 1);
          render(false);
        },
      }));
    });
  }

  function bindStepContent() {
    const missionSelect = document.querySelector('[name="selected_mission_id"]');
    if (missionSelect && !editMode && !fiche) {
      missionSelect.addEventListener("change", async (event) => {
        if (!event.target.value) {
          missionId = null;
          campaign = null;
          assignments = [];
          render(false);
          return;
        }
        try {
          await selectExistingMission(event.target.value);
          render(false);
          showState("Mission sélectionnée. Continuez avec l’entreprise concernée par cette collecte.");
        } catch (error) {
          showState(error?.message || "Impossible de charger cette mission.", { error: true });
        }
      });
    }
    const campaignSelect = document.querySelector(
      '[name="campaign_id"]'
    );

    if (campaignSelect && isDraft()) {
      campaignSelect.addEventListener("change", async (event) => {
        capture();
        state.campaign_id = event.target.value;
        hideState();

        if (!state.campaign_id || state.campaign_id === "__new__") {
          if (missionId) {
            state.campaign_id = mission?.campagne_id || campagneId || "";
            render(false);
            showState(
              "Sélectionnez une campagne existante pour cette mission brouillon.",
              { error: true }
            );
            return;
          }
          mission = null;
          missionId = null;
          campagneId = null;
          render();
          return;
        }

        try {
          await selectExistingCampaign(state.campaign_id);
        } catch (error) {
          render();
          showState(
            error?.message || "Impossible de charger la mission de cette campagne.",
            { error: true }
          );
        }
      });
    }

    $("#collectZoneSearch")?.addEventListener("focus", event => renderZoneMatches(event.target.value));
    $("#collectZoneSearch")?.addEventListener("input", event => renderZoneMatches(event.target.value));
    $("#openQuickZone")?.addEventListener("click", openQuickZoneDialog);
    $("#openQuickEnterprise")?.addEventListener("click", () => openQuickEnterpriseDialog());

    $("#changeEnterprise")?.addEventListener("click", () => {
      if (!isDraft()) return;
      selectedEnterprise = null;
      state.entreprise_id = "";
      render();
    });

    $("#enterpriseSearch")?.addEventListener(
      "input",
      (event) => {
        clearTimeout(enterpriseSearchTimer);
        const query = event.target.value.trim();

        if (query.length < 2) {
          $("#enterpriseSearchResults").innerHTML = `
            <div class="document-placeholder">
              Saisissez au moins 2 caractères.
            </div>
          `;
          return;
        }

        enterpriseSearchTimer = setTimeout(
          () => searchEnterprises(query),
          300
        );
      }
    );

    hydrateCollectionEntryActions();

    $("#collectFiles")?.addEventListener(
      "change",
      (event) => {
        pendingFiles = Array.from(event.target.files || []);
        render();
      }
    );

    applyReadOnlyState();
    refreshIcons();
  }

  async function selectExistingMission(selectedMissionId) {
    const selectedMission = await apiGet(`/api/v1/missions/${encodeURIComponent(selectedMissionId)}`);
    const selectedCampaign = await apiGet(`/api/v1/campagnes/${encodeURIComponent(selectedMission.campagne_id)}`);
    const selectedAssignments = await apiGet(`/api/v1/missions/${encodeURIComponent(selectedMissionId)}/affectations`);
    missionId = selectedMission.id;
    mission = selectedMission;
    campaign = selectedCampaign;
    campagneId = selectedMission.campagne_id;
    assignments = selectedAssignments;
    Object.assign(state, {
      campaign_id: selectedMission.campagne_id,
      mission_code: selectedMission.code || "",
      mission_object: selectedMission.objet || "",
      zone_id: selectedMission.zone_id || "",
      planned_start: selectedMission.date_debut_prevue || "",
      planned_end: selectedMission.date_fin_prevue || "",
      priority: selectedMission.priorite || "",
      assigned_user_id: "",
    });
  }

  function render(captureCurrent = true) {
    if (captureCurrent) capture();

    $("#collectFormContent").innerHTML =
      renderers[step]();

    $("#collectProgress").textContent =
      `Étape ${step} sur 6`;

    $("#collectPrevious").hidden = step === 1;
    $("#collectNext").hidden = step === 6;

    document.querySelectorAll(
      "#collectStepper button"
    ).forEach((button) => {
      const number = Number(button.dataset.step);

      button.classList.toggle(
        "active",
        number === step
      );

      button.classList.toggle(
        "completed",
        number < step
      );
    });

    bindStepContent();
  }

  async function searchEnterprises(query) {
    const container = $("#enterpriseSearchResults");

    try {
      const payload = await apiGet(
        `/api/v1/entreprises?search=${encodeURIComponent(query)}&limit=10&offset=0`
      );

      const items = payload.items || [];

      if (!items.length) {
        container.innerHTML = `
          <div class="document-placeholder quick-empty-company">
            <span>Aucune entreprise trouvée.</span>
            ${hasPermission("COLLECTE.CREER") ? `<button type="button" class="btn btn-outline-secondary app-btn" id="createFromEnterpriseSearch"><i data-lucide="building-2"></i>Précréer « ${escapeHtml(query)} »</button>` : ""}
          </div>
        `;
        $("#createFromEnterpriseSearch")?.addEventListener("click", () => openQuickEnterpriseDialog(query));
        refreshIcons();
        return;
      }

      container.innerHTML = items.map((item) => `
        <button
          type="button"
          class="cert-doc-row"
          data-enterprise-id="${escapeHtml(item.id)}"
        >
          <span>${icon("building-2")}</span>
          <div>
            <strong>
              ${escapeHtml(
                item.raison_sociale
                || item.nom_commercial
                || item.identifiant_national
              )}
            </strong>
            <small>
              ${escapeHtml(item.identifiant_national || "")}
            </small>
          </div>
          <span class="more-button">${icon("check")}</span>
        </button>
      `).join("");

      container
        .querySelectorAll("[data-enterprise-id]")
        .forEach((button) => {
          button.addEventListener("click", async () => {
            selectedEnterprise = await apiGet(
              `/api/v1/entreprises/${button.dataset.enterpriseId}`
            );

            state.entreprise_id = selectedEnterprise.id;
            render();
          });
        });

      refreshIcons();
    } catch (error) {
      container.innerHTML = `
        <div class="document-placeholder">
          ${escapeHtml(error?.message || "Recherche impossible.")}
        </div>
      `;
    }
  }


function activeZoneOptions(excludeId = null) {
  return (workspace.zones || []).filter(z => String(z.id) !== String(excludeId || ""));
}

function renderZoneMatches(query = "") {
  const box = $("#collectZoneResults");
  if (!box) return;
  const q = query.trim().toLowerCase();
  const matches = activeZoneOptions().filter(z => !q || String(z.label || z.nom || "").toLowerCase().includes(q)).slice(0, 12);
  box.innerHTML = matches.map(z => `<button type="button" data-collect-zone="${escapeHtml(z.id)}"><span>${icon("map-pin")}</span><div><strong>${escapeHtml(z.label || z.nom || "Zone")}</strong><small>${escapeHtml(z.type_zone || "")}</small></div></button>`).join("") || `<div class="document-placeholder">Aucune zone correspondante.</div>`;
  box.querySelectorAll('[data-collect-zone]').forEach(button => button.onclick = () => {
    const zone = activeZoneOptions().find(z => String(z.id) === String(button.dataset.collectZone));
    if (!zone) return;
    state.zone_id = zone.id;
    const hidden = document.querySelector('[name="zone_id"]');
    if (hidden) hidden.value = zone.id;
    const search = $("#collectZoneSearch");
    if (search) search.value = zone.label || zone.nom || "";
    box.innerHTML = "";
  });
  refreshIcons();
}

function openQuickZoneDialog() {
  const parent = $("#quickZoneParent");
  parent.innerHTML = '<option value="">Aucune</option>' + activeZoneOptions().map(z => `<option value="${escapeHtml(z.id)}">${escapeHtml(z.label || z.nom || "Zone")}</option>`).join("");
  $("#quickZoneName").value = $("#collectZoneSearch")?.value.trim() || "";
  $("#quickZoneCode").value = "";
  $("#quickZoneType").value = "LOCALITE";
  $("#quickZoneDialog").showModal();
  refreshIcons();
}

async function saveQuickZone(event) {
  event.preventDefault();
  try {
    const created = await apiPost('/api/v1/zones-administratives/quick-create', {
      type_zone: $("#quickZoneType").value,
      code: $("#quickZoneCode").value.trim() || null,
      nom: $("#quickZoneName").value.trim(),
      parent_id: $("#quickZoneParent").value || null,
    });
    workspace.zones = [...(workspace.zones || []), {id: created.id, label: created.path || created.nom, nom: created.nom, type_zone: created.type_zone}];
    state.zone_id = created.id;
    $("#quickZoneDialog").close();
    render();
    showState('Zone créée et sélectionnée dans la mission.');
  } catch (error) { showState(error?.message || 'Création de la zone impossible.', {error:true}); }
}

function openQuickEnterpriseDialog(defaultName = "") {
  if (!state.zone_id) { showState('Sélectionnez d’abord la zone administrative de la mission.', {error:true}); return; }
  const zone = (workspace.zones || []).find(z => String(z.id) === String(state.zone_id));
  $("#quickEnterpriseName").value = defaultName || $("#enterpriseSearch")?.value.trim() || "";
  $("#quickEnterpriseZoneLabel").value = zone?.label || zone?.nom || state.zone_id;
  $("#quickEnterpriseAddress").value = zone?.label || zone?.nom || "";
  $("#quickEnterpriseLatitude").value = "";
  $("#quickEnterpriseLongitude").value = "";
  $("#quickEnterprisePhone").value = state.telephone_declarant || "";
  $("#quickEnterpriseEmail").value = state.email_declarant || "";
  $("#quickEnterpriseDialog").showModal();
  refreshIcons();
}

async function saveQuickEnterprise(event) {
  event.preventDefault();
  try {
    const created = await apiPost('/api/v1/collectes/quick-enterprises', {
      raison_sociale: $("#quickEnterpriseName").value.trim(),
      zone_siege_id: state.zone_id,
      adresse_siege: $("#quickEnterpriseAddress").value.trim() || null,
      latitude: $("#quickEnterpriseLatitude").value || null,
      longitude: $("#quickEnterpriseLongitude").value || null,
      telephone_principal: $("#quickEnterprisePhone").value.trim() || null,
      email_principal: $("#quickEnterpriseEmail").value.trim() || null,
    });
    selectedEnterprise = created;
    state.entreprise_id = created.id;
    $("#quickEnterpriseDialog").close();
    render();
    showState('Entreprise précréée. Son dossier reste marqué À compléter dans le registre.');
  } catch (error) {
    const detail = error?.detail;
    const enterpriseId = detail?.entreprise_id;
    if (enterpriseId) {
      selectedEnterprise = await apiGet(`/api/v1/entreprises/${enterpriseId}`);
      state.entreprise_id = selectedEnterprise.id;
      $("#quickEnterpriseDialog").close();
      render();
      showState('Une entreprise identique existait déjà : elle a été sélectionnée.');
      return;
    }
    showState(error?.message || 'Précréation impossible.', {error:true});
  }
}

function locateQuickEnterprise() {
  if (!navigator.geolocation) {
    showState("La géolocalisation n’est pas disponible dans ce navigateur. Saisissez les coordonnées manuellement.", {error: true});
    return;
  }
  const button = $("#quickEnterpriseLocate");
  button.disabled = true;
  button.innerHTML = `${icon("loader-circle")}Localisation…`;
  navigator.geolocation.getCurrentPosition(
    (position) => {
      $("#quickEnterpriseLatitude").value = Number(position.coords.latitude).toFixed(6);
      $("#quickEnterpriseLongitude").value = Number(position.coords.longitude).toFixed(6);
      button.disabled = false;
      button.innerHTML = `${icon("locate-fixed")}Position récupérée`;
      refreshIcons();
    },
    (error) => {
      button.disabled = false;
      button.innerHTML = `${icon("locate-fixed")}Utiliser ma position`;
      refreshIcons();
      const messages = {
        1: "L’accès à la position a été refusé. Vous pouvez saisir latitude et longitude manuellement.",
        2: "La position est indisponible. Réessayez ou saisissez les coordonnées manuellement.",
        3: "La localisation a expiré. Réessayez ou saisissez les coordonnées manuellement.",
      };
      showState(messages[error?.code] || "Localisation impossible.", {error: true});
    },
    { enableHighAccuracy: true, timeout: 12000, maximumAge: 60000 }
  );
}

  function validateDates(start, end, label) {
    if (start && end && end < start) {
      showState(
        `La date de fin ${label} doit être postérieure ou égale au début.`,
        { error: true }
      );
      return false;
    }

    return true;
  }

  function validateCurrentStep() {
    capture();
    hideState();

    if (step === 1) {
      if (!editMode && !fiche) {
        if (!missionId) {
          showState(
            "Sélectionnez une mission affectée avant de commencer une collecte.",
            { error: true }
          );
          return false;
        }
        return true;
      }
      if (!hasPermission("COLLECTE.AFFECTER") && !missionId) {
        showState(
          "Vous n’avez pas la permission de créer une mission.",
          { error: true }
        );
        return false;
      }

      if (!state.campaign_id || !state.zone_id) {
        showState(
          "La campagne et la zone sont obligatoires.",
          { error: true }
        );
        return false;
      }

      if (
        state.campaign_id === "__new__"
        && !state.new_campaign_code.trim()
      ) {
        showState(
          "Le code de la nouvelle campagne est obligatoire.",
          { error: true }
        );
        return false;
      }

      if (
        !validateDates(
          state.planned_start,
          state.planned_end,
          "prévue"
        )
      ) {
        return false;
      }

      if (
        state.campaign_id === "__new__"
        && !validateDates(
          state.new_campaign_start,
          state.new_campaign_end,
          "de campagne"
        )
      ) {
        return false;
      }
    }

    if (step === 4) {
      const invalid = declaredCertifications.find((item) => (
        item.date_obtention
        && item.date_expiration
        && item.date_expiration < item.date_obtention
      ));

      if (invalid) {
        showState(
          "Une certification déclarée possède une expiration antérieure à sa date d’obtention.",
          { error: true }
        );
        return false;
      }
    }

    return true;
  }

  async function createCampaignIfNeeded() {
    if (state.campaign_id !== "__new__") {
      campagneId = state.campaign_id;
      return;
    }

    if (!hasPermission("COLLECTE.AFFECTER")) {
      throw new Error(
        "Permission COLLECTE.AFFECTER requise pour créer une campagne."
      );
    }

    const created = await apiPost(
      "/api/v1/campagnes",
      {
        code: state.new_campaign_code.trim(),
        nom: state.new_campaign_name.trim() || null,
        objet: null,
        objectif: null,
        date_debut: state.new_campaign_start || null,
        date_fin: state.new_campaign_end || null,
        responsable_id: currentUser.id,
        statut: "ACTIVE",
      }
    );

    campagneId = created.id;
    state.campaign_id = created.id;

    workspace.campaigns.unshift({
      id: created.id,
      code: created.code,
      label: created.nom
        ? `${created.code} — ${created.nom}`
        : created.code,
    });
  }

  function missionPayload() {
    return {
      code: state.mission_code.trim() || null,
      objet: state.mission_object.trim() || null,
      zone_id: state.zone_id,
      date_debut_prevue: state.planned_start || null,
      date_fin_prevue: state.planned_end || null,
      date_debut_reelle: null,
      date_fin_reelle: null,
      priorite: state.priority || null,
      progression: mission?.progression ?? 0,
      statut: mission?.statut || "PLANIFIEE",
    };
  }

  function fichePayload() {
    return {
      entreprise_id: state.entreprise_id || null,
      version_formulaire:
        state.version_formulaire || "HAUQE-COLLECTE-SIMPLIFIEE-V1",
      consentement_obtenu:
        Boolean(state.consentement_obtenu),
      nom_declarant:
        state.nom_declarant.trim() || null,
      fonction_declarant:
        state.fonction_declarant.trim() || null,
      telephone_declarant:
        state.telephone_declarant.trim() || null,
      email_declarant:
        state.email_declarant.trim() || null,
      signature_declarant:
        state.signature_declarant.trim() || null,
      observations:
        state.observations.trim() || null,
    };
  }

  async function ensureMissionAndFiche() {
    if (!fiche) {
      if (!missionId) {
        throw new Error(
          "Sélectionnez d’abord une mission de collecte à laquelle vous êtes affecté."
        );
      }
      if (!hasPermission("COLLECTE.CREER")) {
        throw new Error("Permission COLLECTE.CREER requise pour démarrer la fiche.");
      }
      fiche = await apiPost(
        `/api/v1/missions/${missionId}/fiches`,
        fichePayload()
      );
      ficheId = fiche.id;

      window.history.replaceState(
        null,
        "",
        `#/collectes/modifier/${missionId}/${fiche.id}`
      );

      $("#collectFormMode").textContent = "Modification";
      $("#collectFormTitle").textContent =
        `Mission ${mission.code || mission.id}`;

      return;
    }
    if (isDraft()) {
      if (!hasPermission("COLLECTE.MODIFIER")) {
        throw new Error(
          "Permission COLLECTE.MODIFIER requise."
        );
      }

      fiche = await apiPatch(
        `/api/v1/missions/${missionId}/fiches/${fiche.id}`,
        fichePayload()
      );
    }
  }

  async function addAssignment(userId) {
    const duplicate = assignments.some(
      (item) => (
        String(item.utilisateur_id) === String(userId)
        && String(item.statut || "").toUpperCase() !== "INACTIF"
      )
    );

    if (duplicate) return;

    const created = await apiPost(
      `/api/v1/missions/${missionId}/affectations`,
      {
        utilisateur_id: userId,
        role_mission: "AGENT_COLLECTE",
        date_debut: state.planned_start || null,
        date_fin: state.planned_end || null,
        motif: "Affectation depuis l’espace Collecte",
        statut: "ACTIF",
      }
    );

    assignments.push(created);
  }

  function offerPayload(item) {
    return {
      type_offre: item.type_offre || null,
      nom: item.nom || null,
      description: item.description || null,
      categorie: item.categorie || null,
      volume: item.volume === "" ? null : Number(item.volume),
      unite: item.unite || null,
      capacite:
        item.capacite === ""
          ? null
          : Number(item.capacite),
      marches_vises: item.marches_vises || null,
      statut: item.statut || "ACTIF",
    };
  }

  async function saveOffers() {
    if (!fiche || !isDraft()) return;
    if (saveOffersPromise) return saveOffersPromise;

    saveOffersPromise = (async () => {
      const saved = [];

      for (const item of uniqueOffers(offers)) {
      const hasValue = [
        item.type_offre,
        item.nom,
        item.description,
        item.categorie,
        item.volume,
        item.unite,
        item.capacite,
        item.marches_vises,
      ].some((value) => (
        value !== null
        && value !== undefined
        && String(value).trim() !== ""
      ));

      if (!hasValue && !item.id) continue;

      let result;

      if (item.id) {
        result = await apiPatch(
          `/api/v1/missions/${missionId}/fiches/${fiche.id}/offres/${item.id}`,
          offerPayload(item)
        );
      } else {
        result = await apiPost(
          `/api/v1/missions/${missionId}/fiches/${fiche.id}/offres`,
          offerPayload(item)
        );
      }

        saved.push(result);
      }

      offers = uniqueOffers(saved);
    })();

    try {
      return await saveOffersPromise;
    } finally {
      saveOffersPromise = null;
    }
  }

  function declaredCertificationPayload(item) {
    let copy = null;

    if (
      item.copie_disponible === true
      || item.copie_disponible === "true"
    ) {
      copy = true;
    } else if (
      item.copie_disponible === false
      || item.copie_disponible === "false"
    ) {
      copy = false;
    }

    return {
      nom_certification:
        item.nom_certification || null,
      numero:
        item.numero || null,
      organisme_declare:
        item.organisme_declare || null,
      norme_declaree:
        item.norme_declaree || null,
      portee:
        item.portee || null,
      date_obtention:
        item.date_obtention || null,
      date_expiration:
        item.date_expiration || null,
      copie_disponible:
        copy,
      situation_declaree:
        item.situation_declaree || null,
    };
  }

  async function saveDeclaredCertifications() {
    if (!fiche || !isDraft()) return;
    if (saveCertificationsPromise) return saveCertificationsPromise;

    saveCertificationsPromise = (async () => {
      const saved = [];

      for (const item of uniqueDeclaredCertifications(declaredCertifications)) {
      const hasValue = [
        item.nom_certification,
        item.numero,
        item.organisme_declare,
        item.norme_declaree,
        item.portee,
        item.date_obtention,
        item.date_expiration,
        item.situation_declaree,
      ].some((value) => (
        value !== null
        && value !== undefined
        && String(value).trim() !== ""
      ));

      if (!hasValue && !item.id) continue;

      let result;

      if (item.id) {
        result = await apiPatch(
          `/api/v1/missions/${missionId}/fiches/${fiche.id}/certifications/${item.id}`,
          declaredCertificationPayload(item)
        );
      } else {
        result = await apiPost(
          `/api/v1/missions/${missionId}/fiches/${fiche.id}/certifications`,
          declaredCertificationPayload(item)
        );
      }

        saved.push(result);
      }

      declaredCertifications = uniqueDeclaredCertifications(saved);
    })();

    try {
      return await saveCertificationsPromise;
    } finally {
      saveCertificationsPromise = null;
    }
  }

  async function uploadPendingDocuments() {
    if (
      !fiche
      || !isDraft()
      || !pendingFiles.length
    ) {
      return;
    }

    if (!hasPermission("DOCUMENTS.DEPOSER")) {
      throw new Error(
        "Permission DOCUMENTS.DEPOSER requise pour ajouter des fichiers."
      );
    }

    for (const file of pendingFiles) {
      const body = new FormData();

      body.append("file", file);
      body.append("type_document", "JUSTIFICATIF_COLLECTE");
      body.append("ressource_type", "FICHE_COLLECTE");
      body.append("ressource_id", fiche.id);
      body.append("confidentialite", "INTERNE");
      body.append("source", "FORMULAIRE_COLLECTE");

      const uploaded = await apiPost(
        "/api/v1/documents/upload",
        body
      );

      documents.push(uploaded);
    }

    pendingFiles = [];
  }

  async function refreshFiche() {
    if (!missionId) return;

    fiche = await apiGet(
      `/api/v1/missions/${missionId}/fiches/${ficheId || fiche.id}`
    );
  }

  async function saveCurrentStep() {
    capture();

    await ensureMissionAndFiche();

    if (step >= 3) {
      await saveOffers();
    }

    if (step >= 4) {
      await saveDeclaredCertifications();
    }

    if (step >= 5) {
      await uploadPendingDocuments();
    }

    await refreshFiche();
  }

  async function saveAll() {
    capture();

    await ensureMissionAndFiche();
    await saveOffers();
    await saveDeclaredCertifications();
    await uploadPendingDocuments();
    await refreshFiche();
  }

  async function createRevision(event) {
    if (!fiche || isDraft()) return;

    const commentaire = window.prompt(
      "Motif de création de la nouvelle révision :"
    );

    if (!commentaire?.trim()) return;

    const task = async () => {
      fiche = await apiPost(
        `/api/v1/missions/${missionId}/fiches/${fiche.id}/revision`,
        {
          commentaire: commentaire.trim(),
        }
      );

      await loadFicheSubresources();
      updateActionState();
      render();

      if (fiche?.id) {
        const { renderDossierParcours } = await import("/static/js/core/dossier-parcours.js?v=20260921-1");
        await renderDossierParcours({
          target: "#collecteDossierParcours",
          source: "fiche",
          resourceId: fiche.id,
          apiGet,
        });
      }
    };

    try {
      if (window.HAUQE_ACTION_LOADER) {
        await window.HAUQE_ACTION_LOADER.run(task, {
          button: event.currentTarget,
          title: "Nouvelle révision",
          message: "Création du brouillon suivant",
          detail: "La révision précédente reste historisée.",
        });
      } else {
        await task();
      }
    } catch (error) {
      showState(
        error?.message || "Création de révision impossible.",
        { error: true }
      );
    }
  }

  async function submit(event) {
    if (!fiche) {
      showState(
        "Enregistrez d’abord le brouillon.",
        { error: true }
      );
      return;
    }

    if (!isDraft()) {
      showState(
        `La fiche courante est déjà ${fiche.statut}.`,
        { error: true }
      );
      return;
    }

    if (!hasPermission("COLLECTE.SOUMETTRE")) {
      showState(
        "Permission COLLECTE.SOUMETTRE requise.",
        { error: true }
      );
      return;
    }

    const commentaire = window.prompt(
      "Commentaire de soumission (facultatif) :",
      ""
    );

    if (commentaire === null) return;

    const task = async () => {
      await saveAll();

      fiche = await apiPost(
        `/api/v1/missions/${missionId}/fiches/${fiche.id}/submit`,
        {
          commentaire: commentaire.trim() || null,
        }
      );

      updateActionState();
      step = 6;
      render();

      showState(
        "La fiche a été soumise. Elle n’est plus modifiable tant qu’une nouvelle révision n’est pas créée."
      );
    };

    try {
      if (window.HAUQE_ACTION_LOADER) {
        await window.HAUQE_ACTION_LOADER.run(task, {
          button: event.currentTarget,
          title: "Soumission de la collecte",
          message: "Contrôle de complétude",
          detail: "Le seuil est appliqué par la règle métier publiée côté serveur.",
        });
      } else {
        await task();
      }
    } catch (error) {
      showState(
        error?.message || "Soumission impossible.",
        { error: true }
      );
    }
  }

  function resetUnsavedFormState() {
    Object.assign(state, {
      campaign_id: "",
      new_campaign_code: "",
      new_campaign_name: "",
      new_campaign_start: "",
      new_campaign_end: "",
      mission_code: "",
      mission_object: "",
      zone_id: "",
      planned_start: "",
      planned_end: "",
      priority: "",
      assigned_user_id: "",
      entreprise_id: "",
      version_formulaire: "HAUQE-COLLECTE-SIMPLIFIEE-V1",
      consentement_obtenu: false,
      nom_declarant: "",
      fonction_declarant: "",
      telephone_declarant: "",
      email_declarant: "",
      signature_declarant: "",
      observations: "",
    });
    campagneId = null;
    campaign = null;
    mission = null;
    missionId = null;
    fiche = null;
    assignments = [];
    offers = [];
    declaredCertifications = [];
    documents = [];
    ficheHistory = [];
    selectedEnterprise = null;
    pendingFiles = [];
  }

  async function resetDraft(event) {
    if (!isDraft()) {
      showState(
        "Seul un brouillon courant peut être réinitialisé.",
        { error: true }
      );
      return;
    }

    const savedDraft = Boolean(fiche && missionId);
    const message = savedDraft
      ? "Réinitialiser cette fiche brouillon ? Seules les saisies de cette collecte (entreprise, déclarant, offres et certifications) seront effacées. La mission, sa campagne, sa zone et ses agents resteront inchangés. Les documents déposés seront désactivés, sans suppression physique."
      : "Réinitialiser toutes les saisies non enregistrées de ce formulaire ?";

    if (!window.confirm(message)) return;

    const task = async () => {
      if (savedDraft) {
        fiche = await apiPost(
          `/api/v1/missions/${missionId}/fiches/${fiche.id}/reset`
        );
        selectedEnterprise = null;
        pendingFiles = [];
        step = 1;
        await loadExisting();
        showState(
          "Brouillon réinitialisé. Reprenez la saisie de cette entreprise ; la mission, la campagne, la zone et les agents sont inchangés."
        );
      } else {
        resetUnsavedFormState();
        step = 1;
        showState("Formulaire non enregistré réinitialisé.");
      }

      updateActionState();
      render(false);
    };

    try {
      if (window.HAUQE_ACTION_LOADER) {
        await window.HAUQE_ACTION_LOADER.run(task, {
          button: event.currentTarget,
          title: "Réinitialisation du brouillon",
          message: "Nettoyage des saisies de collecte",
          detail: savedDraft
            ? "Les données métier sont retirées, l'historique est conservé."
            : "Aucune donnée n'avait encore été enregistrée.",
        });
      } else {
        await task();
      }
    } catch (error) {
      showState(
        error?.message || "Réinitialisation du brouillon impossible.",
        { error: true }
      );
    }
  }

  function updateActionState() {
    const saveButton = $("#saveCollectDraft");
    const resetButton = $("#resetCollectDraft");
    const submitButton = $("#submitCollect");
    const revisionButton = $("#createRevision");

    const editable = isDraft()
      && (
        hasPermission("COLLECTE.MODIFIER")
        || (!fiche && hasPermission("COLLECTE.CREER"))
      );

    saveButton.hidden = !editable;
    resetButton.hidden = !editable;

    submitButton.hidden = !(
      isDraft()
      && hasPermission("COLLECTE.SOUMETTRE")
    );

    revisionButton.hidden = !(
      fiche
      && !isDraft()
      && hasPermission("COLLECTE.MODIFIER")
    );
  }

  async function loadFicheSubresources() {
    if (!fiche) {
      offers = [];
      declaredCertifications = [];
      documents = [];
      ficheHistory = [];
      return;
    }

    const [offerData, certData, documentData, historyData] =
      await Promise.all([
        apiGet(
          `/api/v1/missions/${missionId}/fiches/${fiche.id}/offres`
        ),
        apiGet(
          `/api/v1/missions/${missionId}/fiches/${fiche.id}/certifications`
        ),
        apiGet(
          `/api/v1/documents?ressource_type=FICHE_COLLECTE&ressource_id=${encodeURIComponent(fiche.id)}&limit=100&offset=0`
        ),
        apiGet(
          `/api/v1/missions/${missionId}/fiches/${fiche.id}/history`
        ),
      ]);

    offers = Array.isArray(offerData)
      ? uniqueOffers(offerData)
      : [];

    declaredCertifications = Array.isArray(certData)
      ? uniqueDeclaredCertifications(certData)
      : [];

    documents = documentData.items || [];
    ficheHistory = Array.isArray(historyData)
      ? historyData
      : [];
  }

  async function loadExisting() {
    if (!missionId) return;

    mission = await apiGet(
      `/api/v1/missions/${missionId}`
    );

    campagneId = mission.campagne_id;

    campaign = await apiGet(
      `/api/v1/campagnes/${campagneId}`
    );

    assignments = await apiGet(
      `/api/v1/missions/${missionId}/affectations`
    );

    Object.assign(state, {
      campaign_id: mission.campagne_id,
      mission_code: mission.code || "",
      mission_object: mission.objet || "",
      zone_id: mission.zone_id || "",
      planned_start: mission.date_debut_prevue || "",
      planned_end: mission.date_fin_prevue || "",
      priority: mission.priorite || "",
      assigned_user_id: "",
    });

    try {
      // Le mode « nouvelle collecte » démarre une fiche vierge même si la
      // mission contient déjà des collectes d'autres entreprises.
      fiche = editMode && ficheId
        ? await apiGet(`/api/v1/missions/${missionId}/fiches/${ficheId}`)
        : null;
    } catch (error) {
      if (error?.status !== 404) throw error;
      fiche = null;
    }

    if (fiche) {
      Object.assign(state, {
        entreprise_id: fiche.entreprise_id || "",
        version_formulaire:
          fiche.version_formulaire
          || "HAUQE-COLLECTE-SIMPLIFIEE-V1",
        consentement_obtenu:
          Boolean(fiche.consentement_obtenu),
        nom_declarant: fiche.nom_declarant || "",
        fonction_declarant:
          fiche.fonction_declarant || "",
        telephone_declarant:
          fiche.telephone_declarant || "",
        email_declarant:
          fiche.email_declarant || "",
        signature_declarant:
          fiche.signature_declarant || "",
        observations:
          fiche.observations || "",
      });

      if (fiche.entreprise_id) {
        selectedEnterprise = await apiGet(
          `/api/v1/entreprises/${fiche.entreprise_id}`
        );
      }

      await loadFicheSubresources();
    }

    $("#collectFormMode").textContent = "Modification";

    $("#collectFormTitle").textContent =
      `Mission ${mission.code || mission.id}`;
  }

  document.addEventListener("submit", event => {
    if (event.target.id === "quickZoneForm") saveQuickZone(event);
    if (event.target.id === "quickEnterpriseForm") saveQuickEnterprise(event);
  }, true);

  document.addEventListener("click", event => {
    if (event.target.closest("#quickEnterpriseLocate")) locateQuickEnterprise();
  });

  async function bootstrap() {
    const api = await import("/static/js/core/api.js");

    apiGet = api.apiGet;
    apiPost = api.apiPost;
    apiPatch = api.apiPatch;
    apiRequest = api.apiRequest;

    const task = async () => {
      const [me, filterData] = await Promise.all([
        apiGet("/api/v1/me"),
        apiGet("/api/v1/collectes/filters"),
      ]);

      currentUser = me;
      workspace = filterData;

      if (!editMode) {
        const assignedFilter = hasPermission("COLLECTE.AFFECTER")
          ? ""
          : `?assigned_user_id=${encodeURIComponent(currentUser.id)}&`;
        const missionsResponse = await apiGet(
          `/api/v1/missions${assignedFilter}${assignedFilter ? "limit=200" : "?limit=200"}`
        );
        workspace.missions = Array.isArray(missionsResponse)
          ? missionsResponse
          : (missionsResponse.items || []);
      }

      await loadExisting();

      if (
        !missionId
        && !hasPermission("COLLECTE.CREER")
      ) {
        throw new Error(
          "La création d’une collecte nécessite COLLECTE.CREER et une affectation active à la mission."
        );
      }

      updateActionState();
      render();

      if (fiche?.id) {
        const { renderDossierParcours } = await import("/static/js/core/dossier-parcours.js?v=20260921-1");
        await renderDossierParcours({
          target: "#collecteDossierParcours",
          source: "fiche",
          resourceId: fiche.id,
          apiGet,
        });
      }
    };

    try {
      if (window.HAUQE_ACTION_LOADER) {
        await window.HAUQE_ACTION_LOADER.run(task, {
          title: editMode
            ? "Mission de collecte"
            : "Nouvelle collecte",
          message: "Préparation du dossier",
          detail: "Campagnes, zones, affectations et fiche courante.",
          minVisibleMs: 340,
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

    $("#collectNext").addEventListener(
      "click",
      async (event) => {
        if (!validateCurrentStep()) return;

        const task = async () => {
          if (isDraft()) {
            await saveCurrentStep();
          }

          step = Math.min(6, step + 1);
          updateActionState();
          render();
        };

        try {
          if (window.HAUQE_ACTION_LOADER) {
            await window.HAUQE_ACTION_LOADER.run(task, {
              button: event.currentTarget,
              title: "Brouillon de collecte",
              message: "Enregistrement de l’étape",
              detail: "Les données sont sauvegardées côté serveur.",
              minVisibleMs: 260,
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
    );

    $("#collectPrevious").addEventListener(
      "click",
      () => {
        capture();
        step = Math.max(1, step - 1);
        render();
      }
    );

    document.querySelectorAll(
      "#collectStepper button"
    ).forEach((button) => {
      button.addEventListener("click", () => {
        capture();
        step = Number(button.dataset.step);
        render();
      });
    });

    $("#saveCollectDraft").addEventListener(
      "click",
      async (event) => {
        if (!validateCurrentStep()) return;

        const task = async () => {
          await saveAll();
          updateActionState();
          render();

          showState(
            "Brouillon enregistré côté serveur."
          );
        };

        try {
          if (window.HAUQE_ACTION_LOADER) {
            await window.HAUQE_ACTION_LOADER.run(task, {
              button: event.currentTarget,
              title: "Brouillon de collecte",
              message: "Enregistrement complet",
              detail: "Fiche, offres, certifications déclarées et documents.",
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
    );

    $("#resetCollectDraft").addEventListener(
      "click",
      resetDraft
    );

    $("#submitCollect").addEventListener(
      "click",
      submit
    );

    $("#createRevision").addEventListener(
      "click",
      createRevision
    );

    refreshIcons();
  }

  bootstrap();
})();
