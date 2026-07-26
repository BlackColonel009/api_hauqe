"""
Routes FastAPI des offres d'entreprise.

URL RACINE
----------
/api/v1/entreprises/{entreprise_id}/offres

PERMISSIONS
-----------
Lecture : ENTREPRISES.LIRE
Création : ENTREPRISES.CREER
Modification / désactivation / restauration : ENTREPRISES.MODIFIER
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.permissions.auth import require_permission
from app.schemas.offre_entreprise import (
    OffreEntrepriseCreateRequest,
    OffreEntrepriseResponse,
    OffreEntrepriseStatusRequest,
    OffreEntrepriseUpdateRequest,
)
from app.services.auth_service import AuthContext
from app.services.offre_entreprise_service import OffreEntrepriseService


router = APIRouter(
    prefix="/entreprises/{entreprise_id}/offres",
    tags=["Entreprises - Offres"],
)


@router.get(
    "",
    response_model=list[OffreEntrepriseResponse],
)
async def list_offres(
    entreprise_id: UUID,
    include_inactive: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("ENTREPRISES.LIRE")
    ),
):
    return await OffreEntrepriseService.list_offres(
        db,
        entreprise_id=entreprise_id,
        include_inactive=include_inactive,
    )


@router.get(
    "/{offre_id}",
    response_model=OffreEntrepriseResponse,
)
async def get_offre(
    entreprise_id: UUID,
    offre_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("ENTREPRISES.LIRE")
    ),
):
    return await OffreEntrepriseService.get_offre(
        db,
        entreprise_id=entreprise_id,
        offre_id=offre_id,
    )


@router.post(
    "",
    response_model=OffreEntrepriseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_offre(
    entreprise_id: UUID,
    payload: OffreEntrepriseCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("ENTREPRISES.CREER")
    ),
):
    return await OffreEntrepriseService.create_offre(
        db,
        entreprise_id=entreprise_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@router.patch(
    "/{offre_id}",
    response_model=OffreEntrepriseResponse,
)
async def update_offre(
    entreprise_id: UUID,
    offre_id: UUID,
    payload: OffreEntrepriseUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("ENTREPRISES.MODIFIER")
    ),
):
    return await OffreEntrepriseService.update_offre(
        db,
        entreprise_id=entreprise_id,
        offre_id=offre_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@router.post(
    "/{offre_id}/deactivate",
    response_model=OffreEntrepriseResponse,
)
async def deactivate_offre(
    entreprise_id: UUID,
    offre_id: UUID,
    payload: OffreEntrepriseStatusRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("ENTREPRISES.MODIFIER")
    ),
):
    return await OffreEntrepriseService.deactivate_offre(
        db,
        entreprise_id=entreprise_id,
        offre_id=offre_id,
        motif=payload.motif,
        actor=actor,
        request=request,
    )


@router.post(
    "/{offre_id}/restore",
    response_model=OffreEntrepriseResponse,
)
async def restore_offre(
    entreprise_id: UUID,
    offre_id: UUID,
    payload: OffreEntrepriseStatusRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("ENTREPRISES.MODIFIER")
    ),
):
    return await OffreEntrepriseService.restore_offre(
        db,
        entreprise_id=entreprise_id,
        offre_id=offre_id,
        motif=payload.motif,
        actor=actor,
        request=request,
    )
