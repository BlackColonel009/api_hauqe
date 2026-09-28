"""Proposition et allocation sûre des codes de collecte.

Les codes sont lisibles par les équipes et générés à partir de la base :
HAUQE-CAMP-AAAA-NNNN, HAUQE-MIS-AAAA-NNNN et HAUQE-ZON-AAAA-NNNN.
"""

from __future__ import annotations

import re
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campagne import Campagne
from app.models.mission_collecte import MissionCollecte
from app.models.zone_administrative import ZoneAdministrative


class CollecteCodeService:
    """Centralise les trois séquences de codes utilisées en collecte."""

    _TYPES = {
        "CAMPAGNE": ("HAUQE-CAMP", Campagne.code),
        "MISSION": ("HAUQE-MIS", MissionCollecte.code),
        "ZONE": ("HAUQE-ZON", ZoneAdministrative.code),
    }

    @classmethod
    def _config(cls, resource_type: str):
        normalized = (resource_type or "").strip().upper()
        config = cls._TYPES.get(normalized)
        if config is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Type de code de collecte invalide.",
            )
        return normalized, config

    @classmethod
    async def propose(cls, db: AsyncSession, resource_type: str) -> str:
        _, (prefix, column) = cls._config(resource_type)
        year = datetime.now().year
        expression = re.compile(rf"^{re.escape(prefix)}-{year}-(\d{{4,}})$")
        highest = 0

        values = (await db.execute(select(column))).scalars().all()
        for value in values:
            match = expression.match(str(value or "").strip().upper())
            if match:
                highest = max(highest, int(match.group(1)))

        return f"{prefix}-{year}-{highest + 1:04d}"

    @classmethod
    async def allocate_next(cls, db: AsyncSession, resource_type: str) -> str:
        """Alloue le prochain code sous verrou transactionnel PostgreSQL."""
        normalized, _ = cls._config(resource_type)
        await db.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:scope))"),
            {"scope": f"HAUQE_COLLECTE_CODE:{normalized}"},
        )
        return await cls.propose(db, normalized)
