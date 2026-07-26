"""
Routes API de validation hiérarchisée et corrections.

PAGE FRONTEND
-------------
`validations.html` / route SPA `#/validations`.

La page consomme les résultats de Vérification et FUCCS mais n'est pas
autorisée à les modifier.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.permissions.auth import require_permission
from app.schemas.validation_bnec import (
    CorrectionCreateRequest,
    CorrectionResponse,
    CorrectionResubmitRequest,
    CorrectionUpdateRequest,
    ValidationDecisionRequest,
    ValidationListResponse,
    ValidationQueueItem,
    ValidationResponse,
)
from app.services.auth_service import AuthContext
from app.services.validation_bnec_service import ValidationBnecService


router = APIRouter(
    prefix="/validations",
    tags=["Validation hiérarchisée"],
)


@router.get("", response_model=ValidationListResponse)
async def list_validations(
    fiche_id: UUID | None = Query(default=None),
    niveau: str | None = Query(default=None, max_length=255),
    decision: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("VALIDATION.LIRE")),
):
    return await ValidationBnecService.list_validations(
        db,
        fiche_id=fiche_id,
        niveau=niveau,
        decision=decision,
        limit=limit,
        offset=offset,
    )


# Route statique placée avant /{validation_id}.
@router.get("/queue", response_model=list[ValidationQueueItem])
async def validation_queue(
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("VALIDATION.LIRE")),
):
    return await ValidationBnecService.queue(db)


@router.post(
    "/from-fiche/{fiche_id}/level-1",
    response_model=ValidationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def level_1_review(
    fiche_id: UUID,
    payload: ValidationDecisionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("VALIDATION.REVUE_N1")
    ),
):
    return await ValidationBnecService.create_level_decision(
        db,
        fiche_id=fiche_id,
        level="NIVEAU_1",
        payload=payload,
        actor=actor,
        request=request,
    )


@router.post(
    "/from-fiche/{fiche_id}/level-2",
    response_model=ValidationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def level_2_validation(
    fiche_id: UUID,
    payload: ValidationDecisionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("VALIDATION.DECIDER_N2")
    ),
):
    return await ValidationBnecService.create_level_decision(
        db,
        fiche_id=fiche_id,
        level="NIVEAU_2",
        payload=payload,
        actor=actor,
        request=request,
    )


@router.get("/{validation_id}", response_model=ValidationResponse)
async def get_validation(
    validation_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("VALIDATION.LIRE")),
):
    item = await ValidationBnecService.get_validation(db, validation_id)
    from app.services.validation_bnec_service import validation_response
    return validation_response(item)


@router.get(
    "/{validation_id}/corrections",
    response_model=list[CorrectionResponse],
)
async def list_corrections(
    validation_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("VALIDATION.LIRE")),
):
    return await ValidationBnecService.list_corrections(db, validation_id)


@router.post(
    "/{validation_id}/corrections",
    response_model=CorrectionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_correction(
    validation_id: UUID,
    payload: CorrectionCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("VALIDATION.DEMANDER_CORRECTION")
    ),
):
    return await ValidationBnecService.create_correction(
        db,
        validation_id=validation_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@router.patch(
    "/{validation_id}/corrections/{correction_id}",
    response_model=CorrectionResponse,
)
async def update_correction(
    validation_id: UUID,
    correction_id: UUID,
    payload: CorrectionUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("VALIDATION.DEMANDER_CORRECTION")
    ),
):
    return await ValidationBnecService.update_correction(
        db,
        validation_id=validation_id,
        correction_id=correction_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@router.post(
    "/{validation_id}/corrections/{correction_id}/resubmit",
    response_model=CorrectionResponse,
)
async def resubmit_correction(
    validation_id: UUID,
    correction_id: UUID,
    payload: CorrectionResubmitRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("VALIDATION.RESOUMETTRE_CORRECTION")
    ),
):
    return await ValidationBnecService.resubmit_correction(
        db,
        validation_id=validation_id,
        correction_id=correction_id,
        payload=payload,
        actor=actor,
        request=request,
    )
