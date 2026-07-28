(function(){
  "use strict";
  const qs=s=>document.querySelector(s);
  function note(target,html,cls="rule-note"){
    if(!target||target.parentElement.querySelector(`.${cls}`))return;
    target.insertAdjacentHTML("afterend",`<div class="${cls}"><i data-lucide="info"></i><span>${html}</span></div>`);
  }
  function enhanceEnterprise(){
    const rccm=qs('[name="rccm"]');if(!rccm)return;
    rccm.required=false;
    const label=rccm.closest(".form-field")?.querySelector("label");if(label)label.innerHTML="Numéro RCCM <span class=\"rule-conditional\">Conditionnel</span>";
    note(rccm.closest(".identifier-wrap"),"<strong>RM-11/RM-12 :</strong> le RCCM reste unique. Sans RCCM, l’entreprise sera enregistrée « En attente de régularisation » et une alerte sera créée.");
    const name=qs('[name="name"]'),region=qs('[name="region"]'),commune=qs('[name="commune"]'),phone=qs('[name="phone"]'),email=qs('[name="email"]');
    [name,region,commune].forEach(x=>x&&(x.required=true));if(phone&&email){note(email,"Au moins un téléphone ou un courriel principal est obligatoire pour valider l’entreprise.");}
  }
  function enhanceCertification(){
    const expiry=qs('[name="expiry"]');if(expiry&&!qs("#noExpiryRule")){
      expiry.closest(".form-field").insertAdjacentHTML("beforeend",`<label class="rule-check" id="noExpiryRule"><input type="checkbox"> Référentiel sans échéance explicite</label><div class="rule-note"><i data-lucide="calendar-check"></i><span><strong>RM-01 :</strong> sans expiration, le certificat reste « À vérifier » sauf si le référentiel autorise cette exception.</span></div>`);
      qs("#noExpiryRule input").onchange=e=>{expiry.required=!e.target.checked;if(e.target.checked){expiry.value="";expiry.disabled=true}else expiry.disabled=false};
    }
    const issue=qs('[name="issue"]');if(issue)issue.max=new Date().toISOString().slice(0,10);
    const file=[...document.querySelectorAll('input[type="file"]')].find(x=>x.closest(".form-field")?.textContent.includes("Certificat principal"));
    if(file){file.required=true;note(file,"<strong>RM-19/RM-42 :</strong> une preuve officielle est obligatoire. Sans preuve, la certification est classée « À vérifier ».");}
  }
  function enhanceBody(){
    const status=qs('[name="status"]');if(status&&!status.querySelector('option[value="Non accrédité"]'))status.insertAdjacentHTML("beforeend",'<option value="Non accrédité">Non accrédité — certificats à vérifier</option>');
    if(status)note(status,"Un organisme non accrédité peut être conservé. Ses certificats sont automatiquement placés sous vérification.");
    const acc=qs("#accList");
    if(acc&&acc.dataset.rmAccreditationNote!=="true"){
      acc.dataset.rmAccreditationNote="true";
      acc.insertAdjacentHTML("afterend",'<div class="rule-note rule-accreditation-note"><i data-lucide="shield-alert"></i><span>Une suspension, un retrait ou une perte d’accréditation déclenche la vérification des certificats concernés, sans invalidation automatique.</span></div>');
    }
  }
  function enhanceUsers(){
    const role=qs('select[name="role"]');if(!role||role.dataset.rmEnhanced)return;role.dataset.rmEnhanced="true";
    ["Administrateur système","Administrateur fonctionnel BNEC","Point focal BNEC","Agent vérificateur","Validateur HAUQE","Contrôleur / évaluateur","Cellule de veille","Direction / décideur","Auditeur / consultation"].forEach(x=>role.insertAdjacentHTML("beforeend",`<option>${x}</option>`));
    note(role,"Les permissions réelles sont accordées selon le moindre privilège. Les intervenants externes sont en lecture seule par défaut.");
  }
  function enhanceScoring(){
    const title=qs(".global-score p");if(title)title.textContent="Classification globale de l’entreprise";
    const badge=qs(".global-score .provisional-badge");if(badge)badge.innerHTML='<i data-lucide="settings-2"></i>Modèle paramétrable et versionné';
    const scale=qs(".score-scale header");if(scale){scale.querySelector("h2").textContent="Classification entreprise";scale.querySelector("p").textContent="Résultat distinct de l’INFC et du SNCC."}
    const labels=qs(".scale-labels");if(labels)labels.innerHTML="<span><b>0–59</b>Non conforme</span><span><b>60–84</b>À surveiller</span><span><b>85–100</b>Conforme</span>";
    const decision=qs("#globalDecision"),value=Number(qs("#globalIndex")?.textContent||0);if(decision)decision.textContent=`Classification entreprise : ${value>=85?"Conforme":value>=60?"À surveiller":"Non conforme"}`;
  }
  function enhanceValidation(){
    const heading=qs(".validations-page .page-heading");if(heading&&!qs("#validatedWorkflow"))heading.insertAdjacentHTML("afterend",`<section class="rule-workflow" id="validatedWorkflow">${["Collecte","Vérification","Contrôle","Validation","Intégration","Classification/INFC","SNCC","Veille"].map((x,i)=>`<span class="${i===3?"active":""}"><b>${i+1}</b>${x}</span>`).join("<i></i>")}</section>`);
  }
  function enhance(){
    const route=location.hash.replace(/^#\/?/,"").split("/")[0];
    if(route==="entreprises")enhanceEnterprise();
    if(route==="certifications")enhanceCertification();
    if(route==="organismes")enhanceBody();
    if(route==="utilisateurs")enhanceUsers();
    if(route==="scoring")enhanceScoring();
    if(route==="validations")enhanceValidation();
    if(window.lucide)window.lucide.createIcons({attrs:{"stroke-width":1.8}});
  }
  window.addEventListener("hauqe:page-ready",enhance);
  const observer=new MutationObserver(()=>{clearTimeout(window.__hauqeRmTimer);window.__hauqeRmTimer=setTimeout(enhance,20)});
  const start=()=>{const page=qs("#pageContent");if(page)observer.observe(page,{childList:true,subtree:true})};
  document.readyState==="loading"?document.addEventListener("DOMContentLoaded",start):start();
})();
