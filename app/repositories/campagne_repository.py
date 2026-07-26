"""
Repository PostgreSQL des campagnes de collecte.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campagne import Campagne
from app.models.utilisateur import Utilisateur


class CampagneRepository:

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        campagne_id: UUID,
    ) -> Campagne | None:
        result = await db.execute(
            select(Campagne).where(Campagne.id == campagne_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_code(
        db: AsyncSession,
        code: str,
    ) -> Campagne | None:
        result = await db.execute(
            select(Campagne).where(Campagne.code == code)
        )
        return result.scalar_one_or_none()

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
    async def list(
        db: AsyncSession,
        *,
        search: str | None,
        statut: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Campagne], int]:
        filters = []

        if statut:
            filters.append(Campagne.statut == statut.strip())

        if search and search.strip():
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    Campagne.code.ilike(pattern),
                    Campagne.nom.ilike(pattern),
                    Campagne.objet.ilike(pattern),
                )
            )

        result = await db.execute(
            select(Campagne)
            .where(*filters)
            .order_by(
                Campagne.date_debut.desc(),
                Campagne.code,
            )
            .limit(limit)
            .offset(offset)
        )

        count = await db.execute(
            select(func.count(Campagne.id)).where(*filters)
        )

        return list(result.scalars().all()), int(count.scalar_one())
