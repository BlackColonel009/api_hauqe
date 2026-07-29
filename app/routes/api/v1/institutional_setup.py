from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.permissions.auth import require_permission
from app.schemas.institutional_setup import (
    CompletenessCatalogResponse,
    CompletenessValidateRequest,
    CompletenessValidateResponse,
    InstitutionalReadinessResponse,
)
from app.services.auth_service import AuthContext
from app.services.institutional_setup_service import InstitutionalSetupService


router = APIRouter(
    prefix="/governance/setup",
    tags=["Gouvernance - Paramétrage institutionnel"],
)


@router.get(
    "/readiness",
    response_model=InstitutionalReadinessResponse,
)
async def readiness(
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("GOUVERNANCE.LIRE")),
):
    return await InstitutionalSetupService.readiness(db)


@router.get(
    "/collecte-completeness/catalog",
    response_model=CompletenessCatalogResponse,
)
async def completeness_catalog(
    actor: AuthContext = Depends(require_permission("GOUVERNANCE.LIRE")),
):
    return InstitutionalSetupService.completeness_catalog()


@router.post(
    "/collecte-completeness/validate",
    response_model=CompletenessValidateResponse,
)
async def validate_completeness(
    payload: CompletenessValidateRequest,
    actor: AuthContext = Depends(
        require_permission("GOUVERNANCE.ADMINISTRER_REGLES")
    ),
):
    return InstitutionalSetupService.validate_completeness(
        payload.parametres
    )
