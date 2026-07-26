"""
Routes API — Scoring / Classification entreprise / INFC / SNCC.

PAGES FRONTEND
--------------
- `scoring.html` / `#/scoring` :
  synthèse des trois résultats indépendants + historiques.
- `#/infc` :
  calcul, validation et historique INFC par certification.
- `#/classement-sncc` :
  classement courant, historique et reclassements.
- `regles-codification.html` :
  administration des modèles de scoring et pondérations.

Aucun endpoint ne convertit automatiquement le score FUCCS en INFC.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.permissions.auth import require_permission
from app.schemas.scoring import (
    EnterpriseClassificationListResponse,
    EnterpriseClassificationResponse,
    InfcResultListResponse,
    InfcResultResponse,
    InfcValidateRequest,
    ScoreComputationPreviewResponse,
    ScoreEvaluationInput,
    ScoringModelCloneRequest,
    ScoringModelCreateRequest,
    ScoringModelPublishRequest,
    ScoringModelResponse,
    ScoringModelRetireRequest,
    ScoringModelUpdateRequest,
    ScoringWeightCreateRequest,
    ScoringWeightResponse,
    ScoringWeightUpdateRequest,
    SnccCloseRequest,
    SnccCreateRequest,
    SnccListResponse,
    SnccReclassifyRequest,
    SnccResponse,
)
from app.services.auth_service import AuthContext
from app.services.scoring_service import ScoringService


# ============================================================
# MODÈLES DE SCORING
# ============================================================

scoring_router = APIRouter(
    prefix="/scoring",
    tags=["Scoring - Modèles"],
)


@scoring_router.get(
    "/models",
    response_model=list[ScoringModelResponse],
)
async def list_models(
    objet_evalue: str | None = Query(default=None, max_length=255),
    statut: str | None = Query(default=None, max_length=255),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("SCORING.LIRE")),
):
    return await ScoringService.list_models(
        db,
        objet_evalue=objet_evalue,
        statut=statut,
    )


# Route statique avant /models/{model_id}.
@scoring_router.get(
    "/models/active",
    response_model=ScoringModelResponse,
)
async def active_model(
    objet_evalue: str = Query(min_length=1, max_length=255),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("SCORING.LIRE")),
):
    return await ScoringService.active_model_response(
        db,
        objet_evalue,
    )


@scoring_router.post(
    "/models",
    response_model=ScoringModelResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_model(
    payload: ScoringModelCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("SCORING.ADMINISTRER_MODELE")
    ),
):
    return await ScoringService.create_model(
        db,
        payload=payload,
        actor=actor,
        request=request,
    )


@scoring_router.get(
    "/models/{model_id}",
    response_model=ScoringModelResponse,
)
async def get_model(
    model_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("SCORING.LIRE")),
):
    model = await ScoringService.require_model(db, model_id)
    return await ScoringService.model_response(db, model)


@scoring_router.patch(
    "/models/{model_id}",
    response_model=ScoringModelResponse,
)
async def update_model(
    model_id: UUID,
    payload: ScoringModelUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("SCORING.ADMINISTRER_MODELE")
    ),
):
    return await ScoringService.update_model(
        db,
        model_id=model_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@scoring_router.post(
    "/models/{model_id}/clone",
    response_model=ScoringModelResponse,
    status_code=status.HTTP_201_CREATED,
)
async def clone_model(
    model_id: UUID,
    payload: ScoringModelCloneRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("SCORING.ADMINISTRER_MODELE")
    ),
):
    return await ScoringService.clone_model(
        db,
        model_id=model_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@scoring_router.post(
    "/models/{model_id}/publish",
    response_model=ScoringModelResponse,
)
async def publish_model(
    model_id: UUID,
    payload: ScoringModelPublishRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("SCORING.ADMINISTRER_MODELE")
    ),
):
    return await ScoringService.publish_model(
        db,
        model_id=model_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@scoring_router.post(
    "/models/{model_id}/retire",
    response_model=ScoringModelResponse,
)
async def retire_model(
    model_id: UUID,
    payload: ScoringModelRetireRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("SCORING.ADMINISTRER_MODELE")
    ),
):
    return await ScoringService.retire_model(
        db,
        model_id=model_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@scoring_router.get(
    "/models/{model_id}/weights",
    response_model=list[ScoringWeightResponse],
)
async def list_weights(
    model_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("SCORING.LIRE")),
):
    return await ScoringService.list_weights(db, model_id)


@scoring_router.post(
    "/models/{model_id}/weights",
    response_model=ScoringWeightResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_weight(
    model_id: UUID,
    payload: ScoringWeightCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("SCORING.ADMINISTRER_MODELE")
    ),
):
    return await ScoringService.create_weight(
        db,
        model_id=model_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@scoring_router.patch(
    "/models/{model_id}/weights/{weight_id}",
    response_model=ScoringWeightResponse,
)
async def update_weight(
    model_id: UUID,
    weight_id: UUID,
    payload: ScoringWeightUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("SCORING.ADMINISTRER_MODELE")
    ),
):
    return await ScoringService.update_weight(
        db,
        model_id=model_id,
        weight_id=weight_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@scoring_router.post(
    "/models/{model_id}/weights/{weight_id}/deactivate",
    response_model=ScoringWeightResponse,
)
async def deactivate_weight(
    model_id: UUID,
    weight_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("SCORING.ADMINISTRER_MODELE")
    ),
):
    return await ScoringService.deactivate_weight(
        db,
        model_id=model_id,
        weight_id=weight_id,
        actor=actor,
        request=request,
    )


@scoring_router.post(
    "/preview/{object_type}",
    response_model=ScoreComputationPreviewResponse,
)
async def preview_calculation(
    object_type: str,
    payload: ScoreEvaluationInput,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("SCORING.LIRE")),
):
    """
    Simulation sans écriture.

    Sert notamment au simulateur de `regles-codification.html`.
    """
    return await ScoringService.preview(
        db,
        object_type=object_type,
        payload=payload,
    )


# ============================================================
# CLASSIFICATION ENTREPRISE
# ============================================================

enterprise_classification_router = APIRouter(
    prefix="/entreprises/{enterprise_id}/classifications",
    tags=["Classification entreprise"],
)


@enterprise_classification_router.get(
    "",
    response_model=EnterpriseClassificationListResponse,
)
async def list_enterprise_classifications(
    enterprise_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("CLASSIFICATION.LIRE")
    ),
):
    return await ScoringService.list_enterprise_classifications(
        db,
        enterprise_id,
    )


@enterprise_classification_router.get(
    "/latest",
    response_model=EnterpriseClassificationResponse,
)
async def latest_enterprise_classification(
    enterprise_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("CLASSIFICATION.LIRE")
    ),
):
    return await ScoringService.latest_enterprise_classification(
        db,
        enterprise_id,
    )


@enterprise_classification_router.post(
    "/evaluate",
    response_model=EnterpriseClassificationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def evaluate_enterprise(
    enterprise_id: UUID,
    payload: ScoreEvaluationInput,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("CLASSIFICATION.CALCULER_VALIDER")
    ),
):
    return await ScoringService.evaluate_enterprise(
        db,
        enterprise_id=enterprise_id,
        payload=payload,
        actor=actor,
        request=request,
    )


# ============================================================
# INFC
# ============================================================

infc_router = APIRouter(
    prefix="/infc",
    tags=["INFC"],
)

cert_infc_router = APIRouter(
    prefix="/certifications/{certification_id}/infc",
    tags=["INFC"],
)


@infc_router.get(
    "/results",
    response_model=InfcResultListResponse,
)
async def list_infc_results(
    certification_id: UUID | None = Query(default=None),
    model_id: UUID | None = Query(default=None),
    statut: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("INFC.LIRE")),
):
    return await ScoringService.list_infc(
        db,
        certification_id=certification_id,
        model_id=model_id,
        statut_filter=statut,
        limit=limit,
        offset=offset,
    )


@infc_router.post(
    "/results/{result_id}/validate",
    response_model=InfcResultResponse,
)
async def validate_infc_result(
    result_id: UUID,
    payload: InfcValidateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("INFC.VALIDER")),
):
    return await ScoringService.validate_infc(
        db,
        result_id=result_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@cert_infc_router.get(
    "",
    response_model=InfcResultListResponse,
)
async def certification_infc_history(
    certification_id: UUID,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("INFC.LIRE")),
):
    return await ScoringService.list_infc(
        db,
        certification_id=certification_id,
        model_id=None,
        statut_filter=None,
        limit=limit,
        offset=offset,
    )


@cert_infc_router.get(
    "/latest",
    response_model=InfcResultResponse,
)
async def latest_infc_result(
    certification_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("INFC.LIRE")),
):
    return await ScoringService.latest_infc(
        db,
        certification_id,
    )


@cert_infc_router.post(
    "/calculate",
    response_model=InfcResultResponse,
    status_code=status.HTTP_201_CREATED,
)
async def calculate_infc(
    certification_id: UUID,
    payload: ScoreEvaluationInput,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("INFC.CALCULER")),
):
    return await ScoringService.calculate_infc(
        db,
        certification_id=certification_id,
        payload=payload,
        actor=actor,
        request=request,
    )


# ============================================================
# SNCC
# ============================================================

sncc_router = APIRouter(
    prefix="/sncc",
    tags=["SNCC"],
)

cert_sncc_router = APIRouter(
    prefix="/certifications/{certification_id}/sncc",
    tags=["SNCC"],
)


@sncc_router.get(
    "",
    response_model=SnccListResponse,
)
async def list_sncc(
    certification_id: UUID | None = Query(default=None),
    classe: str | None = Query(default=None, max_length=255),
    statut_administratif: str | None = Query(default=None, max_length=255),
    niveau_risque: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("SNCC.LIRE")),
):
    return await ScoringService.list_sncc(
        db,
        certification_id=certification_id,
        classe=classe,
        statut_administratif=statut_administratif,
        niveau_risque=niveau_risque,
        limit=limit,
        offset=offset,
    )


@sncc_router.post(
    "/{sncc_id}/close",
    response_model=SnccResponse,
)
async def close_sncc(
    sncc_id: UUID,
    payload: SnccCloseRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("SNCC.RECLASSER")),
):
    return await ScoringService.close_sncc(
        db,
        sncc_id=sncc_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@cert_sncc_router.get(
    "",
    response_model=SnccListResponse,
)
async def certification_sncc_history(
    certification_id: UUID,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("SNCC.LIRE")),
):
    return await ScoringService.list_sncc(
        db,
        certification_id=certification_id,
        classe=None,
        statut_administratif=None,
        niveau_risque=None,
        limit=limit,
        offset=offset,
    )


@cert_sncc_router.get(
    "/current",
    response_model=SnccResponse,
)
async def current_sncc(
    certification_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("SNCC.LIRE")),
):
    return await ScoringService.current_sncc(
        db,
        certification_id,
    )


@cert_sncc_router.post(
    "",
    response_model=SnccResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_sncc(
    certification_id: UUID,
    payload: SnccCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("SNCC.CLASSER")),
):
    return await ScoringService.create_sncc(
        db,
        certification_id=certification_id,
        payload=payload,
        actor=actor,
        request=request,
    )


@cert_sncc_router.post(
    "/reclassify",
    response_model=SnccResponse,
    status_code=status.HTTP_201_CREATED,
)
async def reclassify_sncc(
    certification_id: UUID,
    payload: SnccReclassifyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("SNCC.RECLASSER")),
):
    return await ScoringService.reclassify_sncc(
        db,
        certification_id=certification_id,
        payload=payload,
        actor=actor,
        request=request,
    )
