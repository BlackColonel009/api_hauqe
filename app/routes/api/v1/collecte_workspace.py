from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.permissions.auth import require_permission
from app.schemas.collecte_workspace import (
    CollecteRegistryResponse,
    CollecteWorkspaceFiltersResponse,
    CollecteQuickEnterpriseCreateRequest,
    CollecteQuickEnterpriseResponse,
)
from app.services.auth_service import AuthContext
from app.services.collecte_workspace_service import (
    CollecteWorkspaceService,
)


router = APIRouter(
    prefix="/collectes",
    tags=["Collecte - Espace de travail"],
)


@router.get(
    "/filters",
    response_model=CollecteWorkspaceFiltersResponse,
)
async def collecte_workspace_filters(
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("COLLECTE.LIRE")
    ),
):
    return await CollecteWorkspaceService.filters(db)


@router.get(
    "/registry",
    response_model=CollecteRegistryResponse,
)
async def collecte_workspace_registry(
    search: str | None = Query(default=None, max_length=255),
    campagne_id: UUID | None = Query(default=None),
    zone_id: UUID | None = Query(default=None),
    assigned_user_id: UUID | None = Query(default=None),
    mission_statut: str | None = Query(default=None, max_length=255),
    fiche_statut: str | None = Query(default=None, max_length=255),
    sort: str = Query(default="planned", max_length=64),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("COLLECTE.LIRE")
    ),
):
    return await CollecteWorkspaceService.registry(
        db,
        search=search,
        campagne_id=campagne_id,
        zone_id=zone_id,
        assigned_user_id=assigned_user_id,
        mission_statut=mission_statut,
        fiche_statut=fiche_statut,
        sort=sort,
        limit=limit,
        offset=offset,
    )

@router.post(
    "/quick-enterprises",
    response_model=CollecteQuickEnterpriseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def quick_create_enterprise(
    payload: CollecteQuickEnterpriseCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("COLLECTE.CREER")),
):
    return await CollecteWorkspaceService.quick_create_enterprise(
        db, payload=payload, actor=actor, request=request
    )

