"""Repository PostgreSQL du domaine Vérification."""
from __future__ import annotations
from uuid import UUID
from sqlalchemy import func, or_, select
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

class VerificationRepository:
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
