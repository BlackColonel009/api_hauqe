"""
Repository PostgreSQL du module Entreprises.

RÔLE DU FICHIER
---------------
Centraliser les requêtes SQLAlchemy relatives aux entreprises.

Le repository :
    - lit PostgreSQL ;
    - recherche les entreprises ;
    - vérifie les zones administratives.

Le repository NE décide PAS :
    - des permissions ;
    - des règles métier ;
    - du contenu du journal d'audit.

Ces responsabilités appartiennent aux couches supérieures.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import (
    func,
    or_,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entreprise import Entreprise
from app.models.zone_administrative import (
    ZoneAdministrative,
)


class EntrepriseRepository:

    # ========================================================
    # RECHERCHE PAR IDENTIFIANT TECHNIQUE
    # ========================================================

    @staticmethod
    async def get_by_id(
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
    # RECHERCHE PAR IDENTIFIANT NATIONAL
    # ========================================================

    @staticmethod
    async def get_by_identifiant_national(
        db: AsyncSession,
        identifiant_national: str,
    ) -> Entreprise | None:
        """
        identifiant_national possède une contrainte UNIQUE
        dans PostgreSQL.
        """

        result = await db.execute(
            select(Entreprise).where(
                Entreprise.identifiant_national
                == identifiant_national
            )
        )

        return result.scalar_one_or_none()


    # ========================================================
    # VÉRIFICATION DE LA ZONE ADMINISTRATIVE
    # ========================================================

    @staticmethod
    async def zone_exists(
        db: AsyncSession,
        zone_id: UUID,
    ) -> bool:
        """
        Évite de laisser PostgreSQL découvrir tardivement
        une zone_siege_id inexistante via une erreur FK.
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
    # LISTE / RECHERCHE
    # ========================================================

    @staticmethod
    async def list_entreprises(
        db: AsyncSession,
        *,
        search: str | None,
        statut: str | None,
        zone_siege_id: UUID | None,
        include_archived: bool,
        limit: int,
        offset: int,
    ) -> tuple[list[Entreprise], int]:
        """
        Recherche paginée.

        search recherche notamment dans :
        - identifiant national ;
        - raison sociale ;
        - nom commercial ;
        - RCCM ;
        - NIF ;
        - IFU.
        """

        filters = []

        # ----------------------------------------------------
        # Par défaut, les archives ne polluent pas la liste
        # opérationnelle.
        # ----------------------------------------------------

        if not include_archived:
            filters.append(
                or_(
                    Entreprise.statut.is_(None),
                    Entreprise.statut != "ARCHIVE",
                )
            )

        # ----------------------------------------------------
        # Filtre explicite de statut
        # ----------------------------------------------------

        if statut:
            filters.append(
                Entreprise.statut
                == statut.strip().upper()
            )

        # ----------------------------------------------------
        # Filtre géographique
        # ----------------------------------------------------

        if zone_siege_id is not None:
            filters.append(
                Entreprise.zone_siege_id
                == zone_siege_id
            )

        # ----------------------------------------------------
        # Recherche textuelle
        # ----------------------------------------------------

        if search and search.strip():

            pattern = (
                f"%{search.strip()}%"
            )

            filters.append(
                or_(
                    Entreprise.identifiant_national.ilike(
                        pattern
                    ),
                    Entreprise.raison_sociale.ilike(
                        pattern
                    ),
                    Entreprise.nom_commercial.ilike(
                        pattern
                    ),
                    Entreprise.rccm.ilike(
                        pattern
                    ),
                    Entreprise.nif.ilike(
                        pattern
                    ),
                    Entreprise.ifu.ilike(
                        pattern
                    ),
                )
            )

        # ----------------------------------------------------
        # Requête de données
        # ----------------------------------------------------

        query = (
            select(Entreprise)
            .where(*filters)
            .order_by(
                Entreprise.raison_sociale,
                Entreprise.nom_commercial,
                Entreprise.identifiant_national,
            )
            .limit(limit)
            .offset(offset)
        )

        result = await db.execute(query)

        entreprises = list(
            result.scalars().all()
        )

        # ----------------------------------------------------
        # COUNT séparé pour la pagination frontend.
        # ----------------------------------------------------

        count_query = (
            select(
                func.count(Entreprise.id)
            )
            .where(*filters)
        )

        total_result = await db.execute(
            count_query
        )

        total = int(
            total_result.scalar_one()
        )

        return entreprises, total