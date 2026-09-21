(async function(){
  'use strict';
  const api=await import('/static/js/core/api.js');
  const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
  let user=null,zones=[],editing=null,statusTarget=null,timer=null;
  const f={search:'',type:'',status:''};
  const esc=v=>String(v??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#039;');
  const icons=()=>window.lucide?.createIcons({attrs:{'stroke-width':1.8}});
  const has=p=>user?.permissions?.includes(p);
  const normalizeZoneType=value=>{
    const normalized=String(value??'').trim().toUpperCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');
    const aliases={REGIONS:'REGION',PREFECTURES:'PREFECTURE',COMMUNES:'COMMUNE',LOCALITES:'LOCALITE'};
    return aliases[normalized]||normalized;
  };
  // Les lignes sont reconstituées après chaque filtre. Les actions sont donc
  // créées après le rendu depuis un emplacement neutre, avec leur écouteur
  // direct : patron validé dans Gestion des campagnes et Entreprises.
  const serializeZone=zone=>encodeURIComponent(JSON.stringify(zone));
  function zoneFromActionSlot(slot){try{return JSON.parse(decodeURIComponent(slot.dataset.zonePayload||''))}catch{return null}}
  function createZoneActionButton({label,iconName,danger=false,handler}){
    const button=document.createElement('button');
    button.type='button';
    button.className=`zone-action-button${danger?' zone-status-action':''}`;
    button.setAttribute('aria-label',label);
    button.setAttribute('title',label);
    button.setAttribute('data-no-action-loader','true');
    button.innerHTML=`<i data-lucide="${iconName}"></i>`;
    button.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();handler()});
    return button;
  }
  function hydrateZoneActionButtons(){
    document.querySelectorAll('[data-zone-action-slot]').forEach(slot=>{
      const zone=zoneFromActionSlot(slot);
      if(!zone?.id)return;
      slot.replaceChildren();
      if(slot.dataset.zoneActionSlot==='edit')slot.appendChild(createZoneActionButton({label:`Modifier ${zone.nom||'la zone'}`,iconName:'pencil',handler:()=>openForm(zone)}));
      if(slot.dataset.zoneActionSlot==='status')slot.appendChild(createZoneActionButton({label:`Modifier le statut de ${zone.nom||'la zone'}`,iconName:'power',danger:String(zone.statut||'ACTIF').toUpperCase()!=='INACTIF',handler:()=>openStatus(zone)}));
    });
  }
  function state(message,error=false){const n=$('#zonesApiState');n.hidden=false;n.className=`dashboard-api-state ${error?'error':''}`.trim();n.innerHTML=`<i data-lucide="${error?'triangle-alert':'info'}"></i><div><strong>${error?'Opération impossible':'Information'}</strong><span>${esc(message)}</span></div>`;icons()}
  async function run(task,options={}){return window.HAUQE_ACTION_LOADER?window.HAUQE_ACTION_LOADER.run(task,options):task()}
  function pathLabel(z){return z.chemin||[z.parent_nom,z.nom].filter(Boolean).join(' › ')||z.nom||'—'}
  function filtered(){const q=f.search.toLowerCase();return zones.filter(z=>(!f.type||z.type_zone===f.type)&&(!f.status||z.statut===f.status)&&(!q||[z.nom,z.code,z.chemin,z.parent_nom].filter(Boolean).join(' ').toLowerCase().includes(q)))}
  function summary(){const counts=t=>zones.filter(z=>z.type_zone===t&&z.statut!=='INACTIF').length;$('#zonesSummary').innerHTML=[['map','Zones',zones.length],['landmark','Régions',counts('REGION')],['map-pinned','Préfectures',counts('PREFECTURE')],['building-2','Communes',counts('COMMUNE')],['locate-fixed','Localités',counts('LOCALITE')]].map(([i,l,v])=>`<article><span><i data-lucide="${i}"></i></span><div><small>${l}</small><strong>${v}</strong></div></article>`).join('');icons()}
  function rows(){const data=filtered();$('#zonesEmpty').hidden=!!data.length;$('#zoneRows').innerHTML=data.map(z=>{const payload=esc(serializeZone(z));return `<tr><td><div class="zone-name"><strong>${esc(z.nom)}</strong><small>${esc(pathLabel(z))}</small></div></td><td><span class="zone-type">${esc(z.type_zone||'—')}</span></td><td><code>${esc(z.code||'—')}</code></td><td>${esc(z.parent_nom||'Racine')}</td><td>${z.latitude!=null&&z.longitude!=null?`${esc(z.latitude)}, ${esc(z.longitude)}`:'—'}</td><td><span class="user-status ${String(z.statut||'ACTIF').toLowerCase()}"><i></i>${esc(z.statut||'ACTIF')}</span></td><td><div class="zone-actions">${has('REFERENTIELS.MODIFIER')?`<span data-zone-action-slot="edit" data-zone-payload="${payload}"></span>`:''}${has('REFERENTIELS.DESACTIVER')?`<span data-zone-action-slot="status" data-zone-payload="${payload}"></span>`:''}</div></td></tr>`}).join('');hydrateZoneActionButtons();icons()}
  function parentOptions(current=null){$('#zoneFormParent').innerHTML='<option value="">Aucune — niveau racine</option>'+zones.filter(z=>z.id!==current?.id&&z.statut!=='INACTIF').map(z=>`<option value="${z.id}">${esc(pathLabel(z))} · ${esc(z.type_zone)}</option>`).join('')}
  function openForm(z=null){editing=z;parentOptions(z);$('#zoneDialogTitle').textContent=z?'Modifier la zone':'Nouvelle zone';$('#zoneFormType').value=normalizeZoneType(z?.type_zone);$('#zoneFormCode').value=z?.code||'';$('#zoneFormName').value=z?.nom||'';$('#zoneFormParent').value=z?.parent_id||'';$('#zoneFormLatitude').value=z?.latitude??'';$('#zoneFormLongitude').value=z?.longitude??'';$('#zoneFormStatus').value=String(z?.statut||'ACTIF').toUpperCase();$('#zoneDialog').showModal();icons()}
  function payload(){const num=(id,min,max)=>{const raw=$(id).value.trim();if(raw==='')return null;const value=Number(raw);if(!Number.isFinite(value)||value<min||value>max)throw new Error(`${id.includes('Latitude')?'La latitude':'La longitude'} doit être comprise entre ${min} et ${max}.`);return value};return{type_zone:normalizeZoneType($('#zoneFormType').value),code:$('#zoneFormCode').value.trim()||null,nom:$('#zoneFormName').value.trim(),parent_id:$('#zoneFormParent').value||null,latitude:num('#zoneFormLatitude',-90,90),longitude:num('#zoneFormLongitude',-180,180),statut:$('#zoneFormStatus').value}}
  async function save(ev){ev.preventDefault();if(!ev.currentTarget.reportValidity())return;try{const body=payload();if(!body.type_zone||!body.nom)throw new Error('Le nom et le type de zone sont obligatoires.');await run(()=>editing?api.apiPatch(`/api/v1/zones-administratives/${editing.id}`,body):api.apiPost('/api/v1/zones-administratives',body),{button:ev.submitter,title:'Zone administrative',message:editing?'Mise à jour de la zone':'Création de la zone',detail:'La hiérarchie et les doublons sont contrôlés côté serveur.'});const wasEditing=Boolean(editing);$('#zoneDialog').close();await load();state(wasEditing?'Zone mise à jour.':'Zone créée.')}catch(e){const detail=Array.isArray(e?.detail)?e.detail.map(item=>item?.msg).filter(Boolean).join(' · '):'';state(detail||e?.message||'Enregistrement impossible.',true)}}
  function syncStatusDialog(){
    if(!statusTarget)return;
    const next=$('#zoneNewStatus').value;
    const activating=next==='ACTIF';
    $('#zoneStatusDialog').classList.toggle('is-activating',activating);
    $('#zoneStatusDialog').classList.toggle('is-deactivating',!activating);
    $('#zoneStatusExplanation').textContent=activating
      ? 'La zone redeviendra disponible dans les formulaires, affectations et filtres.'
      : 'La zone sera masquée des nouvelles sélections, sans supprimer son historique ni ses liaisons.';
    $('#applyZoneStatus span').textContent=activating?'Réactiver la zone':'Désactiver la zone';
  }
  function openStatus(z){statusTarget=z;$('#zoneStatusTitle').textContent='Modifier le statut';$('#zoneStatusZoneName').textContent=pathLabel(z);$('#zoneNewStatus').value=z.statut==='INACTIF'?'ACTIF':'INACTIF';$('#zoneStatusReason').value='';syncStatusDialog();$('#zoneStatusDialog').showModal();icons()}
  async function saveStatus(ev){ev.preventDefault();if(!statusTarget)return;try{await run(()=>api.apiPatch(`/api/v1/zones-administratives/${statusTarget.id}/status`,{statut:$('#zoneNewStatus').value,motif:$('#zoneStatusReason').value.trim()||null}),{button:ev.submitter,title:'Zone administrative',message:'Changement du statut'});$('#zoneStatusDialog').close();await load();state('Statut de la zone mis à jour.')}catch(e){state(e?.message||'Changement impossible.',true)}}
  async function loadAllZones(){
    const pageSize=500;
    let offset=0;
    const result=[];

    while(true){
      const page=await api.apiGet(`/api/v1/zones-administratives?limit=${pageSize}&offset=${offset}`);
      const items=Array.isArray(page)?page:Array.isArray(page?.items)?page.items:[];
      const total=Number(page?.total??items.length);

      result.push(...items);

      if(!items.length||result.length>=total||items.length<pageSize)break;
      offset+=items.length;
    }

    return result;
  }
  async function load(){zones=await loadAllZones();summary();rows()}
  function bindStaticButton(selector,handler){const button=$(selector);button.setAttribute('data-no-action-loader','true');button.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();handler(event)})}
  function bind(){
    $('#zoneForm').addEventListener('submit',save);$('#zoneStatusForm').addEventListener('submit',saveStatus);$('#zoneNewStatus').addEventListener('change',syncStatusDialog);
    $$('[data-dialog-close]').forEach(button=>{button.setAttribute('data-no-action-loader','true');button.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();button.closest('dialog')?.close()})});
    bindStaticButton('#newZone',()=>openForm());
    bindStaticButton('#refreshZones',event=>run(load,{button:event.currentTarget,title:'Zones administratives',message:'Actualisation du référentiel'}));
    bindStaticButton('#resetZoneFilters',()=>{f.search=f.type=f.status='';$('#zoneSearch').value='';$('#zoneType').value='';$('#zoneStatus').value='';rows()});
    $('#zoneSearch').addEventListener('input',e=>{clearTimeout(timer);timer=setTimeout(()=>{f.search=e.target.value.trim();rows()},180)});
    $('#zoneType').addEventListener('change',e=>{f.type=e.target.value;rows()});$('#zoneStatus').addEventListener('change',e=>{f.status=e.target.value;rows()});
  }
  try{bind();[user,zones]=await Promise.all([api.apiGet('/api/v1/me'),loadAllZones()]);$('#newZone').hidden=!has('REFERENTIELS.CREER');summary();rows()}catch(e){state(e?.message||'Référentiel géographique indisponible.',true)}icons();
})();
