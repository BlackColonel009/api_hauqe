from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.permissions.auth import require_permission
from app.schemas.validation_workspace import (
    ValidationWorkspaceFiltersResponse,
    ValidationWorkspaceItem,
    ValidationWorkspaceRegistryResponse,
)
from app.services.auth_service import AuthContext
from app.services.validation_workspace_service import (
    ValidationWorkspaceService,
)


router = APIRouter(
    prefix="/validations/workspace",
    tags=["Validation - Espace de travail"],
)


@router.get(
    "/filters",
    response_model=ValidationWorkspaceFiltersResponse,
)
async def validation_workspace_filters(
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("VALIDATION.LIRE")
    ),
):
    return await ValidationWorkspaceService.filters(db)


@router.get(
    "/registry",
    response_model=ValidationWorkspaceRegistryResponse,
)
async def validation_workspace_registry(
    search: str | None = Query(
        default=None,
        max_length=255,
    ),
    stage: str | None = Query(
        default=None,
        max_length=64,
    ),
    decision: str | None = Query(
        default=None,
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
        require_permission("VALIDATION.LIRE")
    ),
):
    return await ValidationWorkspaceService.registry(
        db,
        search=search,
        stage=stage,
        decision=decision,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{fiche_id}",
    response_model=ValidationWorkspaceItem,
)
async def validation_workspace_context(
    fiche_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("VALIDATION.LIRE")
    ),
):
    return await ValidationWorkspaceService.context(
        db,
        fiche_id,
    )
