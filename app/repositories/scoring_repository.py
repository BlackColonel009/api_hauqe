"""
Repository PostgreSQL — Scoring / Classification / INFC / SNCC.

Les règles métier et les calculs restent dans le service.
Le repository garantit surtout :
- existence et récupération des modèles ;
- historique des pondérations ;
- historique complet des résultats ;
- sélection du modèle publié actif ;
- sélection du classement SNCC courant.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.certification import Certification
from app.models.classement_sncc import ClassementSncc
from app.models.classification_entreprise import ClassificationEntreprise
from app.models.entreprise import Entreprise
from app.models.modele_scoring import ModeleScoring
from app.models.ponderation_scoring import PonderationScoring
from app.models.resultat_infc import ResultatInfc


class ScoringRepository:

    # ========================================================
    # MODÈLES
    # ========================================================

    @staticmethod
    async def get_model(db: AsyncSession, model_id: UUID) -> ModeleScoring | None:
        result = await db.execute(
            select(ModeleScoring).where(ModeleScoring.id == model_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def find_model_version(
        db: AsyncSession,
        *,
        code: str,
        version: str,
    ) -> ModeleScoring | None:
        result = await db.execute(
            select(ModeleScoring).where(
                ModeleScoring.code == code,
                ModeleScoring.version == version,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_models(
        db: AsyncSession,
        *,
        objet_evalue: str | None,
        statut: str | None,
    ) -> list[ModeleScoring]:
        filters = []
        if objet_evalue:
            filters.append(
                ModeleScoring.objet_evalue == objet_evalue.strip().upper()
            )
        if statut:
            filters.append(ModeleScoring.statut == statut.strip().upper())

        result = await db.execute(
            select(ModeleScoring)
            .where(*filters)
            .order_by(
                ModeleScoring.date_debut_validite.desc().nullslast(),
                ModeleScoring.created_at.desc(),
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def active_model(
        db: AsyncSession,
        objet_evalue: str,
    ) -> ModeleScoring | None:
        today = date.today()
        result = await db.execute(
            select(ModeleScoring)
            .where(
                ModeleScoring.objet_evalue == objet_evalue.strip().upper(),
                ModeleScoring.statut == "PUBLIE",
                or_(
                    ModeleScoring.date_debut_validite.is_(None),
                    ModeleScoring.date_debut_validite <= today,
                ),
                or_(
                    ModeleScoring.date_fin_validite.is_(None),
                    ModeleScoring.date_fin_validite >= today,
                ),
            )
            .order_by(
                ModeleScoring.date_debut_validite.desc().nullslast(),
                ModeleScoring.created_at.desc(),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    # ========================================================
    # PONDÉRATIONS
    # ========================================================

    @staticmethod
    async def list_weights(
        db: AsyncSession,
        model_id: UUID,
        *,
        active_only: bool = False,
    ) -> list[PonderationScoring]:
        filters = [PonderationScoring.modele_scoring_id == model_id]
        if active_only:
            filters.append(
                or_(
                    PonderationScoring.statut.is_(None),
                    PonderationScoring.statut == "ACTIF",
                )
            )

        result = await db.execute(
            select(PonderationScoring)
            .where(*filters)
            .order_by(
                PonderationScoring.domaine,
                PonderationScoring.created_at,
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_weight(
        db: AsyncSession,
        *,
        model_id: UUID,
        weight_id: UUID,
    ) -> PonderationScoring | None:
        result = await db.execute(
            select(PonderationScoring).where(
                PonderationScoring.id == weight_id,
                PonderationScoring.modele_scoring_id == model_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def active_weight_by_domain(
        db: AsyncSession,
        *,
        model_id: UUID,
        domain: str,
    ) -> PonderationScoring | None:
        result = await db.execute(
            select(PonderationScoring)
            .where(
                PonderationScoring.modele_scoring_id == model_id,
                func.upper(PonderationScoring.domaine) == domain.strip().upper(),
                or_(
                    PonderationScoring.statut.is_(None),
                    PonderationScoring.statut == "ACTIF",
                ),
            )
            .order_by(PonderationScoring.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    # ========================================================
    # ENTREPRISE
    # ========================================================

    @staticmethod
    async def get_enterprise(
        db: AsyncSession,
        enterprise_id: UUID,
    ) -> Entreprise | None:
        result = await db.execute(
            select(Entreprise).where(Entreprise.id == enterprise_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_enterprise_classifications(
        db: AsyncSession,
        enterprise_id: UUID,
    ) -> list[ClassificationEntreprise]:
        result = await db.execute(
            select(ClassificationEntreprise)
            .where(ClassificationEntreprise.entreprise_id == enterprise_id)
            .order_by(
                ClassificationEntreprise.date_validation.desc().nullslast(),
                ClassificationEntreprise.created_at.desc(),
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def latest_enterprise_classification(
        db: AsyncSession,
        enterprise_id: UUID,
    ) -> ClassificationEntreprise | None:
        result = await db.execute(
            select(ClassificationEntreprise)
            .where(ClassificationEntreprise.entreprise_id == enterprise_id)
            .order_by(
                ClassificationEntreprise.date_validation.desc().nullslast(),
                ClassificationEntreprise.created_at.desc(),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    # ========================================================
    # CERTIFICATION / INFC
    # ========================================================

    @staticmethod
    async def get_certification(
        db: AsyncSession,
        certification_id: UUID,
    ) -> Certification | None:
        result = await db.execute(
            select(Certification).where(Certification.id == certification_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_infc_results(
        db: AsyncSession,
        *,
        certification_id: UUID | None,
        model_id: UUID | None,
        statut: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[ResultatInfc], int]:
        filters = []
        if certification_id:
            filters.append(ResultatInfc.certification_id == certification_id)
        if model_id:
            filters.append(ResultatInfc.modele_scoring_id == model_id)
        if statut:
            filters.append(ResultatInfc.statut == statut.strip().upper())

        result = await db.execute(
            select(ResultatInfc)
            .where(*filters)
            .order_by(
                ResultatInfc.date_calcul.desc().nullslast(),
                ResultatInfc.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        count = await db.execute(
            select(func.count(ResultatInfc.id)).where(*filters)
        )
        return list(result.scalars().all()), int(count.scalar_one())

    @staticmethod
    async def get_infc_result(
        db: AsyncSession,
        result_id: UUID,
    ) -> ResultatInfc | None:
        result = await db.execute(
            select(ResultatInfc).where(ResultatInfc.id == result_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def latest_infc_result(
        db: AsyncSession,
        certification_id: UUID,
    ) -> ResultatInfc | None:
        result = await db.execute(
            select(ResultatInfc)
            .where(ResultatInfc.certification_id == certification_id)
            .order_by(
                ResultatInfc.date_calcul.desc().nullslast(),
                ResultatInfc.created_at.desc(),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    # ========================================================
    # SNCC
    # ========================================================

    @staticmethod
    async def list_sncc(
        db: AsyncSession,
        *,
        certification_id: UUID | None,
        classe: str | None,
        statut_administratif: str | None,
        niveau_risque: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[ClassementSncc], int]:
        filters = []
        if certification_id:
            filters.append(ClassementSncc.certification_id == certification_id)
        if classe:
            filters.append(ClassementSncc.classe == classe.strip())
        if statut_administratif:
            filters.append(
                ClassementSncc.statut_administratif
                == statut_administratif.strip().upper()
            )
        if niveau_risque:
            filters.append(
                ClassementSncc.niveau_risque == niveau_risque.strip().upper()
            )

        result = await db.execute(
            select(ClassementSncc)
            .where(*filters)
            .order_by(
                ClassementSncc.date_effet.desc().nullslast(),
                ClassementSncc.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        count = await db.execute(
            select(func.count(ClassementSncc.id)).where(*filters)
        )
        return list(result.scalars().all()), int(count.scalar_one())

    @staticmethod
    async def get_sncc(
        db: AsyncSession,
        sncc_id: UUID,
    ) -> ClassementSncc | None:
        result = await db.execute(
            select(ClassementSncc).where(ClassementSncc.id == sncc_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def current_sncc(
        db: AsyncSession,
        certification_id: UUID,
    ) -> ClassementSncc | None:
        result = await db.execute(
            select(ClassementSncc)
            .where(
                ClassementSncc.certification_id == certification_id,
                ClassementSncc.date_fin.is_(None),
            )
            .order_by(
                ClassementSncc.date_effet.desc().nullslast(),
                ClassementSncc.created_at.desc(),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()
