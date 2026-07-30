(async function () {
  "use strict";
  const api = await import("/static/js/core/api.js");
  const $ = (s) => document.querySelector(s);
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const icons = () => window.lucide?.createIcons({ attrs: { "stroke-width": 1.8 } });
  const today = () => new Date().toISOString().slice(0, 10);
  let me, publications = [], rules = [], stage = "draft";
  const has = (p) => me?.permissions?.includes(p);
  const stageMap = {
    draft: { title: "Brouillons", statuses: ["BROUILLON"] },
    approval: { title: "À approuver", statuses: ["SOUMISE", "REJETEE"] },
    publication: { title: "Publication", statuses: ["APPROUVEE", "PUBLIEE"] },
    retired: { title: "Publications retirées", statuses: ["RETIREE"] },
  };
  const statusLabel = (s) => ({ BROUILLON: "Brouillon", SOUMISE: "À approuver", APPROUVEE: "Approuvée", REJETEE: "Rejetée", PUBLIEE: "Publiée", RETIREE: "Retirée" })[s] || s;
  const statusClass = (s) => s === "PUBLIEE" ? "published" : s === "REJETEE" ? "rejected" : s === "RETIREE" ? "retired" : "";
  function toast(message, error = false) {
    const b = $("#publicationToast"); b.querySelector("span").textContent = message;
    b.classList.toggle("error", error); b.hidden = false; setTimeout(() => b.hidden = true, 2800);
  }
  async function load() {
    const [pubs, ruleData] = await Promise.all([
      api.apiRequest("/api/v1/publications?limit=200&offset=0"),
      api.apiRequest("/api/v1/governance/rules?logical_code=PUBLIC_DASHBOARD_INDICATORS&statut=PUBLIE"),
    ]);
    publications = pubs.items || []; rules = Array.isArray(ruleData) ? ruleData : (ruleData.items || []);
    fillRules(); render();
  }
  function fillRules() {
    const select = $("#publicationForm [name=resource]");
    select.innerHTML = `<option value="">Sélectionner une configuration publiée…</option>${rules.map((r) => `<option value="${r.id}">${esc(r.libelle || r.code)} · ${esc(r.version || "version active")}</option>`).join("")}`;
    $("#publicationRuleHelp").textContent = rules.length ? `${rules.length} configuration(s) publique(s) disponible(s).` : "Aucune règle PUBLIC_DASHBOARD_INDICATORS publiée : configurez-la d’abord dans Règles et codification.";
  }
  function filtered() {
    const q = $("#publicationSearch").value.trim().toLowerCase();
    const confidentiality = $("#publicationConfidentiality").value;
    return publications.filter((x) => stageMap[stage].statuses.includes(x.statut)
      && (!q || `${x.objet} ${x.perimetre} ${x.autorite_approbation} ${x.ressource_type}`.toLowerCase().includes(q))
      && (!confidentiality || x.niveau_confidentialite === confidentiality));
  }
  function actions(x) {
    if (x.statut === "BROUILLON" && has("PUBLICATIONS.DEMANDER")) return `<button class="btn btn-primary app-btn" data-submit="${x.id}"><i data-lucide="send"></i>Soumettre</button>`;
    if (x.statut === "SOUMISE" && has("PUBLICATIONS.APPROUVER")) return `<button class="btn btn-primary app-btn" data-approve="${x.id}"><i data-lucide="stamp"></i>Décider</button>`;
    if (x.statut === "APPROUVEE" && has("PUBLICATIONS.PUBLIER")) return `<button class="btn btn-primary app-btn" data-publish="${x.id}"><i data-lucide="globe-2"></i>Publier</button>`;
    if (x.statut === "PUBLIEE" && has("PUBLICATIONS.PUBLIER")) return `<button class="btn btn-outline-danger app-btn" data-retire="${x.id}"><i data-lucide="archive-x"></i>Retirer</button>`;
    return "";
  }
  function render() {
    const rows = filtered(), counts = (statuses) => publications.filter((x) => statuses.includes(x.statut)).length;
    $("#publicationKpis").innerHTML = [
      ["file-pen-line", "Brouillons", counts(["BROUILLON"]), "En préparation"],
      ["stamp", "À approuver", counts(["SOUMISE"]), "Décision attendue"],
      ["globe-2", "Publiées", counts(["PUBLIEE"]), "Visibles publiquement"],
      ["archive-x", "Retirées", counts(["RETIREE"]), "Historique conservé"],
    ].map((x) => `<article class="publication-kpi"><span><i data-lucide="${x[0]}"></i></span><div><small>${x[1]}</small><strong>${x[2]}</strong><em>${x[3]}</em></div></article>`).join("");
    $("#publicationStageTitle").textContent = stageMap[stage].title;
    $("#publicationCount").textContent = `${rows.length} demande${rows.length > 1 ? "s" : ""}`;
    $("#publicationCards").innerHTML = rows.map((x) => `<article class="publication-card"><header><div><span class="pub-ref">${esc(String(x.id).slice(0, 8))} · ${esc(x.ressource_type)}</span><h3>${esc(x.objet)}</h3></div><span class="publication-state ${statusClass(x.statut)}">${statusLabel(x.statut)}</span></header><p>${esc(x.perimetre)}</p><dl><dt>Confidentialité</dt><dd>${esc(x.niveau_confidentialite)}</dd><dt>Demandée le</dt><dd>${esc(x.date_demande || "—")}</dd>${x.autorite_approbation ? `<dt>Autorité</dt><dd>${esc(x.autorite_approbation)}</dd>` : ""}${x.reserve ? `<dt>Réserve</dt><dd>${esc(x.reserve)}</dd>` : ""}${x.date_publication ? `<dt>Publiée le</dt><dd>${esc(x.date_publication)}</dd>` : ""}</dl><footer>${actions(x)}</footer></article>`).join("");
    $("#publicationEmpty").hidden = rows.length > 0; $("#publicationCards").hidden = !rows.length;
    bindActions(); icons();
  }
  function bindActions() {
    document.querySelectorAll("[data-submit]").forEach((b) => b.onclick = async () => {
      const comment = prompt("Commentaire de soumission à l’autorité (facultatif) :");
      if (comment === null) return;
      await act(`/api/v1/publications/${b.dataset.submit}/submit`, { commentaire: comment || null }, "Demande transmise pour approbation.");
    });
    document.querySelectorAll("[data-approve]").forEach((b) => b.onclick = () => {
      const f = $("#approvalForm"); f.reset(); f.id.value = b.dataset.approve; $("#approvalDialog").showModal(); icons();
    });
    document.querySelectorAll("[data-publish]").forEach((b) => b.onclick = () => {
      const f = $("#publishForm"); f.reset(); f.id.value = b.dataset.publish; f.date.value = today(); $("#publishDialog").showModal(); icons();
    });
    document.querySelectorAll("[data-retire]").forEach((b) => b.onclick = () => {
      const f = $("#retireForm"); f.reset(); f.id.value = b.dataset.retire; $("#retireDialog").showModal(); icons();
    });
  }
  async function act(path, body, success) {
    try { await api.apiRequest(path, { method: "POST", body }); toast(success); await load(); }
    catch (e) { toast(e.message, true); }
  }
  document.querySelectorAll("[data-stage]").forEach((b) => b.onclick = () => {
    stage = b.dataset.stage; document.querySelectorAll("[data-stage]").forEach((x) => x.classList.toggle("active", x === b)); render();
  });
  $("#publicationSearch").oninput = render; $("#publicationConfidentiality").onchange = render; $("#publicationRefresh").onclick = load;
  $("#publicationNew").onclick = () => {
    if (!rules.length) return toast("Aucune configuration d’indicateurs publics publiée n’est disponible.", true);
    $("#publicationDialog").showModal(); icons();
  };
  document.querySelectorAll("[data-close]").forEach((b) => b.onclick = () => b.closest("dialog").close());
  $("#publicationForm").onsubmit = async (e) => {
    e.preventDefault(); const f = e.currentTarget;
    try {
      await api.apiRequest("/api/v1/publications", { method: "POST", body: { ressource_type: "PUBLIC_DASHBOARD_RULE", ressource_id: f.resource.value, objet: f.subject.value, perimetre: f.scope.value, niveau_confidentialite: f.confidentiality.value } });
      f.closest("dialog").close(); f.reset(); toast("Brouillon de publication créé."); await load();
    } catch (err) { toast(err.message, true); }
  };
  $("#approvalForm").onsubmit = async (e) => {
    e.preventDefault(); const f = e.currentTarget;
    if (f.decision.value === "REJETE" && !f.reserve.value.trim()) return toast("Le motif du rejet est obligatoire.", true);
    f.closest("dialog").close();
    await act(`/api/v1/publications/${f.id.value}/approve`, { decision: f.decision.value, autorite_approbation: f.authority.value, reserve: f.reserve.value || null }, f.decision.value === "APPROUVE" ? "Publication approuvée." : "Demande rejetée.");
  };
  $("#publishForm").onsubmit = async (e) => {
    e.preventDefault(); const f = e.currentTarget;
    if (!confirm("Confirmer la mise à disposition de ces indicateurs sur le tableau de bord public ?")) return;
    f.closest("dialog").close();
    await act(`/api/v1/publications/${f.id.value}/publish`, { date_publication: f.date.value, commentaire: f.comment.value || null }, "Indicateurs autorisés sur le tableau de bord public.");
  };
  $("#retireForm").onsubmit = async (e) => {
    e.preventDefault(); const f = e.currentTarget;
    if (!confirm("Confirmer le retrait de cette publication du tableau public ?")) return;
    f.closest("dialog").close();
    await act(`/api/v1/publications/${f.id.value}/retire`, { motif: f.reason.value }, "Publication retirée et historisée.");
  };
  try {
    me = await api.apiRequest("/api/v1/me"); $("#publicationNew").hidden = !has("PUBLICATIONS.DEMANDER"); await load();
  } catch (error) { toast(error.message, true); }
})();
