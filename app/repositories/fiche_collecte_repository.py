"""
Repository des fiches de collecte, déclarations et historique.

La notion de "révision courante" n'a pas de booléen dédié dans le MPD.
Le backend considère donc comme courante la fiche ayant le plus grand
`numero_revision` pour une mission.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.certification_declaree import CertificationDeclaree
from app.models.entreprise import Entreprise
from app.models.evenement_collecte import EvenementCollecte
from app.models.fiche_collecte import FicheCollecte
from app.models.offre_declaree import OffreDeclaree
from app.models.regle_metier import RegleMetier
from app.rules.business_rule_resolver import resolve_business_rule


class FicheCollecteRepository:

    @staticmethod
    async def get_entreprise(
        db: AsyncSession,
        entreprise_id: UUID,
    ) -> Entreprise | None:
        result = await db.execute(
            select(Entreprise).where(Entreprise.id == entreprise_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_for_mission(
        db: AsyncSession,
        *,
        mission_id: UUID,
        fiche_id: UUID,
    ) -> FicheCollecte | None:
        result = await db.execute(
            select(FicheCollecte).where(
                FicheCollecte.id == fiche_id,
                FicheCollecte.mission_id == mission_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_revisions(
        db: AsyncSession,
        mission_id: UUID,
    ) -> list[FicheCollecte]:
        result = await db.execute(
            select(FicheCollecte)
            .where(FicheCollecte.mission_id == mission_id)
            .order_by(
                FicheCollecte.numero_revision.desc().nullslast(),
                FicheCollecte.created_at.desc(),
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_current(
        db: AsyncSession,
        mission_id: UUID,
    ) -> FicheCollecte | None:
        result = await db.execute(
            select(FicheCollecte)
            .where(FicheCollecte.mission_id == mission_id)
            .order_by(
                FicheCollecte.numero_revision.desc().nullslast(),
                FicheCollecte.created_at.desc(),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_completeness_rule(
        db: AsyncSession,
    ) -> RegleMetier | None:
        """
        Résout la version publiée applicable du code logique
        COLLECTE_COMPLETUDE.

        `regles_metier.code` est un identifiant physique versionné,
        par exemple COLLECTE_COMPLETUDE__V1_0.
        """
        return await resolve_business_rule(
            db,
            "COLLECTE_COMPLETUDE",
        )

    @staticmethod
    async def list_offres(
        db: AsyncSession,
        fiche_id: UUID,
    ) -> list[OffreDeclaree]:
        result = await db.execute(
            select(OffreDeclaree)
            .where(OffreDeclaree.fiche_collecte_id == fiche_id)
            .order_by(OffreDeclaree.created_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_offre(
        db: AsyncSession,
        *,
        fiche_id: UUID,
        offre_id: UUID,
    ) -> OffreDeclaree | None:
        result = await db.execute(
            select(OffreDeclaree).where(
                OffreDeclaree.id == offre_id,
                OffreDeclaree.fiche_collecte_id == fiche_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_certifications(
        db: AsyncSession,
        fiche_id: UUID,
    ) -> list[CertificationDeclaree]:
        result = await db.execute(
            select(CertificationDeclaree)
            .where(
                CertificationDeclaree.fiche_collecte_id == fiche_id
            )
            .order_by(CertificationDeclaree.created_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_certification(
        db: AsyncSession,
        *,
        fiche_id: UUID,
        certification_declaree_id: UUID,
    ) -> CertificationDeclaree | None:
        result = await db.execute(
            select(CertificationDeclaree).where(
                CertificationDeclaree.id
                == certification_declaree_id,
                CertificationDeclaree.fiche_collecte_id == fiche_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_events(
        db: AsyncSession,
        fiche_id: UUID,
    ) -> list[EvenementCollecte]:
        result = await db.execute(
            select(EvenementCollecte)
            .where(
                EvenementCollecte.fiche_collecte_id == fiche_id
            )
            .order_by(
                EvenementCollecte.date_evenement.desc(),
                EvenementCollecte.created_at.desc(),
            )
        )
        return list(result.scalars().all())
