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
    // La page Veille possède son propre gestionnaire de soumission : lui seul
    // connaît les champs de la relance et le dossier sélectionné. Ne jamais
    // intercepter ce formulaire ici, sinon un ancien mapping de noms peut
    // vider les valeurs avant l'appel API.
    if (form.id === "followupForm" && location.hash === "#/veille") return;
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
