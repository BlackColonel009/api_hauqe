"""Routes d'administration et de sélection des zones administratives."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.permissions.auth import require_permission
from app.schemas.zone_administrative import (
    ZoneAdministrativeCreateRequest,
    ZoneAdministrativeListResponse,
    ZoneAdministrativeQuickCreateRequest,
    ZoneAdministrativeResponse,
    ZoneAdministrativeStatusRequest,
    ZoneAdministrativeUpdateRequest,
)
from app.services.auth_service import AuthContext
from app.services.zone_administrative_service import (
    ZoneAdministrativeService,
)


router = APIRouter(
    prefix="/zones-administratives",
    tags=["Référentiels - Zones administratives"],
)


@router.get("", response_model=ZoneAdministrativeListResponse)
async def list_zones(
    search: str | None = Query(default=None, max_length=255),
    type_zone: str | None = Query(default=None, max_length=255),
    parent_id: UUID | None = Query(default=None),
    statut: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("REFERENTIELS.LIRE")
    ),
):
    return await ZoneAdministrativeService.list(
        db,
        search=search,
        type_zone=type_zone,
        parent_id=parent_id,
        statut=statut,
        limit=limit,
        offset=offset,
    )


@router.get("/{zone_id}", response_model=ZoneAdministrativeResponse)
async def get_zone(
    zone_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("REFERENTIELS.LIRE")
    ),
):
    return await ZoneAdministrativeService.get(db, zone_id)


@router.post(
    "",
    response_model=ZoneAdministrativeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_zone(
    payload: ZoneAdministrativeCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("REFERENTIELS.CREER")
    ),
):
    return await ZoneAdministrativeService.create(
        db,
        payload=payload,
        actor=actor,
        request=request,
        source="ADMINISTRATION",
    )


@router.post(
    "/quick-create",
    response_model=ZoneAdministrativeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def quick_create_zone(
    payload: ZoneAdministrativeQuickCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("COLLECTE.CREER")
    ),
):
    return await ZoneAdministrativeService.create(
        db,
        payload=payload,
        actor=actor,
        request=request,
        source="COLLECTE_TERRAIN",
    )


@router.patch("/{zone_id}", response_model=ZoneAdministrativeResponse)
async def update_zone(
    zone_id: UUID,
    payload: ZoneAdministrativeUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("REFERENTIELS.MODIFIER")
    ),
):
    return await ZoneAdministrativeService.update(
        db,
        zone_id=zone_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@router.patch(
    "/{zone_id}/status",
    response_model=ZoneAdministrativeResponse,
)
async def change_zone_status(
    zone_id: UUID,
    payload: ZoneAdministrativeStatusRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("REFERENTIELS.DESACTIVER")
    ),
):
    return await ZoneAdministrativeService.change_status(
        db,
        zone_id=zone_id,
        new_status=payload.statut,
        motif=payload.motif,
        actor=actor,
        request=request,
    )
