(() => {
  "use strict";
  const $ = (s) => document.querySelector(s);
  const choices = '<fieldset class="sharing-context"><legend>Informations à joindre au message</legend><label><input type="checkbox" value="ENTREPRISE" checked> Entreprise et identifiant</label><label><input type="checkbox" value="MISSION" checked> Mission de collecte</label><label><input type="checkbox" value="CERTIFICATIONS" checked> Certifications déclarées</label><label><input type="checkbox" value="DATES" checked> Dates de début et d’expiration</label><label><input type="checkbox" value="PRODUITS" checked> Produits / offres</label></fieldset>';
  const selected = (root) => [...root.querySelectorAll('.sharing-context input:checked')].map((input) => input.value);

  function inject() {
    const route = location.hash;
    if (route === "#/echanges-organismes") {
      const fields = $("#stage13Fields");
      if (fields && !fields.querySelector(".sharing-context")) fields.insertAdjacentHTML("beforeend", choices);
    }
    if (/^#\/verifications\//.test(route)) {
      const grid = $("#cAdd")?.previousElementSibling;
      if (grid && !grid.querySelector(".sharing-context")) grid.insertAdjacentHTML("beforeend", `<div class="form-field full">${choices}</div>`);
    }
    if (route === "#/veille") {
      const fields = $(".followup-dialog-fields");
      if (fields && !fields.querySelector(".sharing-context")) fields.insertAdjacentHTML("beforeend", `<label class="full">${choices}<small>Les informations disponibles du dossier de veille seront ajoutées au message.</small></label>`);
    }
  }

  document.addEventListener("submit", async (event) => {
    const form = event.target;
    if (form.id === "followupForm" && location.hash === "#/veille") {
      event.preventDefault(); event.stopImmediatePropagation();
      const detail = $("#watchCaseDetail");
      const data = new FormData(form), picked = selected(form), enterprise = detail?.querySelector("header h2")?.textContent?.trim(), certification = detail?.querySelector("header p")?.textContent?.trim();
      const context = [picked.includes("ENTREPRISE") && enterprise ? `Entreprise : ${enterprise}` : null, picked.includes("CERTIFICATIONS") && certification ? `Certification : ${certification}` : null].filter(Boolean);
      try {
        const api = await import("/static/js/core/api.js");
        const caseId = document.querySelector(".watch-case-row.active")?.dataset?.case;
        if (!caseId) throw new Error("Dossier de veille non sélectionné.");
        await api.apiPost(`/api/v1/veille/dossiers/${caseId}/relances`, { destinataire:data.get("followupRecipient"),adresse_email:data.get("followupEmail"),canal:data.get("followupChannel"),objet:data.get("followupSubject"),contenu:[data.get("followupMessage"),context.length?`\n\nInformations partagées :\n- ${context.join("\n- ")}`:""].join(""),date_envoi:data.get("followupSendDate")||null,date_echeance:data.get("followupDueDate")||null,statut:"EN_ATTENTE" });
        location.reload();
      } catch (error) { alert(error?.message || "Relance impossible."); }
      return;
    }
    if (form.id !== "stage13Form" || location.hash !== "#/echanges-organismes") return;
    event.preventDefault(); event.stopImmediatePropagation();
    const data = new FormData(form), dossierId = data.get("dossier_id");
    try {
      const api = await import("/static/js/core/api.js");
      await api.apiPost(`/api/v1/verifications/${dossierId}/confirmations`, { destinataire:data.get("destinataire"),canal:data.get("canal"),objet:data.get("objet"),contenu_demande:data.get("contenu_demande"),date_envoi:data.get("date_envoi")||null,date_echeance:data.get("date_echeance")||null,statut:"EN_ATTENTE",organisme_id:null,informations_partagees:selected(form) });
      location.reload();
    } catch (error) { alert(error?.message || "Envoi impossible."); }
  }, true);

  new MutationObserver(inject).observe(document.documentElement,{childList:true,subtree:true});
  window.addEventListener("hashchange", inject); inject();
})();
