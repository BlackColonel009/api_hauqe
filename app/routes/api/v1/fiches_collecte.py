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

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.dossier_verification import DossierVerification
from app.permissions.auth import get_current_auth, require_permission
from app.schemas.declarations_collecte import (
    CertificationDeclareeCreateRequest,
    CertificationDeclareeResponse,
    CertificationDeclareeUpdateRequest,
    CollecteQuickOrganismeCreateRequest,
    CollecteQuickOrganismeResponse,
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


@router.post(
    "/quick-organismes",
    response_model=CollecteQuickOrganismeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def quick_create_declared_organisme(
    mission_id: UUID,
    payload: CollecteQuickOrganismeCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("COLLECTE.MODIFIER")),
):
    """Précrée un organisme certificateur depuis une fiche terrain.

    Le service vérifie en complément que l'agent est bien affecté à la
    mission : la permission ne permet pas de créer un organisme depuis une
    mission qui ne lui est pas attribuée.
    """
    return await FicheCollecteService.quick_create_declared_organisme(
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
    actor: AuthContext = Depends(get_current_auth),
):
    """Retourne une fiche de collecte selon son contexte d'utilisation.

    Une fiche rattachée à un dossier de vérification est nécessaire à la
    lecture du dossier par un vérificateur. Ce cas limité ne doit pas ouvrir
    au rôle VERIFICATEUR la consultation générale du module Collecte.
    """
    if "COLLECTE.LIRE" not in actor.permissions:
        dossier_id = None
        if "VERIFICATION.LIRE" in actor.permissions:
            dossier_id = await db.scalar(
                select(DossierVerification.id)
                .where(DossierVerification.fiche_collecte_id == fiche_id)
                .limit(1)
            )
        if dossier_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission insuffisante.",
            )

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
    "/{fiche_id}/reset",
    response_model=FicheCollecteResponse,
)
async def reset_draft_fiche(
    mission_id: UUID,
    fiche_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("COLLECTE.MODIFIER")
    ),
):
    """Réinitialise le contenu d'une fiche courante en brouillon."""
    return await FicheCollecteService.reset_draft(
        db,
        mission_id=mission_id,
        fiche_id=fiche_id,
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


@router.delete("/{fiche_id}/offres/{offre_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_offre(
    mission_id: UUID,
    fiche_id: UUID,
    offre_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("COLLECTE.MODIFIER")),
):
    await FicheCollecteService.delete_offre(
        db, mission_id=mission_id, fiche_id=fiche_id, offre_id=offre_id,
        actor=actor, request=request,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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


@router.delete("/{fiche_id}/certifications/{certification_declaree_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_certification_declaree(
    mission_id: UUID,
    fiche_id: UUID,
    certification_declaree_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("COLLECTE.MODIFIER")),
):
    await FicheCollecteService.delete_certification(
        db, mission_id=mission_id, fiche_id=fiche_id,
        certification_declaree_id=certification_declaree_id,
        actor=actor, request=request,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
