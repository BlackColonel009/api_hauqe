"""
Repository des missions de collecte et de leurs affectations.

L'affectation conserve son auteur (`attribue_par_id`) et n'est jamais
réécrite par le client.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.affectation_mission import AffectationMission
from app.models.mission_collecte import MissionCollecte
from app.models.utilisateur import Utilisateur
from app.models.zone_administrative import ZoneAdministrative


class MissionCollecteRepository:

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        mission_id: UUID,
    ) -> MissionCollecte | None:
        result = await db.execute(
            select(MissionCollecte).where(
                MissionCollecte.id == mission_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_for_campaign(
        db: AsyncSession,
        *,
        campagne_id: UUID,
        mission_id: UUID,
    ) -> MissionCollecte | None:
        result = await db.execute(
            select(MissionCollecte).where(
                MissionCollecte.id == mission_id,
                MissionCollecte.campagne_id == campagne_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def zone_exists(
        db: AsyncSession,
        zone_id: UUID,
    ) -> bool:
        result = await db.execute(
            select(ZoneAdministrative.id).where(
                ZoneAdministrative.id == zone_id
            )
        )
        return result.scalar_one_or_none() is not None

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
        campagne_id: UUID | None,
        zone_id: UUID | None,
        statut: str | None,
        assigned_user_id: UUID | None,
        limit: int,
        offset: int,
    ) -> tuple[list[MissionCollecte], int]:
        filters = []

        if campagne_id:
            filters.append(
                MissionCollecte.campagne_id == campagne_id
            )
        if zone_id:
            filters.append(MissionCollecte.zone_id == zone_id)
        if statut:
            filters.append(MissionCollecte.statut == statut.strip())

        query = select(MissionCollecte)
        count_query = select(func.count(func.distinct(MissionCollecte.id)))

        if assigned_user_id is not None:
            query = query.join(
                AffectationMission,
                AffectationMission.mission_id == MissionCollecte.id,
            )
            count_query = count_query.select_from(
                MissionCollecte
            ).join(
                AffectationMission,
                AffectationMission.mission_id == MissionCollecte.id,
            )
            filters.append(
                AffectationMission.utilisateur_id == assigned_user_id
            )
            filters.append(
                or_(
                    AffectationMission.statut.is_(None),
                    AffectationMission.statut == "ACTIF",
                )
            )

        result = await db.execute(
            query.where(*filters)
            .distinct()
            .order_by(
                MissionCollecte.date_debut_prevue.desc(),
                MissionCollecte.code,
            )
            .limit(limit)
            .offset(offset)
        )

        total_result = await db.execute(
            count_query.where(*filters)
        )

        return (
            list(result.scalars().all()),
            int(total_result.scalar_one()),
        )

    @staticmethod
    async def list_assignments(
        db: AsyncSession,
        mission_id: UUID,
    ) -> list[AffectationMission]:
        result = await db.execute(
            select(AffectationMission)
            .where(AffectationMission.mission_id == mission_id)
            .order_by(
                AffectationMission.date_debut.desc(),
                AffectationMission.created_at.desc(),
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_assignment(
        db: AsyncSession,
        *,
        mission_id: UUID,
        affectation_id: UUID,
    ) -> AffectationMission | None:
        result = await db.execute(
            select(AffectationMission).where(
                AffectationMission.id == affectation_id,
                AffectationMission.mission_id == mission_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_active_assignment_for_user(
        db: AsyncSession,
        *,
        mission_id: UUID,
        utilisateur_id: UUID,
    ) -> AffectationMission | None:
        result = await db.execute(
            select(AffectationMission).where(
                AffectationMission.mission_id == mission_id,
                AffectationMission.utilisateur_id == utilisateur_id,
                or_(
                    AffectationMission.statut.is_(None),
                    AffectationMission.statut == "ACTIF",
                ),
            )
        )
        return result.scalar_one_or_none()
