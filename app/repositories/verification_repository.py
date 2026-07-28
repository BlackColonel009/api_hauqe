"""Repository PostgreSQL du domaine Vérification."""
from __future__ import annotations
from uuid import UUID
from sqlalchemy import distinct, func, literal, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.affectation_verification import AffectationVerification
from app.models.anomalie_verification import AnomalieVerification
from app.models.confirmation_externe import ConfirmationExterne
from app.models.document import Document
from app.models.dossier_verification import DossierVerification
from app.models.fiche_collecte import FicheCollecte
from app.models.organisme import Organisme
from app.models.point_verification import PointVerification
from app.models.utilisateur import Utilisateur
from app.models.campagne import Campagne
from app.models.entreprise import Entreprise
from app.models.mission_collecte import MissionCollecte
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.utilisateur_role import UtilisateurRole
from app.models.zone_administrative import ZoneAdministrative

class VerificationRepository:

    @staticmethod
    async def workspace_filters(db: AsyncSession):
        async def values(column):
            r=await db.execute(select(column).where(column.is_not(None),func.trim(column)!="").distinct().order_by(column))
            return [str(v).strip() for v in r.scalars().all() if v]
        vr=await db.execute(
            select(Utilisateur.id,Utilisateur.prenoms,Utilisateur.nom,Utilisateur.email)
            .select_from(Utilisateur)
            .join(UtilisateurRole,UtilisateurRole.utilisateur_id==Utilisateur.id)
            .join(Role,Role.id==UtilisateurRole.role_id)
            .join(RolePermission,RolePermission.role_id==Role.id)
            .join(Permission,Permission.id==RolePermission.permission_id)
            .where(
                or_(Utilisateur.statut.is_(None),func.upper(Utilisateur.statut)=="ACTIF"),
                or_(UtilisateurRole.statut.is_(None),func.upper(UtilisateurRole.statut)=="ACTIF"),
                Permission.code=="VERIFICATION.VERIFIER",
            ).distinct().order_by(Utilisateur.prenoms,Utilisateur.nom,Utilisateur.email)
        )
        verifiers=[]
        for row in vr.all():
            name=" ".join(x for x in (row.prenoms,row.nom) if x).strip()
            verifiers.append({"id":row.id,"label":name or row.email,"code":row.email})
        return {
            "statuses":await values(DossierVerification.statut),
            "opinions":await values(DossierVerification.avis),
            "priorities":await values(DossierVerification.priorite),
            "verifiers":verifiers,
        }

    @staticmethod
    def workspace_filters_sql(*,search,statut,avis,priorite,verificateur_id):
        f=[]
        if statut: f.append(func.upper(DossierVerification.statut)==statut.strip().upper())
        if avis: f.append(func.upper(DossierVerification.avis)==avis.strip().upper())
        if priorite: f.append(func.upper(DossierVerification.priorite)==priorite.strip().upper())
        if verificateur_id:
            f.append(select(AffectationVerification.id).where(
                AffectationVerification.dossier_verification_id==DossierVerification.id,
                AffectationVerification.verificateur_id==verificateur_id,
                or_(AffectationVerification.statut.is_(None),func.upper(AffectationVerification.statut)=="ACTIF")
            ).exists())
        if search and search.strip():
            p=f"%{search.strip()}%"
            f.append(or_(MissionCollecte.code.ilike(p),Campagne.code.ilike(p),Campagne.nom.ilike(p),ZoneAdministrative.nom.ilike(p),Entreprise.identifiant_national.ilike(p),Entreprise.raison_sociale.ilike(p),Entreprise.nom_commercial.ilike(p),DossierVerification.synthese.ilike(p)))
        return f

    @staticmethod
    def workspace_base():
        def c(model,*where):
            return select(func.count(model.id)).where(*where).correlate(DossierVerification).scalar_subquery()
        points=c(PointVerification,PointVerification.dossier_verification_id==DossierVerification.id)
        anomalies=c(AnomalieVerification,AnomalieVerification.dossier_verification_id==DossierVerification.id)
        unresolved=c(AnomalieVerification,AnomalieVerification.dossier_verification_id==DossierVerification.id,AnomalieVerification.date_resolution.is_(None))
        pending=c(ConfirmationExterne,ConfirmationExterne.dossier_verification_id==DossierVerification.id,ConfirmationExterne.date_reponse.is_(None))
        assignments=c(AffectationVerification,AffectationVerification.dossier_verification_id==DossierVerification.id,or_(AffectationVerification.statut.is_(None),func.upper(AffectationVerification.statut)=="ACTIF"))
        assigned_names=(select(func.string_agg(distinct(func.concat_ws(literal(" "),Utilisateur.prenoms,Utilisateur.nom)),literal(", ")))
            .select_from(AffectationVerification).join(Utilisateur,Utilisateur.id==AffectationVerification.verificateur_id)
            .where(AffectationVerification.dossier_verification_id==DossierVerification.id,or_(AffectationVerification.statut.is_(None),func.upper(AffectationVerification.statut)=="ACTIF"))
            .correlate(DossierVerification).scalar_subquery())
        docs=(select(func.count(Document.id)).where(Document.ressource_type=="FICHE_COLLECTE",Document.ressource_id==FicheCollecte.id,or_(Document.statut.is_(None),func.upper(Document.statut)=="ACTIF")).correlate(FicheCollecte).scalar_subquery())
        return (select(
            DossierVerification,
            FicheCollecte.mission_id.label("mission_id"),FicheCollecte.entreprise_id.label("entreprise_id"),FicheCollecte.statut.label("fiche_status"),FicheCollecte.numero_revision.label("fiche_revision"),FicheCollecte.taux_completude.label("completeness"),FicheCollecte.soumise_at.label("submitted_at"),
            MissionCollecte.code.label("mission_code"),Campagne.code.label("campaign_code"),Campagne.nom.label("campaign_name"),ZoneAdministrative.nom.label("zone_name"),
            Entreprise.identifiant_national.label("entreprise_identifiant"),Entreprise.raison_sociale.label("entreprise_name"),Entreprise.nom_commercial.label("entreprise_trade_name"),
            points.label("points_count"),anomalies.label("anomalies_count"),unresolved.label("unresolved_anomalies_count"),pending.label("confirmations_pending_count"),assignments.label("assignments_count"),assigned_names.label("assigned_names"),docs.label("documents_count")
        ).select_from(DossierVerification)
         .join(FicheCollecte,FicheCollecte.id==DossierVerification.fiche_collecte_id)
         .join(MissionCollecte,MissionCollecte.id==FicheCollecte.mission_id)
         .join(Campagne,Campagne.id==MissionCollecte.campagne_id)
         .join(ZoneAdministrative,ZoneAdministrative.id==MissionCollecte.zone_id)
         .outerjoin(Entreprise,Entreprise.id==FicheCollecte.entreprise_id))

    @staticmethod
    async def workspace_registry(db: AsyncSession, *,search,statut,avis,priorite,verificateur_id,sort,limit,offset):
        f=VerificationRepository.workspace_filters_sql(search=search,statut=statut,avis=avis,priorite=priorite,verificateur_id=verificateur_id)
        order={"recent":DossierVerification.created_at.desc(),"priority":DossierVerification.priorite.asc().nullslast(),"company":Entreprise.raison_sociale.asc().nullslast(),"status":DossierVerification.statut.asc().nullslast()}.get(sort,DossierVerification.date_ouverture.desc().nullslast())
        r=await db.execute(VerificationRepository.workspace_base().where(*f).order_by(order,DossierVerification.created_at.desc()).limit(limit).offset(offset))
        base=(select(DossierVerification.id).select_from(DossierVerification).join(FicheCollecte,FicheCollecte.id==DossierVerification.fiche_collecte_id).join(MissionCollecte,MissionCollecte.id==FicheCollecte.mission_id).join(Campagne,Campagne.id==MissionCollecte.campagne_id).join(ZoneAdministrative,ZoneAdministrative.id==MissionCollecte.zone_id).outerjoin(Entreprise,Entreprise.id==FicheCollecte.entreprise_id).where(*f).subquery())
        cr=await db.execute(select(func.count(base.c.id)))
        return r.all(),int(cr.scalar_one() or 0)

    @staticmethod
    async def workspace_summary(db: AsyncSession, *,search,statut,avis,priorite,verificateur_id):
        f=VerificationRepository.workspace_filters_sql(search=search,statut=statut,avis=avis,priorite=priorite,verificateur_id=verificateur_id)
        def q(extra=None):
            stmt=(select(func.count(DossierVerification.id)).select_from(DossierVerification).join(FicheCollecte,FicheCollecte.id==DossierVerification.fiche_collecte_id).join(MissionCollecte,MissionCollecte.id==FicheCollecte.mission_id).join(Campagne,Campagne.id==MissionCollecte.campagne_id).join(ZoneAdministrative,ZoneAdministrative.id==MissionCollecte.zone_id).outerjoin(Entreprise,Entreprise.id==FicheCollecte.entreprise_id).where(*f))
            return stmt.where(extra) if extra is not None else stmt
        unresolved=select(AnomalieVerification.id).where(AnomalieVerification.dossier_verification_id==DossierVerification.id,AnomalieVerification.date_resolution.is_(None)).exists()
        pending=select(ConfirmationExterne.id).where(ConfirmationExterne.dossier_verification_id==DossierVerification.id,ConfirmationExterne.date_reponse.is_(None)).exists()
        assigned=select(AffectationVerification.id).where(AffectationVerification.dossier_verification_id==DossierVerification.id,or_(AffectationVerification.statut.is_(None),func.upper(AffectationVerification.statut)=="ACTIF")).exists()
        vals=[]
        for stmt in [q(),q(DossierVerification.date_fin.is_(None)),q(DossierVerification.date_fin.is_not(None)),q(~assigned),q(unresolved),q(pending)]:
            rr=await db.execute(stmt); vals.append(int(rr.scalar_one() or 0))
        return {"total":vals[0],"open":vals[1],"finished":vals[2],"unassigned":vals[3],"with_unresolved_anomalies":vals[4],"with_pending_confirmations":vals[5]}

    @staticmethod
    async def workspace_item(db: AsyncSession,dossier_id: UUID):
        r=await db.execute(VerificationRepository.workspace_base().where(DossierVerification.id==dossier_id))
        return r.one_or_none()

    @staticmethod
    async def eligible_fiches(db: AsyncSession, *,search,limit,offset):
        exists=select(DossierVerification.id).where(DossierVerification.fiche_collecte_id==FicheCollecte.id).exists()
        f=[func.upper(FicheCollecte.statut)=="SOUMISE",~exists]
        if search and search.strip():
            p=f"%{search.strip()}%"; f.append(or_(MissionCollecte.code.ilike(p),Campagne.code.ilike(p),Campagne.nom.ilike(p),ZoneAdministrative.nom.ilike(p),Entreprise.identifiant_national.ilike(p),Entreprise.raison_sociale.ilike(p),Entreprise.nom_commercial.ilike(p)))
        base=(select(FicheCollecte.id.label("fiche_id"),FicheCollecte.mission_id.label("mission_id"),FicheCollecte.entreprise_id.label("entreprise_id"),FicheCollecte.numero_revision.label("fiche_revision"),FicheCollecte.taux_completude.label("completeness"),FicheCollecte.soumise_at.label("submitted_at"),MissionCollecte.code.label("mission_code"),Campagne.code.label("campaign_code"),Campagne.nom.label("campaign_name"),ZoneAdministrative.nom.label("zone_name"),Entreprise.identifiant_national.label("entreprise_identifiant"),Entreprise.raison_sociale.label("entreprise_name"),Entreprise.nom_commercial.label("entreprise_trade_name"))
            .select_from(FicheCollecte).join(MissionCollecte,MissionCollecte.id==FicheCollecte.mission_id).join(Campagne,Campagne.id==MissionCollecte.campagne_id).join(ZoneAdministrative,ZoneAdministrative.id==MissionCollecte.zone_id).outerjoin(Entreprise,Entreprise.id==FicheCollecte.entreprise_id).where(*f))
        r=await db.execute(base.order_by(FicheCollecte.soumise_at.asc().nullslast()).limit(limit).offset(offset))
        cr=await db.execute(base.with_only_columns(func.count(FicheCollecte.id)).order_by(None))
        return r.all(),int(cr.scalar_one() or 0)

    @staticmethod
    async def get_fiche(db: AsyncSession, fiche_id: UUID):
        r = await db.execute(select(FicheCollecte).where(FicheCollecte.id == fiche_id))
        return r.scalar_one_or_none()

    @staticmethod
    async def get_dossier(db: AsyncSession, dossier_id: UUID):
        r = await db.execute(select(DossierVerification).where(DossierVerification.id == dossier_id))
        return r.scalar_one_or_none()

    @staticmethod
    async def find_open_for_fiche(db: AsyncSession, fiche_id: UUID):
        r = await db.execute(
            select(DossierVerification)
            .where(DossierVerification.fiche_collecte_id == fiche_id,
                   DossierVerification.date_fin.is_(None))
            .order_by(DossierVerification.created_at.desc()).limit(1)
        )
        return r.scalar_one_or_none()

    @staticmethod
    async def list_dossiers(db: AsyncSession, *, statut, avis, priorite, verificateur_id, limit, offset):
        filters = []
        if statut: filters.append(DossierVerification.statut == statut.strip())
        if avis: filters.append(DossierVerification.avis == avis.strip())
        if priorite: filters.append(DossierVerification.priorite == priorite.strip())
        q = select(DossierVerification)
        cq = select(func.count(func.distinct(DossierVerification.id))).select_from(DossierVerification)
        if verificateur_id:
            q = q.join(AffectationVerification, AffectationVerification.dossier_verification_id == DossierVerification.id)
            cq = cq.join(AffectationVerification, AffectationVerification.dossier_verification_id == DossierVerification.id)
            filters += [
                AffectationVerification.verificateur_id == verificateur_id,
                or_(AffectationVerification.statut.is_(None), AffectationVerification.statut == "ACTIF"),
            ]
        r = await db.execute(q.where(*filters).distinct().order_by(DossierVerification.created_at.desc()).limit(limit).offset(offset))
        c = await db.execute(cq.where(*filters))
        return list(r.scalars().all()), int(c.scalar_one())

    @staticmethod
    async def counts(db: AsyncSession, dossier_id: UUID):
        async def count(model, *filters):
            r = await db.execute(select(func.count(model.id)).where(*filters))
            return int(r.scalar_one())
        return (
            await count(PointVerification, PointVerification.dossier_verification_id == dossier_id),
            await count(AnomalieVerification, AnomalieVerification.dossier_verification_id == dossier_id),
            await count(ConfirmationExterne,
                        ConfirmationExterne.dossier_verification_id == dossier_id,
                        ConfirmationExterne.date_reponse.is_(None)),
            await count(AffectationVerification, AffectationVerification.dossier_verification_id == dossier_id),
        )

    @staticmethod
    async def unresolved_anomaly_count(db: AsyncSession, dossier_id: UUID):
        r = await db.execute(select(func.count(AnomalieVerification.id)).where(
            AnomalieVerification.dossier_verification_id == dossier_id,
            AnomalieVerification.date_resolution.is_(None),
        ))
        return int(r.scalar_one())

    @staticmethod
    async def get_user(db, user_id):
        r = await db.execute(select(Utilisateur).where(Utilisateur.id == user_id))
        return r.scalar_one_or_none()

    @staticmethod
    async def list_assignments(db, dossier_id):
        r = await db.execute(select(AffectationVerification).where(
            AffectationVerification.dossier_verification_id == dossier_id
        ).order_by(AffectationVerification.created_at.desc()))
        return list(r.scalars().all())

    @staticmethod
    async def get_assignment(db, *, dossier_id, assignment_id):
        r = await db.execute(select(AffectationVerification).where(
            AffectationVerification.id == assignment_id,
            AffectationVerification.dossier_verification_id == dossier_id))
        return r.scalar_one_or_none()

    @staticmethod
    async def active_assignment(db, *, dossier_id, verifier_id):
        r = await db.execute(select(AffectationVerification).where(
            AffectationVerification.dossier_verification_id == dossier_id,
            AffectationVerification.verificateur_id == verifier_id,
            or_(AffectationVerification.statut.is_(None), AffectationVerification.statut == "ACTIF")))
        return r.scalar_one_or_none()

    @staticmethod
    async def list_points(db, dossier_id):
        r = await db.execute(select(PointVerification).where(
            PointVerification.dossier_verification_id == dossier_id
        ).order_by(PointVerification.categorie, PointVerification.code))
        return list(r.scalars().all())

    @staticmethod
    async def get_point(db, *, dossier_id, point_id):
        r = await db.execute(select(PointVerification).where(
            PointVerification.id == point_id,
            PointVerification.dossier_verification_id == dossier_id))
        return r.scalar_one_or_none()

    @staticmethod
    async def get_point_by_code(db, *, dossier_id, code):
        r = await db.execute(select(PointVerification).where(
            PointVerification.dossier_verification_id == dossier_id,
            PointVerification.code == code))
        return r.scalar_one_or_none()

    @staticmethod
    async def list_anomalies(db, dossier_id):
        r = await db.execute(select(AnomalieVerification).where(
            AnomalieVerification.dossier_verification_id == dossier_id
        ).order_by(AnomalieVerification.created_at.desc()))
        return list(r.scalars().all())

    @staticmethod
    async def get_anomaly(db, *, dossier_id, anomaly_id):
        r = await db.execute(select(AnomalieVerification).where(
            AnomalieVerification.id == anomaly_id,
            AnomalieVerification.dossier_verification_id == dossier_id))
        return r.scalar_one_or_none()

    @staticmethod
    async def list_confirmations(db, dossier_id):
        r = await db.execute(select(ConfirmationExterne).where(
            ConfirmationExterne.dossier_verification_id == dossier_id
        ).order_by(ConfirmationExterne.created_at.desc()))
        return list(r.scalars().all())

    @staticmethod
    async def get_confirmation(db, *, dossier_id, confirmation_id):
        r = await db.execute(select(ConfirmationExterne).where(
            ConfirmationExterne.id == confirmation_id,
            ConfirmationExterne.dossier_verification_id == dossier_id))
        return r.scalar_one_or_none()

    @staticmethod
    async def get_organisme(db, organisme_id):
        r = await db.execute(select(Organisme).where(Organisme.id == organisme_id))
        return r.scalar_one_or_none()

    @staticmethod
    async def get_active_document(db, document_id):
        r = await db.execute(select(Document).where(
            Document.id == document_id,
            or_(Document.statut.is_(None), Document.statut == "ACTIF")))
        return r.scalar_one_or_none()
