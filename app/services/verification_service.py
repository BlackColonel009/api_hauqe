"""Service métier du domaine Vérification."""
from __future__ import annotations
from datetime import date
from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.audit.service import write_audit_event
from app.models.affectation_verification import AffectationVerification
from app.models.anomalie_verification import AnomalieVerification
from app.models.confirmation_externe import ConfirmationExterne
from app.models.dossier_verification import DossierVerification
from app.models.point_verification import PointVerification
from app.repositories.verification_repository import VerificationRepository
from app.schemas.verification import *
from app.services.auth_service import AuthContext

def ip(request): return request.client.host if request.client else None
def txt(v): return (v.strip() or None) if isinstance(v, str) else v

def assignment_response(x):
    return VerificationAssignmentResponse(
        id=x.id,dossier_verification_id=x.dossier_verification_id,verificateur_id=x.verificateur_id,
        date_debut=x.date_debut,date_fin=x.date_fin,date_echeance=x.date_echeance,
        motif=x.motif,statut=x.statut,created_at=x.created_at,updated_at=x.updated_at)

def point_response(x):
    return VerificationPointResponse(
        id=x.id,dossier_verification_id=x.dossier_verification_id,code=x.code,libelle=x.libelle,
        categorie=x.categorie,resultat=x.resultat,observation=x.observation,
        date_verification=x.date_verification,preuve_document_id=x.preuve_document_id,
        verifie_par_id=x.verifie_par_id,created_at=x.created_at,updated_at=x.updated_at)

def anomaly_response(x):
    return VerificationAnomalyResponse(
        id=x.id,dossier_verification_id=x.dossier_verification_id,
        point_verification_id=x.point_verification_id,categorie=x.categorie,gravite=x.gravite,
        description=x.description,statut=x.statut,resolution=x.resolution,
        date_resolution=x.date_resolution,escalade=x.escalade,created_at=x.created_at,updated_at=x.updated_at)

def confirmation_response(x):
    return ExternalConfirmationResponse(
        id=x.id,dossier_verification_id=x.dossier_verification_id,organisme_id=x.organisme_id,
        canal=x.canal,destinataire=x.destinataire,objet=x.objet,date_envoi=x.date_envoi,
        date_echeance=x.date_echeance,date_reponse=x.date_reponse,contenu_reponse=x.contenu_reponse,
        resultat=x.resultat,document_id=x.document_id,statut=x.statut,created_at=x.created_at,updated_at=x.updated_at)

class VerificationService:

    @staticmethod
    def workspace_item_response(row):
        x=row[0]
        return VerificationRegistryItem(
            dossier_id=x.id,fiche_collecte_id=x.fiche_collecte_id,dossier_status=x.statut,opinion=x.avis,priority=x.priorite,risk_level=x.niveau_risque,opened_on=x.date_ouverture,closed_on=x.date_fin,
            mission_id=row.mission_id,mission_code=row.mission_code,campaign_code=row.campaign_code,campaign_name=row.campaign_name,zone_name=row.zone_name,
            entreprise_id=row.entreprise_id,entreprise_name=row.entreprise_name or row.entreprise_trade_name,entreprise_identifiant=row.entreprise_identifiant,
            fiche_status=row.fiche_status,fiche_revision=row.fiche_revision,completeness=float(row.completeness) if row.completeness is not None else None,submitted_at=row.submitted_at,
            points_count=int(row.points_count or 0),anomalies_count=int(row.anomalies_count or 0),unresolved_anomalies_count=int(row.unresolved_anomalies_count or 0),confirmations_pending_count=int(row.confirmations_pending_count or 0),assignments_count=int(row.assignments_count or 0),assigned_names=row.assigned_names,documents_count=int(row.documents_count or 0))

    @staticmethod
    async def workspace_filters(db):
        return VerificationWorkspaceFiltersResponse(**(await VerificationRepository.workspace_filters(db)))

    @staticmethod
    async def workspace_registry(db, **kw):
        rows,total=await VerificationRepository.workspace_registry(db,**kw)
        summary=await VerificationRepository.workspace_summary(db,search=kw['search'],statut=kw['statut'],avis=kw['avis'],priorite=kw['priorite'],verificateur_id=kw['verificateur_id'])
        return VerificationRegistryResponse(total=total,limit=kw['limit'],offset=kw['offset'],summary=VerificationRegistrySummary(**summary),items=[VerificationService.workspace_item_response(r) for r in rows])

    @staticmethod
    async def workspace_item(db,dossier_id):
        row=await VerificationRepository.workspace_item(db,dossier_id)
        if row is None: raise HTTPException(404,"Dossier de vérification introuvable.")
        return VerificationService.workspace_item_response(row)

    @staticmethod
    async def eligible_fiches(db, *,search,limit,offset):
        rows,total=await VerificationRepository.eligible_fiches(db,search=search,limit=limit,offset=offset)
        items=[VerificationEligibleFicheItem(fiche_id=r.fiche_id,mission_id=r.mission_id,mission_code=r.mission_code,campaign_code=r.campaign_code,campaign_name=r.campaign_name,zone_name=r.zone_name,entreprise_id=r.entreprise_id,entreprise_name=r.entreprise_name or r.entreprise_trade_name,entreprise_identifiant=r.entreprise_identifiant,fiche_revision=r.fiche_revision,completeness=float(r.completeness) if r.completeness is not None else None,submitted_at=r.submitted_at) for r in rows]
        return VerificationEligibleFichesResponse(total=total,limit=limit,offset=offset,items=items)

    @staticmethod
    async def get(db, dossier_id):
        x = await VerificationRepository.get_dossier(db, dossier_id)
        if x is None: raise HTTPException(404, "Dossier de vérification introuvable.")
        return x

    @staticmethod
    async def response(db, x):
        p,a,c,af = await VerificationRepository.counts(db, x.id)
        return VerificationDossierResponse(
            id=x.id,fiche_collecte_id=x.fiche_collecte_id,date_ouverture=x.date_ouverture,
            date_fin=x.date_fin,statut=x.statut,avis=x.avis,synthese=x.synthese,
            niveau_risque=x.niveau_risque,priorite=x.priorite,points_count=p,
            anomalies_count=a,confirmations_pending_count=c,affectations_count=af,
            created_at=x.created_at,updated_at=x.updated_at)

    @staticmethod
    async def list(db, **kw):
        items,total = await VerificationRepository.list_dossiers(db, **kw)
        return VerificationDossierListResponse(
            total=total,limit=kw["limit"],offset=kw["offset"],
            items=[await VerificationService.response(db,x) for x in items])

    @staticmethod
    async def open_from_fiche(db, *, fiche_id, payload, actor, request):
        fiche = await VerificationRepository.get_fiche(db, fiche_id)
        if fiche is None: raise HTTPException(404, "Fiche de collecte introuvable.")
        if (fiche.statut or "").upper() != "SOUMISE":
            raise HTTPException(409, "Seule une fiche SOUMISE peut ouvrir une vérification.")
        if await VerificationRepository.find_open_for_fiche(db, fiche_id):
            raise HTTPException(409, "Un dossier non clôturé existe déjà pour cette fiche.")
        x = DossierVerification(
            fiche_collecte_id=fiche_id,date_ouverture=date.today(),date_fin=None,
            statut="OUVERT",avis=None,synthese=None,niveau_risque=txt(payload.niveau_risque),
            priorite=txt(payload.priorite))
        db.add(x); await db.flush()
        await write_audit_event(db,action="VERIFICATION_DOSSIER_OPEN",categorie="VERIFICATION",
            resultat="SUCCES",utilisateur_id=actor.user.id,ressource_type="dossier_verification",
            ressource_id=x.id,adresse_ip=ip(request),
            valeurs_apres={"fiche_collecte_id":str(fiche_id),"statut":x.statut})
        await db.commit(); await db.refresh(x)
        return await VerificationService.response(db,x)

    @staticmethod
    async def update(db, *, dossier_id, payload, actor, request):
        x = await VerificationService.get(db,dossier_id)
        if x.date_fin: raise HTTPException(409,"Dossier clôturé : réouverture requise.")
        before={"priorite":x.priorite,"niveau_risque":x.niveau_risque,"synthese":x.synthese}
        for k,v in payload.model_dump(exclude_unset=True).items(): setattr(x,k,txt(v))
        await write_audit_event(db,action="VERIFICATION_DOSSIER_UPDATE",categorie="VERIFICATION",
            resultat="SUCCES",utilisateur_id=actor.user.id,ressource_type="dossier_verification",
            ressource_id=x.id,adresse_ip=ip(request),valeurs_avant=before,
            valeurs_apres={"priorite":x.priorite,"niveau_risque":x.niveau_risque,"synthese":x.synthese})
        await db.commit(); await db.refresh(x)
        return await VerificationService.response(db,x)

    @staticmethod
    async def close(db, *, dossier_id, payload, actor, request):
        x = await VerificationService.get(db,dossier_id)
        if x.date_fin: raise HTTPException(409,"Dossier déjà clôturé.")
        points,_,pending,_ = await VerificationRepository.counts(db,dossier_id)
        if points == 0: raise HTTPException(409,"Au moins un point de vérification est requis.")
        unresolved = await VerificationRepository.unresolved_anomaly_count(db,dossier_id)
        if payload.avis == "verified_compliant" and (unresolved or pending):
            raise HTTPException(409,"Avis conforme impossible avec anomalie non résolue ou confirmation en attente.")
        x.statut="TERMINE"; x.avis=payload.avis; x.synthese=payload.synthese.strip()
        x.niveau_risque=txt(payload.niveau_risque); x.date_fin=date.today()
        await write_audit_event(db,action="VERIFICATION_DOSSIER_CLOSE",categorie="VERIFICATION",
            resultat="SUCCES",utilisateur_id=actor.user.id,ressource_type="dossier_verification",
            ressource_id=x.id,adresse_ip=ip(request),
            valeurs_apres={"avis":x.avis,"statut":x.statut,"date_fin":x.date_fin.isoformat()})
        await db.commit(); await db.refresh(x)
        return await VerificationService.response(db,x)

    @staticmethod
    async def reopen(db, *, dossier_id, payload, actor, request):
        x=await VerificationService.get(db,dossier_id)
        if x.date_fin is None: raise HTTPException(409,"Dossier déjà ouvert.")
        x.statut="OUVERT"; x.avis=None; x.date_fin=None
        await write_audit_event(db,action="VERIFICATION_DOSSIER_REOPEN",categorie="VERIFICATION",
            resultat="SUCCES",utilisateur_id=actor.user.id,ressource_type="dossier_verification",
            ressource_id=x.id,adresse_ip=ip(request),contexte={"motif":payload.motif.strip()})
        await db.commit(); await db.refresh(x)
        return await VerificationService.response(db,x)

    @staticmethod
    async def list_assignments(db,dossier_id):
        await VerificationService.get(db,dossier_id)
        return [assignment_response(x) for x in await VerificationRepository.list_assignments(db,dossier_id)]

    @staticmethod
    async def assign(db, *, dossier_id, payload, actor, request):
        dossier=await VerificationService.get(db,dossier_id)
        if dossier.date_fin: raise HTTPException(409,"Dossier clôturé.")
        user=await VerificationRepository.get_user(db,payload.verificateur_id)
        if user is None: raise HTTPException(404,"Vérificateur introuvable.")
        if (user.statut or "").upper()!="ACTIF": raise HTTPException(409,"Vérificateur inactif.")
        if payload.date_debut and payload.date_fin and payload.date_fin < payload.date_debut:
            raise HTTPException(422,"Période d'affectation incohérente.")
        if await VerificationRepository.active_assignment(db,dossier_id=dossier_id,verifier_id=payload.verificateur_id):
            raise HTTPException(409,"Affectation active déjà existante.")
        x=AffectationVerification(dossier_verification_id=dossier_id,verificateur_id=payload.verificateur_id,
            date_debut=payload.date_debut or date.today(),date_fin=payload.date_fin,date_echeance=payload.date_echeance,
            motif=txt(payload.motif),statut=txt(payload.statut) or "ACTIF")
        db.add(x); await db.flush()
        await write_audit_event(db,action="VERIFICATION_ASSIGN",categorie="AFFECTATION",resultat="SUCCES",
            utilisateur_id=actor.user.id,ressource_type="affectation_verification",ressource_id=x.id,
            adresse_ip=ip(request),valeurs_apres={"verificateur_id":str(x.verificateur_id),"statut":x.statut})
        await db.commit(); await db.refresh(x); return assignment_response(x)

    @staticmethod
    async def update_assignment(db, *, dossier_id, assignment_id, payload, actor, request):
        x=await VerificationRepository.get_assignment(db,dossier_id=dossier_id,assignment_id=assignment_id)
        if x is None: raise HTTPException(404,"Affectation introuvable.")
        changes=payload.model_dump(exclude_unset=True)
        start=changes.get("date_debut",x.date_debut); end=changes.get("date_fin",x.date_fin)
        if start and end and end<start: raise HTTPException(422,"Période d'affectation incohérente.")
        for k,v in changes.items(): setattr(x,k,txt(v))
        await write_audit_event(db,action="VERIFICATION_ASSIGN_UPDATE",categorie="AFFECTATION",resultat="SUCCES",
            utilisateur_id=actor.user.id,ressource_type="affectation_verification",ressource_id=x.id,
            adresse_ip=ip(request),valeurs_apres={"statut":x.statut})
        await db.commit(); await db.refresh(x); return assignment_response(x)

    @staticmethod
    async def list_points(db,dossier_id):
        await VerificationService.get(db,dossier_id)
        return [point_response(x) for x in await VerificationRepository.list_points(db,dossier_id)]

    @staticmethod
    async def save_point(db, *, dossier_id, payload, actor, request):
        d=await VerificationService.get(db,dossier_id)
        if d.date_fin: raise HTTPException(409,"Dossier clôturé.")
        code=payload.code.strip().upper()
        if await VerificationRepository.get_point_by_code(db,dossier_id=dossier_id,code=code):
            raise HTTPException(409,"Code de point déjà utilisé dans ce dossier.")
        if payload.preuve_document_id and not await VerificationRepository.get_active_document(db,payload.preuve_document_id):
            raise HTTPException(404,"Preuve documentaire introuvable ou inactive.")
        x=PointVerification(dossier_verification_id=dossier_id,code=code,libelle=payload.libelle.strip(),
            categorie=txt(payload.categorie),resultat=payload.resultat.strip(),observation=txt(payload.observation),
            date_verification=date.today(),preuve_document_id=payload.preuve_document_id,verifie_par_id=actor.user.id)
        db.add(x); await db.flush()
        await write_audit_event(db,action="VERIFICATION_POINT_CREATE",categorie="VERIFICATION",resultat="SUCCES",
            utilisateur_id=actor.user.id,ressource_type="point_verification",ressource_id=x.id,
            adresse_ip=ip(request),valeurs_apres={"code":x.code,"resultat":x.resultat})
        await db.commit(); await db.refresh(x); return point_response(x)

    @staticmethod
    async def update_point(db, *, dossier_id, point_id, payload, actor, request):
        d=await VerificationService.get(db,dossier_id)
        if d.date_fin: raise HTTPException(409,"Dossier clôturé.")
        x=await VerificationRepository.get_point(db,dossier_id=dossier_id,point_id=point_id)
        if x is None: raise HTTPException(404,"Point introuvable.")
        changes=payload.model_dump(exclude_unset=True)
        if changes.get("preuve_document_id") and not await VerificationRepository.get_active_document(db,changes["preuve_document_id"]):
            raise HTTPException(404,"Preuve documentaire introuvable ou inactive.")
        for k,v in changes.items(): setattr(x,k,txt(v))
        x.verifie_par_id=actor.user.id; x.date_verification=date.today()
        await write_audit_event(db,action="VERIFICATION_POINT_UPDATE",categorie="VERIFICATION",resultat="SUCCES",
            utilisateur_id=actor.user.id,ressource_type="point_verification",ressource_id=x.id,
            adresse_ip=ip(request),valeurs_apres={"resultat":x.resultat})
        await db.commit(); await db.refresh(x); return point_response(x)

    @staticmethod
    async def list_anomalies(db,dossier_id):
        await VerificationService.get(db,dossier_id)
        return [anomaly_response(x) for x in await VerificationRepository.list_anomalies(db,dossier_id)]

    @staticmethod
    async def create_anomaly(db, *, dossier_id, payload, actor, request):
        d=await VerificationService.get(db,dossier_id)
        if d.date_fin: raise HTTPException(409,"Dossier clôturé.")
        if payload.point_verification_id and not await VerificationRepository.get_point(
            db,dossier_id=dossier_id,point_id=payload.point_verification_id):
            raise HTTPException(404,"Point de vérification absent de ce dossier.")
        x=AnomalieVerification(dossier_verification_id=dossier_id,point_verification_id=payload.point_verification_id,
            categorie=txt(payload.categorie),gravite=txt(payload.gravite),description=payload.description.strip(),
            statut=txt(payload.statut) or "OUVERTE",resolution=None,date_resolution=None,escalade=payload.escalade)
        db.add(x); await db.flush()
        await write_audit_event(db,action="VERIFICATION_ANOMALY_CREATE",categorie="VERIFICATION",resultat="SUCCES",
            utilisateur_id=actor.user.id,ressource_type="anomalie_verification",ressource_id=x.id,
            adresse_ip=ip(request),valeurs_apres={"gravite":x.gravite,"statut":x.statut,"escalade":x.escalade})
        await db.commit(); await db.refresh(x); return anomaly_response(x)

    @staticmethod
    async def update_anomaly(db, *, dossier_id, anomaly_id, payload, actor, request):
        x=await VerificationRepository.get_anomaly(db,dossier_id=dossier_id,anomaly_id=anomaly_id)
        if x is None: raise HTTPException(404,"Anomalie introuvable.")
        for k,v in payload.model_dump(exclude_unset=True).items(): setattr(x,k,txt(v))
        await write_audit_event(db,action="VERIFICATION_ANOMALY_UPDATE",categorie="VERIFICATION",resultat="SUCCES",
            utilisateur_id=actor.user.id,ressource_type="anomalie_verification",ressource_id=x.id,
            adresse_ip=ip(request),valeurs_apres={"statut":x.statut,"escalade":x.escalade})
        await db.commit(); await db.refresh(x); return anomaly_response(x)

    @staticmethod
    async def resolve_anomaly(db, *, dossier_id, anomaly_id, payload, actor, request):
        x=await VerificationRepository.get_anomaly(db,dossier_id=dossier_id,anomaly_id=anomaly_id)
        if x is None: raise HTTPException(404,"Anomalie introuvable.")
        x.resolution=payload.resolution.strip(); x.date_resolution=date.today(); x.statut=payload.statut.strip()
        await write_audit_event(db,action="VERIFICATION_ANOMALY_RESOLVE",categorie="VERIFICATION",resultat="SUCCES",
            utilisateur_id=actor.user.id,ressource_type="anomalie_verification",ressource_id=x.id,
            adresse_ip=ip(request),valeurs_apres={"statut":x.statut,"date_resolution":x.date_resolution.isoformat()})
        await db.commit(); await db.refresh(x); return anomaly_response(x)

    @staticmethod
    async def escalate_anomaly(db, *, dossier_id, anomaly_id, payload, actor, request):
        x=await VerificationRepository.get_anomaly(db,dossier_id=dossier_id,anomaly_id=anomaly_id)
        if x is None: raise HTTPException(404,"Anomalie introuvable.")
        x.escalade=True
        if not x.statut or x.statut=="OUVERTE": x.statut="ESCALEE"
        await write_audit_event(db,action="VERIFICATION_ANOMALY_ESCALATE",categorie="VERIFICATION",resultat="SUCCES",
            utilisateur_id=actor.user.id,ressource_type="anomalie_verification",ressource_id=x.id,
            adresse_ip=ip(request),contexte={"motif":payload.motif.strip()})
        await db.commit(); await db.refresh(x); return anomaly_response(x)

    @staticmethod
    async def list_confirmations(db,dossier_id):
        await VerificationService.get(db,dossier_id)
        return [confirmation_response(x) for x in await VerificationRepository.list_confirmations(db,dossier_id)]

    @staticmethod
    async def create_confirmation(db, *, dossier_id, payload, actor, request):
        d=await VerificationService.get(db,dossier_id)
        if d.date_fin: raise HTTPException(409,"Dossier clôturé.")
        if payload.organisme_id and not await VerificationRepository.get_organisme(db,payload.organisme_id):
            raise HTTPException(404,"Organisme introuvable.")
        sent=payload.date_envoi or date.today()
        if payload.date_echeance and payload.date_echeance<sent: raise HTTPException(422,"Échéance antérieure à l'envoi.")
        x=ConfirmationExterne(dossier_verification_id=dossier_id,organisme_id=payload.organisme_id,
            canal=txt(payload.canal),destinataire=payload.destinataire.strip(),objet=payload.objet.strip(),
            date_envoi=sent,date_echeance=payload.date_echeance,date_reponse=None,contenu_reponse=None,
            resultat=None,document_id=None,statut=txt(payload.statut) or "EN_ATTENTE")
        db.add(x); await db.flush()
        await write_audit_event(db,action="VERIFICATION_CONFIRMATION_CREATE",categorie="VERIFICATION",resultat="SUCCES",
            utilisateur_id=actor.user.id,ressource_type="confirmation_externe",ressource_id=x.id,
            adresse_ip=ip(request),valeurs_apres={"destinataire":x.destinataire,"statut":x.statut})
        await db.commit(); await db.refresh(x); return confirmation_response(x)

    @staticmethod
    async def update_confirmation(db, *, dossier_id, confirmation_id, payload, actor, request):
        x=await VerificationRepository.get_confirmation(db,dossier_id=dossier_id,confirmation_id=confirmation_id)
        if x is None: raise HTTPException(404,"Confirmation externe introuvable.")
        changes=payload.model_dump(exclude_unset=True)
        if changes.get("organisme_id") and not await VerificationRepository.get_organisme(db,changes["organisme_id"]):
            raise HTTPException(404,"Organisme introuvable.")
        sent=changes.get("date_envoi",x.date_envoi); due=changes.get("date_echeance",x.date_echeance)
        if sent and due and due<sent: raise HTTPException(422,"Échéance antérieure à l'envoi.")
        for k,v in changes.items(): setattr(x,k,txt(v))
        await write_audit_event(db,action="VERIFICATION_CONFIRMATION_UPDATE",categorie="VERIFICATION",resultat="SUCCES",
            utilisateur_id=actor.user.id,ressource_type="confirmation_externe",ressource_id=x.id,
            adresse_ip=ip(request),valeurs_apres={"statut":x.statut})
        await db.commit(); await db.refresh(x); return confirmation_response(x)

    @staticmethod
    async def record_confirmation_response(db, *, dossier_id, confirmation_id, payload, actor, request):
        x=await VerificationRepository.get_confirmation(db,dossier_id=dossier_id,confirmation_id=confirmation_id)
        if x is None: raise HTTPException(404,"Confirmation externe introuvable.")
        if payload.document_id and not await VerificationRepository.get_active_document(db,payload.document_id):
            raise HTTPException(404,"Document de réponse introuvable ou inactif.")
        x.date_reponse=payload.date_reponse or date.today(); x.contenu_reponse=payload.contenu_reponse.strip()
        x.resultat=txt(payload.resultat); x.document_id=payload.document_id; x.statut=txt(payload.statut) or "REPONDU"
        await write_audit_event(db,action="VERIFICATION_CONFIRMATION_RESPONSE",categorie="VERIFICATION",resultat="SUCCES",
            utilisateur_id=actor.user.id,ressource_type="confirmation_externe",ressource_id=x.id,
            adresse_ip=ip(request),valeurs_apres={"date_reponse":x.date_reponse.isoformat(),"statut":x.statut})
        await db.commit(); await db.refresh(x); return confirmation_response(x)
