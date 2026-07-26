"""Service métier FUCCS : versionnement, notation dynamique et verrouillage."""
from __future__ import annotations
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from fastapi import HTTPException
from app.audit.service import write_audit_event
from app.models.constat_controle import ConstatControle
from app.models.controle_fuccs import ControleFuccs
from app.models.critere_fuccs import CritereFuccs
from app.models.grille_fuccs import GrilleFuccs
from app.models.note_critere import NoteCritere
from app.models.rubrique_fuccs import RubriqueFuccs
from app.repositories.fuccs_repository import FuccsRepository
from app.schemas.fuccs import *

ADMISSIBLE={"verified_compliant","verified_with_reservation"}
def ip(r): return r.client.host if r.client else None
def txt(v): return (v.strip() or None) if isinstance(v,str) else v

def rubric_response(x): return FuccsRubricResponse(id=x.id,grille_fuccs_id=x.grille_fuccs_id,code=x.code,
    libelle=x.libelle,description=x.description,ordre_affichage=x.ordre_affichage,created_at=x.created_at,updated_at=x.updated_at)
def criterion_response(x): return FuccsCriterionResponse(id=x.id,rubrique_fuccs_id=x.rubrique_fuccs_id,code=x.code,
    libelle=x.libelle,description=x.description,score_maximal=x.score_maximal,poids=x.poids,
    ordre_affichage=x.ordre_affichage,commentaire_obligatoire=x.commentaire_obligatoire,
    preuve_obligatoire=x.preuve_obligatoire,created_at=x.created_at,updated_at=x.updated_at)
def note_response(x): return FuccsNoteResponse(id=x.id,controle_fuccs_id=x.controle_fuccs_id,
    critere_fuccs_id=x.critere_fuccs_id,score=x.score,commentaire=x.commentaire,
    preuve_document_id=x.preuve_document_id,note_par_id=x.note_par_id,created_at=x.created_at,updated_at=x.updated_at)
def finding_response(x): return FuccsFindingResponse(id=x.id,controle_fuccs_id=x.controle_fuccs_id,
    type_constat=x.type_constat,gravite=x.gravite,titre=x.titre,description=x.description,
    statut=x.statut,created_at=x.created_at,updated_at=x.updated_at)

class FuccsService:
    @staticmethod
    async def require_grid(db,grid_id):
        x=await FuccsRepository.get_grid(db,grid_id)
        if x is None: raise HTTPException(404,"Grille FUCCS introuvable.")
        return x

    @staticmethod
    def require_draft(x):
        if (x.statut_publication or "").upper()!="BROUILLON":
            raise HTTPException(409,"Grille publiée/retirée immuable : clonez une nouvelle version.")

    @staticmethod
    async def grid_response(db,x):
        r,c,s=await FuccsRepository.grid_counts(db,x.id)
        return FuccsGridResponse(id=x.id,code=x.code,libelle=x.libelle,version=x.version,date_effet=x.date_effet,
            date_fin=x.date_fin,reference_approbation=x.reference_approbation,statut_publication=x.statut_publication,
            rubriques_count=r,criteres_count=c,score_maximal_calcule=Decimal(str(s or 0)),
            created_at=x.created_at,updated_at=x.updated_at)

    @staticmethod
    async def list_grids(db):
        return [await FuccsService.grid_response(db,x) for x in await FuccsRepository.list_grids(db)]

    @staticmethod
    async def active_grid(db):
        x=await FuccsRepository.active_grid(db)
        if x is None: raise HTTPException(404,"Aucune grille FUCCS active publiée.")
        return await FuccsService.grid_response(db,x)

    @staticmethod
    async def create_grid(db,*,payload,actor,request):
        code=payload.code.strip().upper(); version=payload.version.strip()
        if await FuccsRepository.find_grid_version(db,code=code,version=version):
            raise HTTPException(409,"Cette version de grille existe déjà.")
        x=GrilleFuccs(code=code,libelle=payload.libelle.strip(),version=version,date_effet=payload.date_effet,
            date_fin=None,reference_approbation=None,statut_publication="BROUILLON")
        db.add(x); await db.flush()
        await write_audit_event(db,action="FUCCS_GRID_CREATE",categorie="REFERENTIEL",resultat="SUCCES",
            utilisateur_id=actor.user.id,ressource_type="grille_fuccs",ressource_id=x.id,adresse_ip=ip(request),
            valeurs_apres={"code":x.code,"version":x.version,"statut_publication":x.statut_publication})
        await db.commit(); await db.refresh(x); return await FuccsService.grid_response(db,x)

    @staticmethod
    async def update_grid(db,*,grid_id,payload,actor,request):
        x=await FuccsService.require_grid(db,grid_id); FuccsService.require_draft(x)
        for k,v in payload.model_dump(exclude_unset=True).items(): setattr(x,k,txt(v))
        await write_audit_event(db,action="FUCCS_GRID_UPDATE",categorie="REFERENTIEL",resultat="SUCCES",
            utilisateur_id=actor.user.id,ressource_type="grille_fuccs",ressource_id=x.id,adresse_ip=ip(request))
        await db.commit(); await db.refresh(x); return await FuccsService.grid_response(db,x)

    @staticmethod
    async def clone_grid(db,*,grid_id,payload,actor,request):
        source=await FuccsService.require_grid(db,grid_id)
        code=payload.code.strip().upper(); version=payload.version.strip()
        if await FuccsRepository.find_grid_version(db,code=code,version=version): raise HTTPException(409,"Version cible déjà existante.")
        target=GrilleFuccs(code=code,libelle=payload.libelle.strip(),version=version,date_effet=payload.date_effet,
            date_fin=None,reference_approbation=None,statut_publication="BROUILLON")
        db.add(target); await db.flush()
        for rub in await FuccsRepository.list_rubrics(db,source.id):
            nr=RubriqueFuccs(grille_fuccs_id=target.id,code=rub.code,libelle=rub.libelle,
                description=rub.description,ordre_affichage=rub.ordre_affichage)
            db.add(nr); await db.flush()
            for c in await FuccsRepository.list_criteria_for_rubric(db,rub.id):
                db.add(CritereFuccs(rubrique_fuccs_id=nr.id,code=c.code,libelle=c.libelle,
                    description=c.description,score_maximal=c.score_maximal,poids=c.poids,
                    ordre_affichage=c.ordre_affichage,commentaire_obligatoire=c.commentaire_obligatoire,
                    preuve_obligatoire=c.preuve_obligatoire))
        await write_audit_event(db,action="FUCCS_GRID_CLONE",categorie="REFERENTIEL",resultat="SUCCES",
            utilisateur_id=actor.user.id,ressource_type="grille_fuccs",ressource_id=target.id,
            adresse_ip=ip(request),contexte={"source_grid_id":str(source.id)})
        await db.commit(); await db.refresh(target); return await FuccsService.grid_response(db,target)

    @staticmethod
    async def publish_grid(db,*,grid_id,payload,actor,request):
        x=await FuccsService.require_grid(db,grid_id); FuccsService.require_draft(x)
        r,c,s=await FuccsRepository.grid_counts(db,grid_id)
        if r==0 or c==0 or Decimal(str(s or 0))<=0: raise HTTPException(409,"Une grille vide ou sans score maximal ne peut pas être publiée.")
        x.date_effet=payload.date_effet; x.reference_approbation=payload.reference_approbation.strip(); x.statut_publication="PUBLIE"
        await write_audit_event(db,action="FUCCS_GRID_PUBLISH",categorie="REFERENTIEL",resultat="SUCCES",
            utilisateur_id=actor.user.id,ressource_type="grille_fuccs",ressource_id=x.id,adresse_ip=ip(request),
            valeurs_apres={"criteres_count":c,"score_maximal_calcule":str(s),"reference_approbation":x.reference_approbation})
        await db.commit(); await db.refresh(x); return await FuccsService.grid_response(db,x)

    @staticmethod
    async def retire_grid(db,*,grid_id,payload,actor,request):
        x=await FuccsService.require_grid(db,grid_id)
        if (x.statut_publication or "").upper()!="PUBLIE": raise HTTPException(409,"Seule une grille publiée peut être retirée.")
        if x.date_effet and payload.date_fin<x.date_effet: raise HTTPException(422,"Date de retrait antérieure à la date d'effet.")
        x.date_fin=payload.date_fin; x.statut_publication="RETIRE"
        await write_audit_event(db,action="FUCCS_GRID_RETIRE",categorie="REFERENTIEL",resultat="SUCCES",
            utilisateur_id=actor.user.id,ressource_type="grille_fuccs",ressource_id=x.id,adresse_ip=ip(request),
            contexte={"motif":payload.motif.strip()})
        await db.commit(); await db.refresh(x); return await FuccsService.grid_response(db,x)

    @staticmethod
    async def list_rubrics(db,grid_id):
        await FuccsService.require_grid(db,grid_id)
        return [rubric_response(x) for x in await FuccsRepository.list_rubrics(db,grid_id)]

    @staticmethod
    async def create_rubric(db,*,grid_id,payload,actor,request):
        g=await FuccsService.require_grid(db,grid_id); FuccsService.require_draft(g)
        x=RubriqueFuccs(grille_fuccs_id=grid_id,code=payload.code.strip().upper(),libelle=payload.libelle.strip(),
            description=txt(payload.description),ordre_affichage=payload.ordre_affichage)
        db.add(x); await db.flush()
        await write_audit_event(db,action="FUCCS_RUBRIC_CREATE",categorie="REFERENTIEL",resultat="SUCCES",
            utilisateur_id=actor.user.id,ressource_type="rubrique_fuccs",ressource_id=x.id,adresse_ip=ip(request))
        await db.commit(); await db.refresh(x); return rubric_response(x)

    @staticmethod
    async def update_rubric(db,*,grid_id,rubric_id,payload,actor,request):
        g=await FuccsService.require_grid(db,grid_id); FuccsService.require_draft(g)
        x=await FuccsRepository.get_rubric(db,grid_id=grid_id,rubric_id=rubric_id)
        if x is None: raise HTTPException(404,"Rubrique introuvable.")
        for k,v in payload.model_dump(exclude_unset=True).items():
            setattr(x,k,v.strip().upper() if k=="code" and v else txt(v))
        await write_audit_event(db,action="FUCCS_RUBRIC_UPDATE",categorie="REFERENTIEL",resultat="SUCCES",
            utilisateur_id=actor.user.id,ressource_type="rubrique_fuccs",ressource_id=x.id,adresse_ip=ip(request))
        await db.commit(); await db.refresh(x); return rubric_response(x)

    @staticmethod
    async def delete_rubric(db,*,grid_id,rubric_id,actor,request):
        g=await FuccsService.require_grid(db,grid_id); FuccsService.require_draft(g)
        x=await FuccsRepository.get_rubric(db,grid_id=grid_id,rubric_id=rubric_id)
        if x is None: raise HTTPException(404,"Rubrique introuvable.")
        await write_audit_event(db,action="FUCCS_RUBRIC_DELETE_DRAFT",categorie="REFERENTIEL",resultat="SUCCES",
            utilisateur_id=actor.user.id,ressource_type="rubrique_fuccs",ressource_id=x.id,adresse_ip=ip(request))
        await FuccsRepository.delete_rubric_with_criteria(db,rubric_id); await db.commit()

    @staticmethod
    async def list_criteria(db,grid_id):
        await FuccsService.require_grid(db,grid_id)
        return [criterion_response(x) for x in await FuccsRepository.list_criteria_for_grid(db,grid_id)]

    @staticmethod
    async def create_criterion(db,*,grid_id,rubric_id,payload,actor,request):
        g=await FuccsService.require_grid(db,grid_id); FuccsService.require_draft(g)
        if not await FuccsRepository.get_rubric(db,grid_id=grid_id,rubric_id=rubric_id): raise HTTPException(404,"Rubrique introuvable.")
        x=CritereFuccs(rubrique_fuccs_id=rubric_id,code=payload.code.strip().upper(),libelle=payload.libelle.strip(),
            description=txt(payload.description),score_maximal=payload.score_maximal,poids=payload.poids,
            ordre_affichage=payload.ordre_affichage,commentaire_obligatoire=payload.commentaire_obligatoire,
            preuve_obligatoire=payload.preuve_obligatoire)
        db.add(x); await db.flush()
        await write_audit_event(db,action="FUCCS_CRITERION_CREATE",categorie="REFERENTIEL",resultat="SUCCES",
            utilisateur_id=actor.user.id,ressource_type="critere_fuccs",ressource_id=x.id,adresse_ip=ip(request))
        await db.commit(); await db.refresh(x); return criterion_response(x)

    @staticmethod
    async def update_criterion(db,*,grid_id,rubric_id,criterion_id,payload,actor,request):
        g=await FuccsService.require_grid(db,grid_id); FuccsService.require_draft(g)
        x=await FuccsRepository.get_criterion_for_rubric(db,rubric_id=rubric_id,criterion_id=criterion_id)
        if x is None: raise HTTPException(404,"Critère introuvable.")
        for k,v in payload.model_dump(exclude_unset=True).items():
            setattr(x,k,v.strip().upper() if k=="code" and v else txt(v))
        await write_audit_event(db,action="FUCCS_CRITERION_UPDATE",categorie="REFERENTIEL",resultat="SUCCES",
            utilisateur_id=actor.user.id,ressource_type="critere_fuccs",ressource_id=x.id,adresse_ip=ip(request))
        await db.commit(); await db.refresh(x); return criterion_response(x)

    @staticmethod
    async def delete_criterion(db,*,grid_id,rubric_id,criterion_id,actor,request):
        g=await FuccsService.require_grid(db,grid_id); FuccsService.require_draft(g)
        x=await FuccsRepository.get_criterion_for_rubric(db,rubric_id=rubric_id,criterion_id=criterion_id)
        if x is None: raise HTTPException(404,"Critère introuvable.")
        await write_audit_event(db,action="FUCCS_CRITERION_DELETE_DRAFT",categorie="REFERENTIEL",resultat="SUCCES",
            utilisateur_id=actor.user.id,ressource_type="critere_fuccs",ressource_id=x.id,adresse_ip=ip(request))
        await FuccsRepository.delete_criterion(db,criterion_id); await db.commit()

    @staticmethod
    async def require_control(db,control_id):
        x=await FuccsRepository.get_control(db,control_id)
        if x is None: raise HTTPException(404,"Contrôle FUCCS introuvable.")
        return x

    @staticmethod
    async def control_response(db,x):
        n,c,f=await FuccsRepository.control_counts(db,x.id,x.grille_fuccs_id)
        return FuccsControlResponse(id=x.id,dossier_verification_id=x.dossier_verification_id,
            grille_fuccs_id=x.grille_fuccs_id,controleur_id=x.controleur_id,date_debut=x.date_debut,
            date_fin=x.date_fin,score_brut=x.score_brut,score_maximal=x.score_maximal,taux=x.taux,
            synthese=x.synthese,statut=x.statut,notes_count=n,criteres_count=c,constats_count=f,
            created_at=x.created_at,updated_at=x.updated_at)

    @staticmethod
    async def list_controls(db,**kw):
        items,total=await FuccsRepository.list_controls(db,**kw)
        return FuccsControlListResponse(total=total,limit=kw["limit"],offset=kw["offset"],
            items=[await FuccsService.control_response(db,x) for x in items])

    @staticmethod
    async def create_control(db,*,dossier_id,payload,actor,request):
        d=await FuccsRepository.get_dossier(db,dossier_id)
        if d is None: raise HTTPException(404,"Dossier de vérification introuvable.")
        if d.date_fin is None: raise HTTPException(409,"Clôturez d'abord la vérification.")
        if d.avis not in ADMISSIBLE: raise HTTPException(409,"Avis de vérification non admissible au FUCCS.")
        g=await FuccsService.require_grid(db,payload.grille_fuccs_id) if payload.grille_fuccs_id else await FuccsRepository.active_grid(db)
        if g is None or (g.statut_publication or "").upper()!="PUBLIE": raise HTTPException(409,"Aucune grille publiée utilisable.")
        _,count,maxscore=await FuccsRepository.grid_counts(db,g.id)
        if count==0: raise HTTPException(409,"Grille sans critères.")
        x=ControleFuccs(dossier_verification_id=dossier_id,grille_fuccs_id=g.id,controleur_id=actor.user.id,
            date_debut=date.today(),date_fin=None,score_brut=Decimal("0"),score_maximal=Decimal(str(maxscore or 0)),
            taux="0.00",synthese=None,statut="BROUILLON")
        db.add(x); await db.flush()
        await write_audit_event(db,action="FUCCS_CONTROL_CREATE",categorie="CONTROLE_FUCCS",resultat="SUCCES",
            utilisateur_id=actor.user.id,ressource_type="controle_fuccs",ressource_id=x.id,adresse_ip=ip(request),
            valeurs_apres={"grille_fuccs_id":str(g.id),"criteres_count":count,"score_maximal":str(x.score_maximal)})
        await db.commit(); await db.refresh(x); return await FuccsService.control_response(db,x)

    @staticmethod
    async def recalculate(db,x):
        criteria=await FuccsRepository.list_criteria_for_grid(db,x.grille_fuccs_id)
        notes=await FuccsRepository.list_notes(db,x.id)
        mx=sum((Decimal(str(c.score_maximal or 0)) for c in criteria),Decimal("0"))
        sc=sum((Decimal(str(n.score or 0)) for n in notes),Decimal("0"))
        x.score_brut=sc; x.score_maximal=mx
        rate=(sc*Decimal("100")/mx).quantize(Decimal("0.01"),rounding=ROUND_HALF_UP) if mx>0 else Decimal("0")
        x.taux=format(rate,"f")

    @staticmethod
    async def list_notes(db,control_id):
        await FuccsService.require_control(db,control_id)
        return [note_response(x) for x in await FuccsRepository.list_notes(db,control_id)]

    @staticmethod
    async def upsert_note(db,*,control_id,criterion_id,payload,actor,request):
        c=await FuccsService.require_control(db,control_id)
        if (c.statut or "").upper()=="FINALISE": raise HTTPException(409,"Contrôle finalisé : réouverture requise.")
        crit=await FuccsRepository.get_criterion_for_grid(db,grid_id=c.grille_fuccs_id,criterion_id=criterion_id)
        if crit is None: raise HTTPException(404,"Critère absent de la grille du contrôle.")
        if payload.score>Decimal(str(crit.score_maximal or 0)): raise HTTPException(422,"Score supérieur au maximum du critère.")
        if crit.commentaire_obligatoire and not txt(payload.commentaire): raise HTTPException(422,"Commentaire obligatoire.")
        if crit.preuve_obligatoire and payload.preuve_document_id is None: raise HTTPException(422,"Preuve obligatoire.")
        if payload.preuve_document_id and not await FuccsRepository.get_active_document(db,payload.preuve_document_id):
            raise HTTPException(404,"Preuve documentaire introuvable ou inactive.")
        x=await FuccsRepository.get_note(db,control_id=control_id,criterion_id=criterion_id)
        action="FUCCS_NOTE_UPDATE"
        if x is None:
            action="FUCCS_NOTE_CREATE"; x=NoteCritere(controle_fuccs_id=control_id,critere_fuccs_id=criterion_id,
                score=payload.score,commentaire=txt(payload.commentaire),preuve_document_id=payload.preuve_document_id,
                note_par_id=actor.user.id); db.add(x)
        else:
            x.score=payload.score; x.commentaire=txt(payload.commentaire); x.preuve_document_id=payload.preuve_document_id; x.note_par_id=actor.user.id
        await db.flush(); await FuccsService.recalculate(db,c)
        await write_audit_event(db,action=action,categorie="CONTROLE_FUCCS",resultat="SUCCES",
            utilisateur_id=actor.user.id,ressource_type="note_critere",ressource_id=x.id,adresse_ip=ip(request),
            valeurs_apres={"score":str(x.score),"score_brut_controle":str(c.score_brut),"taux_controle":c.taux})
        await db.commit(); await db.refresh(x); return note_response(x)

    @staticmethod
    async def list_findings(db,control_id):
        await FuccsService.require_control(db,control_id)
        return [finding_response(x) for x in await FuccsRepository.list_findings(db,control_id)]

    @staticmethod
    async def create_finding(db,*,control_id,payload,actor,request):
        c=await FuccsService.require_control(db,control_id)
        if (c.statut or "").upper()=="FINALISE": raise HTTPException(409,"Contrôle finalisé.")
        x=ConstatControle(controle_fuccs_id=control_id,type_constat=txt(payload.type_constat),gravite=txt(payload.gravite),
            titre=payload.titre.strip(),description=payload.description.strip(),statut=txt(payload.statut) or "OUVERT")
        db.add(x); await db.flush()
        await write_audit_event(db,action="FUCCS_FINDING_CREATE",categorie="CONTROLE_FUCCS",resultat="SUCCES",
            utilisateur_id=actor.user.id,ressource_type="constat_controle",ressource_id=x.id,adresse_ip=ip(request))
        await db.commit(); await db.refresh(x); return finding_response(x)

    @staticmethod
    async def update_finding(db,*,control_id,finding_id,payload,actor,request):
        c=await FuccsService.require_control(db,control_id)
        if (c.statut or "").upper()=="FINALISE": raise HTTPException(409,"Contrôle finalisé.")
        x=await FuccsRepository.get_finding(db,control_id=control_id,finding_id=finding_id)
        if x is None: raise HTTPException(404,"Constat introuvable.")
        for k,v in payload.model_dump(exclude_unset=True).items(): setattr(x,k,txt(v))
        await write_audit_event(db,action="FUCCS_FINDING_UPDATE",categorie="CONTROLE_FUCCS",resultat="SUCCES",
            utilisateur_id=actor.user.id,ressource_type="constat_controle",ressource_id=x.id,adresse_ip=ip(request))
        await db.commit(); await db.refresh(x); return finding_response(x)

    @staticmethod
    async def finalize(db,*,control_id,payload,actor,request):
        c=await FuccsService.require_control(db,control_id)
        if (c.statut or "").upper()=="FINALISE": raise HTTPException(409,"Contrôle déjà finalisé.")
        criteria=await FuccsRepository.list_criteria_for_grid(db,c.grille_fuccs_id)
        notes=await FuccsRepository.list_notes(db,c.id); by={n.critere_fuccs_id:n for n in notes}
        missing=[x.code or str(x.id) for x in criteria if x.id not in by]
        if missing: raise HTTPException(409,"Critères non notés : "+", ".join(missing[:10]))
        for crit in criteria:
            note=by[crit.id]
            if crit.commentaire_obligatoire and not txt(note.commentaire): raise HTTPException(409,f"Commentaire manquant pour {crit.code}.")
            if crit.preuve_obligatoire and not note.preuve_document_id: raise HTTPException(409,f"Preuve manquante pour {crit.code}.")
        await FuccsService.recalculate(db,c); c.synthese=payload.synthese.strip(); c.date_fin=date.today(); c.statut="FINALISE"
        await write_audit_event(db,action="FUCCS_CONTROL_FINALIZE",categorie="CONTROLE_FUCCS",resultat="SUCCES",
            utilisateur_id=actor.user.id,ressource_type="controle_fuccs",ressource_id=c.id,adresse_ip=ip(request),
            valeurs_apres={"score_brut":str(c.score_brut),"score_maximal":str(c.score_maximal),"taux":c.taux})
        await db.commit(); await db.refresh(c); return await FuccsService.control_response(db,c)

    @staticmethod
    async def reopen(db,*,control_id,payload,actor,request):
        c=await FuccsService.require_control(db,control_id)
        if (c.statut or "").upper()!="FINALISE": raise HTTPException(409,"Seul un contrôle finalisé peut être rouvert.")
        c.statut="BROUILLON"; c.date_fin=None
        await write_audit_event(db,action="FUCCS_CONTROL_REOPEN",categorie="CONTROLE_FUCCS",resultat="SUCCES",
            utilisateur_id=actor.user.id,ressource_type="controle_fuccs",ressource_id=c.id,adresse_ip=ip(request),
            contexte={"motif":payload.motif.strip()})
        await db.commit(); await db.refresh(c); return await FuccsService.control_response(db,c)
