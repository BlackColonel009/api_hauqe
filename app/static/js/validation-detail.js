(function () {
  "use strict";

  const $ = (selector) => document.querySelector(selector);
  const parts = location.hash.replace(/^#\//, "").split("/");
  const ficheId = parts[1];

  let apiGet;
  let apiPost;

  let currentUser = null;
  let context = null;
  let history = [];
  let corrections = [];

  let decisionLevel = null;
  let correctionValidationId = null;
  let resubmitTarget = null;

  const FAVORABLE = new Set([
    "VALIDE",
    "VALIDE_SOUS_RESERVE",
  ]);

  const stageLabels = {
    READY_N1: "Revue N1 à prononcer",
    N1_REVIEW: "Niveau 1 à réexaminer",
    READY_N2: "Validation N2 à prononcer",
    N2_REVIEW: "Niveau 2 à réexaminer",
    CORRECTION_PENDING: "Correction en attente",
    COMPLETE: "Validation N2 favorable",
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

  function hasPermission(code) {
    return Array.isArray(currentUser?.permissions)
      && currentUser.permissions.includes(code);
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

  function showState(message, { error = false } = {}) {
    const node = $("#validationDetailState");
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
    $("#validationDetailState").hidden = true;
  }

  function decisionClass(value) {
    const decision = String(value || "").toUpperCase();

    if (decision === "VALIDE") return "validated";
    if (decision === "VALIDE_SOUS_RESERVE") return "reservation";
    if (decision === "AJOURNE") return "correction";
    if (decision === "REJETE") return "rejected";

    return "pending";
  }

  function levelCard(level, title, subtitle) {
    const hasDecision = Boolean(level.validation_id);

    return `
      <article class="validation-level-card">
        <header>
          <span>
            ${icon(
              title.includes("1")
                ? "badge-1"
                : "badge-2"
            )}
          </span>

          <div>
            <small>${escapeHtml(subtitle)}</small>
            <strong>${escapeHtml(title)}</strong>
          </div>

          <span class="validation-level ${decisionClass(level.decision)}">
            ${escapeHtml(level.decision || "À prononcer")}
          </span>
        </header>

        <div class="validation-level-body">
          <div>
            <small>Validateur</small>
            <strong>
              ${escapeHtml(level.validator_name || "—")}
            </strong>
          </div>

          <div>
            <small>Date</small>
            <strong>
              ${escapeHtml(formatDate(level.validation_date))}
            </strong>
          </div>

          <div>
            <small>Corrections</small>
            <strong>
              ${escapeHtml(level.corrections_count || 0)}
              ${
                level.pending_corrections_count
                  ? ` · ${escapeHtml(level.pending_corrections_count)} en attente`
                  : ""
              }
            </strong>
          </div>

          ${
            level.reserves
              ? `
                <div class="full">
                  <small>Réserves</small>
                  <p>${escapeHtml(level.reserves)}</p>
                </div>
              `
              : ""
          }

          ${
            level.justification
              ? `
                <div class="full">
                  <small>Justification</small>
                  <p>${escapeHtml(level.justification)}</p>
                </div>
              `
              : ""
          }
        </div>

        ${
          hasDecision
          && ["AJOURNE", "VALIDE_SOUS_RESERVE"].includes(
            level.decision
          )
          && hasPermission("VALIDATION.DEMANDER_CORRECTION")
            ? `
              <footer>
                <button
                  class="btn btn-outline-secondary app-btn"
                  type="button"
                  data-request-correction="${escapeHtml(level.validation_id)}"
                >
                  ${icon("undo-2")}
                  Demander une correction
                </button>
              </footer>
            `
            : ""
        }
      </article>
    `;
  }

  function renderHeader() {
    const company =
      context.entreprise_name
      || "Entreprise non renseignée";

    $("#validationBreadcrumb").textContent =
      `${company} · ${context.mission_code || "Mission"}`;

    $("#validationDetailTitle").textContent = company;

    $("#validationDetailSubtitle").textContent =
      [
        context.mission_code,
        context.campaign_code,
        context.zone_name,
      ].filter(Boolean).join(" · ")
      || "Validation hiérarchisée";

    const stage = $("#validationDetailStage");

    stage.className =
      `validation-stage ${context.stage.toLowerCase()}`;

    stage.textContent =
      stageLabels[context.stage] || context.stage;

    $("#validationDetailRefs").innerHTML = `
      <span>
        <b>FUCCS</b>
        ${escapeHtml(context.control_score || "0")}
        /
        ${escapeHtml(context.control_maximum || "0")}
        · ${escapeHtml(context.control_rate || "0.00")} %
      </span>

      <span>
        <b>Contrôleur</b>
        ${escapeHtml(context.controller_name || "—")}
      </span>

      <span>
        <b>Vérification</b>
        ${escapeHtml(context.verification_opinion || "—")}
      </span>

      <span>
        <b>Révision</b>
        ${escapeHtml(context.fiche_revision ?? "—")}
      </span>
    `;

    $("#validationLevels").innerHTML =
      levelCard(
        context.level_1,
        "Niveau 1",
        "Revue technique"
      )
      + levelCard(
        context.level_2,
        "Niveau 2",
        "Validation définitive"
      );

    document
      .querySelectorAll("[data-request-correction]")
      .forEach((button) => {
        button.addEventListener(
          "click",
          () => openCorrectionDialog(
            button.dataset.requestCorrection
          )
        );
      });

    const n1Favorable =
      FAVORABLE.has(context.level_1.decision);

    const n2Favorable =
      FAVORABLE.has(context.level_2.decision);

    $("#decisionN1").hidden =
      !(
        hasPermission("VALIDATION.REVUE_N1")
        && !n1Favorable
      );

    $("#decisionN2").hidden =
      !(
        hasPermission("VALIDATION.DECIDER_N2")
        && n1Favorable
        && !n2Favorable
      );

    refreshIcons();
  }

  function renderOverview() {
    $("#validationTabContent").innerHTML = `
      <div class="validation-overview-grid">
        <article class="panel">
          <div class="panel-heading">
            <div>
              <h2>Sources de décision</h2>
              <p>
                Les résultats précédents sont consultés sans être modifiés.
              </p>
            </div>
          </div>

          <div class="validation-source-list">
            <div>
              <span>${icon("folder-search")}</span>
              <div>
                <strong>Vérification documentaire</strong>
                <small>
                  Avis ${escapeHtml(context.verification_opinion || "—")}
                  · risque ${escapeHtml(context.verification_risk || "—")}
                </small>
              </div>
              <a
                href="#/verifications/${escapeHtml(context.verification_id)}"
                class="btn btn-outline-secondary app-btn"
              >
                Voir
              </a>
            </div>

            <div>
              <span>${icon("clipboard-check")}</span>
              <div>
                <strong>Contrôle FUCCS finalisé</strong>
                <small>
                  ${escapeHtml(context.control_score || "0")}
                  /
                  ${escapeHtml(context.control_maximum || "0")}
                  · ${escapeHtml(context.control_rate || "0.00")} %
                  · fin ${escapeHtml(formatDate(context.control_ended_on))}
                </small>
              </div>
              <a
                href="#/controle/${escapeHtml(context.control_id)}"
                class="btn btn-outline-secondary app-btn"
              >
                Voir
              </a>
            </div>
          </div>
        </article>

        <aside class="panel">
          <div class="panel-heading">
            <div>
              <h2>Règles hiérarchiques</h2>
              <p>Contrôlées par FastAPI</p>
            </div>
          </div>

          <ul class="validation-rules-list">
            <li>
              ${icon("check")}
              Un FUCCS finalisé est obligatoire.
            </li>
            <li>
              ${icon("check")}
              N1 favorable avant toute décision N2.
            </li>
            <li>
              ${icon("check")}
              N1 et N2 doivent être prononcés par deux personnes différentes.
            </li>
            <li>
              ${icon("check")}
              Une validation sous réserve exige des réserves explicites.
            </li>
            <li>
              ${icon("check")}
              Une correction ne supprime jamais la décision d’origine.
            </li>
          </ul>

          ${
            context.integration_possible
              ? `
                <div class="validation-next-step">
                  ${icon("arrow-right-circle")}
                  <div>
                    <strong>Validation N2 favorable</strong>
                    <small>
                      Le dossier peut passer à l’étape 09 :
                      Intégration BNEC.
                    </small>
                  </div>
                </div>
              `
              : ""
          }
        </aside>
      </div>
    `;

    refreshIcons();
  }

  function validationLabel(item) {
    const level = item.niveau_validation === "NIVEAU_1"
      ? "Niveau 1"
      : item.niveau_validation === "NIVEAU_2"
        ? "Niveau 2"
        : item.niveau_validation || "Validation";

    return `${level} · ${item.decision || "—"}`;
  }

  function renderHistory() {
    $("#validationHistoryCount").textContent =
      String(history.length);

    const content = history.length
      ? history.map((item) => `
          <article class="validation-history-row">
            <span class="${decisionClass(item.decision)}">
              ${icon("shield-check")}
            </span>

            <div>
              <strong>
                ${escapeHtml(validationLabel(item))}
              </strong>

              <small>
                ${escapeHtml(formatDate(item.date_validation))}
                · statut ${escapeHtml(item.statut || "—")}
              </small>

              ${
                item.reserves
                  ? `
                    <p>
                      <b>Réserves :</b>
                      ${escapeHtml(item.reserves)}
                    </p>
                  `
                  : ""
              }

              ${
                item.justification
                  ? `
                    <p>
                      <b>Justification :</b>
                      ${escapeHtml(item.justification)}
                    </p>
                  `
                  : ""
              }
            </div>
          </article>
        `).join("")
      : `
        <div class="priority-empty">
          Aucune décision enregistrée.
        </div>
      `;

    $("#validationTabContent").innerHTML = `
      <article class="panel mt-3">
        <div class="panel-heading">
          <div>
            <h2>Historique des décisions</h2>
            <p>
              Chaque nouvelle décision est conservée séparément.
            </p>
          </div>
        </div>

        <div class="validation-history-list">
          ${content}
        </div>
      </article>
    `;

    refreshIcons();
  }

  function correctionStatusClass(value) {
    const status = String(value || "").toUpperCase();

    if (status === "RESOUMISE") return "validated";
    if (["DEMANDEE", "EN_COURS"].includes(status)) return "correction";

    return "pending";
  }

  function renderCorrections() {
    $("#validationCorrectionCount").textContent =
      String(corrections.length);

    const content = corrections.length
      ? corrections.map((item) => `
          <article class="validation-correction-card">
            <header>
              <span class="${correctionStatusClass(item.statut)}">
                ${icon("undo-2")}
              </span>

              <div>
                <strong>
                  ${escapeHtml(item.statut || "Correction")}
                </strong>

                <small>
                  Demandée ${escapeHtml(formatDate(item.date_demande))}
                  · échéance ${escapeHtml(formatDate(item.date_echeance))}
                </small>
              </div>
            </header>

            <div>
              <p>
                <b>Motif :</b>
                ${escapeHtml(item.motif || "—")}
              </p>

              <p>
                <b>Instructions :</b>
                ${escapeHtml(item.instructions || "—")}
              </p>

              ${
                item.reponse
                  ? `
                    <p class="correction-response">
                      <b>Réponse :</b>
                      ${escapeHtml(item.reponse)}
                      <br>
                      <small>
                        Resoumise ${escapeHtml(
                          formatDate(item.date_resoumission)
                        )}
                      </small>
                    </p>
                  `
                  : ""
              }
            </div>

            ${
              !item.date_resoumission
              && hasPermission("VALIDATION.RESOUMETTRE_CORRECTION")
                ? `
                  <footer>
                    <button
                      class="btn btn-primary app-btn"
                      type="button"
                      data-resubmit-correction="${escapeHtml(item.id)}"
                      data-validation-id="${escapeHtml(item.validation_id)}"
                    >
                      ${icon("send")}
                      Resoumettre
                    </button>
                  </footer>
                `
                : ""
            }
          </article>
        `).join("")
      : `
        <div class="priority-empty">
          Aucune correction demandée.
        </div>
      `;

    $("#validationTabContent").innerHTML = `
      <article class="panel mt-3">
        <div class="panel-heading">
          <div>
            <h2>Corrections</h2>
            <p>
              Les corrections restent rattachées à la décision qui les a créées.
            </p>
          </div>
        </div>

        <div class="validation-corrections-list">
          ${content}
        </div>
      </article>
    `;

    document
      .querySelectorAll("[data-resubmit-correction]")
      .forEach((button) => {
        button.addEventListener(
          "click",
          () => openResubmitDialog({
            correctionId:
              button.dataset.resubmitCorrection,
            validationId:
              button.dataset.validationId,
          })
        );
      });

    refreshIcons();
  }

  function showTab(name) {
    document
      .querySelectorAll(".detail-tabs button")
      .forEach((button) => {
        button.classList.toggle(
          "active",
          button.dataset.tab === name
        );
      });

    if (name === "history") return renderHistory();
    if (name === "corrections") return renderCorrections();

    return renderOverview();
  }

  function openDecisionDialog(level) {
    decisionLevel = level;

    $("#decisionDialogTitle").textContent =
      level === "NIVEAU_1"
        ? "Revue de niveau 1"
        : "Validation définitive de niveau 2";

    $("#decisionValue").value = "";
    $("#decisionReserves").value = "";
    $("#decisionJustification").value = "";
    $("#decisionReserveField").hidden = true;

    $("#validationDecisionDialog").showModal();
    refreshIcons();
  }

  function openCorrectionDialog(validationId) {
    correctionValidationId = validationId;

    $("#correctionReason").value = "";
    $("#correctionInstructions").value = "";
    $("#correctionDueDate").value = "";

    $("#correctionDialog").showModal();
    refreshIcons();
  }

  function openResubmitDialog(target) {
    resubmitTarget = target;

    $("#resubmitResponse").value = "";
    $("#resubmitDate").value = "";

    $("#resubmitCorrectionDialog").showModal();
    refreshIcons();
  }

  function closeDialog(id) {
    const dialog = document.getElementById(id);

    if (dialog?.open) {
      dialog.close();
    }
  }

  async function submitDecision(event) {
    event.preventDefault();

    const decision = $("#decisionValue").value;
    const reserves =
      $("#decisionReserves").value.trim();

    const justification =
      $("#decisionJustification").value.trim();

    if (!decision || !justification) {
      showState(
        "Décision et justification sont obligatoires.",
        { error: true }
      );
      return;
    }

    if (
      decision === "VALIDE_SOUS_RESERVE"
      && !reserves
    ) {
      showState(
        "Les réserves sont obligatoires pour une validation sous réserve.",
        { error: true }
      );
      return;
    }

    const endpoint = decisionLevel === "NIVEAU_1"
      ? `/api/v1/validations/from-fiche/${ficheId}/level-1`
      : `/api/v1/validations/from-fiche/${ficheId}/level-2`;

    const task = async () => {
      await apiPost(
        endpoint,
        {
          decision,
          reserves: reserves || null,
          justification,
        }
      );

      closeDialog("validationDecisionDialog");

      await reloadAll();
      renderHeader();
      showTab("history");
    };

    try {
      if (window.HAUQE_ACTION_LOADER) {
        await window.HAUQE_ACTION_LOADER.run(task, {
          title: "Décision de validation",
          message: decisionLevel === "NIVEAU_1"
            ? "Enregistrement de la revue N1"
            : "Enregistrement de la validation N2",
          detail: "La décision est historisée et auditée.",
        });
      } else {
        await task();
      }
    } catch (error) {
      showState(
        error?.message || "Décision impossible.",
        { error: true }
      );
    }
  }

  async function submitCorrection(event) {
    event.preventDefault();

    const motif =
      $("#correctionReason").value.trim();

    const instructions =
      $("#correctionInstructions").value.trim();

    if (!motif || !instructions) {
      showState(
        "Motif et instructions sont obligatoires.",
        { error: true }
      );
      return;
    }

    const task = async () => {
      await apiPost(
        `/api/v1/validations/${correctionValidationId}/corrections`,
        {
          motif,
          instructions,
          date_echeance:
            $("#correctionDueDate").value || null,
        }
      );

      closeDialog("correctionDialog");

      await reloadAll();
      renderHeader();
      showTab("corrections");
    };

    try {
      if (window.HAUQE_ACTION_LOADER) {
        await window.HAUQE_ACTION_LOADER.run(task, {
          title: "Demande de correction",
          message: "Enregistrement des corrections attendues",
          detail: "La décision d’origine reste intacte.",
        });
      } else {
        await task();
      }
    } catch (error) {
      showState(
        error?.message || "Demande impossible.",
        { error: true }
      );
    }
  }

  async function submitResubmission(event) {
    event.preventDefault();

    const response =
      $("#resubmitResponse").value.trim();

    if (!response) {
      showState(
        "La réponse de resoumission est obligatoire.",
        { error: true }
      );
      return;
    }

    const task = async () => {
      await apiPost(
        `/api/v1/validations/${resubmitTarget.validationId}`
        + `/corrections/${resubmitTarget.correctionId}/resubmit`,
        {
          reponse: response,
          date_resoumission:
            $("#resubmitDate").value || null,
        }
      );

      closeDialog("resubmitCorrectionDialog");

      await reloadAll();
      renderHeader();
      showTab("corrections");
    };

    try {
      if (window.HAUQE_ACTION_LOADER) {
        await window.HAUQE_ACTION_LOADER.run(task, {
          title: "Resoumission de correction",
          message: "Enregistrement de la réponse",
          detail: "Le dossier peut ensuite être réexaminé.",
        });
      } else {
        await task();
      }
    } catch (error) {
      showState(
        error?.message || "Resoumission impossible.",
        { error: true }
      );
    }
  }

  async function loadCorrectionsFor(validationId) {
    if (!validationId) return [];

    try {
      return await apiGet(
        `/api/v1/validations/${validationId}/corrections`
      );
    } catch (error) {
      if (error?.status === 403) return [];
      throw error;
    }
  }

  async function reloadAll() {
    [context, history] = await Promise.all([
      apiGet(
        `/api/v1/validations/workspace/${ficheId}`
      ),
      apiGet(
        `/api/v1/validations?fiche_id=${encodeURIComponent(ficheId)}`
        + `&limit=200&offset=0`
      ).then((payload) => payload.items || []),
    ]);

    const correctionLists = await Promise.all(
      history.map((item) =>
        loadCorrectionsFor(item.id)
      )
    );

    corrections = correctionLists
      .flat()
      .sort((a, b) =>
        String(b.created_at || "")
          .localeCompare(String(a.created_at || ""))
      );

    $("#validationHistoryCount").textContent =
      String(history.length);

    $("#validationCorrectionCount").textContent =
      String(corrections.length);
  }

  async function bootstrap() {
    if (!ficheId) {
      showState(
        "Identifiant de fiche absent.",
        { error: true }
      );
      return;
    }

    const api = await import("/static/js/core/api.js");

    apiGet = api.apiGet;
    apiPost = api.apiPost;

    const task = async () => {
      currentUser = await apiGet("/api/v1/me");

      await reloadAll();

      hideState();
      renderHeader();
      showTab("overview");
    };

    try {
      if (window.HAUQE_ACTION_LOADER) {
        await window.HAUQE_ACTION_LOADER.run(task, {
          title: "Validation hiérarchisée",
          message: "Chargement du dossier",
          detail: "FUCCS, décisions N1/N2 et corrections.",
          minVisibleMs: 340,
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

    document
      .querySelectorAll(".detail-tabs button")
      .forEach((button) => {
        button.addEventListener(
          "click",
          () => showTab(button.dataset.tab)
        );
      });

    $("#decisionN1").addEventListener(
      "click",
      () => openDecisionDialog("NIVEAU_1")
    );

    $("#decisionN2").addEventListener(
      "click",
      () => openDecisionDialog("NIVEAU_2")
    );

    $("#decisionValue").addEventListener(
      "change",
      (event) => {
        $("#decisionReserveField").hidden =
          event.target.value !==
          "VALIDE_SOUS_RESERVE";
      }
    );

    $("#validationDecisionForm").addEventListener(
      "submit",
      submitDecision
    );

    $("#correctionForm").addEventListener(
      "submit",
      submitCorrection
    );

    $("#resubmitCorrectionForm").addEventListener(
      "submit",
      submitResubmission
    );

    document
      .querySelectorAll("[data-close-dialog]")
      .forEach((button) => {
        button.addEventListener(
          "click",
          () => closeDialog(
            button.dataset.closeDialog
          )
        );
      });

    refreshIcons();
  }

  bootstrap();
})();
