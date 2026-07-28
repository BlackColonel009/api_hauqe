(function () {
  "use strict";

  const $ = (selector) => document.querySelector(selector);
  const parts = location.hash.replace(/^#\//, "").split("/");
  const controlId = parts[1];

  let apiGet;
  let apiPost;
  let apiPatch;
  let apiRequest;
  let apiBlob;

  let currentUser = null;
  let control = null;
  let context = null;
  let grid = null;
  let rubrics = [];
  let criteria = [];
  let notes = [];
  let findings = [];
  let documents = [];

  let activeRubricId = null;
  const dirty = new Map();

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

  function isFinalized() {
    return String(control?.statut || "").toUpperCase()
      === "FINALISE";
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

  function showState(message, { error = false } = {}) {
    const node = $("#fuccsDetailState");

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
    $("#fuccsDetailState").hidden = true;
  }

  function statusClass(value) {
    return String(value || "").toUpperCase() === "FINALISE"
      ? "valid"
      : "watch";
  }

  function noteFor(criterionId) {
    return notes.find(
      (note) => String(note.critere_fuccs_id)
        === String(criterionId)
    ) || null;
  }

  function rubricCriteria(rubricId) {
    return criteria.filter(
      (criterion) => (
        String(criterion.rubrique_fuccs_id)
        === String(rubricId)
      )
    );
  }

  function noteScore(note) {
    if (!note || note.score === null || note.score === undefined) {
      return 0;
    }

    return Number(note.score);
  }

  function rubricStats(rubricId) {
    const items = rubricCriteria(rubricId);
    const rubricNotes = items
      .map((item) => noteFor(item.id))
      .filter(Boolean);

    const score = rubricNotes.reduce(
      (sum, note) => sum + noteScore(note),
      0
    );

    const maximum = items.reduce(
      (sum, item) => sum + Number(item.score_maximal || 0),
      0
    );

    return {
      criteria: items.length,
      answered: rubricNotes.length,
      score,
      maximum,
    };
  }

  function globalProgress() {
    const answered = notes.length;
    const count = criteria.length;

    return {
      answered,
      count,
      percent: count > 0
        ? Math.round((answered / count) * 100)
        : 0,
    };
  }

  function renderHeader() {
    const company =
      context.entreprise_name
      || "Entreprise non renseignée";

    $("#fuccsBreadcrumb").textContent =
      `${company} · ${context.mission_code || "Mission"}`;

    $("#fuccsDetailTitle").textContent = company;

    $("#fuccsDetailSubtitle").textContent =
      [
        context.mission_code,
        context.campaign_code,
        context.zone_name,
      ].filter(Boolean).join(" · ")
      || "Contrôle FUCCS";

    const status = $("#fuccsDetailStatus");

    status.className =
      `cert-status ${statusClass(control.statut)}`;

    status.innerHTML =
      `<i></i>${escapeHtml(control.statut || "Non renseigné")}`;

    $("#fuccsDetailRefs").innerHTML = `
      <span>
        <b>Grille</b>
        ${escapeHtml(grid.code || grid.libelle || "FUCCS")}
        v${escapeHtml(grid.version || "—")}
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
        <b>Risque</b>
        ${escapeHtml(context.verification_risk || "—")}
      </span>
    `;

    $("#fuccsGridLabel").textContent =
      `${grid.libelle || grid.code || "Grille FUCCS"}`
      + ` · version ${grid.version || "—"}`;

    updateActions();
    renderScoreOverview();
    refreshIcons();
  }

  function updateActions() {
    $("#saveAllNotes").hidden =
      !(
        hasPermission("FUCCS.CONTROLER")
        && !isFinalized()
      );

    $("#finalizeFuccs").hidden =
      !(
        hasPermission("FUCCS.FINALISER")
        && !isFinalized()
      );

    $("#reopenFuccs").hidden =
      !(
        hasPermission("FUCCS.REOUVRIR")
        && isFinalized()
      );

    $("#addFuccsFinding").hidden =
      !(
        hasPermission("FUCCS.CONTROLER")
        && !isFinalized()
      );
  }

  function renderScoreOverview() {
    const progress = globalProgress();

    const raw = Number(control.score_brut || 0);
    const maximum = Number(control.score_maximal || 0);

    const rate = Number(
      String(control.taux || "0").replace(",", ".")
    );

    const cards = [
      [
        "score",
        "Score brut",
        `${raw} / ${maximum}`,
        `${Number.isFinite(rate) ? rate.toFixed(2) : "0.00"} %`,
      ],
      [
        "progress",
        "Critères notés",
        `${progress.answered} / ${progress.count}`,
        `${progress.percent} % de la grille`,
      ],
      [
        "grid",
        "Grille",
        `${grid.criteres_count ?? criteria.length} critère(s)`,
        `${grid.rubriques_count ?? rubrics.length} rubrique(s)`,
      ],
      [
        "findings",
        "Constats",
        findings.length,
        "Éléments transversaux",
      ],
    ];

    $("#fuccsScoreOverview").innerHTML = cards.map(
      ([kind, label, value, detail]) => `
        <article class="fuccs-score-card ${kind}">
          <small>${escapeHtml(label)}</small>
          <strong>${escapeHtml(value)}</strong>
          <span>${escapeHtml(detail)}</span>
        </article>
      `
    ).join("");
  }

  function renderRubricNav() {
    $("#fuccsRubricNav").innerHTML = rubrics.map((rubric) => {
      const stats = rubricStats(rubric.id);

      return `
        <button
          type="button"
          class="fuccs-rubric-button
            ${String(rubric.id) === String(activeRubricId) ? "active" : ""}
            ${stats.answered === stats.criteria && stats.criteria > 0 ? "complete" : ""}
          "
          data-rubric-id="${escapeHtml(rubric.id)}"
        >
          <span>
            ${icon(
              stats.answered === stats.criteria && stats.criteria > 0
                ? "circle-check"
                : "circle-dashed"
            )}
          </span>

          <div>
            <strong>
              ${escapeHtml(rubric.libelle || rubric.code || "Rubrique")}
            </strong>
            <small>
              ${stats.answered} / ${stats.criteria} critère(s)
            </small>
          </div>

          <b>
            ${stats.score} / ${stats.maximum}
          </b>
        </button>
      `;
    }).join("");

    document
      .querySelectorAll("[data-rubric-id]")
      .forEach((button) => {
        button.addEventListener("click", () => {
          activeRubricId =
            button.dataset.rubricId;

          renderRubricNav();
          renderActiveRubric();
        });
      });

    refreshIcons();
  }

  function proofOptions(currentValue) {
    return `
      <option value="">Aucune preuve</option>
      ${documents.map((document) => `
        <option
          value="${escapeHtml(document.id)}"
          ${String(document.id) === String(currentValue) ? "selected" : ""}
        >
          ${escapeHtml(
            document.nom_original
            || document.type_document
            || document.id
          )}
        </option>
      `).join("")}
    `;
  }

  function scoreInput(criterion, note) {
    const maximum = Number(
      criterion.score_maximal || 0
    );

    const current = note?.score;

    if (
      Number.isInteger(maximum)
      && maximum >= 1
      && maximum <= 5
    ) {
      return `
        <div class="fuccs-score-choices">
          ${Array.from(
            { length: maximum + 1 },
            (_, index) => index
          ).map((value) => `
            <button
              type="button"
              class="fuccs-score-choice
                ${Number(current) === value ? "selected" : ""}
              "
              data-score-choice="${value}"
            >
              ${value}
            </button>
          `).join("")}
        </div>
      `;
    }

    return `
      <input
        class="fuccs-score-input"
        type="number"
        min="0"
        max="${escapeHtml(maximum)}"
        step="0.01"
        value="${escapeHtml(current ?? "")}"
      >
    `;
  }

  function renderActiveRubric() {
    const rubric = rubrics.find(
      (item) => String(item.id)
        === String(activeRubricId)
    );

    if (!rubric) {
      $("#fuccsCriteriaList").innerHTML = `
        <div class="priority-empty">
          Aucune rubrique disponible.
        </div>
      `;
      return;
    }

    const items = rubricCriteria(rubric.id);
    const stats = rubricStats(rubric.id);

    $("#fuccsRubricCode").textContent =
      rubric.code || "Rubrique";

    $("#fuccsRubricTitle").textContent =
      rubric.libelle || rubric.code || "Rubrique";

    $("#fuccsRubricDescription").textContent =
      rubric.description || "";

    $("#fuccsRubricScore").textContent =
      `${stats.score} / ${stats.maximum}`;

    $("#fuccsCriteriaList").innerHTML = items.length
      ? items.map((criterion, index) => {
          const note = noteFor(criterion.id);

          return `
            <article
              class="fuccs-criterion"
              data-criterion-id="${escapeHtml(criterion.id)}"
            >
              <div class="fuccs-criterion-index">
                ${index + 1}
              </div>

              <div class="fuccs-criterion-main">
                <div class="fuccs-criterion-copy">
                  <strong>
                    ${escapeHtml(
                      criterion.libelle
                      || criterion.code
                      || "Critère"
                    )}
                  </strong>

                  <small>
                    ${escapeHtml(criterion.description || "")}
                  </small>

                  <div class="fuccs-requirements">
                    ${
                      criterion.commentaire_obligatoire
                        ? `
                          <span>
                            ${icon("message-square-text")}
                            Commentaire requis
                          </span>
                        `
                        : ""
                    }

                    ${
                      criterion.preuve_obligatoire
                        ? `
                          <span>
                            ${icon("paperclip")}
                            Preuve requise
                          </span>
                        `
                        : ""
                    }

                    <span>
                      Max ${escapeHtml(criterion.score_maximal)}
                    </span>
                  </div>
                </div>

                <div class="fuccs-criterion-score">
                  ${scoreInput(criterion, note)}
                </div>

                <div class="fuccs-criterion-fields">
                  <label>
                    <span>Commentaire</span>
                    <textarea
                      rows="2"
                      data-note-comment
                      ${isFinalized() ? "disabled" : ""}
                    >${escapeHtml(note?.commentaire || "")}</textarea>
                  </label>

                  <label>
                    <span>Preuve documentaire</span>
                    <select
                      data-note-proof
                      ${isFinalized() ? "disabled" : ""}
                    >
                      ${proofOptions(note?.preuve_document_id)}
                    </select>
                  </label>
                </div>

                ${
                  !isFinalized()
                  && hasPermission("FUCCS.CONTROLER")
                    ? `
                      <div class="fuccs-criterion-actions">
                        <button
                          class="btn btn-outline-secondary app-btn"
                          type="button"
                          data-save-criterion
                        >
                          ${icon("save")}
                          Enregistrer
                        </button>
                      </div>
                    `
                    : ""
                }
              </div>
            </article>
          `;
        }).join("")
      : `
        <div class="priority-empty">
          Cette rubrique ne contient aucun critère.
        </div>
      `;

    document
      .querySelectorAll("[data-criterion-id]")
      .forEach(bindCriterion);

    refreshIcons();
  }

  function criterionPayload(card) {
    const criterionId = card.dataset.criterionId;

    const criterion = criteria.find(
      (item) => String(item.id)
        === String(criterionId)
    );

    const selected = card.querySelector(
      ".fuccs-score-choice.selected"
    );

    const numberInput = card.querySelector(
      ".fuccs-score-input"
    );

    const scoreValue = selected
      ? selected.dataset.scoreChoice
      : numberInput?.value;

    if (
      scoreValue === ""
      || scoreValue === null
      || scoreValue === undefined
    ) {
      throw new Error(
        "Sélectionnez une note pour ce critère."
      );
    }

    const score = Number(scoreValue);
    const maximum = Number(
      criterion.score_maximal || 0
    );

    if (
      !Number.isFinite(score)
      || score < 0
      || score > maximum
    ) {
      throw new Error(
        `La note doit être comprise entre 0 et ${maximum}.`
      );
    }

    const comment = card.querySelector(
      "[data-note-comment]"
    ).value.trim();

    const proof = card.querySelector(
      "[data-note-proof]"
    ).value || null;

    if (
      criterion.commentaire_obligatoire
      && !comment
    ) {
      throw new Error(
        "Le commentaire est obligatoire pour ce critère."
      );
    }

    if (
      criterion.preuve_obligatoire
      && !proof
    ) {
      throw new Error(
        "Une preuve documentaire est obligatoire pour ce critère."
      );
    }

    return {
      criterionId,
      payload: {
        score,
        commentaire: comment || null,
        preuve_document_id: proof,
      },
    };
  }

  function bindCriterion(card) {
    card
      .querySelectorAll("[data-score-choice]")
      .forEach((button) => {
        button.disabled = isFinalized();

        button.addEventListener("click", () => {
          if (isFinalized()) return;

          card
            .querySelectorAll("[data-score-choice]")
            .forEach((candidate) => {
              candidate.classList.remove("selected");
            });

          button.classList.add("selected");
          markDirty(card);
        });
      });

    card
      .querySelector(".fuccs-score-input")
      ?.addEventListener(
        "input",
        () => markDirty(card)
      );

    card
      .querySelector("[data-note-comment]")
      ?.addEventListener(
        "input",
        () => markDirty(card)
      );

    card
      .querySelector("[data-note-proof]")
      ?.addEventListener(
        "change",
        () => markDirty(card)
      );

    card
      .querySelector("[data-save-criterion]")
      ?.addEventListener(
        "click",
        (event) => saveCriterion(
          event.currentTarget,
          card
        )
      );
  }

  function markDirty(card) {
    dirty.set(
      card.dataset.criterionId,
      true
    );

    card.classList.add("dirty");
  }

  async function saveCriterion(button, card) {
    let item;

    try {
      item = criterionPayload(card);
    } catch (error) {
      showState(
        error.message,
        { error: true }
      );
      return;
    }

    const task = async () => {
      await apiRequest(
        `/api/v1/fuccs/controles/${controlId}/notes/${item.criterionId}`,
        {
          method: "PUT",
          body: item.payload,
        }
      );

      dirty.delete(item.criterionId);
      card.classList.remove("dirty");

      await reloadControlAndNotes();
      renderHeader();
      renderRubricNav();
      renderActiveRubric();
    };

    try {
      if (window.HAUQE_ACTION_LOADER) {
        await window.HAUQE_ACTION_LOADER.run(task, {
          button,
          title: "Critère FUCCS",
          message: "Enregistrement de la note",
          detail: "Le score global est recalculé côté serveur.",
          minVisibleMs: 250,
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

  async function saveAllDirty(event) {
    const cards = Array.from(
      document.querySelectorAll(
        "[data-criterion-id].dirty"
      )
    );

    if (!cards.length) {
      showState(
        "Aucune modification de critère à enregistrer."
      );
      return;
    }

    const task = async () => {
      for (const card of cards) {
        const item = criterionPayload(card);

        await apiRequest(
          `/api/v1/fuccs/controles/${controlId}/notes/${item.criterionId}`,
          {
            method: "PUT",
            body: item.payload,
          }
        );
      }

      dirty.clear();

      await reloadControlAndNotes();
      renderHeader();
      renderRubricNav();
      renderActiveRubric();
    };

    try {
      if (window.HAUQE_ACTION_LOADER) {
        await window.HAUQE_ACTION_LOADER.run(task, {
          button: event.currentTarget,
          title: "Contrôle FUCCS",
          message: "Enregistrement des critères modifiés",
          detail: "Chaque note reste historisée côté backend.",
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

  function renderFindings() {
    const content = findings.length
      ? findings.map((finding) => `
          <article
            class="cert-doc-row"
            data-finding-id="${escapeHtml(finding.id)}"
          >
            <span>${icon("clipboard-list")}</span>

            <div>
              <strong>
                ${escapeHtml(finding.titre || "Constat")}
              </strong>

              <small>
                ${escapeHtml(finding.type_constat || "Constat")}
                · gravité ${escapeHtml(finding.gravite || "—")}
                · statut ${escapeHtml(finding.statut || "—")}
                <br>
                ${escapeHtml(finding.description || "")}
              </small>
            </div>

            ${
              !isFinalized()
              && hasPermission("FUCCS.CONTROLER")
                ? `
                  <button
                    class="btn btn-outline-secondary app-btn"
                    type="button"
                    data-edit-finding="${escapeHtml(finding.id)}"
                  >
                    ${icon("square-pen")}
                    Modifier
                  </button>
                `
                : ""
            }
          </article>
        `).join("")
      : `
        <div class="priority-empty">
          Aucun constat transversal.
        </div>
      `;

    $("#fuccsFindings").innerHTML = content;

    document
      .querySelectorAll("[data-edit-finding]")
      .forEach((button) => {
        button.addEventListener(
          "click",
          () => editFinding(
            button,
            button.dataset.editFinding
          )
        );
      });

    refreshIcons();
  }

  async function createFinding(event) {
    const title = window.prompt(
      "Titre du constat :"
    );

    if (!title?.trim()) return;

    const description = window.prompt(
      "Description du constat :"
    );

    if (!description?.trim()) return;

    const type = window.prompt(
      "Type de constat (facultatif) :",
      ""
    );

    if (type === null) return;

    const severity = window.prompt(
      "Gravité (facultatif) :",
      ""
    );

    if (severity === null) return;

    const task = async () => {
      await apiPost(
        `/api/v1/fuccs/controles/${controlId}/constats`,
        {
          type_constat: type.trim() || null,
          gravite: severity.trim() || null,
          titre: title.trim(),
          description: description.trim(),
          statut: "OUVERT",
        }
      );

      findings = await apiGet(
        `/api/v1/fuccs/controles/${controlId}/constats`
      );

      await reloadControlAndNotes();
      renderHeader();
      renderFindings();
    };

    try {
      if (window.HAUQE_ACTION_LOADER) {
        await window.HAUQE_ACTION_LOADER.run(task, {
          button: event.currentTarget,
          title: "Constat FUCCS",
          message: "Enregistrement du constat",
          detail: "Le constat reste distinct des notes de critères.",
        });
      } else {
        await task();
      }
    } catch (error) {
      showState(
        error?.message || "Ajout impossible.",
        { error: true }
      );
    }
  }

  async function editFinding(button, findingId) {
    const finding = findings.find(
      (item) => String(item.id)
        === String(findingId)
    );

    if (!finding) return;

    const description = window.prompt(
      "Description :",
      finding.description || ""
    );

    if (description === null) return;

    const status = window.prompt(
      "Statut :",
      finding.statut || "OUVERT"
    );

    if (status === null) return;

    try {
      await apiPatch(
        `/api/v1/fuccs/controles/${controlId}/constats/${findingId}`,
        {
          description: description.trim() || null,
          statut: status.trim() || null,
        }
      );

      findings = await apiGet(
        `/api/v1/fuccs/controles/${controlId}/constats`
      );

      renderFindings();
    } catch (error) {
      showState(
        error?.message || "Modification impossible.",
        { error: true }
      );
    }
  }

  async function finalize(event) {
    if (dirty.size) {
      showState(
        "Enregistrez d’abord les critères modifiés.",
        { error: true }
      );
      return;
    }

    const progress = globalProgress();

    if (progress.answered !== progress.count) {
      showState(
        `La grille n’est pas complète : ${progress.answered}/${progress.count} critère(s) noté(s).`,
        { error: true }
      );
      return;
    }

    const synthesis = window.prompt(
      "Synthèse finale du contrôle FUCCS :",
      control.synthese || ""
    );

    if (!synthesis?.trim()) return;

    const task = async () => {
      control = await apiPost(
        `/api/v1/fuccs/controles/${controlId}/finalize`,
        {
          synthese: synthesis.trim(),
        }
      );

      await reloadContext();
      renderHeader();
      renderRubricNav();
      renderActiveRubric();
      renderFindings();

      showState(
        "Contrôle FUCCS finalisé. Le score reste distinct de l’INFC et du classement SNCC."
      );
    };

    try {
      if (window.HAUQE_ACTION_LOADER) {
        await window.HAUQE_ACTION_LOADER.run(task, {
          button: event.currentTarget,
          title: "Finalisation FUCCS",
          message: "Contrôle des critères obligatoires",
          detail: "Le backend vérifie notes, commentaires et preuves requis.",
        });
      } else {
        await task();
      }
    } catch (error) {
      showState(
        error?.message || "Finalisation impossible.",
        { error: true }
      );
    }
  }

  async function reopen(event) {
    const reason = window.prompt(
      "Motif de réouverture :"
    );

    if (!reason?.trim()) return;

    const task = async () => {
      control = await apiPost(
        `/api/v1/fuccs/controles/${controlId}/reopen`,
        {
          motif: reason.trim(),
        }
      );

      await reloadContext();
      renderHeader();
      renderRubricNav();
      renderActiveRubric();
      renderFindings();
    };

    try {
      if (window.HAUQE_ACTION_LOADER) {
        await window.HAUQE_ACTION_LOADER.run(task, {
          button: event.currentTarget,
          title: "Réouverture FUCCS",
          message: "Réouverture du contrôle",
          detail: "Le motif est enregistré dans l’audit.",
        });
      } else {
        await task();
      }
    } catch (error) {
      showState(
        error?.message || "Réouverture impossible.",
        { error: true }
      );
    }
  }

  async function reloadControlAndNotes() {
    [control, notes] = await Promise.all([
      apiGet(`/api/v1/fuccs/controles/${controlId}`),
      apiGet(`/api/v1/fuccs/controles/${controlId}/notes`),
    ]);
  }

  async function reloadContext() {
    context = await apiGet(
      `/api/v1/fuccs/controles/${controlId}/context`
    );
  }

  async function bootstrap() {
    if (!controlId) {
      showState(
        "Identifiant du contrôle absent.",
        { error: true }
      );
      return;
    }

    const api = await import("/static/js/core/api.js");

    apiGet = api.apiGet;
    apiPost = api.apiPost;
    apiPatch = api.apiPatch;
    apiRequest = api.apiRequest;
    apiBlob = api.apiBlob;

    const task = async () => {
      [
        currentUser,
        control,
        context,
      ] = await Promise.all([
        apiGet("/api/v1/me"),
        apiGet(`/api/v1/fuccs/controles/${controlId}`),
        apiGet(`/api/v1/fuccs/controles/${controlId}/context`),
      ]);

      [
        grid,
        rubrics,
        criteria,
        notes,
        findings,
      ] = await Promise.all([
        apiGet(`/api/v1/fuccs/grilles/${control.grille_fuccs_id}`),
        apiGet(`/api/v1/fuccs/grilles/${control.grille_fuccs_id}/rubriques`),
        apiGet(`/api/v1/fuccs/grilles/${control.grille_fuccs_id}/criteres`),
        apiGet(`/api/v1/fuccs/controles/${controlId}/notes`),
        apiGet(`/api/v1/fuccs/controles/${controlId}/constats`),
      ]);

      const documentPayload = await apiGet(
        `/api/v1/documents?ressource_type=FICHE_COLLECTE`
        + `&ressource_id=${encodeURIComponent(context.fiche_id)}`
        + `&limit=100&offset=0`
      );

      documents = documentPayload.items || [];

      activeRubricId = rubrics[0]?.id || null;

      hideState();
      renderHeader();
      renderRubricNav();
      renderActiveRubric();
      renderFindings();
    };

    try {
      if (window.HAUQE_ACTION_LOADER) {
        await window.HAUQE_ACTION_LOADER.run(task, {
          title: "Contrôle FUCCS",
          message: "Chargement de la grille",
          detail: "Grille versionnée, critères, notes, preuves et constats.",
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

    $("#saveAllNotes").addEventListener(
      "click",
      saveAllDirty
    );

    $("#finalizeFuccs").addEventListener(
      "click",
      finalize
    );

    $("#reopenFuccs").addEventListener(
      "click",
      reopen
    );

    $("#addFuccsFinding").addEventListener(
      "click",
      createFinding
    );

    refreshIcons();
  }

  bootstrap();
})();
