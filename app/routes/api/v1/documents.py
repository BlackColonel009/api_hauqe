"""
Routes sécurisées de gestion documentaire.

Les fichiers privés ne sont jamais servis depuis `app/static`.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.permissions.auth import require_permission
from app.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
    DocumentStatusRequest,
    DocumentVerificationRequest,
)
from app.services.auth_service import AuthContext
from app.services.document_service import DocumentService, build_response


router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    ressource_type: str | None = Query(default=None, max_length=255),
    ressource_id: UUID | None = Query(default=None),
    include_inactive: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("DOCUMENTS.LIRE")),
):
    return await DocumentService.list(
        db, ressource_type=ressource_type, ressource_id=ressource_id,
        include_inactive=include_inactive, limit=limit, offset=offset
    )


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    type_document: str = Form(...),
    ressource_type: str = Form(...),
    ressource_id: UUID = Form(...),
    confidentialite: str | None = Form(default="INTERNE"),
    source: str | None = Form(default="API"),
    date_document: date | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("DOCUMENTS.DEPOSER")),
):
    return await DocumentService.upload(
        db, file=file, type_document=type_document,
        ressource_type=ressource_type, ressource_id=ressource_id,
        confidentialite=confidentialite, source=source,
        date_document=date_document, actor=actor, request=request
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("DOCUMENTS.LIRE")),
):
    return build_response(await DocumentService.get(db, document_id))


@router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("DOCUMENTS.TELECHARGER")),
):
    item, path = await DocumentService.secure_path(db, document_id)
    return FileResponse(
        path=path,
        filename=item.nom_original or item.nom_stockage,
        media_type="application/octet-stream",
    )


@router.post("/{document_id}/verification", response_model=DocumentResponse)
async def verify_document(
    document_id: UUID,
    payload: DocumentVerificationRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("DOCUMENTS.VERIFIER")),
):
    return await DocumentService.verify(
        db, document_id=document_id,
        statut_verification=payload.statut_verification,
        motif=payload.motif, actor=actor, request=request
    )


@router.post("/{document_id}/deactivate", response_model=DocumentResponse)
async def deactivate_document(
    document_id: UUID,
    payload: DocumentStatusRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("DOCUMENTS.VERIFIER")),
):
    return await DocumentService.deactivate(
        db, document_id=document_id, motif=payload.motif,
        actor=actor, request=request
    )


@router.post("/{document_id}/restore", response_model=DocumentResponse)
async def restore_document(
    document_id: UUID,
    payload: DocumentStatusRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("DOCUMENTS.VERIFIER")),
):
    return await DocumentService.restore(
        db, document_id=document_id, motif=payload.motif,
        actor=actor, request=request
    )
