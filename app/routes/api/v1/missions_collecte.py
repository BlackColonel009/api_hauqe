"""
Routes API des missions et affectations de collecte.

Deux vues sont exposées :
- `/missions` : file globale filtrable ;
- `/campagnes/{campagne_id}/missions` : relation parent/enfant explicite.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.permissions.auth import require_permission
from app.schemas.mission_collecte import (
    AffectationMissionCreateRequest,
    AffectationMissionResponse,
    AffectationMissionUpdateRequest,
    MissionCollecteCreateRequest,
    MissionCollecteListResponse,
    MissionCollecteResponse,
    MissionCollecteUpdateRequest,
)
from app.services.auth_service import AuthContext
from app.services.mission_collecte_service import (
    MissionCollecteService,
    build_mission,
)


global_router = APIRouter(
    prefix="/missions",
    tags=["Collecte - Missions"],
)

campaign_router = APIRouter(
    prefix="/campagnes/{campagne_id}/missions",
    tags=["Collecte - Missions"],
)


@global_router.get(
    "",
    response_model=MissionCollecteListResponse,
)
async def list_all_missions(
    campagne_id: UUID | None = Query(default=None),
    zone_id: UUID | None = Query(default=None),
    statut: str | None = Query(default=None, max_length=255),
    assigned_user_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("COLLECTE.LIRE")
    ),
):
    return await MissionCollecteService.list(
        db,
        campagne_id=campagne_id,
        zone_id=zone_id,
        statut=statut,
        assigned_user_id=assigned_user_id,
        limit=limit,
        offset=offset,
    )


@global_router.get(
    "/{mission_id}",
    response_model=MissionCollecteResponse,
)
async def get_mission_global(
    mission_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("COLLECTE.LIRE")
    ),
):
    return build_mission(
        await MissionCollecteService.get(db, mission_id)
    )


@campaign_router.get(
    "",
    response_model=MissionCollecteListResponse,
)
async def list_campaign_missions(
    campagne_id: UUID,
    zone_id: UUID | None = Query(default=None),
    statut: str | None = Query(default=None, max_length=255),
    assigned_user_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("COLLECTE.LIRE")
    ),
):
    return await MissionCollecteService.list(
        db,
        campagne_id=campagne_id,
        zone_id=zone_id,
        statut=statut,
        assigned_user_id=assigned_user_id,
        limit=limit,
        offset=offset,
    )


@campaign_router.post(
    "",
    response_model=MissionCollecteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_mission(
    campagne_id: UUID,
    payload: MissionCollecteCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("COLLECTE.AFFECTER")
    ),
):
    return await MissionCollecteService.create(
        db,
        campagne_id=campagne_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@campaign_router.patch(
    "/{mission_id}",
    response_model=MissionCollecteResponse,
)
async def update_mission(
    campagne_id: UUID,
    mission_id: UUID,
    payload: MissionCollecteUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("COLLECTE.AFFECTER")
    ),
):
    return await MissionCollecteService.update(
        db,
        campagne_id=campagne_id,
        mission_id=mission_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@global_router.get(
    "/{mission_id}/affectations",
    response_model=list[AffectationMissionResponse],
)
async def list_assignments(
    mission_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("COLLECTE.LIRE")
    ),
):
    return await MissionCollecteService.list_assignments(
        db,
        mission_id,
    )


@global_router.post(
    "/{mission_id}/affectations",
    response_model=AffectationMissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_assignment(
    mission_id: UUID,
    payload: AffectationMissionCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("COLLECTE.AFFECTER")
    ),
):
    return await MissionCollecteService.assign(
        db,
        mission_id=mission_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@global_router.patch(
    "/{mission_id}/affectations/{affectation_id}",
    response_model=AffectationMissionResponse,
)
async def update_assignment(
    mission_id: UUID,
    affectation_id: UUID,
    payload: AffectationMissionUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("COLLECTE.AFFECTER")
    ),
):
    return await MissionCollecteService.update_assignment(
        db,
        mission_id=mission_id,
        affectation_id=affectation_id,
        payload=payload,
        actor=actor,
        request=request,
    )
