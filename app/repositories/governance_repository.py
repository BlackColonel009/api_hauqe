"""
Repository PostgreSQL — Gouvernance / Qualité / Continuité.

Le repository conserve les accès aux dix tables du lot.
Les transitions, permissions et règles restent dans le service.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.archive import Archive
from app.models.decision_institutionnelle import DecisionInstitutionnelle
from app.models.document import Document
from app.models.audit import EvenementAudit
from app.models.incident import Incident
from app.models.plan_action import PlanAction
from app.models.publication import Publication
from app.models.rapport_genere import RapportGenere
from app.models.regle_metier import RegleMetier
from app.models.revue_qualite import RevueQualite
from app.models.sauvegarde import Sauvegarde
from app.models.utilisateur import Utilisateur


class GovernanceRepository:

    # ========================================================
    # COMMUN
    # ========================================================

    @staticmethod
    async def get_user(db: AsyncSession, user_id: UUID) -> Utilisateur | None:
        result = await db.execute(
            select(Utilisateur).where(Utilisateur.id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_active_document(
        db: AsyncSession,
        document_id: UUID,
    ) -> Document | None:
        result = await db.execute(
            select(Document).where(
                Document.id == document_id,
                or_(Document.statut.is_(None), Document.statut == "ACTIF"),
            )
        )
        return result.scalar_one_or_none()

    # ========================================================
    # RÈGLES MÉTIER
    # ========================================================

    @staticmethod
    async def get_rule(db: AsyncSession, rule_id: UUID) -> RegleMetier | None:
        result = await db.execute(
            select(RegleMetier).where(RegleMetier.id == rule_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_rules(
        db: AsyncSession,
        *,
        logical_code: str | None,
        famille: str | None,
        statut: str | None,
    ) -> list[RegleMetier]:
        filters = []
        if famille:
            filters.append(RegleMetier.famille == famille.strip().upper())
        if statut:
            filters.append(RegleMetier.statut == statut.strip().upper())

        result = await db.execute(
            select(RegleMetier)
            .where(*filters)
            .order_by(
                RegleMetier.date_debut_effet.desc().nullslast(),
                RegleMetier.created_at.desc(),
            )
        )
        rows = list(result.scalars().all())

        if logical_code:
            logical_code = logical_code.strip().upper()
            rows = [
                row for row in rows
                if (
                    row.code == logical_code
                    or (
                        isinstance(row.parametres, dict)
                        and str(
                            row.parametres.get("_logical_code", "")
                        ).strip().upper() == logical_code
                    )
                )
            ]
        return rows

    @staticmethod
    async def published_rules(db: AsyncSession) -> list[RegleMetier]:
        result = await db.execute(
            select(RegleMetier)
            .where(RegleMetier.statut == "PUBLIE")
            .order_by(
                RegleMetier.date_debut_effet.desc().nullslast(),
                RegleMetier.created_at.desc(),
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def find_physical_rule_code(
        db: AsyncSession,
        physical_code: str,
    ) -> RegleMetier | None:
        result = await db.execute(
            select(RegleMetier).where(RegleMetier.code == physical_code)
        )
        return result.scalar_one_or_none()

    # ========================================================
    # REVUES QUALITÉ / PLANS
    # ========================================================

    @staticmethod
    async def get_quality_review(
        db: AsyncSession,
        review_id: UUID,
    ) -> RevueQualite | None:
        result = await db.execute(
            select(RevueQualite).where(RevueQualite.id == review_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_quality_reviews(
        db: AsyncSession,
        *,
        statut: str | None,
        responsable_id: UUID | None,
        limit: int,
        offset: int,
    ) -> tuple[list[RevueQualite], int]:
        filters = []
        if statut:
            filters.append(RevueQualite.statut == statut.strip().upper())
        if responsable_id:
            filters.append(RevueQualite.responsable_id == responsable_id)

        result = await db.execute(
            select(RevueQualite)
            .where(*filters)
            .order_by(RevueQualite.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        count = await db.execute(
            select(func.count(RevueQualite.id)).where(*filters)
        )
        return list(result.scalars().all()), int(count.scalar_one())

    @staticmethod
    async def action_plan_count_for_review(
        db: AsyncSession,
        review_id: UUID,
    ) -> int:
        result = await db.execute(
            select(func.count(PlanAction.id)).where(
                PlanAction.revue_qualite_id == review_id
            )
        )
        return int(result.scalar_one())

    @staticmethod
    async def get_action_plan(
        db: AsyncSession,
        plan_id: UUID,
    ) -> PlanAction | None:
        result = await db.execute(
            select(PlanAction).where(PlanAction.id == plan_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_action_plans(
        db: AsyncSession,
        *,
        review_id: UUID | None,
        responsable_id: UUID | None,
        statut: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[PlanAction], int]:
        filters = []
        if review_id:
            filters.append(PlanAction.revue_qualite_id == review_id)
        if responsable_id:
            filters.append(PlanAction.responsable_id == responsable_id)
        if statut:
            filters.append(PlanAction.statut == statut.strip().upper())

        result = await db.execute(
            select(PlanAction)
            .where(*filters)
            .order_by(
                PlanAction.date_echeance.asc().nullslast(),
                PlanAction.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        count = await db.execute(
            select(func.count(PlanAction.id)).where(*filters)
        )
        return list(result.scalars().all()), int(count.scalar_one())

    # ========================================================
    # DÉCISIONS
    # ========================================================

    @staticmethod
    async def get_decision(
        db: AsyncSession,
        decision_id: UUID,
    ) -> DecisionInstitutionnelle | None:
        result = await db.execute(
            select(DecisionInstitutionnelle).where(
                DecisionInstitutionnelle.id == decision_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_decisions(
        db: AsyncSession,
        *,
        ressource_type: str | None,
        ressource_id: UUID | None,
        statut: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[DecisionInstitutionnelle], int]:
        filters = []
        if ressource_type:
            filters.append(
                DecisionInstitutionnelle.ressource_type
                == ressource_type.strip().upper()
            )
        if ressource_id:
            filters.append(
                DecisionInstitutionnelle.ressource_id == ressource_id
            )
        if statut:
            filters.append(
                DecisionInstitutionnelle.statut == statut.strip().upper()
            )

        result = await db.execute(
            select(DecisionInstitutionnelle)
            .where(*filters)
            .order_by(
                DecisionInstitutionnelle.date_decision.desc().nullslast(),
                DecisionInstitutionnelle.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        count = await db.execute(
            select(func.count(DecisionInstitutionnelle.id)).where(*filters)
        )
        return list(result.scalars().all()), int(count.scalar_one())

    # ========================================================
    # PUBLICATIONS
    # ========================================================

    @staticmethod
    async def get_publication(
        db: AsyncSession,
        publication_id: UUID,
    ) -> Publication | None:
        result = await db.execute(
            select(Publication).where(Publication.id == publication_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_publications(
        db: AsyncSession,
        *,
        statut: str | None,
        niveau_confidentialite: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Publication], int]:
        filters = []
        if statut:
            filters.append(Publication.statut == statut.strip().upper())
        if niveau_confidentialite:
            filters.append(
                Publication.niveau_confidentialite
                == niveau_confidentialite.strip().upper()
            )

        result = await db.execute(
            select(Publication)
            .where(*filters)
            .order_by(
                Publication.date_publication.desc().nullslast(),
                Publication.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        count = await db.execute(
            select(func.count(Publication.id)).where(*filters)
        )
        return list(result.scalars().all()), int(count.scalar_one())

    # ========================================================
    # RAPPORTS
    # ========================================================

    @staticmethod
    async def get_generated_report(
        db: AsyncSession,
        report_id: UUID,
    ) -> RapportGenere | None:
        result = await db.execute(
            select(RapportGenere).where(RapportGenere.id == report_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_generated_reports(
        db: AsyncSession,
        *,
        categorie: str | None,
        statut: str | None,
        demandeur_id: UUID | None,
        limit: int,
        offset: int,
    ) -> tuple[list[RapportGenere], int]:
        filters = []
        if categorie:
            filters.append(RapportGenere.categorie == categorie.strip().upper())
        if statut:
            filters.append(RapportGenere.statut == statut.strip().upper())
        if demandeur_id:
            filters.append(RapportGenere.demandeur_id == demandeur_id)

        result = await db.execute(
            select(RapportGenere)
            .where(*filters)
            .order_by(RapportGenere.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        count = await db.execute(
            select(func.count(RapportGenere.id)).where(*filters)
        )
        return list(result.scalars().all()), int(count.scalar_one())

    # ========================================================
    # AUDIT — LECTURE SEULE
    # ========================================================

    @staticmethod
    async def get_audit_event(
        db: AsyncSession,
        event_id: UUID,
    ) -> EvenementAudit | None:
        result = await db.execute(
            select(EvenementAudit).where(EvenementAudit.id == event_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_audit_events(
        db: AsyncSession,
        *,
        utilisateur_id: UUID | None,
        action: str | None,
        categorie: str | None,
        ressource_type: str | None,
        ressource_id: UUID | None,
        resultat: str | None,
        start_at: datetime | None,
        end_at: datetime | None,
        limit: int,
        offset: int,
    ) -> tuple[list[EvenementAudit], int]:
        filters = []
        if utilisateur_id:
            filters.append(EvenementAudit.utilisateur_id == utilisateur_id)
        if action:
            filters.append(EvenementAudit.action == action.strip().upper())
        if categorie:
            filters.append(EvenementAudit.categorie == categorie.strip().upper())
        if ressource_type:
            filters.append(
                EvenementAudit.ressource_type == ressource_type.strip()
            )
        if ressource_id:
            filters.append(EvenementAudit.ressource_id == ressource_id)
        if resultat:
            filters.append(EvenementAudit.resultat == resultat)
        if start_at:
            filters.append(EvenementAudit.date_evenement >= start_at)
        if end_at:
            filters.append(EvenementAudit.date_evenement <= end_at)

        query = (
            select(EvenementAudit)
            .where(*filters)
            .order_by(
                EvenementAudit.date_evenement.desc().nullslast(),
                EvenementAudit.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(query)
        count = await db.execute(
            select(func.count(EvenementAudit.id)).where(*filters)
        )
        return list(result.scalars().all()), int(count.scalar_one())

    # ========================================================
    # ARCHIVES
    # ========================================================

    @staticmethod
    async def get_archive(
        db: AsyncSession,
        archive_id: UUID,
    ) -> Archive | None:
        result = await db.execute(
            select(Archive).where(Archive.id == archive_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_archives(
        db: AsyncSession,
        *,
        ressource_type: str | None,
        ressource_id: UUID | None,
        statut: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Archive], int]:
        filters = []
        if ressource_type:
            filters.append(Archive.ressource_type == ressource_type.strip().upper())
        if ressource_id:
            filters.append(Archive.ressource_id == ressource_id)
        if statut:
            filters.append(Archive.statut == statut.strip().upper())

        result = await db.execute(
            select(Archive)
            .where(*filters)
            .order_by(Archive.date_archivage.desc().nullslast())
            .limit(limit)
            .offset(offset)
        )
        count = await db.execute(
            select(func.count(Archive.id)).where(*filters)
        )
        return list(result.scalars().all()), int(count.scalar_one())

    @staticmethod
    async def active_archive_for_resource(
        db: AsyncSession,
        *,
        ressource_type: str,
        ressource_id: UUID,
    ) -> Archive | None:
        result = await db.execute(
            select(Archive)
            .where(
                Archive.ressource_type == ressource_type,
                Archive.ressource_id == ressource_id,
                Archive.statut == "ARCHIVE",
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    # ========================================================
    # SAUVEGARDES
    # ========================================================

    @staticmethod
    async def get_backup(
        db: AsyncSession,
        backup_id: UUID,
    ) -> Sauvegarde | None:
        result = await db.execute(
            select(Sauvegarde).where(Sauvegarde.id == backup_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_backups(
        db: AsyncSession,
        *,
        type_enregistrement: str | None,
        statut: str | None,
        parent_id: UUID | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Sauvegarde], int]:
        filters = []
        if type_enregistrement:
            filters.append(
                Sauvegarde.type_enregistrement
                == type_enregistrement.strip().upper()
            )
        if statut:
            filters.append(Sauvegarde.statut == statut.strip().upper())
        if parent_id:
            filters.append(Sauvegarde.parent_id == parent_id)

        result = await db.execute(
            select(Sauvegarde)
            .where(*filters)
            .order_by(Sauvegarde.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        count = await db.execute(
            select(func.count(Sauvegarde.id)).where(*filters)
        )
        return list(result.scalars().all()), int(count.scalar_one())

    # ========================================================
    # INCIDENTS
    # ========================================================

    @staticmethod
    async def get_incident(
        db: AsyncSession,
        incident_id: UUID,
    ) -> Incident | None:
        result = await db.execute(
            select(Incident).where(Incident.id == incident_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def incident_code_exists(
        db: AsyncSession,
        code: str,
    ) -> bool:
        result = await db.execute(
            select(Incident.id).where(Incident.code == code).limit(1)
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def list_incidents(
        db: AsyncSession,
        *,
        categorie: str | None,
        gravite: str | None,
        responsable_id: UUID | None,
        statut: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Incident], int]:
        filters = []
        if categorie:
            filters.append(Incident.categorie == categorie.strip().upper())
        if gravite:
            filters.append(Incident.gravite == gravite.strip().upper())
        if responsable_id:
            filters.append(Incident.responsable_id == responsable_id)
        if statut:
            filters.append(Incident.statut == statut.strip().upper())

        result = await db.execute(
            select(Incident)
            .where(*filters)
            .order_by(
                Incident.date_declaration.desc().nullslast(),
                Incident.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        count = await db.execute(
            select(func.count(Incident.id)).where(*filters)
        )
        return list(result.scalars().all()), int(count.scalar_one())

    # ========================================================
    # DASHBOARD
    # ========================================================

    @staticmethod
    async def dashboard_counts(db: AsyncSession) -> tuple[int, int, int, int, int, int]:
        draft_rules = await db.execute(
            select(func.count(RegleMetier.id)).where(
                RegleMetier.statut == "BROUILLON"
            )
        )
        open_plans = await db.execute(
            select(func.count(PlanAction.id)).where(
                PlanAction.date_cloture.is_(None)
            )
        )
        open_incidents = await db.execute(
            select(func.count(Incident.id)).where(
                Incident.date_cloture.is_(None)
            )
        )
        pending_publications = await db.execute(
            select(func.count(Publication.id)).where(
                Publication.statut.in_(["BROUILLON", "SOUMISE", "APPROUVEE"])
            )
        )
        pending_reports = await db.execute(
            select(func.count(RapportGenere.id)).where(
                RapportGenere.statut.in_(["DEMANDE", "EN_GENERATION"])
            )
        )
        failed_backups = await db.execute(
            select(func.count(Sauvegarde.id)).where(
                Sauvegarde.statut == "ECHEC"
            )
        )

        return (
            int(draft_rules.scalar_one()),
            int(open_plans.scalar_one()),
            int(open_incidents.scalar_one()),
            int(pending_publications.scalar_one()),
            int(pending_reports.scalar_one()),
            int(failed_backups.scalar_one()),
        )
