"""
Routes API de la file d'intégration BNEC.

PAGE FRONTEND
-------------
`integrations.html` / route SPA `#/integrations`.

La validation autorise l'entrée dans cette file ; elle n'intègre pas
automatiquement les données.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.permissions.auth import require_permission
from app.schemas.validation_bnec import (
    IntegrationCheckRequest,
    IntegrationElementCreateRequest,
    IntegrationElementResponse,
    IntegrationElementResultRequest,
    IntegrationElementUpdateRequest,
    IntegrationListResponse,
    IntegrationOpenRequest,
    IntegrationQueueItem,
    IntegrationResponse,
    IntegrationStartRequest,
)
from app.services.auth_service import AuthContext
from app.services.validation_bnec_service import ValidationBnecService


router = APIRouter(
    prefix="/integrations-bnec",
    tags=["Intégration BNEC"],
)

validation_integration_router = APIRouter(
    prefix="/validations/{validation_id}/integration-bnec",
    tags=["Intégration BNEC"],
)


@router.get("", response_model=IntegrationListResponse)
async def list_integrations(
    statut: str | None = Query(default=None, max_length=255),
    validation_id: UUID | None = Query(default=None),
    administrateur_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("INTEGRATION.LIRE")),
):
    return await ValidationBnecService.list_integrations(
        db,
        statut=statut,
        validation_id=validation_id,
        administrateur_id=administrateur_id,
        limit=limit,
        offset=offset,
    )


# Route statique avant /{integration_id}.
@router.get("/queue", response_model=list[IntegrationQueueItem])
async def integration_queue(
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("INTEGRATION.LIRE")),
):
    return await ValidationBnecService.integration_queue(db)


@validation_integration_router.post(
    "",
    response_model=IntegrationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def open_integration(
    validation_id: UUID,
    payload: IntegrationOpenRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("INTEGRATION.OUVRIR")),
):
    return await ValidationBnecService.open_integration(
        db,
        validation_id=validation_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@router.get("/{integration_id}", response_model=IntegrationResponse)
async def get_integration(
    integration_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("INTEGRATION.LIRE")),
):
    item = await ValidationBnecService.get_integration(db, integration_id)
    return await ValidationBnecService.integration_response(db, item)


@router.post("/{integration_id}/precontrol", response_model=IntegrationResponse)
async def precontrol(
    integration_id: UUID,
    payload: IntegrationCheckRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("INTEGRATION.PRECONTROLER")
    ),
):
    return await ValidationBnecService.precontrol(
        db,
        integration_id=integration_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@router.post("/{integration_id}/start", response_model=IntegrationResponse)
async def start_integration(
    integration_id: UUID,
    payload: IntegrationStartRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("INTEGRATION.EXECUTER")),
):
    return await ValidationBnecService.start(
        db,
        integration_id=integration_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@router.get(
    "/{integration_id}/elements",
    response_model=list[IntegrationElementResponse],
)
async def list_elements(
    integration_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("INTEGRATION.LIRE")),
):
    return await ValidationBnecService.list_elements(db, integration_id)


@router.post(
    "/{integration_id}/elements",
    response_model=IntegrationElementResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_element(
    integration_id: UUID,
    payload: IntegrationElementCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("INTEGRATION.EXECUTER")),
):
    return await ValidationBnecService.create_element(
        db,
        integration_id=integration_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@router.patch(
    "/{integration_id}/elements/{element_id}",
    response_model=IntegrationElementResponse,
)
async def update_element(
    integration_id: UUID,
    element_id: UUID,
    payload: IntegrationElementUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("INTEGRATION.EXECUTER")),
):
    return await ValidationBnecService.update_element(
        db,
        integration_id=integration_id,
        element_id=element_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@router.post(
    "/{integration_id}/elements/{element_id}/result",
    response_model=IntegrationElementResponse,
)
async def element_result(
    integration_id: UUID,
    element_id: UUID,
    payload: IntegrationElementResultRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("INTEGRATION.EXECUTER")),
):
    return await ValidationBnecService.element_result(
        db,
        integration_id=integration_id,
        element_id=element_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@router.post("/{integration_id}/postcontrol", response_model=IntegrationResponse)
async def postcontrol(
    integration_id: UUID,
    payload: IntegrationCheckRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("INTEGRATION.POSTCONTROLER")
    ),
):
    return await ValidationBnecService.postcontrol(
        db,
        integration_id=integration_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@router.post("/{integration_id}/complete", response_model=IntegrationResponse)
async def complete_integration(
    integration_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("INTEGRATION.CLOTURER")
    ),
):
    return await ValidationBnecService.complete(
        db,
        integration_id=integration_id,
        actor=actor,
        request=request,
    )
