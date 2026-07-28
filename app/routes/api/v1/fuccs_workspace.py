from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.permissions.auth import require_permission
from app.schemas.fuccs_workspace import (
    FuccsControlRegistryItem,
    FuccsControlRegistryResponse,
    FuccsEligibleVerificationsResponse,
    FuccsWorkspaceFiltersResponse,
)
from app.services.auth_service import AuthContext
from app.services.fuccs_workspace_service import (
    FuccsWorkspaceService,
)


router = APIRouter(
    prefix="/fuccs",
    tags=["FUCCS - Espace de travail"],
)


@router.get(
    "/workspace/filters",
    response_model=FuccsWorkspaceFiltersResponse,
)
async def fuccs_workspace_filters(
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("FUCCS.LIRE")
    ),
):
    return await FuccsWorkspaceService.filters(db)


@router.get(
    "/workspace/registry",
    response_model=FuccsControlRegistryResponse,
)
async def fuccs_workspace_registry(
    search: str | None = Query(
        default=None,
        max_length=255,
    ),
    statut: str | None = Query(
        default=None,
        max_length=255,
    ),
    sort: str = Query(
        default="started",
        max_length=64,
    ),
    limit: int = Query(
        default=25,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("FUCCS.LIRE")
    ),
):
    return await FuccsWorkspaceService.registry(
        db,
        search=search,
        statut=statut,
        sort=sort,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/workspace/eligible-verifications",
    response_model=FuccsEligibleVerificationsResponse,
)
async def fuccs_workspace_eligible_verifications(
    search: str | None = Query(
        default=None,
        max_length=255,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("FUCCS.LIRE")
    ),
):
    return (
        await FuccsWorkspaceService
        .eligible_verifications(
            db,
            search=search,
            limit=limit,
            offset=offset,
        )
    )


@router.get(
    "/controles/{control_id}/context",
    response_model=FuccsControlRegistryItem,
)
async def fuccs_control_context(
    control_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("FUCCS.LIRE")
    ),
):
    return await FuccsWorkspaceService.context(
        db,
        control_id,
    )
