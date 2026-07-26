"""
Repository PostgreSQL des offres d'entreprise.

RESPONSABILITÉS
---------------
- vérifier l'existence de l'entreprise ;
- lister les offres appartenant à une entreprise ;
- récupérer une offre uniquement lorsqu'elle appartient à l'entreprise
  présente dans l'URL.

Le repository n'applique ni permission ni règle métier de cycle de vie.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entreprise import Entreprise
from app.models.offre_entreprise import OffreEntreprise


class OffreEntrepriseRepository:

    @staticmethod
    async def get_entreprise(
        db: AsyncSession,
        entreprise_id: UUID,
    ) -> Entreprise | None:
        result = await db.execute(
            select(Entreprise).where(
                Entreprise.id == entreprise_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_offres(
        db: AsyncSession,
        *,
        entreprise_id: UUID,
        include_inactive: bool,
    ) -> list[OffreEntreprise]:
        filters = [
            OffreEntreprise.entreprise_id == entreprise_id
        ]

        if not include_inactive:
            filters.append(
                or_(
                    OffreEntreprise.statut.is_(None),
                    OffreEntreprise.statut == "ACTIF",
                )
            )

        result = await db.execute(
            select(OffreEntreprise)
            .where(*filters)
            .order_by(
                OffreEntreprise.type_offre,
                OffreEntreprise.nom,
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_offre(
        db: AsyncSession,
        *,
        entreprise_id: UUID,
        offre_id: UUID,
    ) -> OffreEntreprise | None:
        """
        La double condition empêche de manipuler l'offre d'une autre
        entreprise en changeant simplement les UUID dans l'URL.
        """
        result = await db.execute(
            select(OffreEntreprise).where(
                OffreEntreprise.id == offre_id,
                OffreEntreprise.entreprise_id == entreprise_id,
            )
        )
        return result.scalar_one_or_none()
