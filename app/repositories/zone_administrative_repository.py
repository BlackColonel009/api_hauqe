"""Accès PostgreSQL du référentiel des zones administratives."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.zone_administrative import ZoneAdministrative


class ZoneAdministrativeRepository:

    @staticmethod
    async def get(
        db: AsyncSession,
        zone_id: UUID,
    ) -> ZoneAdministrative | None:
        result = await db.execute(
            select(ZoneAdministrative).where(
                ZoneAdministrative.id == zone_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list(
        db: AsyncSession,
        *,
        search: str | None,
        type_zone: str | None,
        parent_id: UUID | None,
        statut: str | None,
        limit: int,
        offset: int,
    ):
        parent = aliased(ZoneAdministrative)
        child = aliased(ZoneAdministrative)

        filters = []
        if search:
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    ZoneAdministrative.nom.ilike(pattern),
                    ZoneAdministrative.code.ilike(pattern),
                    ZoneAdministrative.type_zone.ilike(pattern),
                    parent.nom.ilike(pattern),
                )
            )
        if type_zone:
            filters.append(
                func.upper(ZoneAdministrative.type_zone)
                == type_zone.strip().upper()
            )
        if parent_id:
            filters.append(ZoneAdministrative.parent_id == parent_id)
        if statut:
            filters.append(
                func.upper(ZoneAdministrative.statut)
                == statut.strip().upper()
            )

        base = (
            select(
                ZoneAdministrative,
                parent.nom.label("parent_nom"),
                func.count(child.id).label("enfants_count"),
            )
            .outerjoin(parent, parent.id == ZoneAdministrative.parent_id)
            .outerjoin(child, child.parent_id == ZoneAdministrative.id)
            .where(*filters)
            .group_by(ZoneAdministrative.id, parent.nom)
        )

        rows = await db.execute(
            base.order_by(
                func.coalesce(ZoneAdministrative.type_zone, ""),
                func.coalesce(ZoneAdministrative.nom, ""),
            )
            .limit(limit)
            .offset(offset)
        )

        count_base = (
            select(func.count(func.distinct(ZoneAdministrative.id)))
            .select_from(ZoneAdministrative)
            .outerjoin(parent, parent.id == ZoneAdministrative.parent_id)
            .where(*filters)
        )
        count_result = await db.execute(count_base)

        return rows.all(), int(count_result.scalar_one() or 0)

    @staticmethod
    async def duplicate(
        db: AsyncSession,
        *,
        nom: str,
        type_zone: str,
        parent_id: UUID | None,
        exclude_id: UUID | None = None,
    ) -> ZoneAdministrative | None:
        conditions = [
            func.lower(func.trim(ZoneAdministrative.nom))
            == nom.strip().lower(),
            func.upper(func.trim(ZoneAdministrative.type_zone))
            == type_zone.strip().upper(),
        ]

        if parent_id is None:
            conditions.append(ZoneAdministrative.parent_id.is_(None))
        else:
            conditions.append(ZoneAdministrative.parent_id == parent_id)

        if exclude_id is not None:
            conditions.append(ZoneAdministrative.id != exclude_id)

        result = await db.execute(
            select(ZoneAdministrative).where(and_(*conditions))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def code_owner(
        db: AsyncSession,
        code: str,
        *,
        exclude_id: UUID | None = None,
    ) -> ZoneAdministrative | None:
        filters = [
            func.upper(func.trim(ZoneAdministrative.code))
            == code.strip().upper()
        ]
        if exclude_id is not None:
            filters.append(ZoneAdministrative.id != exclude_id)

        result = await db.execute(
            select(ZoneAdministrative).where(*filters)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def is_descendant(
        db: AsyncSession,
        *,
        candidate_parent_id: UUID,
        zone_id: UUID,
    ) -> bool:
        """Vrai si candidate_parent_id appartient aux descendants de zone_id."""
        descendants = (
            select(ZoneAdministrative.id)
            .where(ZoneAdministrative.parent_id == zone_id)
            .cte(name="zone_descendants", recursive=True)
        )
        descendants = descendants.union_all(
            select(ZoneAdministrative.id).where(
                ZoneAdministrative.parent_id == descendants.c.id
            )
        )

        result = await db.execute(
            select(func.count())
            .select_from(descendants)
            .where(descendants.c.id == candidate_parent_id)
        )
        return bool(result.scalar_one() or 0)

    @staticmethod
    async def path_names(
        db: AsyncSession,
        zone: ZoneAdministrative,
    ) -> list[str]:
        names = [zone.nom or zone.code or str(zone.id)]
        current_parent = zone.parent_id
        guard: set[UUID] = {zone.id}

        while current_parent and current_parent not in guard:
            guard.add(current_parent)
            parent = await ZoneAdministrativeRepository.get(
                db,
                current_parent,
            )
            if parent is None:
                break
            names.append(parent.nom or parent.code or str(parent.id))
            current_parent = parent.parent_id

        names.reverse()
        return names
