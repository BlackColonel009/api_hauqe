"""API de lecture du parcours opérationnel d'une fiche de collecte."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.permissions.auth import get_current_auth
from app.schemas.dossier_parcours import ParcoursDossierResponse
from app.services.auth_service import AuthContext
from app.services.dossier_parcours_service import DossierParcoursService


router = APIRouter(prefix="/parcours-dossier", tags=["Parcours de dossier"])


@router.get("/{source}/{resource_id}", response_model=ParcoursDossierResponse)
async def get_dossier_parcours(
    source: Literal["fiche", "verification", "controle", "validation", "integration"],
    resource_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(get_current_auth),
):
    """Expose uniquement l'état opérationnel d'un dossier déjà accessible."""
    return await DossierParcoursService.for_source(
        db, source=source, resource_id=resource_id
    )
