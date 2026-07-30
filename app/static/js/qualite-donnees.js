(async function () {
  "use strict";
  const api = await import("/static/js/core/api.js");
  const $ = (s) => document.querySelector(s);
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const icons = () => window.lucide?.createIcons({ attrs: { "stroke-width": 1.8 } });
  let me, reviews = [], plans = [];
  const has = (p) => me?.permissions?.includes(p);
  function toast(message, error = false) { const b = $("#qualityToast"); b.querySelector("span").textContent = message; b.classList.toggle("error", error); b.hidden = false; setTimeout(() => b.hidden = true, 2600); }
  async function load() {
    const status = $("#qualityStatus").value;
    const [r, p] = await Promise.all([
      api.apiRequest(`/api/v1/quality/reviews?limit=200${status ? `&statut=${status}` : ""}`),
      api.apiRequest("/api/v1/quality/action-plans?limit=500"),
    ]);
    reviews = r.items || []; plans = p.items || []; render();
  }
  function render() {
    const q = $("#qualitySearch").value.trim().toLowerCase();
    const shown = reviews.filter((r) => !q || `${r.perimetre} ${r.resultat_global} ${r.statut}`.toLowerCase().includes(q));
    $("#qualityCount").textContent = `${shown.length} revue${shown.length > 1 ? "s" : ""}`;
    $("#qualityRows").innerHTML = shown.map((r) => `<tr><td><strong>${esc(r.periode_debut || "—")}</strong><small> au ${esc(r.periode_fin || "—")}</small></td><td>${esc(r.perimetre || "—")}</td><td>${esc(r.resultat_global || "En attente de mesure")}</td><td>${r.plans_action_count}</td><td><span class="quality-state ${r.statut === "VALIDEE" ? "done" : ""}">${r.statut === "VALIDEE" ? "Validée" : "Brouillon"}</span></td><td>${r.statut !== "VALIDEE" && has("QUALITE.VALIDER") ? `<button class="icon-button" data-validate="${r.id}" title="Valider"><i data-lucide="badge-check"></i></button>` : ""}</td></tr>`).join("");
    $("#qualityEmpty").hidden = shown.length > 0; $("#qualityRows").closest(".table-responsive").hidden = !shown.length;
    const late = plans.filter((p) => p.date_echeance && new Date(p.date_echeance) < new Date() && p.statut !== "CLOTURE").length;
    const progress = plans.length ? Math.round(plans.reduce((n, p) => n + (p.progression || 0), 0) / plans.length) : 0;
    $("#qualityKpis").innerHTML = [
      ["badge-check", "Revues validées", reviews.filter((r) => r.statut === "VALIDEE").length, "Mesures approuvées"],
      ["clipboard-list", "Revues en cours", reviews.filter((r) => r.statut !== "VALIDEE").length, "À compléter"],
      ["list-todo", "Plans d’action", plans.length, `${progress} % de progression moyenne`],
      ["clock-alert", "Actions en retard", late, "Échéances dépassées"],
    ].map((x) => `<article><span><i data-lucide="${x[0]}"></i></span><div><small>${x[1]}</small><strong>${x[2]}</strong><em>${x[3]}</em></div></article>`).join("");
    $("#qualityPlans").innerHTML = plans.length ? plans.map((p) => `<article class="quality-plan"><header><strong>${esc(p.titre)}</strong><span class="quality-state ${p.statut === "CLOTURE" ? "done" : ""}">${esc((p.statut || "PLANIFIE").replaceAll("_", " "))}</span></header><p>${esc(p.objectif || "")}</p><small>Échéance : ${esc(p.date_echeance || "—")}</small><progress max="100" value="${p.progression || 0}"></progress><b>${p.progression || 0} %</b></article>`).join("") : `<div class="quality-empty"><span>Aucun plan d’action enregistré.</span></div>`;
    document.querySelectorAll("[data-validate]").forEach((b) => b.onclick = async () => {
      const result = prompt("Résultat global validé (ex. 94 % — Satisfaisant) :"); if (!result) return;
      try { await api.apiRequest(`/api/v1/quality/reviews/${b.dataset.validate}/validate`, { method: "POST", body: { resultat_global: result, commentaire: null } }); toast("Revue validée."); await load(); } catch (e) { toast(e.message, true); }
    });
    icons();
  }
  $("#qualitySearch").oninput = render; $("#qualityStatus").onchange = load; $("#qualityRefresh").onclick = load;
  $("#qualityNew").onclick = () => $("#qualityReviewDialog").showModal();
  $("#qualityNewPlan").onclick = () => $("#qualityPlanDialog").showModal();
  document.querySelectorAll("[data-close]").forEach((b) => b.onclick = () => b.closest("dialog").close());
  $("#qualityReviewForm").onsubmit = async (e) => {
    e.preventDefault(); const f = e.currentTarget;
    try {
      await api.apiRequest("/api/v1/quality/reviews", { method: "POST", body: { periode_debut: f.start.value, periode_fin: f.end.value, perimetre: f.scope.value, constats: f.findings.value ? { observation: f.findings.value } : {}, preuves: {}, responsable_id: me.id } });
      f.closest("dialog").close(); f.reset(); toast("Revue créée et auditée."); await load();
    } catch (err) { toast(err.message, true); }
  };
  $("#qualityPlanForm").onsubmit = async (e) => {
    e.preventDefault(); const f = e.currentTarget;
    try {
      await api.apiRequest("/api/v1/quality/action-plans", { method: "POST", body: { titre: f.title.value, objectif: f.objective.value, responsable_id: me.id, date_echeance: f.deadline.value, priorite: f.priority.value, indicateur: f.indicator.value } });
      f.closest("dialog").close(); f.reset(); toast("Plan d’action créé."); await load();
    } catch (err) { toast(err.message, true); }
  };
  try {
    me = await api.apiRequest("/api/v1/me");
    $("#qualityNew").hidden = !has("QUALITE.GERER"); $("#qualityNewPlan").hidden = !has("QUALITE.GERER");
    await load();
  } catch (error) { toast(error.message, true); }
})();
