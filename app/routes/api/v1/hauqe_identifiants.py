"""API de proposition et contrôle des identifiants HAUQE."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.permissions.auth import get_current_auth
from app.services.auth_service import AuthContext
from app.services.hauqe_identifier_service import HauqeIdentifierService


router = APIRouter(prefix="/identifiants-hauqe", tags=["Identifiants HAUQE"])


@router.get("/proposer")
async def propose_identifier(
    type: str = Query(..., min_length=3, max_length=32),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(get_current_auth),
):
    identifiant = await HauqeIdentifierService.propose(db, type)
    return {"identifiant": identifiant, "disponible": True}


@router.get("/verifier")
async def check_identifier(
    valeur: str = Query(..., min_length=1, max_length=255),
    exclude_type: str | None = Query(default=None, max_length=32),
    exclude_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(get_current_auth),
):
    duplicate = await HauqeIdentifierService.find_duplicate(
        db, valeur, exclude_type=exclude_type, exclude_id=exclude_id
    )
    return {"disponible": duplicate is None, "doublon": duplicate}
