from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alerte import Alerte
from app.models.audit_certification import AuditCertification
from app.models.certification import Certification
from app.models.dossier_veille import DossierVeille
from app.models.echeance import Echeance
from app.models.entreprise import Entreprise
from app.models.norme import Norme
from app.models.organisme import Organisme
from app.models.rapport_veille import RapportVeille
from app.models.renouvellement_certification import RenouvellementCertification
from app.models.utilisateur import Utilisateur


class WatchWorkspaceRepository:
    @staticmethod
    async def distinct_values(db: AsyncSession, column):
        result = await db.execute(
            select(column)
            .where(column.is_not(None), func.trim(column) != "")
            .distinct()
            .order_by(column)
        )
        return [str(v).strip() for v in result.scalars().all() if v]

    @staticmethod
    async def active_users(db: AsyncSession, limit: int = 100):
        result = await db.execute(
            select(Utilisateur)
            .where(func.upper(func.coalesce(Utilisateur.statut, "")) == "ACTIF")
            .order_by(
                Utilisateur.nom.asc().nullslast(),
                Utilisateur.prenoms.asc().nullslast(),
            )
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def certifications(db: AsyncSession, limit: int = 100):
        result = await db.execute(
            select(
                Certification.id,
                Certification.identifiant_national,
                Certification.numero_certificat,
                Entreprise.raison_sociale,
                Entreprise.nom_commercial,
                Norme.code,
                Norme.nom,
            )
            .select_from(Certification)
            .join(Entreprise, Entreprise.id == Certification.entreprise_id)
            .join(Norme, Norme.id == Certification.norme_id)
            .order_by(
                Entreprise.raison_sociale.asc().nullslast(),
                Certification.identifiant_national.asc(),
            )
            .limit(limit)
        )
        return result.all()

    @staticmethod
    async def user_name(db: AsyncSession, user_id: UUID | None):
        if user_id is None:
            return None
        result = await db.execute(
            select(Utilisateur.prenoms, Utilisateur.nom, Utilisateur.email)
            .where(Utilisateur.id == user_id)
        )
        row = result.one_or_none()
        if row is None:
            return None
        return " ".join(
            p for p in (row.prenoms, row.nom) if p
        ).strip() or row.email

    @staticmethod
    async def resource_context(
        db: AsyncSession,
        *,
        resource_type: str | None,
        resource_id: UUID | None,
    ):
        if not resource_type or resource_id is None:
            return {"label": None, "subtitle": None, "route": None}

        code = resource_type.strip().upper()

        if code == "CERTIFICATION":
            result = await db.execute(
                select(
                    Certification.id,
                    Certification.identifiant_national,
                    Certification.numero_certificat,
                    Entreprise.raison_sociale,
                    Entreprise.nom_commercial,
                    Norme.code.label("standard_code"),
                )
                .select_from(Certification)
                .join(Entreprise, Entreprise.id == Certification.entreprise_id)
                .join(Norme, Norme.id == Certification.norme_id)
                .where(Certification.id == resource_id)
            )
            row = result.one_or_none()
            if row:
                company = row.raison_sociale or row.nom_commercial
                return {
                    "label": f"{company} · {row.identifiant_national}" if company else row.identifiant_national,
                    "subtitle": " · ".join(v for v in (row.numero_certificat, row.standard_code) if v) or None,
                    "route": f"#/certifications/{row.id}",
                }

        if code == "AUDIT_CERTIFICATION":
            result = await db.execute(
                select(
                    AuditCertification.id,
                    AuditCertification.type_audit,
                    Certification.id.label("certification_id"),
                    Certification.identifiant_national,
                    Entreprise.raison_sociale,
                    Entreprise.nom_commercial,
                )
                .select_from(AuditCertification)
                .join(Certification, Certification.id == AuditCertification.certification_id)
                .join(Entreprise, Entreprise.id == Certification.entreprise_id)
                .where(AuditCertification.id == resource_id)
            )
            row = result.one_or_none()
            if row:
                company = row.raison_sociale or row.nom_commercial
                return {
                    "label": f"{company} · {row.type_audit or 'Audit'}" if company else (row.type_audit or "Audit"),
                    "subtitle": row.identifiant_national,
                    "route": f"#/certifications/{row.certification_id}",
                }

        if code == "RENOUVELLEMENT_CERTIFICATION":
            result = await db.execute(
                select(
                    RenouvellementCertification.id,
                    Certification.id.label("certification_id"),
                    Certification.identifiant_national,
                    Entreprise.raison_sociale,
                    Entreprise.nom_commercial,
                )
                .select_from(RenouvellementCertification)
                .join(Certification, Certification.id == RenouvellementCertification.certification_id)
                .join(Entreprise, Entreprise.id == Certification.entreprise_id)
                .where(RenouvellementCertification.id == resource_id)
            )
            row = result.one_or_none()
            if row:
                company = row.raison_sociale or row.nom_commercial
                return {
                    "label": f"{company} · Renouvellement" if company else "Renouvellement",
                    "subtitle": row.identifiant_national,
                    "route": f"#/certifications/{row.certification_id}",
                }

        return {"label": f"{code} · {resource_id}", "subtitle": None, "route": None}

    @staticmethod
    async def deadline_summary(db: AsyncSession):
        today = date.today()
        active_filter = ~func.upper(func.coalesce(Echeance.statut, "")).in_(["TERMINEE", "ANNULEE"])

        async def count(*filters):
            value = await db.scalar(
                select(func.count(Echeance.id)).where(*filters)
            )
            return int(value or 0)

        return {
            "total": await count(),
            "active": await count(active_filter),
            "overdue": await count(Echeance.date_echeance < today, active_filter),
            "due_30": await count(Echeance.date_echeance.between(today, today + timedelta(days=30)), active_filter),
            "due_90": await count(Echeance.date_echeance.between(today, today + timedelta(days=90)), active_filter),
            "due_180": await count(Echeance.date_echeance.between(today, today + timedelta(days=180)), active_filter),
            "completed": await count(func.upper(func.coalesce(Echeance.statut, "")) == "TERMINEE"),
        }

    @staticmethod
    async def alert_summary(db: AsyncSession):
        async def count(*filters):
            value = await db.scalar(
                select(func.count(Alerte.id)).where(*filters)
            )
            return int(value or 0)

        active = func.upper(func.coalesce(Alerte.statut, "")) != "RESOLUE"
        return {
            "total": await count(),
            "active": await count(active),
            "level_1": await count(Alerte.niveau == 1, active),
            "level_2": await count(Alerte.niveau == 2, active),
            "level_3": await count(Alerte.niveau == 3, active),
            "level_4": await count(Alerte.niveau == 4, active),
            "resolved": await count(func.upper(func.coalesce(Alerte.statut, "")) == "RESOLUE"),
        }

    @staticmethod
    async def watch_case_context(db: AsyncSession, case_id: UUID):
        result = await db.execute(
            select(
                DossierVeille,
                Certification.identifiant_national,
                Certification.numero_certificat,
                Certification.date_expiration,
                Entreprise.raison_sociale,
                Entreprise.nom_commercial,
                Norme.code.label("standard_code"),
                Organisme.nom_officiel.label("organization_name"),
                Organisme.sigle.label("organization_acronym"),
                Utilisateur.prenoms.label("responsible_first_names"),
                Utilisateur.nom.label("responsible_last_name"),
                Utilisateur.email.label("responsible_email"),
            )
            .select_from(DossierVeille)
            .join(Certification, Certification.id == DossierVeille.certification_id)
            .join(Entreprise, Entreprise.id == Certification.entreprise_id)
            .join(Norme, Norme.id == Certification.norme_id)
            .join(Organisme, Organisme.id == Certification.organisme_id)
            .join(Utilisateur, Utilisateur.id == DossierVeille.responsable_id)
            .where(DossierVeille.id == case_id)
        )
        return result.one_or_none()
