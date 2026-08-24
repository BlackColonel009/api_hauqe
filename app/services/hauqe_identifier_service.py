"""Gestion centralisée des identifiants métier HAUQE."""

from __future__ import annotations

import re
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.certification import Certification
from app.models.entreprise import Entreprise
from app.models.organisme import Organisme


class HauqeIdentifierService:
    """Propose et protège les identifiants HAUQE dans les trois registres."""

    _TYPES = {
        "ENTREPRISE": ("ENT", "entreprise", Entreprise),
        "ORGANISME": ("ORG", "organisme", Organisme),
        "CERTIFICATION": ("CERT", "certification", Certification),
    }

    @staticmethod
    def normalize(value: str | None) -> str:
        return (value or "").strip().upper()

    @classmethod
    def require_type(cls, resource_type: str) -> tuple[str, str, type]:
        config = cls._TYPES.get((resource_type or "").strip().upper())
        if config is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Type d’identifiant HAUQE invalide.",
            )
        return config

    @classmethod
    async def find_duplicate(
        cls,
        db: AsyncSession,
        value: str,
        *,
        exclude_type: str | None = None,
        exclude_id: UUID | None = None,
    ) -> dict | None:
        identifier = cls.normalize(value)
        if not identifier:
            return None

        excluded_type = (exclude_type or "").strip().upper()
        for resource_type, (_, label, model) in cls._TYPES.items():
            result = await db.execute(
                select(model.id, model.identifiant_national).where(
                    model.identifiant_national.is_not(None)
                )
            )
            for item_id, stored_value in result.all():
                if cls.normalize(stored_value) != identifier:
                    continue
                if resource_type == excluded_type and item_id == exclude_id:
                    continue
                return {
                    "type": resource_type,
                    "libelle": label,
                    "id": str(item_id),
                    "identifiant": identifier,
                }
        return None

    @classmethod
    async def ensure_available(
        cls,
        db: AsyncSession,
        value: str | None,
        *,
        exclude_type: str | None = None,
        exclude_id: UUID | None = None,
    ) -> str | None:
        identifier = cls.normalize(value)
        if not identifier:
            return None
        duplicate = await cls.find_duplicate(
            db,
            identifier,
            exclude_type=exclude_type,
            exclude_id=exclude_id,
        )
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"L’identifiant HAUQE « {identifier} » est déjà utilisé "
                    f"par une {duplicate['libelle']}. Modifiez l’identifiant."
                ),
            )
        return identifier

    @classmethod
    async def propose(cls, db: AsyncSession, resource_type: str) -> str:
        prefix, _, _ = cls.require_type(resource_type)
        year = __import__("datetime").datetime.now().year
        base = f"HAUQE-{prefix}-{year}-"
        pattern = re.compile(rf"^{re.escape(base)}(\d{{4,}})$")
        highest = 0

        for _, _, model in cls._TYPES.values():
            result = await db.execute(select(model.identifiant_national))
            for (stored_value,) in result.all():
                match = pattern.match(cls.normalize(stored_value))
                if match:
                    highest = max(highest, int(match.group(1)))

        return f"{base}{highest + 1:04d}"
