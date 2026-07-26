"""
Repository PostgreSQL des contacts entreprise.

RESPONSABILITÉS
---------------
- rechercher une entreprise ;
- lister ses contacts ;
- rechercher un contact appartenant à une entreprise.

IMPORTANT
---------
Le filtrage utilise simultanément :
    contact.id
    +
    contact.entreprise_id

Cela empêche qu'un utilisateur manipule l'UUID d'un contact
appartenant à une autre entreprise.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import (
    or_,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact_entreprise import (
    ContactEntreprise,
)
from app.models.entreprise import Entreprise


class ContactEntrepriseRepository:

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
    # LISTE DES CONTACTS
    # ========================================================

    @staticmethod
    async def list_contacts(
        db: AsyncSession,
        *,
        entreprise_id: UUID,
        include_inactive: bool,
    ) -> list[ContactEntreprise]:

        filters = [
            ContactEntreprise.entreprise_id
            == entreprise_id
        ]

        # ----------------------------------------------------
        # Par défaut, les contacts désactivés sont masqués.
        # ----------------------------------------------------

        if not include_inactive:
            filters.append(
                or_(
                    ContactEntreprise.statut.is_(None),
                    ContactEntreprise.statut == "ACTIF",
                )
            )

        result = await db.execute(
            select(ContactEntreprise)
            .where(*filters)
            .order_by(
                ContactEntreprise.contact_principal.desc(),
                ContactEntreprise.nom,
                ContactEntreprise.prenoms,
            )
        )

        return list(
            result.scalars().all()
        )


    # ========================================================
    # CONTACT APPARTENANT À UNE ENTREPRISE
    # ========================================================

    @staticmethod
    async def get_contact(
        db: AsyncSession,
        *,
        entreprise_id: UUID,
        contact_id: UUID,
    ) -> ContactEntreprise | None:
        """
        La double condition protège contre une manipulation
        d'UUID entre entreprises.
        """

        result = await db.execute(
            select(ContactEntreprise).where(
                ContactEntreprise.id == contact_id,
                ContactEntreprise.entreprise_id
                == entreprise_id,
            )
        )

        return result.scalar_one_or_none()