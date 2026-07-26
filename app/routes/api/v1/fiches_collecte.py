"""
Routes API des fiches, révisions et déclarations de collecte.

PERMISSIONS
-----------
COLLECTE.LIRE      : consultation
COLLECTE.CREER     : création initiale
COLLECTE.MODIFIER  : édition d'un brouillon et déclarations
COLLECTE.SOUMETTRE : soumission
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.permissions.auth import require_permission
from app.schemas.declarations_collecte import (
    CertificationDeclareeCreateRequest,
    CertificationDeclareeResponse,
    CertificationDeclareeUpdateRequest,
    OffreDeclareeCreateRequest,
    OffreDeclareeResponse,
    OffreDeclareeUpdateRequest,
)
from app.schemas.fiche_collecte import (
    EvenementCollecteResponse,
    FicheCollecteCreateRequest,
    FicheCollecteResponse,
    FicheCollecteRevisionRequest,
    FicheCollecteSubmitRequest,
    FicheCollecteUpdateRequest,
)
from app.services.auth_service import AuthContext
from app.services.fiche_collecte_service import (
    FicheCollecteService,
)


router = APIRouter(
    prefix="/missions/{mission_id}/fiches",
    tags=["Collecte - Fiches"],
)


# Route statique avant /{fiche_id}.
@router.get(
    "/current",
    response_model=FicheCollecteResponse,
)
async def get_current_fiche(
    mission_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("COLLECTE.LIRE")
    ),
):
    return await FicheCollecteService.current(db, mission_id)


@router.get(
    "",
    response_model=list[FicheCollecteResponse],
)
async def list_revisions(
    mission_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("COLLECTE.LIRE")
    ),
):
    return await FicheCollecteService.list_revisions(
        db,
        mission_id,
    )


@router.post(
    "",
    response_model=FicheCollecteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_fiche(
    mission_id: UUID,
    payload: FicheCollecteCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("COLLECTE.CREER")
    ),
):
    return await FicheCollecteService.create(
        db,
        mission_id=mission_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@router.get(
    "/{fiche_id}",
    response_model=FicheCollecteResponse,
)
async def get_fiche(
    mission_id: UUID,
    fiche_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("COLLECTE.LIRE")
    ),
):
    from app.services.fiche_collecte_service import fiche_response
    return fiche_response(
        await FicheCollecteService.get(
            db,
            mission_id=mission_id,
            fiche_id=fiche_id,
        )
    )


@router.patch(
    "/{fiche_id}",
    response_model=FicheCollecteResponse,
)
async def update_fiche(
    mission_id: UUID,
    fiche_id: UUID,
    payload: FicheCollecteUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("COLLECTE.MODIFIER")
    ),
):
    return await FicheCollecteService.update(
        db,
        mission_id=mission_id,
        fiche_id=fiche_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@router.post(
    "/{fiche_id}/submit",
    response_model=FicheCollecteResponse,
)
async def submit_fiche(
    mission_id: UUID,
    fiche_id: UUID,
    payload: FicheCollecteSubmitRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("COLLECTE.SOUMETTRE")
    ),
):
    return await FicheCollecteService.submit(
        db,
        mission_id=mission_id,
        fiche_id=fiche_id,
        commentaire=payload.commentaire,
        actor=actor,
        request=request,
    )


@router.post(
    "/{fiche_id}/revision",
    response_model=FicheCollecteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_revision(
    mission_id: UUID,
    fiche_id: UUID,
    payload: FicheCollecteRevisionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("COLLECTE.MODIFIER")
    ),
):
    return await FicheCollecteService.create_revision(
        db,
        mission_id=mission_id,
        fiche_id=fiche_id,
        commentaire=payload.commentaire,
        actor=actor,
        request=request,
    )


@router.get(
    "/{fiche_id}/offres",
    response_model=list[OffreDeclareeResponse],
)
async def list_offres(
    mission_id: UUID,
    fiche_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("COLLECTE.LIRE")
    ),
):
    return await FicheCollecteService.list_offres(
        db,
        mission_id=mission_id,
        fiche_id=fiche_id,
    )


@router.post(
    "/{fiche_id}/offres",
    response_model=OffreDeclareeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_offre(
    mission_id: UUID,
    fiche_id: UUID,
    payload: OffreDeclareeCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("COLLECTE.MODIFIER")
    ),
):
    return await FicheCollecteService.create_offre(
        db,
        mission_id=mission_id,
        fiche_id=fiche_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@router.patch(
    "/{fiche_id}/offres/{offre_id}",
    response_model=OffreDeclareeResponse,
)
async def update_offre(
    mission_id: UUID,
    fiche_id: UUID,
    offre_id: UUID,
    payload: OffreDeclareeUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("COLLECTE.MODIFIER")
    ),
):
    return await FicheCollecteService.update_offre(
        db,
        mission_id=mission_id,
        fiche_id=fiche_id,
        offre_id=offre_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@router.get(
    "/{fiche_id}/certifications",
    response_model=list[CertificationDeclareeResponse],
)
async def list_certifications_declarees(
    mission_id: UUID,
    fiche_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("COLLECTE.LIRE")
    ),
):
    return await FicheCollecteService.list_certifications(
        db,
        mission_id=mission_id,
        fiche_id=fiche_id,
    )


@router.post(
    "/{fiche_id}/certifications",
    response_model=CertificationDeclareeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_certification_declaree(
    mission_id: UUID,
    fiche_id: UUID,
    payload: CertificationDeclareeCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("COLLECTE.MODIFIER")
    ),
):
    return await FicheCollecteService.create_certification(
        db,
        mission_id=mission_id,
        fiche_id=fiche_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@router.patch(
    "/{fiche_id}/certifications/{certification_declaree_id}",
    response_model=CertificationDeclareeResponse,
)
async def update_certification_declaree(
    mission_id: UUID,
    fiche_id: UUID,
    certification_declaree_id: UUID,
    payload: CertificationDeclareeUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("COLLECTE.MODIFIER")
    ),
):
    return await FicheCollecteService.update_certification(
        db,
        mission_id=mission_id,
        fiche_id=fiche_id,
        certification_declaree_id=certification_declaree_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@router.get(
    "/{fiche_id}/history",
    response_model=list[EvenementCollecteResponse],
)
async def fiche_history(
    mission_id: UUID,
    fiche_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("COLLECTE.LIRE")
    ),
):
    return await FicheCollecteService.history(
        db,
        mission_id=mission_id,
        fiche_id=fiche_id,
    )
