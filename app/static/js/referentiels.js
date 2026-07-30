(async function () {
  "use strict";
  const api = await import("/static/js/core/api.js");
  const $ = (s) => document.querySelector(s);
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const icons = () => window.lucide?.createIcons({ attrs: { "stroke-width": 1.8 } });
  let refs = [], current = null, values = [], editing = null;

  function toast(message, error = false) {
    const box = $("#referenceToast");
    box.querySelector("span").textContent = message;
    box.classList.toggle("error", error);
    box.hidden = false;
    setTimeout(() => { box.hidden = true; }, 2600);
  }
  const statusLabel = (s) => String(s || "ACTIF").toUpperCase() === "ACTIF" ? "Actif" : "Inactif";

  async function loadRefs(keep = true) {
    const selected = keep ? current?.id : null;
    const payload = await api.apiRequest("/api/v1/referentiels");
    refs = payload.items || [];
    current = refs.find((x) => x.id === selected) || refs[0] || null;
    renderRefs();
    await loadValues();
  }
  function renderRefs() {
    $("#referenceCategories").innerHTML = refs.length ? refs.map((r) => `
      <button class="reference-category ${r.id === current?.id ? "active" : ""}" data-ref="${r.id}">
        <span><i data-lucide="library-big"></i></span>
        <div><strong>${esc(r.libelle || r.code)}</strong><small>${esc(r.code)}</small></div><b>${r.valeurs_count}</b>
      </button>`).join("") : `<div class="reference-empty">Aucun référentiel enregistré.</div>`;
    document.querySelectorAll("[data-ref]").forEach((b) => b.onclick = async () => {
      current = refs.find((r) => r.id === b.dataset.ref);
      renderRefs();
      await loadValues();
    });
    $("#referenceKpis").innerHTML = [
      ["database", "Référentiels", refs.length, "Nomenclatures réelles"],
      ["list-tree", "Valeurs", refs.reduce((n, r) => n + r.valeurs_count, 0), "Éléments enregistrés"],
      ["circle-check", "Actifs", refs.filter((r) => statusLabel(r.statut) === "Actif").length, "Disponibles à la saisie"],
      ["history", "Traçabilité", "100 %", "Modifications auditées"],
    ].map((x) => `<article class="reference-kpi"><span><i data-lucide="${x[0]}"></i></span><div><small>${x[1]}</small><strong>${x[2]}</strong><em>${x[3]}</em></div></article>`).join("");
    icons();
  }
  async function loadValues() {
    if (!current) {
      values = [];
      renderValues();
      return;
    }
    values = await api.apiRequest(`/api/v1/referentiels/${current.id}/valeurs`);
    renderValues();
  }
  function renderValues() {
    $("#referenceGroup").textContent = current?.type_valeur || "Nomenclature";
    $("#referenceTitle").textContent = current?.libelle || "Aucun référentiel";
    $("#referenceDescription").textContent = current?.description || "Sélectionnez ou créez un référentiel.";
    const q = $("#referenceSearch").value.trim().toLowerCase();
    const status = $("#referenceStatus").value;
    const rows = values.filter((v) => {
      const active = statusLabel(v.statut) === "Actif";
      return (!q || `${v.code} ${v.libelle} ${v.description || ""}`.toLowerCase().includes(q))
        && (status === "all" || (status === "active" ? active : !active));
    });
    $("#referenceCount").textContent = `${rows.length} élément${rows.length > 1 ? "s" : ""}`;
    $("#referenceUsage").textContent = current ? `${current.valeurs_count} valeur(s) dans cette nomenclature` : "";
    $("#referenceResults").innerHTML = rows.length ? `<div class="table-responsive"><table class="table reference-table">
      <thead><tr><th>Code</th><th>Libellé</th><th>Description</th><th>Validité</th><th>Statut</th><th></th></tr></thead>
      <tbody>${rows.map((v) => `<tr>
        <td><code>${esc(v.code)}</code></td><td><strong>${esc(v.libelle)}</strong></td>
        <td>${esc(v.description || "—")}</td>
        <td>${esc(v.date_debut_validite || "—")} ${v.date_fin_validite ? `→ ${esc(v.date_fin_validite)}` : ""}</td>
        <td><span class="reference-status ${statusLabel(v.statut) === "Actif" ? "active" : "inactive"}">${statusLabel(v.statut)}</span></td>
        <td><button class="icon-button" data-edit="${v.id}" title="Modifier"><i data-lucide="pencil"></i></button></td>
      </tr>`).join("")}</tbody></table></div>` : `<div class="reference-empty"><i data-lucide="inbox"></i><strong>Aucune valeur</strong><span>Ajoutez le premier élément de cette nomenclature.</span></div>`;
    document.querySelectorAll("[data-edit]").forEach((b) => b.onclick = (event) => { event.preventDefault(); event.stopPropagation(); openValue(values.find((v) => v.id === b.dataset.edit)); });
    icons();
  }
  function openValue(value = null) {
    if (!current) return toast("Créez d’abord un référentiel.", true);
    editing = value;
    const form = $("#referenceForm");
    form.reset();
    $("#referenceModalTitle").textContent = value ? "Modifier l’élément" : "Nouvel élément";
    form.code.value = value?.code || "";
    if (!value) form.code.value = `${current.code}-${String(values.length + 1).padStart(3, "0")}`;
    form.label.value = value?.libelle || "";
    form.description.value = value?.description || "";
    form.order.value = value?.ordre_affichage || values.length + 1;
    form.active.checked = statusLabel(value?.statut) === "Actif";
    form.parent.innerHTML = `<option value="">Aucun parent</option>${values.filter((v) => v.id !== value?.id).map((v) => `<option value="${v.id}">${esc(v.libelle)}</option>`).join("")}`;
    form.parent.value = value?.parent_id || "";
    $("#referenceModal").hidden = false;
    icons();
  }
  function createRef() {
    const form = $("#referenceCategoryForm"); form.reset();
    const numbers = refs.map((x) => Number(String(x.code).match(/REF-(\d+)/)?.[1] || 0));
    form.code.value = `REF-${String(Math.max(0, ...numbers) + 1).padStart(3, "0")}`;
    $("#referenceCategoryModal").hidden = false; icons();
  }
  $("#referenceSearch").oninput = renderValues;
  $("#referenceStatus").onchange = renderValues;
  $("#newReference").onclick = () => current ? openValue() : createRef();
  $("#newReferenceCategory").onclick = createRef;
  $("#seedReferences").onclick = async () => {
    if (!confirm("Ajouter les référentiels types HAUQE absents ? Les éléments existants ne seront pas modifiés.")) return;
    try { await api.apiRequest("/api/v1/referentiels/initialiser-type", { method: "POST" }); toast("Référentiel type ajouté. Toutes les valeurs restent modifiables."); await loadRefs(false); } catch (error) { toast(error.message, true); }
  };
  document.querySelectorAll("[data-close-reference-category]").forEach((b) => b.onclick = () => { $("#referenceCategoryModal").hidden = true; });
  $("#referenceCategoryForm").onsubmit = async (event) => {
    event.preventDefault(); const f = event.currentTarget;
    try { await api.apiRequest("/api/v1/referentiels", { method: "POST", body: { code: f.code.value, libelle: f.label.value, description: f.description.value || null, type_valeur: "LISTE" } }); $("#referenceCategoryModal").hidden = true; toast("Référentiel créé."); await loadRefs(false); } catch (error) { toast(error.message, true); }
  };
  $("#closeReferenceModal").onclick = $("#cancelReferenceModal").onclick = () => { $("#referenceModal").hidden = true; };
  $("#referenceForm").onsubmit = async (event) => {
    event.preventDefault();
    const f = event.currentTarget;
    const body = {
      code: f.code.value, libelle: f.label.value, description: f.description.value || null,
      parent_id: f.parent.value || null, ordre_affichage: Number(f.order.value) || null,
      statut: f.active.checked ? "ACTIF" : "INACTIF",
    };
    try {
      if (editing) await api.apiRequest(`/api/v1/referentiels/${current.id}/valeurs/${editing.id}`, { method: "PATCH", body });
      else {
        delete body.statut;
        await api.apiRequest(`/api/v1/referentiels/${current.id}/valeurs`, { method: "POST", body });
      }
      $("#referenceModal").hidden = true;
      toast("Élément enregistré et journalisé.");
      await loadRefs();
    } catch (error) { toast(error.message, true); }
  };
  $("#viewDependencies").onclick = () => {
    $("#dependencyList").innerHTML = `<div class="dependency-item"><i data-lucide="shield-check"></i><div><strong>Contrôle serveur actif</strong><small>Les modifications sont tracées dans le journal d’audit.</small></div></div>`;
    $("#dependencyModal").hidden = false; icons();
  };
  $("#closeDependencies").onclick = $("#closeDependenciesFooter").onclick = () => { $("#dependencyModal").hidden = true; };
  $("#exportReferences").onclick = () => {
    const rows = [["Référentiel", "Code", "Libellé", "Statut"], ...values.map((v) => [current?.code, v.code, v.libelle, statusLabel(v.statut)])];
    const csv = rows.map((r) => r.map((v) => `"${String(v ?? "").replaceAll('"', '""')}"`).join(";")).join("\r\n");
    const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8" }));
    a.download = `referentiel-${current?.code || "liste"}.csv`; a.click(); URL.revokeObjectURL(a.href);
  };
  try { await loadRefs(false); } catch (error) { toast(error.message, true); }
})();
