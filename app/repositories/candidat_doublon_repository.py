"""
Repository PostgreSQL du contrôle des doublons d'entreprises.

RELATIONS
---------
candidats_doublon.entreprise_source_id -> entreprises.id
candidats_doublon.entreprise_cible_id  -> entreprises.id
candidats_doublon.examine_par_id       -> utilisateurs.id

Le repository ne prend aucune décision de fusion.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidat_doublon import CandidatDoublon
from app.models.entreprise import Entreprise


class CandidatDoublonRepository:

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
    async def get_by_id(
        db: AsyncSession,
        candidat_id: UUID,
    ) -> CandidatDoublon | None:
        result = await db.execute(
            select(CandidatDoublon).where(
                CandidatDoublon.id == candidat_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_candidats(
        db: AsyncSession,
        *,
        entreprise_id: UUID | None,
        statut_examen: str | None,
        decision: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[CandidatDoublon], int]:
        filters = []

        if entreprise_id is not None:
            filters.append(
                or_(
                    CandidatDoublon.entreprise_source_id == entreprise_id,
                    CandidatDoublon.entreprise_cible_id == entreprise_id,
                )
            )

        if statut_examen:
            filters.append(
                CandidatDoublon.statut_examen
                == statut_examen.strip()
            )

        if decision:
            filters.append(
                CandidatDoublon.decision
                == decision.strip()
            )

        query = (
            select(CandidatDoublon)
            .where(*filters)
            .order_by(
                CandidatDoublon.created_at.desc()
            )
            .limit(limit)
            .offset(offset)
        )

        result = await db.execute(query)
        items = list(result.scalars().all())

        count_result = await db.execute(
            select(func.count(CandidatDoublon.id))
            .where(*filters)
        )

        total = int(count_result.scalar_one())
        return items, total
