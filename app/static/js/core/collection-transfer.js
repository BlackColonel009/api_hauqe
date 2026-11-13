export function missionStateLabel(value) {
  const state=String(value||'').toUpperCase();
  if(state==='ARCHIVEE')return 'Archivée — désarchivage requis';
  if(state==='ANNULEE')return 'Annulée';
  const label={PLANIFIEE:'Planifiée',EN_COURS:'En cours',TERMINEE:'Terminée',CLOTUREE:'Clôturée',ACTIVE:'Active',ACTIF:'Active'}[state]||value||'Statut non renseigné';
  return `Non archivée — ${label}`;
}
export function installCollectionTransfer({apiGet, apiPost, user, refresh}) {
  if (!(user.roles || []).some(role => ['ADMIN_HAUQE','POINT_FOCAL_BNEC'].includes(role))) return;
  const page = document.querySelector('.campaign-management-panel')?.closest('.page-content');
  if (!page) return;
  const dialog = document.createElement('dialog');
  dialog.className = 'hauqe-dialog operational-form-dialog themed-business-dialog';
  dialog.id = 'collectionTransferDialog';
  dialog.innerHTML = `<form><header class="operational-dialog-header"><div class="operational-dialog-title"><div><p class="eyebrow">Campagnes et missions</p><h2>Déplacer les collectes</h2><small>Le dossier conserve toutes ses révisions et son parcours.</small></div></div><span data-transfer-close></span></header><div class="operational-dialog-body themed-business-body"><label class="operational-field"><span>Mission source</span><select name="source" required></select></label><section><strong>Dossiers à déplacer</strong><div data-transfer-items></div></section><label class="operational-field"><span>Mission destination (toutes campagnes)</span><select name="destination" required></select></label><label class="operational-field"><span>Motif obligatoire</span><textarea name="motif" minlength="3" maxlength="2000" required></textarea></label><p>Les responsables doivent être affectés à la destination. Aucune fusion de dossiers ni nouvelle validation n’est effectuée.</p><p data-transfer-error role="alert"></p></div><footer class="operational-dialog-footer"><span data-transfer-archive></span><span data-transfer-submit></span></footer></form>`;
  page.append(dialog);
  const form = dialog.querySelector('form'), source = form.elements.source, destination = form.elements.destination;
  const error = dialog.querySelector('[data-transfer-error]');
  let loading = false, sequence = 0;
  const missionStatuses = new Map();
  const stateNotice=document.createElement('p');stateNotice.setAttribute('role','status');
  source.closest('label').after(stateNotice);
  function updateMissionState() {
    stateNotice.textContent=source.value?`État de la mission source : ${missionStateLabel(missionStatuses.get(source.value))}`:'';
    stateNotice.style.color=missionStatuses.get(source.value)==='ARCHIVEE'?'#b4433e':'#287e5f';
    for(const select of [source,destination])for(const option of [...select.options]){
      if(!option.value)continue;
      const state=missionStatuses.get(option.value);
      if(select===destination && ['ARCHIVEE','ANNULEE'].includes(state)){option.remove();continue;}
      option.textContent=`${option.dataset.missionLabel} — ${missionStateLabel(state)}`;
    }
  }
  function button(slot, label, handler, type='button') {
    const node = document.createElement('button'); node.type=type;
    node.className='btn btn-outline-secondary app-btn'; node.textContent=label;
    node.setAttribute('data-no-action-loader','true');
    if (handler) node.addEventListener('click',handler);
    slot.replaceChildren(node); return node;
  }
  button(dialog.querySelector('[data-transfer-close]'),'Fermer',()=>dialog.close());
  const submit=button(dialog.querySelector('[data-transfer-submit]'),'Confirmer le déplacement',null,'submit');
  const archive=button(dialog.querySelector('[data-transfer-archive]'),'Archiver la mission vide',async()=>{
    if (loading || !source.value) return;
    const motif=form.elements.motif.value.trim();
    if(motif.length<3){error.textContent='Précisez le motif.';return;}
    const archived=missionStatuses.get(source.value)==='ARCHIVEE';
    if(!window.confirm(archived ? 'Désarchiver cette mission ? Elle reprendra au statut Planifiée.' : 'Archiver cette mission vide ? Les affectations et l’historique seront conservés.'))return;
    await perform(async()=>{
      const result=await apiPost(`/api/v1/missions/${source.value}/${archived?'desarchiver':'archiver'}`,{motif});
      missionStatuses.set(source.value,archived?'PLANIFIEE':'ARCHIVEE');
      updateMissionState();
      if(archived && ![...destination.options].some(option=>option.value===source.value)){
        const option=new Option(source.selectedOptions[0].textContent,source.value);
        option.dataset.missionLabel=source.selectedOptions[0].dataset.missionLabel;
        destination.add(option);
      }
      return result;
    },archived?'Mission désarchivée.':'Mission archivée.');
  });
  async function perform(task, success){
    const previousSubmit=submit.disabled,previousArchive=archive.disabled;
    loading=true;submit.disabled=true;archive.disabled=true;error.textContent='';
    try{const result=await task();error.textContent=success+(result?.revisions_deplacees?` ${result.revisions_deplacees} fiche(s)/révision(s) déplacée(s).`:'');await refresh();await loadItems();}
    catch(e){error.textContent=e.message||'Opération impossible.';submit.disabled=previousSubmit;archive.disabled=previousArchive;}
    finally{loading=false;}
  }
  async function loadItems(){
    updateMissionState();
    const ticket=++sequence;archive.disabled=true;submit.disabled=true;
    const container=dialog.querySelector('[data-transfer-items]');container.textContent='Chargement…';
    try{
      if(!source.value){container.textContent='Choisissez une mission.';return;}
      const archived=missionStatuses.get(source.value)==='ARCHIVEE';
      archive.textContent=archived?'Désarchiver la mission':'Archiver la mission vide';
      const payload=await apiGet(`/api/v1/missions/${source.value}/dossiers-deplacement`);
      if(ticket!==sequence)return;
      container.replaceChildren();
      for(const item of payload.items){
        const label=document.createElement('label');label.style.cssText='display:flex;gap:10px;padding:8px;align-items:center';
        const check=document.createElement('input');check.type='checkbox';check.value=item.fiche_id;check.dataset.transferFiche='true';
        const text=document.createElement('span');text.textContent=`${item.entreprise} — ${item.statut || 'Non renseigné'} — ${item.revisions} révision(s)`;
        label.append(check,text);container.append(label);
      }
      if(!payload.total_fiches)container.textContent='Mission vide : archivage possible.';
      if(archived)container.textContent='Mission archivée : désarchivez avant toute autre action.';
      archive.disabled=archived?false:Boolean(payload.total_fiches);submit.disabled=archived||!payload.total_fiches;
    }catch(e){if(ticket===sequence){container.textContent='';error.textContent=e.message;}}
  }
  source.addEventListener('change',()=>{error.textContent='';loadItems();});
  form.addEventListener('submit',async event=>{
    event.preventDefault();if(loading)return;
    const fiche_ids=[...dialog.querySelectorAll('[data-transfer-fiche]:checked')].map(input=>input.value);
    if(!fiche_ids.length){error.textContent='Sélectionnez au moins un dossier.';return;}
    if(source.value===destination.value){error.textContent='Choisissez une autre mission.';return;}
    const sourceLabel=source.selectedOptions[0].textContent,destinationLabel=destination.selectedOptions[0].textContent;
    if(!window.confirm(`Déplacer ${fiche_ids.length} dossier(s) avec toutes leurs révisions de « ${sourceLabel} » vers « ${destinationLabel} » ?`))return;
    await perform(()=>apiPost(`/api/v1/missions/${source.value}/deplacer-collectes`,{destination_id:destination.value,fiche_ids,motif:form.elements.motif.value.trim()}),'Déplacement effectué.');
  });
  const opener=document.createElement('button');opener.type='button';opener.className='btn btn-outline-secondary app-btn';opener.textContent='Déplacer / archiver les missions';opener.setAttribute('data-no-action-loader','true');
  opener.addEventListener('click',async()=>{
    dialog.showModal();error.textContent='';source.replaceChildren();destination.replaceChildren();archive.disabled=true;submit.disabled=true;
    try{
      const campaigns=new Map();let missions=[];
      for(let offset=0;;offset+=200){const result=await apiGet(`/api/v1/campagnes?limit=200&offset=${offset}`);for(const c of result.items||[])campaigns.set(c.id,c.nom||c.code);if((result.items||[]).length<200)break;}
      for(let offset=0;;offset+=200){const result=await apiGet(`/api/v1/missions?limit=200&offset=${offset}`);missions.push(...result.items||[]);if((result.items||[]).length<200)break;}
      missionStatuses.clear();for(const mission of missions)missionStatuses.set(String(mission.id),(mission.statut||'').toUpperCase());
      for(const select of [source,destination]){
        select.add(new Option('Choisissez une mission',''));
        for(const mission of missions){
          if(select===destination && ['ARCHIVEE','ANNULEE'].includes((mission.statut||'').toUpperCase()))continue;
          const label=`${campaigns.get(mission.campagne_id)||'Campagne'} — ${mission.code||mission.objet||'Mission'}`;
          const option=new Option(`${label} — ${missionStateLabel(mission.statut)}`,mission.id);
          option.dataset.missionLabel=label;
          select.add(option);
        }
      }
      await loadItems();
    }catch(e){error.textContent=e.message;}
  });
  page.querySelector('.heading-actions').append(opener);
}
