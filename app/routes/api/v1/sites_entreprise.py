"""
Routes FastAPI des sites entreprise.

URL RACINE
----------
/api/v1/entreprises/{entreprise_id}/sites

PERMISSIONS
-----------
Lecture :
    ENTREPRISES.LIRE

Création :
    ENTREPRISES.CREER

Modification / désactivation / restauration :
    ENTREPRISES.MODIFIER
"""

from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Query,
    Request,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.permissions.auth import require_permission
from app.schemas.site_entreprise import (
    SiteEntrepriseCreateRequest,
    SiteEntrepriseResponse,
    SiteEntrepriseStatusRequest,
    SiteEntrepriseUpdateRequest,
)
from app.services.auth_service import AuthContext
from app.services.site_entreprise_service import (
    SiteEntrepriseService,
)


router = APIRouter(
    prefix="/entreprises/{entreprise_id}/sites",
    tags=["Entreprises - Sites"],
)


# ============================================================
# LISTE
# ============================================================

@router.get(
    "",
    response_model=list[SiteEntrepriseResponse],
)
async def list_sites(
    entreprise_id: UUID,

    include_inactive: bool = Query(
        default=False
    ),

    db: AsyncSession = Depends(get_db),

    actor: AuthContext = Depends(
        require_permission(
            "ENTREPRISES.LIRE"
        )
    ),
):

    return await (
        SiteEntrepriseService.list_sites(
            db,
            entreprise_id=entreprise_id,
            include_inactive=include_inactive,
        )
    )


# ============================================================
# CRÉATION
# ============================================================

@router.post(
    "",
    response_model=SiteEntrepriseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_site(
    entreprise_id: UUID,
    payload: SiteEntrepriseCreateRequest,
    request: Request,

    db: AsyncSession = Depends(get_db),

    actor: AuthContext = Depends(
        require_permission(
            "ENTREPRISES.CREER"
        )
    ),
):

    return await (
        SiteEntrepriseService.create_site(
            db,
            entreprise_id=entreprise_id,
            payload=payload,
            actor=actor,
            request=request,
        )
    )


# ============================================================
# MODIFICATION
# ============================================================

@router.patch(
    "/{site_id}",
    response_model=SiteEntrepriseResponse,
)
async def update_site(
    entreprise_id: UUID,
    site_id: UUID,
    payload: SiteEntrepriseUpdateRequest,
    request: Request,

    db: AsyncSession = Depends(get_db),

    actor: AuthContext = Depends(
        require_permission(
            "ENTREPRISES.MODIFIER"
        )
    ),
):

    return await (
        SiteEntrepriseService.update_site(
            db,
            entreprise_id=entreprise_id,
            site_id=site_id,
            payload=payload,
            actor=actor,
            request=request,
        )
    )


# ============================================================
# DÉSACTIVATION
# ============================================================

@router.post(
    "/{site_id}/deactivate",
    response_model=SiteEntrepriseResponse,
)
async def deactivate_site(
    entreprise_id: UUID,
    site_id: UUID,
    payload: SiteEntrepriseStatusRequest,
    request: Request,

    db: AsyncSession = Depends(get_db),

    actor: AuthContext = Depends(
        require_permission(
            "ENTREPRISES.MODIFIER"
        )
    ),
):

    return await (
        SiteEntrepriseService.deactivate_site(
            db,
            entreprise_id=entreprise_id,
            site_id=site_id,
            motif=payload.motif,
            actor=actor,
            request=request,
        )
    )


# ============================================================
# RESTAURATION
# ============================================================

@router.post(
    "/{site_id}/restore",
    response_model=SiteEntrepriseResponse,
)
async def restore_site(
    entreprise_id: UUID,
    site_id: UUID,
    payload: SiteEntrepriseStatusRequest,
    request: Request,

    db: AsyncSession = Depends(get_db),

    actor: AuthContext = Depends(
        require_permission(
            "ENTREPRISES.MODIFIER"
        )
    ),
):

    return await (
        SiteEntrepriseService.restore_site(
            db,
            entreprise_id=entreprise_id,
            site_id=site_id,
            motif=payload.motif,
            actor=actor,
            request=request,
        )
    )