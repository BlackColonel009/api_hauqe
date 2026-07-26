"""
Routes FastAPI du contrôle des doublons d'entreprises.

CHOIX D'URL
-----------
Le candidat de doublon relie DEUX entreprises. Il n'appartient donc pas
naturellement à une seule entreprise de l'URL.

On utilise :
    /api/v1/doublons-entreprises

et le GET permet de filtrer sur `entreprise_id` pour retrouver tous les
contrôles où l'entreprise apparaît comme source ou cible.

PERMISSIONS
-----------
Lecture : ENTREPRISES.LIRE
Création / décision : VERIFICATION.VERIFIER

Ce choix évite qu'un simple utilisateur autorisé à modifier une fiche
entreprise puisse prononcer une décision de contrôle de doublon.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.permissions.auth import require_permission
from app.schemas.candidat_doublon import (
    CandidatDoublonCreateRequest,
    CandidatDoublonDecisionRequest,
    CandidatDoublonListResponse,
    CandidatDoublonResponse,
)
from app.services.auth_service import AuthContext
from app.services.candidat_doublon_service import (
    CandidatDoublonService,
)


router = APIRouter(
    prefix="/doublons-entreprises",
    tags=["Entreprises - Contrôle doublons"],
)


@router.get(
    "",
    response_model=CandidatDoublonListResponse,
)
async def list_candidats_doublon(
    entreprise_id: UUID | None = Query(default=None),
    statut_examen: str | None = Query(
        default=None,
        max_length=255,
    ),
    decision: str | None = Query(
        default=None,
        max_length=255,
    ),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("ENTREPRISES.LIRE")
    ),
):
    return await CandidatDoublonService.list_candidats(
        db,
        entreprise_id=entreprise_id,
        statut_examen=statut_examen,
        decision=decision,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{candidat_id}",
    response_model=CandidatDoublonResponse,
)
async def get_candidat_doublon(
    candidat_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("ENTREPRISES.LIRE")
    ),
):
    return await CandidatDoublonService.get_candidat(
        db,
        candidat_id=candidat_id,
    )


@router.post(
    "",
    response_model=CandidatDoublonResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_candidat_doublon(
    payload: CandidatDoublonCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("VERIFICATION.VERIFIER")
    ),
):
    return await CandidatDoublonService.create_candidat(
        db,
        payload=payload,
        actor=actor,
        request=request,
    )


@router.post(
    "/{candidat_id}/decision",
    response_model=CandidatDoublonResponse,
)
async def decide_candidat_doublon(
    candidat_id: UUID,
    payload: CandidatDoublonDecisionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("VERIFICATION.VERIFIER")
    ),
):
    return await CandidatDoublonService.decide(
        db,
        candidat_id=candidat_id,
        payload=payload,
        actor=actor,
        request=request,
    )
