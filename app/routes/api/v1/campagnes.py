"""
Routes API des campagnes de collecte.

Lecture : COLLECTE.LIRE
Création / modification : COLLECTE.AFFECTER

Le superviseur/point focal peut ainsi organiser les campagnes et missions
sans attribuer aux agents de collecte des droits d'administration.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.permissions.auth import require_permission
from app.schemas.campagne import (
    CampagneCreateRequest,
    CampagneListResponse,
    CampagneResponse,
    CampagneUpdateRequest,
)
from app.services.auth_service import AuthContext
from app.services.campagne_service import CampagneService


router = APIRouter(
    prefix="/campagnes",
    tags=["Collecte - Campagnes"],
)


@router.get("", response_model=CampagneListResponse)
async def list_campagnes(
    search: str | None = Query(default=None, max_length=255),
    statut: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("COLLECTE.LIRE")
    ),
):
    return await CampagneService.list(
        db,
        search=search,
        statut=statut,
        limit=limit,
        offset=offset,
    )


@router.get("/{campagne_id}", response_model=CampagneResponse)
async def get_campagne(
    campagne_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("COLLECTE.LIRE")
    ),
):
    from app.services.campagne_service import build_response
    return build_response(
        await CampagneService.get(db, campagne_id)
    )


@router.post(
    "",
    response_model=CampagneResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_campagne(
    payload: CampagneCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("COLLECTE.AFFECTER")
    ),
):
    return await CampagneService.create(
        db,
        payload=payload,
        actor=actor,
        request=request,
    )


@router.patch(
    "/{campagne_id}",
    response_model=CampagneResponse,
)
async def update_campagne(
    campagne_id: UUID,
    payload: CampagneUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("COLLECTE.AFFECTER")
    ),
):
    return await CampagneService.update(
        db,
        campagne_id=campagne_id,
        payload=payload,
        actor=actor,
        request=request,
    )
