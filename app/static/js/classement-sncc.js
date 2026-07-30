(async function(){
"use strict";
const api=await import('/static/js/core/api.js');
const ui=await import('/static/js/scoring-workspace.js');
const $=s=>document.querySelector(s),PAGE=25;
let user=null,selectedCert=null,selectedSncc=null,mode='create',offset=0,total=0,timer=null,histories=new Map();
const f={search:'',classe:'',statut_administratif:'',niveau_risque:''};
document.querySelector('.page-heading .heading-actions')?.insertAdjacentHTML('afterbegin','<a class="btn btn-outline-secondary app-btn" href="/static/docs/guide-sncc-hauqe.pdf" target="_blank" rel="noopener"><i data-lucide="book-open-check"></i>Guide</a>');
let hist={classes:[],admins:[],risks:[]};
function fill(node,label,vals){node.innerHTML=`<option value="">${ui.escapeHtml(label)}</option>`+(vals||[]).map(v=>`<option value="${ui.escapeHtml(v)}">${ui.escapeHtml(v)}</option>`).join('');node.disabled=false}
function kpis(s){const cards=[["blue","landmark","Classements",s?.total??0,"Historique complet"],["green","badge-check","Courants",s?.current??0,"Sans date de fin"],["gray","archive","Clôturés",s?.closed??0,"Périodes terminées"],["purple","award","Certifications classées",s?.certifications_ranked??0,"Au moins un classement"]];$('#snccKpis').innerHTML=cards.map(([t,i,l,v,d])=>`<article class="score-stat panel ${t}"><span class="${t}"><i data-lucide="${i}"></i></span><div><small>${ui.escapeHtml(l)}</small><strong>${ui.escapeHtml(v)}</strong><em>${ui.escapeHtml(d)}</em></div></article>`).join('');ui.refreshIcons()}
function qs(){const p=new URLSearchParams({limit:100,offset:0});Object.entries(f).forEach(([k,v])=>v&&p.set(k,v));return p}
function latestOnly(payload){histories=new Map();for(const x of payload?.items||[]){const key=String(x.certification_id||x.certification_identifier);if(!histories.has(key))histories.set(key,[]);histories.get(key).push(x)}return {...payload,total:histories.size,items:[...histories.values()].map(v=>v[0]),summary:{...(payload?.summary||{}),total:histories.size}}}
function bindHistory(){
  [...$('#snccRows').rows].forEach(row=>{
    const key=String(row.dataset.historyKey||'');
    const values=histories.get(key)||[];
    row.classList.add('score-history-row');
    row.tabIndex=0;
    row.setAttribute('role','button');
    row.title='Cliquer pour consulter les classements précédents';
    const openHistory=ev=>{
      if(ev.target.closest('button'))return;
      if(!values.length)return;
      const current=values[0]||{};
      $('#snccHistoryTitle').textContent=current.certification_identifier||'Détail du classement SNCC';
      $('#snccHistoryBody').innerHTML=`
        <section class="sncc-record-overview">
          <div class="sncc-record-class"><small>Classe actuelle</small><strong>${ui.escapeHtml(current.class_code||'—')}</strong></div>
          <div class="sncc-record-summary"><small>Certification</small><strong>${ui.escapeHtml(current.certification_identifier||'—')}</strong><span><i data-lucide="building-2"></i>${ui.escapeHtml(current.enterprise_name||'Entreprise non renseignée')}</span></div>
          <span class="sncc-record-status"><i data-lucide="${current.ended_on?'archive':'activity'}"></i>${current.ended_on?'Clôturé':'Classement courant'}</span>
        </section>
        <div class="sncc-record-layout">
          <main class="sncc-record-main">
            <div class="sncc-record-section-head"><span><i data-lucide="history"></i></span><div><small>Traçabilité</small><h3>Évolution des classements</h3></div><b>${values.length}</b></div>
            <div class="sncc-record-timeline">${values.map((x,index)=>`
              <article class="${index===0?'current':''}">
                <span class="sncc-timeline-marker">${values.length-index}</span>
                <div><small>${index===0?'Situation la plus récente':'Classement antérieur'}</small><strong>${ui.escapeHtml(x.class_code||'—')} · ${ui.escapeHtml(x.administrative_status||'—')}</strong><p>Risque : ${ui.escapeHtml(x.risk_level||'—')} · Effet : ${ui.escapeHtml(ui.formatDate(x.effective_on))}${x.ended_on?` · Fin : ${ui.escapeHtml(ui.formatDate(x.ended_on))}`:' · Période active'}</p></div>
              </article>`).join('')}</div>
          </main>
          <aside class="sncc-record-aside">
            <h3>Repères</h3>
            <div><span><i data-lucide="shield-check"></i></span><section><small>Statut administratif</small><strong>${ui.escapeHtml(current.administrative_status||'—')}</strong></section></div>
            <div><span><i data-lucide="triangle-alert"></i></span><section><small>Niveau de risque</small><strong>${ui.escapeHtml(current.risk_level||'—')}</strong></section></div>
            <div><span><i data-lucide="user-check"></i></span><section><small>Validateur</small><strong>${ui.escapeHtml(current.validator_name||'Non renseigné')}</strong></section></div>
            <div><span><i data-lucide="calendar-days"></i></span><section><small>Date d’effet</small><strong>${ui.escapeHtml(ui.formatDate(current.effective_on))}</strong></section></div>
          </aside>
        </div>`;
      $('#snccHistoryDialog').showModal();
      ui.refreshIcons();
    };
    row.onclick=openHistory;
    row.onkeydown=ev=>{
      if(ev.key!=='Enter'&&ev.key!==' ')return;
      ev.preventDefault();
      openHistory(ev);
    };
  });
}
function rows(payload){total=Number(payload?.total||0);const items=payload?.items||[];kpis(payload?.summary||{});$('#snccCount').textContent=`${total} classement${total>1?'s':''}`;const a=total?offset+1:0,b=Math.min(offset+items.length,total);$('#snccPagination').textContent=total?`${a}–${b} sur ${total}`:'0 résultat';$('#snccPrev').disabled=offset<=0;$('#snccNext').disabled=offset+PAGE>=total;$('#snccEmpty').hidden=!!items.length;$('#snccRows').innerHTML=items.map(x=>`<tr data-history-key="${ui.escapeHtml(String(x.certification_id||x.certification_identifier||''))}"><td><div class="cert-stack"><strong>${ui.escapeHtml(x.certification_identifier)}</strong><small>${ui.escapeHtml(x.standard_code||x.standard_name||'Norme')} · ${ui.escapeHtml(x.organization_name||'Organisme')}</small></div></td><td><div class="cert-stack"><strong>${ui.escapeHtml(x.enterprise_name||'Entreprise')}</strong><small>${ui.escapeHtml(x.enterprise_identifier||'—')}</small></div></td><td><span class="sncc-class-badge">${ui.escapeHtml(x.class_code||'—')}</span></td><td>${ui.escapeHtml(x.administrative_status||'—')}</td><td><span class="sncc-risk-badge">${ui.escapeHtml(x.risk_level||'—')}</span></td><td><div class="cert-stack"><strong>${ui.escapeHtml(ui.formatDate(x.effective_on))}</strong><small>${x.ended_on?`→ ${ui.escapeHtml(ui.formatDate(x.ended_on))}`:'Classement courant'}</small></div></td><td>${ui.escapeHtml(x.validator_name||'—')}</td><td>${!x.ended_on&&ui.hasPermission(user,'SNCC.RECLASSER')?`<button class="btn btn-outline-secondary app-btn" type="button" data-close="${ui.escapeHtml(x.sncc_id)}">Clôturer</button>`:''}</td></tr>`).join('');$('#snccRows').querySelectorAll('[data-close]').forEach(b=>b.onclick=()=>{selectedSncc=b.dataset.close;$('#snccCloseDate').value='';$('#snccCloseMotif').value='';$('#snccCloseDialog').showModal();ui.refreshIcons()});ui.refreshIcons()}
async function loadResults(){try{const result=await ui.runAction(()=>api.apiGet(`/api/v1/scoring/workspace/sncc-results?${qs()}`),{title:'Classement SNCC',message:'Chargement des classements',detail:'Lecture du classement courant et de l’historique.',minVisibleMs:250});rows(latestOnly(result));bindHistory()}catch(e){ui.showState('#snccApiState',e?.message||'Chargement impossible.',{error:true})}}
function action(x){if(!x.eligible){return `<span class="sncc-ineligible" title="${ui.escapeHtml((x.eligibility_reasons||[]).join(' · '))}"><i data-lucide="clock-3"></i>En attente INFC</span>`}if(x.current_sncc_id){return ui.hasPermission(user,'SNCC.RECLASSER')?`<button class="btn btn-primary app-btn" type="button" data-reclass="${ui.escapeHtml(x.certification_id)}"><i data-lucide="refresh-cw"></i>Reclasser</button>`:'<span class="text-muted small">Classement courant</span>'}return ui.hasPermission(user,'SNCC.CLASSER')?`<button class="btn btn-primary app-btn" type="button" data-create="${ui.escapeHtml(x.certification_id)}"><i data-lucide="badge-plus"></i>Classer</button>`:'<span class="text-muted small">Non classée</span>'}
function certs(payload){const items=payload?.items||[],c=$('#snccCertificationList');if(!items.length){c.innerHTML='<div class="priority-empty">Aucune certification trouvée.</div>';return}c.innerHTML=items.map(x=>`<article class="scoring-entity-row"><span><i data-lucide="award"></i></span><div><strong>${ui.escapeHtml(x.certification_identifier)}</strong><small>${ui.escapeHtml(x.enterprise_name||'Entreprise')} · ${ui.escapeHtml(x.standard_code||x.standard_name||'Norme')}</small></div><div class="scoring-latest-result">${x.current_sncc_id?`<strong>${ui.escapeHtml(x.current_sncc_class||'—')} · ${ui.escapeHtml(x.current_admin_status||'—')} · ${ui.escapeHtml(x.current_risk_level||'—')}</strong><small>Effet ${ui.escapeHtml(ui.formatDate(x.current_effective_date))}</small>`:'<strong>Aucun classement courant</strong><small>Disponible pour un premier classement</small>'}</div>${action(x)}</article>`).join('');c.querySelectorAll('[data-create]').forEach(b=>b.onclick=()=>open(items.find(x=>String(x.certification_id)===String(b.dataset.create)),'create'));c.querySelectorAll('[data-reclass]').forEach(b=>b.onclick=()=>open(items.find(x=>String(x.certification_id)===String(b.dataset.reclass)),'reclassify'));ui.refreshIcons()}
async function loadCerts(){try{const p=new URLSearchParams({limit:'70'});if(f.search)p.set('search',f.search);certs(await api.apiGet(`/api/v1/scoring/workspace/sncc-certifications?${p}`))}catch(e){$('#snccCertificationList').innerHTML=`<div class="priority-empty">${ui.escapeHtml(e?.message||'Chargement impossible.')}</div>`}}
function open(x,m){selectedCert=x;mode=m;$('#snccDialogTitle').textContent=`${x.certification_identifier} · ${x.enterprise_name||''}`;$('#snccDialogClass').value=m==='reclassify'?x.current_sncc_class||'':'';$('#snccDialogAdmin').value=m==='reclassify'?x.current_admin_status||'':'';$('#snccDialogRisk').value=m==='reclassify'?x.current_risk_level||'':'';$('#snccDialogDate').value='';$('#snccDialogJustification').value='';$('#snccDialogMotif').value='';$('#snccMotifField').hidden=m!=='reclassify';$('#snccDialogMotif').required=m==='reclassify';$('#snccSaveButton').innerHTML=m==='reclassify'?'<i data-lucide="refresh-cw"></i>Reclasser':'<i data-lucide="badge-check"></i>Classer';$('#snccDialog').showModal();ui.refreshIcons()}
function payload(){const p={classe:$('#snccDialogClass').value.trim(),statut_administratif:$('#snccDialogAdmin').value.trim(),niveau_risque:$('#snccDialogRisk').value.trim(),justification:$('#snccDialogJustification').value.trim(),date_effet:$('#snccDialogDate').value};if(!p.classe||!p.statut_administratif||!p.niveau_risque||!p.justification||!p.date_effet)throw new Error('Classe, statut administratif, risque, date d’effet et justification sont obligatoires.');if(mode==='reclassify'){p.motif_reclassement=$('#snccDialogMotif').value.trim();if(!p.motif_reclassement)throw new Error('Le motif de reclassement est obligatoire.')}return p}
async function save(ev){ev.preventDefault();if(!selectedCert)return;try{const endpoint=mode==='reclassify'?`/api/v1/certifications/${selectedCert.certification_id}/sncc/reclassify`:`/api/v1/certifications/${selectedCert.certification_id}/sncc`;await ui.runAction(async()=>{await api.apiPost(endpoint,payload());$('#snccDialog').close();await Promise.all([loadResults(),loadCerts()]);ui.showState('#snccApiState',mode==='reclassify'?'Reclassement SNCC enregistré.':'Premier classement SNCC enregistré.')},{button:$('#snccSaveButton'),title:'Classement SNCC',message:mode==='reclassify'?'Création du nouveau classement':'Création du classement',detail:'La justification et l’historique sont conservés.'})}catch(e){ui.showState('#snccApiState',e?.message||'Enregistrement impossible.',{error:true})}}
async function close(ev){ev.preventDefault();if(!selectedSncc)return;const date_fin=$('#snccCloseDate').value,motif=$('#snccCloseMotif').value.trim();if(!date_fin||!motif){ui.showState('#snccApiState','Date de fin et motif sont obligatoires.',{error:true});return}try{await ui.runAction(async()=>{await api.apiPost(`/api/v1/sncc/${selectedSncc}/close`,{date_fin,motif});$('#snccCloseDialog').close();selectedSncc=null;await Promise.all([loadResults(),loadCerts()]);ui.showState('#snccApiState','Classement SNCC clôturé.')},{title:'Clôture SNCC',message:'Clôture du classement courant',detail:'Le classement reste historisé.'})}catch(e){ui.showState('#snccApiState',e?.message||'Clôture impossible.',{error:true})}}
async function filters(){try{const x=await api.apiGet('/api/v1/scoring/workspace/sncc-filters');hist={classes:x.classes||[],admins:x.admin_statuses||[],risks:x.risk_levels||[]};fill($('#snccClass'),'Toutes les classes',hist.classes);fill($('#snccAdminStatus'),'Tous les statuts',hist.admins);fill($('#snccRisk'),'Tous les risques',hist.risks);fill($('#snccDialogClass'),'Sélectionner une classe',hist.classes);fill($('#snccDialogAdmin'),'Sélectionner un statut',hist.admins);fill($('#snccDialogRisk'),'Sélectionner un risque',hist.risks)}catch{fill($('#snccClass'),'Toutes les classes',[]);fill($('#snccAdminStatus'),'Tous les statuts',[]);fill($('#snccRisk'),'Tous les risques',[]);fill($('#snccDialogClass'),'Référentiel indisponible',[]);fill($('#snccDialogAdmin'),'Référentiel indisponible',[]);fill($('#snccDialogRisk'),'Référentiel indisponible',[])}}
function bind(){
$('#snccSearch').oninput=e=>{clearTimeout(timer);timer=setTimeout(async()=>{f.search=e.target.value.trim();offset=0;await Promise.all([loadResults(),loadCerts()])},350)};$('#snccClass').onchange=async e=>{f.classe=e.target.value;offset=0;await loadResults()};$('#snccAdminStatus').onchange=async e=>{f.statut_administratif=e.target.value;offset=0;await loadResults()};$('#snccRisk').onchange=async e=>{f.niveau_risque=e.target.value;offset=0;await loadResults()};$('#snccReset').onclick=async()=>{Object.assign(f,{search:'',classe:'',statut_administratif:'',niveau_risque:''});offset=0;$('#snccSearch').value='';$('#snccClass').value='';$('#snccAdminStatus').value='';$('#snccRisk').value='';await Promise.all([loadResults(),loadCerts()])};$('#snccPrev').onclick=async()=>{offset=Math.max(0,offset-PAGE);await loadResults()};$('#snccNext').onclick=async()=>{offset+=PAGE;await loadResults()};$('#snccForm').onsubmit=save;$('#snccCloseForm').onsubmit=close;document.querySelectorAll('[data-close-sncc-dialog]').forEach(b=>b.onclick=()=>document.getElementById(b.dataset.closeSnccDialog)?.close())}
async function start(){bind();try{user=await api.apiGet('/api/v1/me');await filters();await Promise.all([loadResults(),loadCerts()])}catch(e){ui.showState('#snccApiState',e?.message||'Erreur de chargement.',{error:true})}ui.refreshIcons()}
start();
})();
