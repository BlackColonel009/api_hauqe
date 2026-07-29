from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.permissions.auth import require_permission
from app.schemas.watch_workspace import (
    AlertWorkspaceResponse,
    DeadlineWorkspaceResponse,
    WatchCaseWorkspaceResponse,
    WatchFilters,
    WatchFormOptions,
    WatchReportWorkspaceResponse,
)
from app.services.auth_service import AuthContext
from app.services.watch_workspace_service import WatchWorkspaceService


router = APIRouter(
    prefix="/veille/workspace",
    tags=["Veille - Espace de travail"],
)


@router.get("/deadline-filters", response_model=WatchFilters)
async def deadline_filters(
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("ECHEANCES.LIRE")),
):
    return await WatchWorkspaceService.filters(db)


@router.get("/alert-filters", response_model=WatchFilters)
async def alert_filters(
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("ALERTES.LIRE")),
):
    return await WatchWorkspaceService.filters(db)


@router.get("/filters", response_model=WatchFilters)
async def watch_filters(
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("VEILLE.LIRE")),
):
    return await WatchWorkspaceService.filters(db)


@router.get("/deadline-options", response_model=WatchFormOptions)
async def deadline_options(
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("ECHEANCES.GERER")),
):
    return await WatchWorkspaceService.form_options(db)


@router.get("/alert-options", response_model=WatchFormOptions)
async def alert_options(
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("ALERTES.AFFECTER")),
):
    return await WatchWorkspaceService.form_options(db)


@router.get("/watch-options", response_model=WatchFormOptions)
async def watch_options(
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("VEILLE.GERER")),
):
    return await WatchWorkspaceService.form_options(db)


@router.get("/deadlines", response_model=DeadlineWorkspaceResponse)
async def deadlines(
    ressource_type: str | None = Query(default=None, max_length=255),
    ressource_id: UUID | None = Query(default=None),
    type_echeance: str | None = Query(default=None, max_length=255),
    responsable_id: UUID | None = Query(default=None),
    statut: str | None = Query(default=None, max_length=255),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    overdue_only: bool = Query(default=False),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("ECHEANCES.LIRE")),
):
    return await WatchWorkspaceService.deadlines(
        db,
        ressource_type=ressource_type,
        ressource_id=ressource_id,
        type_echeance=type_echeance,
        responsable_id=responsable_id,
        statut=statut,
        start_date=start_date,
        end_date=end_date,
        overdue_only=overdue_only,
        limit=limit,
        offset=offset,
    )


@router.get("/alerts", response_model=AlertWorkspaceResponse)
async def alerts(
    type_alerte: str | None = Query(default=None, max_length=255),
    niveau: int | None = Query(default=None, ge=1, le=4),
    responsable_id: UUID | None = Query(default=None),
    statut: str | None = Query(default=None, max_length=255),
    ressource_type: str | None = Query(default=None, max_length=255),
    ressource_id: UUID | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("ALERTES.LIRE")),
):
    return await WatchWorkspaceService.alerts(
        db,
        type_alerte=type_alerte,
        niveau=niveau,
        responsable_id=responsable_id,
        statut=statut,
        ressource_type=ressource_type,
        ressource_id=ressource_id,
        limit=limit,
        offset=offset,
    )


@router.get("/cases", response_model=WatchCaseWorkspaceResponse)
async def watch_cases(
    certification_id: UUID | None = Query(default=None),
    responsable_id: UUID | None = Query(default=None),
    statut: str | None = Query(default=None, max_length=255),
    priorite: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("VEILLE.LIRE")),
):
    return await WatchWorkspaceService.watch_cases(
        db,
        certification_id=certification_id,
        responsable_id=responsable_id,
        statut=statut,
        priorite=priorite,
        limit=limit,
        offset=offset,
    )


@router.get("/reports", response_model=WatchReportWorkspaceResponse)
async def watch_reports(
    type_rapport: str | None = Query(default=None, max_length=255),
    statut: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("VEILLE.LIRE")),
):
    return await WatchWorkspaceService.reports(
        db,
        type_rapport=type_rapport,
        statut_filter=statut,
        limit=limit,
        offset=offset,
    )
