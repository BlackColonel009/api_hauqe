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
  function state(message,error=false){const n=$('#zonesApiState');n.hidden=false;n.className=`dashboard-api-state ${error?'error':''}`.trim();n.innerHTML=`<i data-lucide="${error?'triangle-alert':'info'}"></i><div><strong>${error?'Opération impossible':'Information'}</strong><span>${esc(message)}</span></div>`;icons()}
  async function run(task,options={}){return window.HAUQE_ACTION_LOADER?window.HAUQE_ACTION_LOADER.run(task,options):task()}
  function pathLabel(z){return z.chemin||[z.parent_nom,z.nom].filter(Boolean).join(' › ')||z.nom||'—'}
  function filtered(){const q=f.search.toLowerCase();return zones.filter(z=>(!f.type||z.type_zone===f.type)&&(!f.status||z.statut===f.status)&&(!q||[z.nom,z.code,z.chemin,z.parent_nom].filter(Boolean).join(' ').toLowerCase().includes(q)))}
  function summary(){const counts=t=>zones.filter(z=>z.type_zone===t&&z.statut!=='INACTIF').length;$('#zonesSummary').innerHTML=[['map','Zones',zones.length],['landmark','Régions',counts('REGION')],['map-pinned','Préfectures',counts('PREFECTURE')],['building-2','Communes',counts('COMMUNE')],['locate-fixed','Localités',counts('LOCALITE')]].map(([i,l,v])=>`<article><span><i data-lucide="${i}"></i></span><div><small>${l}</small><strong>${v}</strong></div></article>`).join('');icons()}
  function rows(){const data=filtered();$('#zonesEmpty').hidden=!!data.length;$('#zoneRows').innerHTML=data.map(z=>`<tr><td><div class="zone-name"><strong>${esc(z.nom)}</strong><small>${esc(pathLabel(z))}</small></div></td><td><span class="zone-type">${esc(z.type_zone||'—')}</span></td><td><code>${esc(z.code||'—')}</code></td><td>${esc(z.parent_nom||'Racine')}</td><td>${z.latitude!=null&&z.longitude!=null?`${esc(z.latitude)}, ${esc(z.longitude)}`:'—'}</td><td><span class="user-status ${String(z.statut||'ACTIF').toLowerCase()}"><i></i>${esc(z.statut||'ACTIF')}</span></td><td><div class="zone-actions">${has('REFERENTIELS.MODIFIER')?`<button type="button" data-edit="${esc(z.id)}" title="Modifier"><i data-lucide="pencil"></i></button>`:''}${has('REFERENTIELS.DESACTIVER')?`<button type="button" data-status="${esc(z.id)}" title="Changer le statut"><i data-lucide="power"></i></button>`:''}</div></td></tr>`).join('');icons()}
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
  function bind(){$('#zoneForm').onsubmit=save;$('#zoneStatusForm').onsubmit=saveStatus;$('#zoneNewStatus').onchange=syncStatusDialog;$('#zoneRows').onclick=ev=>{const button=ev.target.closest('button[data-edit],button[data-status]');if(!button)return;ev.preventDefault();ev.stopPropagation();const isEdit=button.hasAttribute('data-edit');const id=isEdit?button.dataset.edit:button.dataset.status;const zone=zones.find(item=>String(item.id)===String(id));if(!zone){state('Zone introuvable dans la liste courante.',true);return}if(isEdit)openForm(zone);else openStatus(zone)};$$('[data-dialog-close]').forEach(button=>button.onclick=()=>button.closest('dialog')?.close());$('#newZone').onclick=()=>openForm();$('#refreshZones').onclick=ev=>run(load,{button:ev.currentTarget,title:'Zones administratives',message:'Actualisation du référentiel'});$('#zoneSearch').oninput=e=>{clearTimeout(timer);timer=setTimeout(()=>{f.search=e.target.value.trim();rows()},180)};$('#zoneType').onchange=e=>{f.type=e.target.value;rows()};$('#zoneStatus').onchange=e=>{f.status=e.target.value;rows()};$('#resetZoneFilters').onclick=()=>{f.search=f.type=f.status='';$('#zoneSearch').value='';$('#zoneType').value='';$('#zoneStatus').value='';rows()}}
  try{bind();[user,zones]=await Promise.all([api.apiGet('/api/v1/me'),loadAllZones()]);$('#newZone').hidden=!has('REFERENTIELS.CREER');summary();rows()}catch(e){state(e?.message||'Référentiel géographique indisponible.',true)}icons();
})();
