(async function () {
  "use strict";
  const api = await import("/static/js/core/api.js");
  const $ = (s) => document.querySelector(s);
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const icons = () => window.lucide?.createIcons({ attrs: { "stroke-width": 1.8 } });
  const today = () => new Date().toISOString().slice(0, 10);
  let me, items = [];
  const has = (permission) => me?.permissions?.includes(permission);
  const policies = () => items.filter((x) => x.type_enregistrement === "POLITIQUE");
  const operations = () => items.filter((x) => x.type_enregistrement !== "POLITIQUE");
  const statusLabel = (s) => ({ ACTIVE: "Active", EN_COURS: "En cours", TERMINE: "Terminé", ECHEC: "Échec", ECHEC_INTEGRITE: "Échec d’intégrité" })[s] || String(s || "—").replaceAll("_", " ");
  const typeLabel = (t) => t === "TEST_RESTAURATION" ? "Test de restauration" : "Sauvegarde";
  const stateClass = (s) => s === "TERMINE" || s === "ACTIVE" ? "done" : String(s).startsWith("ECHEC") ? "failed" : "";
  function toast(message, error = false) {
    const box = $("#backupToast"); box.querySelector("span").textContent = message;
    box.classList.toggle("error", error); box.hidden = false;
    setTimeout(() => box.hidden = true, 2800);
  }
  function sizeLabel(bytes) {
    if (bytes == null) return "—";
    const units = ["o", "Ko", "Mo", "Go", "To"]; let value = Number(bytes), index = 0;
    while (value >= 1024 && index < units.length - 1) { value /= 1024; index += 1; }
    return `${value.toLocaleString("fr-FR", { maximumFractionDigits: 1 })} ${units[index]}`;
  }
  function showProgress(item) {
    const dialog=$("#backupProgressDialog"), bar=$("#backupProgressBar");
    if(!dialog.open)dialog.showModal();
    const parts=String(item.resultat||"0|Initialisation").split("|"),value=Math.max(0,Math.min(100,Number(parts[0])||0));
    $("#backupProgressMessage").textContent=parts.slice(1).join("|")||"Sauvegarde en cours, veuillez patienter…";$("#backupProgressValue").textContent=`${value} %`;bar.style.width=`${value}%`;bar.style.background=value<=15?"#cf2f3b":value<=25?"#ec8b24":value<=50?"#d5b721":value<=80?"#2478c5":"#20945f";
  }
  async function followRun(id){for(let i=0;i<720;i+=1){const item=await api.apiRequest(`/api/v1/backups/${id}`);showProgress(item);if(item.statut!=="EN_COURS"){setTimeout(()=>$("#backupProgressDialog").close(),700);toast(item.statut==="TERMINE"?"Sauvegarde terminée et contrôlée.":item.message_erreur||"Échec de la sauvegarde.",item.statut!=="TERMINE");await load();return}await new Promise(r=>setTimeout(r,1000))}}
  async function load() {
    const payload = await api.apiRequest("/api/v1/backups?limit=500&offset=0");
    items = payload.items || []; render();
  }
  function render() {
    const runs = operations(), completed = runs.filter((x) => x.statut === "TERMINE");
    const failed = runs.filter((x) => String(x.statut).startsWith("ECHEC"));
    const lastRun = [...completed].sort((a, b) => String(b.date_fin).localeCompare(String(a.date_fin)))[0];
    const restoreTests = runs.filter((x) => x.type_enregistrement === "TEST_RESTAURATION");
    $("#backupKpis").innerHTML = [
      ["shield-check", "Politiques actives", policies().filter((x) => x.statut === "ACTIVE").length, "Plans de protection"],
      ["database-backup", "Sauvegardes réussies", completed.filter((x) => x.type_enregistrement === "EXECUTION").length, "Intégrité validée"],
      ["rotate-ccw", "Tests de restauration", restoreTests.length, `${restoreTests.filter((x) => x.statut === "TERMINE").length} réussi(s)`],
      ["triangle-alert", "Échecs", failed.length, "Opérations à examiner"],
    ].map((x) => `<article class="backup-kpi"><span><i data-lucide="${x[0]}"></i></span><div><small>${x[1]}</small><strong>${x[2]}</strong><em>${x[3]}</em></div></article>`).join("");
    $("#backupPolicies").innerHTML = policies().length ? policies().map((p) => `<section class="backup-policy"><div><h3>${esc(p.perimetre)}</h3><p>${esc(p.emplacement_stockage)}</p><div class="backup-policy-meta"><span><i data-lucide="calendar-sync"></i> ${esc(p.frequence)}</span><span><i data-lucide="archive"></i> Rétention : ${esc(p.retention)}</span><span class="backup-state done">${statusLabel(p.statut)}</span></div></div><div class="backup-policy-actions">${has("SAUVEGARDES.GERER") ? `<button class="btn btn-outline-secondary app-btn" data-run="${p.id}"><i data-lucide="play"></i>Consigner une exécution</button>` : ""}</div></section>`).join("") : `<div class="backup-empty"><i data-lucide="shield-plus"></i><strong>Aucune politique</strong><span>Créez le premier plan de sauvegarde.</span></div>`;
    $("#backupHealth").innerHTML = [
      ["Dernière sauvegarde valide", lastRun?.date_fin || "Aucune", Boolean(lastRun)],
      ["Intégrité du dernier résultat", lastRun?.integrite_validee ? "Validée" : "Non disponible", Boolean(lastRun?.integrite_validee)],
      ["Dernier test de restauration", restoreTests.find((x) => x.statut === "TERMINE")?.date_fin || "Aucun", restoreTests.some((x) => x.statut === "TERMINE")],
      ["Opérations en cours", runs.filter((x) => x.statut === "EN_COURS").length, !runs.some((x) => x.statut === "EN_COURS")],
    ].map((x) => `<div class="backup-health-row"><span>${x[0]}</span><b class="${x[2] ? "good" : "bad"}">${esc(x[1])}</b></div>`).join("");
    renderRows();
    document.querySelectorAll("[data-run]").forEach((b) => b.onclick = async () => {
      if (!confirm("Confirmer l’enregistrement du démarrage de cette sauvegarde ? L’exécution technique reste sous la responsabilité de l’infrastructure.")) return;
      try {
        const run=await api.apiRequest(`/api/v1/backups/policies/${b.dataset.run}/runs`, { method: "POST", body: { date_debut: today() } });
        showProgress(run); followRun(run.id);
      } catch (e) { toast(e.message, true); }
    });
    icons();
  }
  function filtered() {
    const q = $("#backupSearch").value.trim().toLowerCase(), type = $("#backupType").value, status = $("#backupStatus").value;
    return operations().filter((x) => (!q || `${x.perimetre} ${x.resultat} ${x.emplacement_stockage} ${x.message_erreur}`.toLowerCase().includes(q)) && (!type || x.type_enregistrement === type) && (!status || x.statut === status));
  }
  function renderRows() {
    const rows = filtered();
    $("#backupRows").innerHTML = rows.map((x) => `<tr><td><div class="backup-type"><i data-lucide="${x.type_enregistrement === "TEST_RESTAURATION" ? "rotate-ccw" : "database-backup"}"></i> ${typeLabel(x.type_enregistrement)}</div><small>${esc(String(x.id).slice(0, 8))}</small></td><td>${esc(x.perimetre || "—")}<small class="d-block">${esc(x.emplacement_stockage || "")}</small></td><td>${esc(x.date_debut || "—")}<small class="d-block">${x.date_fin ? `Fin : ${esc(x.date_fin)}` : "Non finalisée"}</small></td><td>${sizeLabel(x.taille_octets)}</td><td>${x.integrite_validee == null ? "À contrôler" : x.integrite_validee ? "Validée" : "Non validée"}</td><td>${esc(x.resultat || x.message_erreur || "—")}</td><td><span class="backup-state ${stateClass(x.statut)}">${statusLabel(x.statut)}</span></td><td><div class="backup-policy-actions">${has("SAUVEGARDES.GERER") && x.statut === "EN_COURS" ? `<button class="icon-button" data-complete="${x.id}" title="Finaliser"><i data-lucide="check-circle"></i></button><button class="icon-button" data-fail="${x.id}" title="Déclarer un échec"><i data-lucide="circle-x"></i></button>` : ""}${has("SAUVEGARDES.GERER") && x.type_enregistrement === "EXECUTION" && x.statut === "TERMINE" ? `<button class="icon-button" data-restore="${x.id}" title="Créer un test de restauration"><i data-lucide="rotate-ccw"></i></button>` : ""}</div></td></tr>`).join("");
    $("#backupEmpty").hidden = rows.length > 0; $("#backupRows").closest(".table-responsive").hidden = !rows.length;
    document.querySelectorAll("[data-complete]").forEach((b) => b.onclick = () => { const f = $("#backupCompleteForm"); f.reset(); f.id.value = b.dataset.complete; $("#backupCompleteDialog").showModal(); icons(); });
    document.querySelectorAll("[data-restore]").forEach((b) => b.onclick = () => { const f = $("#restoreForm"); f.reset(); f.id.value = b.dataset.restore; $("#restoreDialog").showModal(); icons(); });
    document.querySelectorAll("[data-fail]").forEach((b) => b.onclick = async () => {
      const message = prompt("Décrivez précisément la cause de l’échec :"); if (!message) return;
      try {
        await api.apiRequest(`/api/v1/backups/${b.dataset.fail}/fail`, { method: "POST", body: { date_fin: today(), message_erreur: message, resultat: "Opération interrompue et à examiner." } });
        toast("Échec enregistré et journalisé.", true); await load();
      } catch (e) { toast(e.message, true); }
    });
    icons();
  }
  $("#backupSearch").oninput = renderRows; $("#backupType").onchange = renderRows; $("#backupStatus").onchange = renderRows;
  $("#backupRefresh").onclick = load; $("#backupNewPolicy").onclick = () => $("#backupPolicyDialog").showModal();
  document.querySelectorAll("[data-close]").forEach((b) => b.onclick = () => b.closest("dialog").close());
  $("#backupPolicyForm").onsubmit = async (e) => {
    e.preventDefault(); const f = e.currentTarget;
    try {
      await api.apiRequest("/api/v1/backups/policies", { method: "POST", body: { frequence: f.frequency.value, retention: f.retention.value, perimetre: f.scope.value, emplacement_stockage: f.location.value } });
      f.closest("dialog").close(); f.reset(); toast("Politique créée et auditée."); await load();
    } catch (err) { toast(err.message, true); }
  };
  $("#backupCompleteForm").onsubmit = async (e) => {
    e.preventDefault(); const f = e.currentTarget;
    if (!f.integrity.checked) return toast("L’intégrité doit être contrôlée avant de déclarer l’opération réussie.", true);
    try {
      await api.apiRequest(`/api/v1/backups/${f.id.value}/complete`, { method: "POST", body: { date_fin: today(), taille_octets: f.size.value ? Number(f.size.value) : null, integrite_validee: true, resultat: f.result.value, preuve_document_id: null } });
      f.closest("dialog").close(); toast("Opération finalisée avec intégrité validée."); await load();
    } catch (err) { toast(err.message, true); }
  };
  $("#restoreForm").onsubmit = async (e) => {
    e.preventDefault(); const f = e.currentTarget;
    if (!confirm("Créer ce test de restauration isolé à partir de la sauvegarde sélectionnée ?")) return;
    try {
      await api.apiRequest(`/api/v1/backups/${f.id.value}/restore-tests`, { method: "POST", body: { perimetre: f.scope.value || null } });
      f.closest("dialog").close(); toast("Test de restauration créé. Son exécution doit maintenant être consignée."); await load();
    } catch (err) { toast(err.message, true); }
  };
  try {
    me = await api.apiRequest("/api/v1/me");
    $("#backupNewPolicy").hidden = !has("SAUVEGARDES.GERER");
    await load();
  } catch (error) { toast(error.message, true); }
})();
