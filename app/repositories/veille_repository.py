"""
Repository PostgreSQL — Échéances / Alertes / Notifications / Veille.

Le repository ne décide pas des seuils métier.
Il expose les lectures/écritures nécessaires au service :
- déduplication des échéances et alertes actives ;
- accès aux certifications, audits et renouvellements ;
- files de notifications ;
- dossiers CVC et relances ;
- agrégats pour les rapports de veille.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alerte import Alerte
from app.models.audit_certification import AuditCertification
from app.models.certification import Certification
from app.models.dossier_veille import DossierVeille
from app.models.echeance import Echeance
from app.models.notification import Notification
from app.models.rapport_veille import RapportVeille
from app.models.regle_metier import RegleMetier
from app.models.relance_veille import RelanceVeille
from app.models.renouvellement_certification import RenouvellementCertification
from app.models.utilisateur import Utilisateur


ACTIVE_DEADLINE_STATUSES = {"PLANIFIEE", "EN_COURS"}
ACTIVE_ALERT_STATUSES = {"NOUVELLE", "AFFECTEE", "EN_COURS"}


class WatchRepository:

    # ========================================================
    # UTILISATEURS / RÈGLES
    # ========================================================

    @staticmethod
    async def get_user(
        db: AsyncSession,
        user_id: UUID,
    ) -> Utilisateur | None:
        result = await db.execute(
            select(Utilisateur).where(Utilisateur.id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def active_alert_rule(
        db: AsyncSession,
        code: str,
    ) -> RegleMetier | None:
        today = date.today()
        result = await db.execute(
            select(RegleMetier)
            .where(
                RegleMetier.code == code,
                RegleMetier.statut == "PUBLIE",
                or_(
                    RegleMetier.date_debut_effet.is_(None),
                    RegleMetier.date_debut_effet <= today,
                ),
                or_(
                    RegleMetier.date_fin_effet.is_(None),
                    RegleMetier.date_fin_effet >= today,
                ),
            )
            .order_by(
                RegleMetier.date_debut_effet.desc().nullslast(),
                RegleMetier.created_at.desc(),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    # ========================================================
    # ÉCHÉANCES
    # ========================================================

    @staticmethod
    async def get_deadline(
        db: AsyncSession,
        deadline_id: UUID,
    ) -> Echeance | None:
        result = await db.execute(
            select(Echeance).where(Echeance.id == deadline_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_deadlines(
        db: AsyncSession,
        *,
        ressource_type: str | None,
        ressource_id: UUID | None,
        type_echeance: str | None,
        responsable_id: UUID | None,
        statut: str | None,
        start_date: date | None,
        end_date: date | None,
        overdue_only: bool,
        limit: int,
        offset: int,
    ) -> tuple[list[Echeance], int]:
        filters = []

        if ressource_type:
            filters.append(
                Echeance.ressource_type == ressource_type.strip().upper()
            )
        if ressource_id:
            filters.append(Echeance.ressource_id == ressource_id)
        if type_echeance:
            filters.append(
                Echeance.type_echeance == type_echeance.strip().upper()
            )
        if responsable_id:
            filters.append(Echeance.responsable_id == responsable_id)
        if statut:
            filters.append(Echeance.statut == statut.strip().upper())
        if start_date:
            filters.append(Echeance.date_echeance >= start_date)
        if end_date:
            filters.append(Echeance.date_echeance <= end_date)
        if overdue_only:
            filters.append(Echeance.date_echeance < date.today())
            filters.append(Echeance.statut.in_(list(ACTIVE_DEADLINE_STATUSES)))

        result = await db.execute(
            select(Echeance)
            .where(*filters)
            .order_by(
                Echeance.date_echeance.asc().nullslast(),
                Echeance.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        count = await db.execute(
            select(func.count(Echeance.id)).where(*filters)
        )
        return list(result.scalars().all()), int(count.scalar_one())

    @staticmethod
    async def find_active_deadline(
        db: AsyncSession,
        *,
        ressource_type: str,
        ressource_id: UUID,
        type_echeance: str,
        due_date: date,
    ) -> Echeance | None:
        result = await db.execute(
            select(Echeance)
            .where(
                Echeance.ressource_type == ressource_type,
                Echeance.ressource_id == ressource_id,
                Echeance.type_echeance == type_echeance,
                Echeance.date_echeance == due_date,
                Echeance.statut.in_(list(ACTIVE_DEADLINE_STATUSES)),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def deadline_alert_count(
        db: AsyncSession,
        deadline_id: UUID,
    ) -> int:
        result = await db.execute(
            select(func.count(Alerte.id)).where(
                Alerte.echeance_id == deadline_id,
                Alerte.statut.in_(list(ACTIVE_ALERT_STATUSES)),
            )
        )
        return int(result.scalar_one())

    @staticmethod
    async def list_deadline_alerts(
        db: AsyncSession,
        deadline_id: UUID,
    ) -> list[Alerte]:
        result = await db.execute(
            select(Alerte)
            .where(Alerte.echeance_id == deadline_id)
            .order_by(Alerte.date_detection.desc().nullslast())
        )
        return list(result.scalars().all())

    # ========================================================
    # ALERTES
    # ========================================================

    @staticmethod
    async def get_alert(
        db: AsyncSession,
        alert_id: UUID,
    ) -> Alerte | None:
        result = await db.execute(
            select(Alerte).where(Alerte.id == alert_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_alerts(
        db: AsyncSession,
        *,
        type_alerte: str | None,
        niveau: int | None,
        responsable_id: UUID | None,
        statut: str | None,
        ressource_type: str | None,
        ressource_id: UUID | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Alerte], int]:
        filters = []

        if type_alerte:
            filters.append(Alerte.type_alerte == type_alerte.strip().upper())
        if niveau is not None:
            filters.append(Alerte.niveau == niveau)
        if responsable_id:
            filters.append(Alerte.responsable_id == responsable_id)
        if statut:
            filters.append(Alerte.statut == statut.strip().upper())
        if ressource_type:
            filters.append(
                Alerte.ressource_type == ressource_type.strip().upper()
            )
        if ressource_id:
            filters.append(Alerte.ressource_id == ressource_id)

        result = await db.execute(
            select(Alerte)
            .where(*filters)
            .order_by(
                Alerte.niveau.desc().nullslast(),
                Alerte.date_detection.desc().nullslast(),
                Alerte.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        count = await db.execute(
            select(func.count(Alerte.id)).where(*filters)
        )
        return list(result.scalars().all()), int(count.scalar_one())

    @staticmethod
    async def find_active_alert_for_rule(
        db: AsyncSession,
        *,
        deadline_id: UUID,
        rule_code: str,
    ) -> Alerte | None:
        result = await db.execute(
            select(Alerte)
            .where(
                Alerte.echeance_id == deadline_id,
                Alerte.regle_notification == rule_code,
                Alerte.statut.in_(list(ACTIVE_ALERT_STATUSES)),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def alert_notification_counts(
        db: AsyncSession,
        alert_id: UUID,
    ) -> tuple[int, int]:
        total = await db.execute(
            select(func.count(Notification.id)).where(
                Notification.alerte_id == alert_id
            )
        )
        unread = await db.execute(
            select(func.count(Notification.id)).where(
                Notification.alerte_id == alert_id,
                Notification.date_lecture.is_(None),
            )
        )
        return int(total.scalar_one()), int(unread.scalar_one())

    # ========================================================
    # NOTIFICATIONS
    # ========================================================

    @staticmethod
    async def get_notification(
        db: AsyncSession,
        notification_id: UUID,
    ) -> Notification | None:
        result = await db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_notifications(
        db: AsyncSession,
        *,
        current_user_id: UUID,
        statut: str | None,
        unread_only: bool,
        limit: int,
        offset: int,
    ) -> tuple[list[Notification], int, int]:
        filters = [
            Notification.destinataire_utilisateur_id == current_user_id
        ]
        if statut:
            filters.append(Notification.statut == statut.strip().upper())
        if unread_only:
            filters.append(Notification.date_lecture.is_(None))

        result = await db.execute(
            select(Notification)
            .where(*filters)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        count = await db.execute(
            select(func.count(Notification.id)).where(*filters)
        )
        unread_count = await db.execute(
            select(func.count(Notification.id)).where(
                Notification.destinataire_utilisateur_id == current_user_id,
                Notification.date_lecture.is_(None),
            )
        )
        return (
            list(result.scalars().all()),
            int(count.scalar_one()),
            int(unread_count.scalar_one()),
        )

    @staticmethod
    async def unread_notifications_for_user(
        db: AsyncSession,
        user_id: UUID,
    ) -> int:
        result = await db.execute(
            select(func.count(Notification.id)).where(
                Notification.destinataire_utilisateur_id == user_id,
                Notification.date_lecture.is_(None),
            )
        )
        return int(result.scalar_one())

    @staticmethod
    async def unread_notification_rows(
        db: AsyncSession,
        user_id: UUID,
    ) -> list[Notification]:
        result = await db.execute(
            select(Notification).where(
                Notification.destinataire_utilisateur_id == user_id,
                Notification.date_lecture.is_(None),
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def pending_email_notifications(
        db: AsyncSession,
        *,
        limit: int = 100,
    ) -> list[Notification]:
        result = await db.execute(
            select(Notification)
            .where(
                func.upper(Notification.canal) == "EMAIL",
                Notification.statut == "EN_ATTENTE",
            )
            .order_by(Notification.created_at)
            .limit(limit)
        )
        return list(result.scalars().all())

    # ========================================================
    # SOURCES POUR LE SCAN QUOTIDIEN
    # ========================================================

    @staticmethod
    async def certifications_with_expiration(
        db: AsyncSession,
    ) -> list[Certification]:
        result = await db.execute(
            select(Certification).where(
                Certification.date_expiration.is_not(None)
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def audits_with_due_date(
        db: AsyncSession,
    ) -> list[AuditCertification]:
        result = await db.execute(
            select(AuditCertification).where(
                AuditCertification.date_prevue.is_not(None)
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def renewals_with_due_date(
        db: AsyncSession,
    ) -> list[RenouvellementCertification]:
        result = await db.execute(
            select(RenouvellementCertification).where(
                RenouvellementCertification.date_limite.is_not(None)
            )
        )
        return list(result.scalars().all())

    # ========================================================
    # DOSSIERS DE VEILLE
    # ========================================================

    @staticmethod
    async def get_certification(
        db: AsyncSession,
        certification_id: UUID,
    ) -> Certification | None:
        result = await db.execute(
            select(Certification).where(
                Certification.id == certification_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_watch_case(
        db: AsyncSession,
        case_id: UUID,
    ) -> DossierVeille | None:
        result = await db.execute(
            select(DossierVeille).where(DossierVeille.id == case_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_watch_cases(
        db: AsyncSession,
        *,
        certification_id: UUID | None,
        responsable_id: UUID | None,
        statut: str | None,
        priorite: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[DossierVeille], int]:
        filters = []
        if certification_id:
            filters.append(DossierVeille.certification_id == certification_id)
        if responsable_id:
            filters.append(DossierVeille.responsable_id == responsable_id)
        if statut:
            filters.append(DossierVeille.statut == statut.strip().upper())
        if priorite:
            filters.append(DossierVeille.priorite == priorite.strip().upper())

        result = await db.execute(
            select(DossierVeille)
            .where(*filters)
            .order_by(
                DossierVeille.prochaine_action_at.asc().nullslast(),
                DossierVeille.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        count = await db.execute(
            select(func.count(DossierVeille.id)).where(*filters)
        )
        return list(result.scalars().all()), int(count.scalar_one())

    @staticmethod
    async def active_watch_case(
        db: AsyncSession,
        *,
        certification_id: UUID,
        event_type: str,
    ) -> DossierVeille | None:
        result = await db.execute(
            select(DossierVeille)
            .where(
                DossierVeille.certification_id == certification_id,
                DossierVeille.type_evenement == event_type,
                DossierVeille.date_cloture.is_(None),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def watch_case_followup_counts(
        db: AsyncSession,
        case_id: UUID,
    ) -> tuple[int, int]:
        total = await db.execute(
            select(func.count(RelanceVeille.id)).where(
                RelanceVeille.dossier_veille_id == case_id
            )
        )
        pending = await db.execute(
            select(func.count(RelanceVeille.id)).where(
                RelanceVeille.dossier_veille_id == case_id,
                RelanceVeille.date_reponse.is_(None),
            )
        )
        return int(total.scalar_one()), int(pending.scalar_one())

    # ========================================================
    # RELANCES
    # ========================================================

    @staticmethod
    async def list_followups(
        db: AsyncSession,
        case_id: UUID,
    ) -> list[RelanceVeille]:
        result = await db.execute(
            select(RelanceVeille)
            .where(RelanceVeille.dossier_veille_id == case_id)
            .order_by(RelanceVeille.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_followup(
        db: AsyncSession,
        *,
        case_id: UUID,
        followup_id: UUID,
    ) -> RelanceVeille | None:
        result = await db.execute(
            select(RelanceVeille).where(
                RelanceVeille.id == followup_id,
                RelanceVeille.dossier_veille_id == case_id,
            )
        )
        return result.scalar_one_or_none()

    # ========================================================
    # RAPPORTS
    # ========================================================

    @staticmethod
    async def get_watch_report(
        db: AsyncSession,
        report_id: UUID,
    ) -> RapportVeille | None:
        result = await db.execute(
            select(RapportVeille).where(RapportVeille.id == report_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_watch_reports(
        db: AsyncSession,
        *,
        type_rapport: str | None,
        statut: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[RapportVeille], int]:
        filters = []
        if type_rapport:
            filters.append(
                RapportVeille.type_rapport == type_rapport.strip().upper()
            )
        if statut:
            filters.append(RapportVeille.statut == statut.strip().upper())

        result = await db.execute(
            select(RapportVeille)
            .where(*filters)
            .order_by(RapportVeille.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        count = await db.execute(
            select(func.count(RapportVeille.id)).where(*filters)
        )
        return list(result.scalars().all()), int(count.scalar_one())

    @staticmethod
    async def watch_cases_in_period(
        db: AsyncSession,
        start: date,
        end: date,
    ) -> list[DossierVeille]:
        result = await db.execute(
            select(DossierVeille).where(
                DossierVeille.date_ouverture >= start,
                DossierVeille.date_ouverture <= end,
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def alerts_in_period(
        db: AsyncSession,
        start: date,
        end: date,
    ) -> list[Alerte]:
        result = await db.execute(
            select(Alerte).where(
                Alerte.date_detection >= start,
                Alerte.date_detection <= end,
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def renewals_in_period(
        db: AsyncSession,
        start: date,
        end: date,
    ) -> list[RenouvellementCertification]:
        result = await db.execute(
            select(RenouvellementCertification).where(
                RenouvellementCertification.date_ouverture >= start,
                RenouvellementCertification.date_ouverture <= end,
            )
        )
        return list(result.scalars().all())

    # ========================================================
    # DASHBOARD CVC
    # ========================================================

    @staticmethod
    async def dashboard_counts(
        db: AsyncSession,
        current_user_id: UUID,
    ) -> tuple[int, int, int, int, int, int]:
        open_cases = await db.execute(
            select(func.count(DossierVeille.id)).where(
                DossierVeille.date_cloture.is_(None)
            )
        )
        overdue = await db.execute(
            select(func.count(Echeance.id)).where(
                Echeance.date_echeance < date.today(),
                Echeance.statut.in_(list(ACTIVE_DEADLINE_STATUSES)),
            )
        )
        active_alerts = await db.execute(
            select(func.count(Alerte.id)).where(
                Alerte.statut.in_(list(ACTIVE_ALERT_STATUSES))
            )
        )
        critical_alerts = await db.execute(
            select(func.count(Alerte.id)).where(
                Alerte.niveau == 4,
                Alerte.statut.in_(list(ACTIVE_ALERT_STATUSES)),
            )
        )
        pending_followups = await db.execute(
            select(func.count(RelanceVeille.id)).where(
                RelanceVeille.date_reponse.is_(None)
            )
        )
        unread = await db.execute(
            select(func.count(Notification.id)).where(
                Notification.destinataire_utilisateur_id == current_user_id,
                Notification.date_lecture.is_(None),
            )
        )

        return (
            int(open_cases.scalar_one()),
            int(overdue.scalar_one()),
            int(active_alerts.scalar_one()),
            int(critical_alerts.scalar_one()),
            int(pending_followups.scalar_one()),
            int(unread.scalar_one()),
        )
