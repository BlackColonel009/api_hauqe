"""Repository PostgreSQL des documents privés."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document


class DocumentRepository:
    @staticmethod
    async def get(db: AsyncSession, document_id: UUID) -> Document | None:
        result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list(
        db: AsyncSession,
        *,
        ressource_type: str | None,
        ressource_id: UUID | None,
        include_inactive: bool,
        limit: int,
        offset: int,
    ) -> tuple[list[Document], int]:
        filters = []

        if ressource_type:
            filters.append(Document.ressource_type == ressource_type.strip().upper())
        if ressource_id:
            filters.append(Document.ressource_id == ressource_id)
        if not include_inactive:
            filters.append(or_(Document.statut.is_(None), Document.statut == "ACTIF"))

        result = await db.execute(
            select(Document)
            .where(*filters)
            .order_by(Document.date_depot.desc(), Document.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        count_result = await db.execute(
            select(func.count(Document.id)).where(*filters)
        )
        return list(result.scalars().all()), int(count_result.scalar_one())
