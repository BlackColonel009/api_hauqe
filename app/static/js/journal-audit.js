(async function () {
  "use strict";
  const api = await import("/static/js/core/api.js");
  const $ = (s) => document.querySelector(s);
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const icons = () => window.lucide?.createIcons({ attrs: { "stroke-width": 1.8 } });
  const actionLabels = {
    CREATE: "Création", UPDATE: "Modification", DELETE: "Suppression",
    LOGIN: "Connexion", LOGOUT: "Déconnexion", EXPORT: "Export",
    VALIDATE: "Validation", COMPLETE: "Finalisation", FAIL: "Échec",
  };
  let rows = [], total = 0, me = null;
  const labelAction = (v) => {
    const code = String(v || "ÉVÉNEMENT").toUpperCase();
    const suffix = Object.entries(actionLabels).find(([key]) => code.includes(key))?.[1];
    return suffix || code.replaceAll("_", " ").toLowerCase().replace(/^\p{L}/u, (c) => c.toUpperCase());
  };
  const isSuccess = (v) => /SUCC|REUSS|OK/i.test(v || "");
  const dateFr = (v) => v ? new Intl.DateTimeFormat("fr-FR", { dateStyle: "medium", timeStyle: "medium", timeZone: "Africa/Lome" }).format(new Date(v)) : "—";
  function toast(message, error = false) {
    const box = $("#auditToast"); box.querySelector("span").textContent = message;
    box.classList.toggle("error", error); box.hidden = false;
    setTimeout(() => { box.hidden = true; }, 2500);
  }
  async function load() {
    const params = new URLSearchParams({ limit: "500" });
    const nature = $("#auditType").value;
    const result = $("#auditResult").value;
    if (nature !== "all") params.set("categorie", nature);
    if (result !== "all") params.set("resultat", result === "success" ? "SUCCES" : "ECHEC");
    const payload = await api.apiRequest(`/api/v1/audit/events?${params}`);
    rows = payload.items || []; total = payload.total || 0; render();
  }
  function filtered() {
    const q = $("#auditSearch").value.trim().toLowerCase();
    return rows.filter((x) => !q || `${x.action} ${x.categorie} ${x.ressource_type} ${x.ressource_id} ${x.adresse_ip} ${x.utilisateur_id}`.toLowerCase().includes(q));
  }
  function render() {
    const list = filtered();
    $("#auditCount").textContent = `${list.length} événement${list.length > 1 ? "s" : ""} affiché${list.length > 1 ? "s" : ""} sur ${total}`;
    $("#auditResults").innerHTML = list.length ? `<div class="table-responsive"><table class="table audit-table"><thead><tr>
      <th>Date et heure</th><th>Auteur</th><th>Nature</th><th>Opération</th><th>Ressource</th><th>Adresse IP</th><th>Résultat</th><th></th>
      </tr></thead><tbody>${list.map((x) => `<tr data-audit="${x.id}">
      <td>${dateFr(x.date_evenement || x.created_at)}</td>
      <td><div class="audit-author"><span><i data-lucide="user-round"></i></span><div><strong>${esc(x.utilisateur_nom || (x.utilisateur_id ? "Utilisateur" : "Système"))}</strong><small>${esc(x.utilisateur_email || (x.utilisateur_id ? "Utilisateur authentifié" : "Traitement automatique"))}</small></div></div></td>
      <td><span class="audit-type">${esc(x.categorie || "Général")}</span></td><td>${esc(labelAction(x.action))}</td>
      <td><code>${esc(x.ressource_type || "—")}${x.ressource_id ? ` · ${esc(String(x.ressource_id).slice(0, 8))}` : ""}</code></td>
      <td>${esc(x.adresse_ip || "—")}</td><td><span class="audit-result ${isSuccess(x.resultat) ? "success" : "failed"}">${isSuccess(x.resultat) ? "Réussi" : "Échec"}</span></td>
      <td><i data-lucide="chevron-right"></i></td></tr>`).join("")}</tbody></table></div>` :
      `<div class="reference-empty"><i data-lucide="inbox"></i><strong>Aucun événement</strong><span>Aucune trace ne correspond aux filtres.</span></div>`;
    const successes = rows.filter((x) => isSuccess(x.resultat)).length;
    $("#auditKpis").innerHTML = [
      ["scroll-text", "Événements", total, "Journal serveur"],
      ["shield-check", "Opérations réussies", successes, rows.length ? `${Math.round(successes / rows.length * 100)} %` : "—"],
      ["shield-alert", "Échecs", rows.length - successes, "À examiner"],
      ["fingerprint", "Empreintes présentes", rows.filter((x) => x.empreinte).length, "Contrôle d’intégrité"],
    ].map((x) => `<article class="audit-kpi"><span><i data-lucide="${x[0]}"></i></span><div><small>${x[1]}</small><strong>${x[2]}</strong><em>${x[3]}</em></div></article>`).join("");
    document.querySelectorAll("[data-audit]").forEach((tr) => tr.onclick = () => open(rows.find((x) => x.id === tr.dataset.audit)));
    icons();
  }
  function prettyJson(value) {
    if (!value || (typeof value === "object" && !Object.keys(value).length)) return "Aucune valeur";
    return esc(JSON.stringify(value, null, 2));
  }
  function open(x) {
    $("#auditDrawerTitle").textContent = labelAction(x.action);
    $("#auditDrawerBody").innerHTML = `<section class="audit-detail">${[
      ["Identifiant", x.id], ["Horodatage", dateFr(x.date_evenement || x.created_at)],
      ["Catégorie", x.categorie || "Général"], ["Ressource", x.ressource_type || "—"],
      ["Adresse IP", x.adresse_ip || "—"], ["Résultat", isSuccess(x.resultat) ? "Réussi" : "Échec"],
      ["Contexte", x.contexte || "—"], ["Empreinte", x.empreinte || "Non renseignée"],
    ].map((y) => `<div class="audit-detail-row"><span>${y[0]}</span><strong>${esc(y[1])}</strong></div>`).join("")}</section>
    <section class="audit-diff"><h3>Valeurs avant et après</h3><div class="diff-row"><b>Avant</b><b>Après</b></div>
    <div class="diff-row"><pre>${prettyJson(x.valeurs_avant)}</pre><pre>${prettyJson(x.valeurs_apres)}</pre></div></section>`;
    $("#auditOverlay").hidden = false; $("#auditDrawer").classList.add("open"); icons();
  }
  $("#auditSearch").oninput = render;
  $("#auditType").innerHTML = `<option value="all">Toutes les catégories</option><option value="SECURITE">Sécurité</option><option value="REFERENTIEL">Référentiel</option><option value="QUALITE">Qualité</option><option value="REPORTING">Rapports</option><option value="METIER">Métier</option>`;
  $("#auditType").onchange = load; $("#auditResult").onchange = load;
  $("#resetAudit").onclick = async () => { $("#auditSearch").value = ""; $("#auditType").value = $("#auditResult").value = "all"; await load(); };
  $("#closeAudit").onclick = $("#auditOverlay").onclick = () => { $("#auditOverlay").hidden = true; $("#auditDrawer").classList.remove("open"); };
  $("#verifyIntegrity").onclick = () => {
    const missing = rows.filter((x) => !x.empreinte).length;
    toast(missing ? `${missing} événement(s) sans empreinte sur la page chargée.` : "Toutes les traces chargées possèdent une empreinte.", Boolean(missing));
  };
  $("#exportAudit").onclick = () => {
    const agent = [me?.prenoms, me?.nom].filter(Boolean).join(" ") || me?.email || "Agent HAUQE";
    const body = filtered().map((x) => `<tr><td>${esc(dateFr(x.date_evenement || x.created_at))}</td><td>${esc(x.utilisateur_nom || "Système")}</td><td>${esc(labelAction(x.action))}</td><td>${esc(x.categorie || "Général")}</td><td>${esc(x.ressource_type || "—")}</td><td>${esc(x.adresse_ip || "—")}</td><td>${isSuccess(x.resultat) ? "Réussi" : "Échec"}</td></tr>`).join("");
    const html = `<!doctype html><html><head><meta charset="utf-8"><style>body{font-family:Arial;color:#173c2e}.head{border-bottom:3px solid #176b4d;padding-bottom:12px}.brand{font-size:22px;font-weight:700;color:#176b4d}.agent{float:right;font-size:11px}.meta{margin:14px 0}table{border-collapse:collapse;width:100%}th{background:#176b4d;color:white;padding:8px;border:1px solid #d4e2db}td{padding:7px;border:1px solid #d4e2db}tr:nth-child(even){background:#f2f8f5}</style></head><body><div class="head"><span class="agent">Export demandé par<br><strong>${esc(agent)}</strong></span><div class="brand">HAUQE</div><div>Haute Autorité de la Qualité et de l’Environnement</div></div><h1>Journal d’audit</h1><div class="meta">Généré le ${esc(new Date().toLocaleString("fr-FR"))} · ${filtered().length} événement(s)</div><table><thead><tr><th>Date</th><th>Agent</th><th>Opération</th><th>Catégorie</th><th>Ressource</th><th>Adresse IP</th><th>Résultat</th></tr></thead><tbody>${body}</tbody></table></body></html>`;
    const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob(["\ufeff" + html], { type: "application/vnd.ms-excel" })); a.download = `journal-audit-${new Date().toISOString().slice(0, 10)}.xls`; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 1000);
    toast("Journal exporté avec l’en-tête institutionnel HAUQE.");
  };
  try { me = await api.apiRequest("/api/v1/me"); await load(); } catch (error) { toast(error.message, true); }
})();
