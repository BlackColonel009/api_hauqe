"""
Repository PostgreSQL — Validation / Corrections / Intégration BNEC.

Le repository assure :
- recherche du contrôle FUCCS finalisé d'une fiche ;
- historique des deux niveaux de validation ;
- corrections liées à une décision ;
- file et journal des intégrations BNEC ;
- éléments d'intégration.

Les règles de décision restent dans le service.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.controle_fuccs import ControleFuccs
from app.models.correction import Correction
from app.models.dossier_verification import DossierVerification
from app.models.element_integration import ElementIntegration
from app.models.fiche_collecte import FicheCollecte
from app.models.integration_bnec import IntegrationBnec
from app.models.validation import Validation


class ValidationBnecRepository:

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    async def get_fiche(db: AsyncSession, fiche_id: UUID) -> FicheCollecte | None:
        result = await db.execute(
            select(FicheCollecte).where(FicheCollecte.id == fiche_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def latest_finalized_control_for_fiche(
        db: AsyncSession,
        fiche_id: UUID,
    ) -> ControleFuccs | None:
        result = await db.execute(
            select(ControleFuccs)
            .join(
                DossierVerification,
                DossierVerification.id == ControleFuccs.dossier_verification_id,
            )
            .where(
                DossierVerification.fiche_collecte_id == fiche_id,
                ControleFuccs.statut == "FINALISE",
                ControleFuccs.date_fin.is_not(None),
            )
            .order_by(
                ControleFuccs.date_fin.desc(),
                ControleFuccs.created_at.desc(),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_validation(
        db: AsyncSession,
        validation_id: UUID,
    ) -> Validation | None:
        result = await db.execute(
            select(Validation).where(Validation.id == validation_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def latest_validation_for_level(
        db: AsyncSession,
        *,
        fiche_id: UUID,
        level: str,
    ) -> Validation | None:
        result = await db.execute(
            select(Validation)
            .where(
                Validation.fiche_collecte_id == fiche_id,
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
    async def list_validations(
        db: AsyncSession,
        *,
        fiche_id: UUID | None,
        niveau: str | None,
        decision: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Validation], int]:
        filters = []

        if fiche_id:
            filters.append(Validation.fiche_collecte_id == fiche_id)
        if niveau:
            filters.append(Validation.niveau_validation == niveau)
        if decision:
            filters.append(Validation.decision == decision)

        result = await db.execute(
            select(Validation)
            .where(*filters)
            .order_by(
                Validation.date_validation.desc().nullslast(),
                Validation.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        count = await db.execute(
            select(func.count(Validation.id)).where(*filters)
        )
        return list(result.scalars().all()), int(count.scalar_one())

    @staticmethod
    async def validation_queue_rows(db: AsyncSession):
        """
        Retourne les contrôles FUCCS finalisés avec leur fiche.

        Le service complète ensuite les décisions N1/N2 afin de garder
        la logique hiérarchique dans la couche métier.
        """
        result = await db.execute(
            select(ControleFuccs, DossierVerification)
            .join(
                DossierVerification,
                DossierVerification.id == ControleFuccs.dossier_verification_id,
            )
            .where(
                ControleFuccs.statut == "FINALISE",
                ControleFuccs.date_fin.is_not(None),
            )
            .order_by(
                ControleFuccs.date_fin.desc(),
                ControleFuccs.created_at.desc(),
            )
        )
        return list(result.all())

    # ========================================================
    # CORRECTIONS
    # ========================================================

    @staticmethod
    async def list_corrections(
        db: AsyncSession,
        validation_id: UUID,
    ) -> list[Correction]:
        result = await db.execute(
            select(Correction)
            .where(Correction.validation_id == validation_id)
            .order_by(Correction.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_correction(
        db: AsyncSession,
        *,
        validation_id: UUID,
        correction_id: UUID,
    ) -> Correction | None:
        result = await db.execute(
            select(Correction).where(
                Correction.id == correction_id,
                Correction.validation_id == validation_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def has_pending_correction(
        db: AsyncSession,
        validation_id: UUID,
    ) -> bool:
        result = await db.execute(
            select(Correction.id)
            .where(
                Correction.validation_id == validation_id,
                Correction.statut.in_(["DEMANDEE", "EN_COURS"]),
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    # ========================================================
    # INTEGRATION
    # ========================================================

    @staticmethod
    async def get_integration(
        db: AsyncSession,
        integration_id: UUID,
    ) -> IntegrationBnec | None:
        result = await db.execute(
            select(IntegrationBnec).where(IntegrationBnec.id == integration_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def latest_integration_for_validation(
        db: AsyncSession,
        validation_id: UUID,
    ) -> IntegrationBnec | None:
        result = await db.execute(
            select(IntegrationBnec)
            .where(IntegrationBnec.validation_id == validation_id)
            .order_by(IntegrationBnec.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def active_integration_for_validation(
        db: AsyncSession,
        validation_id: UUID,
    ) -> IntegrationBnec | None:
        result = await db.execute(
            select(IntegrationBnec)
            .where(
                IntegrationBnec.validation_id == validation_id,
                IntegrationBnec.date_fin.is_(None),
                IntegrationBnec.statut != "INTEGREE",
            )
            .order_by(IntegrationBnec.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_integrations(
        db: AsyncSession,
        *,
        statut: str | None,
        validation_id: UUID | None,
        administrateur_id: UUID | None,
        limit: int,
        offset: int,
    ) -> tuple[list[IntegrationBnec], int]:
        filters = []
        if statut:
            filters.append(IntegrationBnec.statut == statut)
        if validation_id:
            filters.append(IntegrationBnec.validation_id == validation_id)
        if administrateur_id:
            filters.append(IntegrationBnec.administrateur_id == administrateur_id)

        result = await db.execute(
            select(IntegrationBnec)
            .where(*filters)
            .order_by(IntegrationBnec.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        count = await db.execute(
            select(func.count(IntegrationBnec.id)).where(*filters)
        )
        return list(result.scalars().all()), int(count.scalar_one())

    @staticmethod
    async def favorable_level2_validations(db: AsyncSession) -> list[Validation]:
        result = await db.execute(
            select(Validation)
            .where(
                Validation.niveau_validation == "NIVEAU_2",
                Validation.decision.in_(["VALIDE", "VALIDE_SOUS_RESERVE"]),
                Validation.statut == "TERMINE",
            )
            .order_by(
                Validation.date_validation.desc().nullslast(),
                Validation.created_at.desc(),
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_elements(
        db: AsyncSession,
        integration_id: UUID,
    ) -> list[ElementIntegration]:
        result = await db.execute(
            select(ElementIntegration)
            .where(ElementIntegration.integration_bnec_id == integration_id)
            .order_by(ElementIntegration.created_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_element(
        db: AsyncSession,
        *,
        integration_id: UUID,
        element_id: UUID,
    ) -> ElementIntegration | None:
        result = await db.execute(
            select(ElementIntegration).where(
                ElementIntegration.id == element_id,
                ElementIntegration.integration_bnec_id == integration_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def integration_counts(
        db: AsyncSession,
        integration_id: UUID,
    ) -> tuple[int, int, int]:
        total = await db.execute(
            select(func.count(ElementIntegration.id)).where(
                ElementIntegration.integration_bnec_id == integration_id
            )
        )
        success = await db.execute(
            select(func.count(ElementIntegration.id)).where(
                ElementIntegration.integration_bnec_id == integration_id,
                ElementIntegration.statut == "INTEGRE",
            )
        )
        error = await db.execute(
            select(func.count(ElementIntegration.id)).where(
                ElementIntegration.integration_bnec_id == integration_id,
                ElementIntegration.statut == "ECHEC",
            )
        )
        return (
            int(total.scalar_one()),
            int(success.scalar_one()),
            int(error.scalar_one()),
        )
