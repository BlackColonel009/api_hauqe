"""
Repository PostgreSQL des sites entreprise.

RESPONSABILITÉS
---------------
- vérifier l'entreprise ;
- vérifier la zone administrative ;
- lister les sites d'une entreprise ;
- récupérer un site en contrôlant qu'il appartient bien
  à l'entreprise présente dans l'URL.

Aucune permission ni règle métier n'est décidée ici.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entreprise import Entreprise
from app.models.site_entreprise import SiteEntreprise
from app.models.zone_administrative import ZoneAdministrative


class SiteEntrepriseRepository:

    # ========================================================
    # ENTREPRISE
    # ========================================================

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


    # ========================================================
    # ZONE ADMINISTRATIVE
    # ========================================================

    @staticmethod
    async def zone_exists(
        db: AsyncSession,
        zone_id: UUID,
    ) -> bool:
        """
        Vérification explicite avant de laisser PostgreSQL
        déclencher une erreur de clé étrangère.
        """

        result = await db.execute(
            select(ZoneAdministrative.id).where(
                ZoneAdministrative.id == zone_id
            )
        )

        return (
            result.scalar_one_or_none()
            is not None
        )


    # ========================================================
    # LISTE DES SITES
    # ========================================================

    @staticmethod
    async def list_sites(
        db: AsyncSession,
        *,
        entreprise_id: UUID,
        include_inactive: bool,
    ) -> list[SiteEntreprise]:

        filters = [
            SiteEntreprise.entreprise_id
            == entreprise_id
        ]

        if not include_inactive:
            filters.append(
                or_(
                    SiteEntreprise.statut.is_(None),
                    SiteEntreprise.statut == "ACTIF",
                )
            )

        result = await db.execute(
            select(SiteEntreprise)
            .where(*filters)
            .order_by(
                SiteEntreprise.nom,
                SiteEntreprise.type_site,
            )
        )

        return list(
            result.scalars().all()
        )


    # ========================================================
    # SITE D'UNE ENTREPRISE
    # ========================================================

    @staticmethod
    async def get_site(
        db: AsyncSession,
        *,
        entreprise_id: UUID,
        site_id: UUID,
    ) -> SiteEntreprise | None:
        """
        La double condition empêche de manipuler un site
        appartenant à une autre entreprise.
        """

        result = await db.execute(
            select(SiteEntreprise).where(
                SiteEntreprise.id == site_id,
                SiteEntreprise.entreprise_id
                == entreprise_id,
            )
        )

        return result.scalar_one_or_none()