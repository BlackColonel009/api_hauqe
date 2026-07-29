from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.permissions.auth import require_permission
from app.schemas.scoring_workspace import (
    CertificationInfcWorkspaceResponse,
    CertificationSnccWorkspaceResponse,
    ClassificationWorkspaceFilters,
    ClassificationWorkspaceResponse,
    EnterpriseScoringWorkspaceResponse,
    InfcWorkspaceFilters,
    InfcWorkspaceResponse,
    ScoringWorkspaceFilters,
    SnccWorkspaceFilters,
    SnccWorkspaceResponse,
)
from app.services.auth_service import AuthContext
from app.services.scoring_workspace_service import ScoringWorkspaceService


router = APIRouter(
    prefix="/scoring/workspace",
    tags=["Scoring - Espace de travail"],
)


@router.get("/filters", response_model=ScoringWorkspaceFilters)
async def workspace_filters(
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("CLASSIFICATION.LIRE")),
):
    return await ScoringWorkspaceService.filters(db)


@router.get("/classification-filters", response_model=ClassificationWorkspaceFilters)
async def classification_filters(
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("CLASSIFICATION.LIRE")),
):
    return await ScoringWorkspaceService.classification_filters(db)


@router.get("/infc-filters", response_model=InfcWorkspaceFilters)
async def infc_filters(
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("INFC.LIRE")),
):
    return await ScoringWorkspaceService.infc_filters(db)


@router.get("/sncc-filters", response_model=SnccWorkspaceFilters)
async def sncc_filters(
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("SNCC.LIRE")),
):
    return await ScoringWorkspaceService.sncc_filters(db)


@router.get("/classifications", response_model=ClassificationWorkspaceResponse)
async def classifications(
    search: str | None = Query(default=None, max_length=255),
    classe: str | None = Query(default=None, max_length=255),
    statut: str | None = Query(default=None, max_length=255),
    sort: str = Query(default="recent", max_length=64),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("CLASSIFICATION.LIRE")),
):
    return await ScoringWorkspaceService.classifications(
        db,
        search=search,
        classe=classe,
        statut=statut,
        sort=sort,
        limit=limit,
        offset=offset,
    )


@router.get("/enterprises", response_model=EnterpriseScoringWorkspaceResponse)
async def enterprises(
    search: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("CLASSIFICATION.LIRE")),
):
    return await ScoringWorkspaceService.enterprises(
        db,
        search=search,
        limit=limit,
    )


@router.get("/infc-certifications", response_model=CertificationInfcWorkspaceResponse)
async def infc_certifications(
    search: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("INFC.LIRE")),
):
    return await ScoringWorkspaceService.infc_certifications(
        db,
        search=search,
        limit=limit,
    )


@router.get("/infc-results", response_model=InfcWorkspaceResponse)
async def infc_results(
    search: str | None = Query(default=None, max_length=255),
    statut: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("INFC.LIRE")),
):
    return await ScoringWorkspaceService.infc_results(
        db,
        search=search,
        statut=statut,
        limit=limit,
        offset=offset,
    )


@router.get("/sncc-certifications", response_model=CertificationSnccWorkspaceResponse)
async def sncc_certifications(
    search: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("SNCC.LIRE")),
):
    return await ScoringWorkspaceService.sncc_certifications(
        db,
        search=search,
        limit=limit,
    )


@router.get("/sncc-results", response_model=SnccWorkspaceResponse)
async def sncc_results(
    search: str | None = Query(default=None, max_length=255),
    classe: str | None = Query(default=None, max_length=255),
    statut_administratif: str | None = Query(default=None, max_length=255),
    niveau_risque: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("SNCC.LIRE")),
):
    return await ScoringWorkspaceService.sncc_results(
        db,
        search=search,
        classe=classe,
        statut_administratif=statut_administratif,
        niveau_risque=niveau_risque,
        limit=limit,
        offset=offset,
    )
