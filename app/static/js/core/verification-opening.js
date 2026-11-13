export async function chooseVerificationOpening({ficheId,apiGet}) {
  const location=await apiGet(`/api/v1/missions/dossiers/${encodeURIComponent(ficheId)}/localisation`);
  const mission=await apiGet(`/api/v1/missions/${encodeURIComponent(location.mission_id)}`);
  return new Promise(resolve=>{
    const dialog=document.createElement('dialog');
    dialog.className='hauqe-dialog operational-form-dialog themed-business-dialog';
    dialog.innerHTML='<form><header class="operational-dialog-header"><div class="operational-dialog-title"><div><p class="eyebrow">Ouverture de la vérification</p><h2>Priorité et niveau de risque</h2></div></div><span data-close></span></header><div class="operational-dialog-body themed-business-body"><label class="operational-field"><span>Priorité initiale de la mission</span><input name="priority" readonly></label><label class="switch-line"><input name="confirmed" type="checkbox" required><span>Confirmez-vous cette priorité initiale du dossier ?</span></label><label class="operational-field"><span>Niveau de risque initial</span><select name="risk" required><option value="">Choisissez le niveau de risque</option><option value="R1">1 — R1 faible</option><option value="R2">2 — R2 modéré</option><option value="R3">3 — R3 significatif</option><option value="R4">4 — R4 élevé</option><option value="R5">5 — R5 critique</option></select></label></div><footer class="operational-dialog-footer"><span data-cancel></span><span data-submit></span></footer></form>';
    const form=dialog.querySelector('form');
    form.elements.priority.value=mission.priorite||'Non renseignée dans la mission';
    function addButton(slot,label,type,handler){
      const button=document.createElement('button');button.type=type;button.textContent=label;
      button.className='btn btn-outline-secondary app-btn';button.setAttribute('data-no-action-loader','true');
      if(handler)button.addEventListener('click',handler);dialog.querySelector(slot).append(button);
    }
    let selection=null;
    addButton('[data-close]','Fermer','button',()=>dialog.close());
    addButton('[data-cancel]','Annuler','button',()=>dialog.close());
    addButton('[data-submit]','Confirmer et ouvrir','submit');
    form.addEventListener('submit',event=>{
      event.preventDefault();
      selection={priorite:mission.priorite||null,niveau_risque:form.elements.risk.value};
      dialog.close();
    });
    dialog.addEventListener('close',()=>{dialog.remove();resolve(selection);},{once:true});
    document.body.append(dialog);dialog.showModal();
  });
}
