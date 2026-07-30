(async function(){
  "use strict";
  const api=await import("/static/js/core/api.js");
  const $=s=>document.querySelector(s);
  const e=v=>String(v??"—").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;");
  const icons=()=>window.lucide?.createIcons({attrs:{"stroke-width":1.8}});
  const now=new Date(),route=location.hash.replace(/^#\/?/,"").split("/");
  const key=route[0]==="tableaux-de-bord"?route[1]:route[0];
  const configs={
    tactique:{eyebrow:"Pilotage mensuel",title:"Tableau de bord tactique",description:"Suivez les files opérationnelles, les délais, la qualité et la charge de traitement de la Direction technique.",endpoint:"/api/v1/dashboards/tactical",period:"month"},
    strategique:{eyebrow:"Pilotage trimestriel",title:"Tableau de bord stratégique",description:"Analysez les tendances nationales, les risques majeurs et les recommandations destinées à la décision.",endpoint:"/api/v1/dashboards/strategic",period:"quarter"},
    annuel:{eyebrow:"Bilan institutionnel",title:"Tableau de bord annuel",description:"Comparez les résultats annuels, la qualité, la gouvernance et la continuité du dispositif.",endpoint:"/api/v1/dashboards/annual",period:"year"},
    barometre:{eyebrow:"Observation nationale",title:"Baromètre national des certifications",description:"Observez la structure du registre national par région, secteur, norme et organisme certificateur.",endpoint:"/api/v1/barometer",period:"dates"},
    public:{eyebrow:"Données ouvertes autorisées",title:"Tableau de bord public",description:"Consultez uniquement les indicateurs agrégés ayant reçu une autorisation institutionnelle de publication.",endpoint:"/api/v1/public/indicators",period:"public"}
  };
  const cfg=configs[key]||configs.tactique;
  const frenchLabels={
    submitted_forms:"Fiches soumises",
    opened:"Dossiers ouverts",
    closed:"Dossiers clôturés",
    finalized:"Contrôles finalisés",
    average_rate:"Taux moyen",
    decisions:"Décisions",
    completed:"Intégrations terminées",
    new_certifications:"Nouvelles certifications",
    alerts_created:"Alertes détectées",
    alerts_resolved:"Alertes résolues",
    renewal_decisions:"Décisions de renouvellement",
    reviews_validated:"Revues validées",
    open_action_plans:"Plans d’action ouverts",
    open_action_plans_at_generation:"Plans d’action ouverts lors du calcul",
    incidents_declared:"Incidents déclarés",
    quality_reviews_created:"Revues qualité créées",
    backup_failures:"Échecs de sauvegarde",
    publication:"Publication",
    date:"Date de publication",
    version:"Version de la règle",
    enterprises:"Entreprises",
    certifications:"Certifications",
    active_certifications:"Certifications actives",
    average_infc:"INFC moyen"
  };
  const frenchValues={
    OUI:"Oui",NON:"Non",ACTIF:"Actif",ACTIVE:"Active",INACTIF:"Inactif",
    VALIDE:"Validé",VALIDEE:"Validée",EXPIRE:"Expiré",EXPIREE:"Expirée",
    BROUILLON:"Brouillon",PUBLIE:"Publié",PUBLIEE:"Publiée",
    NON_RENSEIGNE:"Non renseigné",ACCEPTEE:"Acceptée",REJETEE:"Rejetée",
    FAVORABLE:"Favorable",DEFAVORABLE:"Défavorable"
  };
  const labelFor=key=>frenchLabels[key]||String(key||"").replaceAll("_"," ");
  const displayed=value=>{
    if(value===null||value===undefined||value==="")return "—";
    if(typeof value==="object")return Object.entries(value).map(([k,v])=>`${labelFor(k)} : ${displayed(v)}`).join(" · ");
    return frenchValues[String(value).toUpperCase()]||value;
  };
  function state(message,error=false){const n=$("#advancedDashboardState");n.hidden=false;n.className=`dashboard-api-state ${error?"error":""}`;n.innerHTML=`<i data-lucide="${error?"triangle-alert":"info"}"></i><div><strong>${error?"Tableau indisponible":"Information"}</strong><span>${e(message)}</span></div>`;icons()}
  function setup(){
    $("#advancedDashboardEyebrow").textContent=cfg.eyebrow;$("#advancedDashboardTitle").textContent=cfg.title;$("#advancedDashboardDescription").textContent=cfg.description;
    const year=now.getFullYear(),month=now.getMonth()+1,quarter=Math.ceil(month/3);
    if(cfg.period==="month")$("#advancedDashboardFilters").innerHTML=`<label>Année<input id="dashYear" type="number" min="2000" max="2100" value="${year}"></label><label>Mois<select id="dashMonth">${Array.from({length:12},(_,i)=>`<option value="${i+1}" ${i+1===month?"selected":""}>${new Intl.DateTimeFormat("fr",{month:"long"}).format(new Date(2020,i,1))}</option>`).join("")}</select></label>`;
    if(cfg.period==="quarter")$("#advancedDashboardFilters").innerHTML=`<label>Année<input id="dashYear" type="number" min="2000" max="2100" value="${year}"></label><label>Trimestre<select id="dashQuarter">${[1,2,3,4].map(x=>`<option ${x===quarter?"selected":""} value="${x}">T${x}</option>`).join("")}</select></label>`;
    if(cfg.period==="year")$("#advancedDashboardFilters").innerHTML=`<label>Année<input id="dashYear" type="number" min="2000" max="2100" value="${year}"></label>`;
    if(cfg.period==="dates")$("#advancedDashboardFilters").innerHTML=`<label>Du<input id="dashStart" type="date" value="${year}-01-01"></label><label>Au<input id="dashEnd" type="date" value="${now.toISOString().slice(0,10)}"></label>`;
    if(cfg.period==="public"){$("#advancedDashboardToolbar").hidden=true}
  }
  function url(){
    const q=new URLSearchParams();
    if($("#dashYear"))q.set("year",$("#dashYear").value);
    if($("#dashMonth"))q.set("month",$("#dashMonth").value);
    if($("#dashQuarter"))q.set("quarter",$("#dashQuarter").value);
    if($("#dashStart"))q.set("start_date",$("#dashStart").value);
    if($("#dashEnd"))q.set("end_date",$("#dashEnd").value);
    return `${cfg.endpoint}${q.size?`?${q}`:""}`;
  }
  const value=x=>{
    if(x===null||x===undefined||x==="")return "—";
    const numeric=typeof x==="number"||(/^[-+]?\d+(?:[.,]\d+)?$/.test(String(x).trim()));
    return numeric?new Intl.NumberFormat("fr-FR",{maximumFractionDigits:2}).format(Number(String(x).replace(",","."))):String(x);
  };
  function kpis(items){$("#advancedDashboardKpis").innerHTML=(items||[]).map(x=>{const delta=Number(x.delta);return `<article><small>${e(displayed(x.label))}</small><strong>${e(value(x.value))}${x.unit?` <small>${e(displayed(x.unit))}</small>`:""}</strong><em class="${delta>0?"positive":delta<0?"negative":""}">${x.previous_value!==null&&x.previous_value!==undefined?`Précédent : ${e(value(x.previous_value))}${delta?` · ${delta>0?"+":""}${e(value(delta))}`:""}`:e(x.definition||"Valeur calculée par le serveur")}</em></article>`}).join("")}
  function bars(items){const max=Math.max(1,...(items||[]).map(x=>Number(x.value)||0));return `<div class="dashboard-bars">${(items||[]).map(x=>`<article><div class="dashboard-bar-head"><span>${e(displayed(x.label))}</span><strong>${e(value(x.value))}${x.percentage!=null?` · ${e(value(x.percentage))} %`:""}</strong></div><div class="dashboard-bar-track"><i style="width:${Math.max(2,(Number(x.value)||0)/max*100)}%"></i></div></article>`).join("")||'<div class="priority-empty">Aucune donnée pour cette période.</div>'}</div>`}
  function series(items){const max=Math.max(1,...(items||[]).map(x=>Number(x.value)||0));return `<div class="dashboard-series">${(items||[]).map(x=>`<article title="${e(value(x.value))}"><i style="height:${Math.max(3,(Number(x.value)||0)/max*100)}%"></i><span>${e(x.period)}</span></article>`).join("")||'<div class="priority-empty">Aucune série disponible.</div>'}</div>`}
  function details(groups){return `<div class="dashboard-detail-grid">${groups.map(([title,data])=>`<article class="dashboard-detail-card"><h3>${e(title)}</h3><dl>${Object.entries(data||{}).slice(0,8).map(([k,v])=>`<div><dt>${e(labelFor(k))}</dt><dd>${typeof v==="number"?e(value(v)):e(displayed(v))}</dd></div>`).join("")||"<div><dt>Aucune donnée</dt><dd>—</dd></div>"}</dl></article>`).join("")}</div>`}
  function render(data){
    $("#advancedDashboardState").hidden=true;$("#advancedDashboardPeriod").innerHTML=`<small>Période observée</small><strong>${e(data.period?.label||data.year||"Publication autorisée")}</strong>`;$("#advancedDashboardUpdated").textContent=data.generated_at?`Calculé le ${new Intl.DateTimeFormat("fr-FR",{dateStyle:"medium",timeStyle:"short"}).format(new Date(data.generated_at))}`:"";
    if(key==="public"){kpis((data.indicators||[]).map(x=>({...x,definition:"Indicateur officiellement publié"})));$("#visualOneTitle").textContent="Publication institutionnelle";$("#advancedVisualOne").innerHTML=details([["Référence",{publication:data.publication_id,date:data.publication_date,version:data.rule_version||"—"}]]);$("#visualTwoTitle").textContent="Période autorisée";$("#advancedVisualTwo").innerHTML=`<div class="dashboard-donut-summary"><div class="dashboard-donut" style="--value:100%"></div><div class="dashboard-donut-label"><strong>100 %</strong><small>Agrégé</small></div></div>`;$("#advancedDashboardAnalysis").innerHTML=`<div class="public-dashboard-disclaimer">${e(data.disclaimer)}</div>`;return}
    if(key==="barometre"){kpis([{label:"Certifications",value:data.certifications_count},{label:"Certifications actives",value:data.active_certifications_count},{label:"Entreprises",value:data.enterprises_count},{label:"INFC national",value:data.national_infc_average,unit:"/ 100"}]);$("#visualOneTitle").textContent="Répartition régionale";$("#advancedVisualOne").innerHTML=bars((data.by_region||[]).map(x=>({label:x.zone_name,value:x.certifications})));$("#visualTwoTitle").textContent="Statuts des certifications";$("#advancedVisualTwo").innerHTML=bars(data.certification_statuses);$("#advancedDashboardAnalysis").innerHTML=details([["Secteurs",Object.fromEntries((data.by_sector||[]).map(x=>[x.label,x.value]))],["Normes",Object.fromEntries((data.by_norm||[]).map(x=>[x.label,x.value]))],["Classes SNCC",Object.fromEntries((data.sncc_classes||[]).map(x=>[x.label,x.value]))]]);return}
    kpis(data.kpis);
    if(key==="tactique"){$("#visualOneTitle").textContent="Chaîne de traitement mensuelle";const chain=[["Collecte",data.collection],["Vérification",data.verification],["Contrôle FUCCS",data.fuccs],["Validation",data.validation],["Intégration",data.integration],["Veille",data.watch]];$("#advancedVisualOne").innerHTML=details(chain);$("#visualTwoTitle").textContent="Qualité du mois";$("#advancedVisualTwo").innerHTML=details([["Qualité",data.quality]]);$("#advancedDashboardAnalysis").innerHTML=details(chain);return}
    if(key==="strategique"){$("#visualOneTitle").textContent="Couverture régionale";$("#advancedVisualOne").innerHTML=bars((data.by_region||[]).map(x=>({label:x.zone_name,value:x.certifications})));$("#visualTwoTitle").textContent="Évolution de l’INFC";$("#advancedVisualTwo").innerHTML=series(data.infc_series);const s=data.synthesis||{};$("#advancedDashboardAnalysis").innerHTML=`<div class="dashboard-synthesis">${[["Constats",s.findings],["Risques majeurs",s.major_risks],["Recommandations prioritaires",s.priority_recommendations]].map(([t,a])=>`<section><h3>${t}</h3><ul>${(a||[]).map(x=>`<li>${e(x)}</li>`).join("")||"<li>Aucun élément signalé.</li>"}</ul></section>`).join("")}</div>`;return}
    $("#visualOneTitle").textContent="Certifications par trimestre";$("#advancedVisualOne").innerHTML=series(data.quarterly_certifications);$("#visualTwoTitle").textContent="INFC trimestriel";$("#advancedVisualTwo").innerHTML=series(data.quarterly_infc);$("#advancedDashboardAnalysis").innerHTML=details([["Qualité",data.quality],["Gouvernance",data.governance],["Continuité",data.continuity]]);
  }
  async function load(ev){try{const task=()=>api.apiGet(url(),key==="public"?{auth:false}:{});const data=window.HAUQE_ACTION_LOADER?await window.HAUQE_ACTION_LOADER.run(task,{button:ev?.currentTarget,title:cfg.title,message:"Consolidation des indicateurs",detail:"Les calculs institutionnels sont exécutés par le serveur."}):await task();render(data)}catch(err){state(err?.message||"Chargement impossible.",true);$("#advancedDashboardKpis").innerHTML="";$("#advancedVisualOne").innerHTML="";$("#advancedVisualTwo").innerHTML="";$("#advancedDashboardAnalysis").innerHTML=""}}
  setup();$("#refreshAdvancedDashboard").onclick=load;await load();icons();
})();
