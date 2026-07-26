"""
Routes FastAPI des contacts d'entreprise.

URL RACINE
----------
/api/v1/entreprises/{entreprise_id}/contacts

SÉCURITÉ
--------
Lecture :
    ENTREPRISES.LIRE

Création :
    ENTREPRISES.CREER

Modification / désactivation / restauration :
    ENTREPRISES.MODIFIER

Nous réutilisons volontairement les permissions Entreprises
existantes afin de ne pas créer artificiellement un nouveau
domaine RBAC uniquement pour les contacts.
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
from app.schemas.contact_entreprise import (
    ContactEntrepriseCreateRequest,
    ContactEntrepriseResponse,
    ContactEntrepriseUpdateRequest,
    ContactStatusRequest,
)
from app.services.auth_service import AuthContext
from app.services.contact_entreprise_service import (
    ContactEntrepriseService,
)


router = APIRouter(
    prefix="/entreprises/{entreprise_id}/contacts",
    tags=["Entreprises - Contacts"],
)


# ============================================================
# LISTE
# ============================================================

@router.get(
    "",
    response_model=list[ContactEntrepriseResponse],
)
async def list_contacts(
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
        ContactEntrepriseService.list_contacts(
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
    response_model=ContactEntrepriseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_contact(
    entreprise_id: UUID,
    payload: ContactEntrepriseCreateRequest,
    request: Request,

    db: AsyncSession = Depends(get_db),

    actor: AuthContext = Depends(
        require_permission(
            "ENTREPRISES.CREER"
        )
    ),
):
    return await (
        ContactEntrepriseService.create_contact(
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
    "/{contact_id}",
    response_model=ContactEntrepriseResponse,
)
async def update_contact(
    entreprise_id: UUID,
    contact_id: UUID,
    payload: ContactEntrepriseUpdateRequest,
    request: Request,

    db: AsyncSession = Depends(get_db),

    actor: AuthContext = Depends(
        require_permission(
            "ENTREPRISES.MODIFIER"
        )
    ),
):
    return await (
        ContactEntrepriseService.update_contact(
            db,
            entreprise_id=entreprise_id,
            contact_id=contact_id,
            payload=payload,
            actor=actor,
            request=request,
        )
    )


# ============================================================
# DÉSACTIVATION
# ============================================================

@router.post(
    "/{contact_id}/deactivate",
    response_model=ContactEntrepriseResponse,
)
async def deactivate_contact(
    entreprise_id: UUID,
    contact_id: UUID,
    payload: ContactStatusRequest,
    request: Request,

    db: AsyncSession = Depends(get_db),

    actor: AuthContext = Depends(
        require_permission(
            "ENTREPRISES.MODIFIER"
        )
    ),
):
    return await (
        ContactEntrepriseService.deactivate_contact(
            db,
            entreprise_id=entreprise_id,
            contact_id=contact_id,
            motif=payload.motif,
            actor=actor,
            request=request,
        )
    )


# ============================================================
# RESTAURATION
# ============================================================

@router.post(
    "/{contact_id}/restore",
    response_model=ContactEntrepriseResponse,
)
async def restore_contact(
    entreprise_id: UUID,
    contact_id: UUID,
    payload: ContactStatusRequest,
    request: Request,

    db: AsyncSession = Depends(get_db),

    actor: AuthContext = Depends(
        require_permission(
            "ENTREPRISES.MODIFIER"
        )
    ),
):
    return await (
        ContactEntrepriseService.restore_contact(
            db,
            entreprise_id=entreprise_id,
            contact_id=contact_id,
            motif=payload.motif,
            actor=actor,
            request=request,
        )
    )