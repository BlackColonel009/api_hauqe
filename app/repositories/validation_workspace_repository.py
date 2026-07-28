from __future__ import annotations

from uuid import UUID

from sqlalchemy import Integer, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campagne import Campagne
from app.models.controle_fuccs import ControleFuccs
from app.models.correction import Correction
from app.models.dossier_verification import DossierVerification
from app.models.entreprise import Entreprise
from app.models.fiche_collecte import FicheCollecte
from app.models.mission_collecte import MissionCollecte
from app.models.utilisateur import Utilisateur
from app.models.validation import Validation
from app.models.zone_administrative import ZoneAdministrative


FAVORABLE = {"VALIDE", "VALIDE_SOUS_RESERVE"}


class ValidationWorkspaceRepository:
    @staticmethod
    def latest_finalized_control_id():
        return (
            select(ControleFuccs.id)
            .join(
                DossierVerification,
                DossierVerification.id
                == ControleFuccs.dossier_verification_id,
            )
            .where(
                DossierVerification.fiche_collecte_id
                == FicheCollecte.id,
                ControleFuccs.statut == "FINALISE",
                ControleFuccs.date_fin.is_not(None),
            )
            .order_by(
                ControleFuccs.date_fin.desc(),
                ControleFuccs.created_at.desc(),
            )
            .limit(1)
            .correlate(FicheCollecte)
            .scalar_subquery()
        )

    @staticmethod
    def base_queue_query():
        latest_control_id = (
            ValidationWorkspaceRepository
            .latest_finalized_control_id()
        )

        return (
            select(
                FicheCollecte,
                MissionCollecte.id.label("mission_id"),
                MissionCollecte.code.label("mission_code"),
                Campagne.code.label("campaign_code"),
                Campagne.nom.label("campaign_name"),
                ZoneAdministrative.nom.label("zone_name"),
                Entreprise.identifiant_national.label(
                    "entreprise_identifiant"
                ),
                Entreprise.raison_sociale.label(
                    "entreprise_name"
                ),
                Entreprise.nom_commercial.label(
                    "entreprise_trade_name"
                ),
                DossierVerification.id.label("verification_id"),
                DossierVerification.avis.label(
                    "verification_opinion"
                ),
                DossierVerification.niveau_risque.label(
                    "verification_risk"
                ),
                ControleFuccs.id.label("control_id"),
                ControleFuccs.statut.label("control_status"),
                ControleFuccs.score_brut.label("control_score"),
                ControleFuccs.score_maximal.label(
                    "control_maximum"
                ),
                ControleFuccs.taux.label("control_rate"),
                ControleFuccs.date_fin.label("control_ended_on"),
                Utilisateur.prenoms.label(
                    "controller_first_names"
                ),
                Utilisateur.nom.label(
                    "controller_last_name"
                ),
                Utilisateur.email.label(
                    "controller_email"
                ),
            )
            .select_from(FicheCollecte)
            .join(
                MissionCollecte,
                MissionCollecte.id
                == FicheCollecte.mission_id,
            )
            .join(
                Campagne,
                Campagne.id
                == MissionCollecte.campagne_id,
            )
            .join(
                ZoneAdministrative,
                ZoneAdministrative.id
                == MissionCollecte.zone_id,
            )
            .outerjoin(
                Entreprise,
                Entreprise.id
                == FicheCollecte.entreprise_id,
            )
            .join(
                DossierVerification,
                DossierVerification.fiche_collecte_id
                == FicheCollecte.id,
            )
            .join(
                ControleFuccs,
                ControleFuccs.id == latest_control_id,
            )
            .join(
                Utilisateur,
                Utilisateur.id
                == ControleFuccs.controleur_id,
            )
            .where(
                ControleFuccs.statut == "FINALISE",
                ControleFuccs.date_fin.is_not(None),
            )
        )

    @staticmethod
    def search_filter(search: str | None):
        if not search or not search.strip():
            return None

        pattern = f"%{search.strip()}%"

        return or_(
            MissionCollecte.code.ilike(pattern),
            Campagne.code.ilike(pattern),
            Campagne.nom.ilike(pattern),
            ZoneAdministrative.nom.ilike(pattern),
            Entreprise.identifiant_national.ilike(pattern),
            Entreprise.raison_sociale.ilike(pattern),
            Entreprise.nom_commercial.ilike(pattern),
        )

    @staticmethod
    async def queue_rows(
        db: AsyncSession,
        *,
        search: str | None,
        limit: int,
        offset: int,
    ):
        search_condition = (
            ValidationWorkspaceRepository.search_filter(
                search
            )
        )

        conditions = []
        if search_condition is not None:
            conditions.append(search_condition)

        query = (
            ValidationWorkspaceRepository
            .base_queue_query()
            .where(*conditions)
            .order_by(
                ControleFuccs.date_fin.desc(),
                ControleFuccs.created_at.desc(),
            )
        )

        result = await db.execute(
            query.limit(limit).offset(offset)
        )

        count_result = await db.execute(
            select(func.count(FicheCollecte.id))
            .select_from(FicheCollecte)
            .join(
                MissionCollecte,
                MissionCollecte.id
                == FicheCollecte.mission_id,
            )
            .join(
                Campagne,
                Campagne.id
                == MissionCollecte.campagne_id,
            )
            .join(
                ZoneAdministrative,
                ZoneAdministrative.id
                == MissionCollecte.zone_id,
            )
            .outerjoin(
                Entreprise,
                Entreprise.id
                == FicheCollecte.entreprise_id,
            )
            .join(
                DossierVerification,
                DossierVerification.fiche_collecte_id
                == FicheCollecte.id,
            )
            .join(
                ControleFuccs,
                ControleFuccs.id
                == ValidationWorkspaceRepository
                .latest_finalized_control_id(),
            )
            .where(*conditions)
        )

        return (
            result.all(),
            int(count_result.scalar_one() or 0),
        )

    @staticmethod
    async def context_row(
        db: AsyncSession,
        fiche_id: UUID,
    ):
        result = await db.execute(
            ValidationWorkspaceRepository
            .base_queue_query()
            .where(FicheCollecte.id == fiche_id)
            .limit(1)
        )

        return result.one_or_none()

    @staticmethod
    async def latest_validation(
        db: AsyncSession,
        *,
        fiche_id: UUID,
        level: str,
    ) -> Validation | None:
        result = await db.execute(
            select(Validation)
            .where(
                Validation.fiche_collecte_id
                == fiche_id,
                Validation.niveau_validation == level,
            )
            .order_by(
                Validation.date_validation.desc().nullslast(),
                Validation.created_at.desc(),
            )
            .limit(1)
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def validator_name(
        db: AsyncSession,
        user_id: UUID | None,
    ) -> str | None:
        if user_id is None:
            return None

        result = await db.execute(
            select(
                Utilisateur.prenoms,
                Utilisateur.nom,
                Utilisateur.email,
            )
            .where(Utilisateur.id == user_id)
        )

        row = result.one_or_none()
        if row is None:
            return None

        full_name = " ".join(
            part
            for part in (row.prenoms, row.nom)
            if part
        ).strip()

        return full_name or row.email

    @staticmethod
    async def correction_counts(
        db: AsyncSession,
        validation_id: UUID | None,
    ) -> tuple[int, int, int]:
        if validation_id is None:
            return (0, 0, 0)

        result = await db.execute(
            select(
                func.count(Correction.id),
                func.sum(
                    func.cast(
                        Correction.statut.in_(
                            ["DEMANDEE", "EN_COURS"]
                        ),
                        Integer,
                    )
                ),
                func.sum(
                    func.cast(
                        Correction.statut == "RESOUMISE",
                        Integer,
                    )
                ),
            )
            .where(
                Correction.validation_id == validation_id
            )
        )

        total, pending, resubmitted = result.one()

        return (
            int(total or 0),
            int(pending or 0),
            int(resubmitted or 0),
        )

    @staticmethod
    async def decisions(
        db: AsyncSession,
    ) -> list[str]:
        result = await db.execute(
            select(Validation.decision)
            .where(
                Validation.decision.is_not(None),
                func.trim(Validation.decision) != "",
            )
            .distinct()
            .order_by(Validation.decision)
        )

        return [
            str(value).strip()
            for value in result.scalars().all()
            if value
        ]
