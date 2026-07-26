"""
Schémas API — Scoring / Classification entreprise / INFC / SNCC.

PRINCIPES
---------
1. Les trois résultats restent indépendants :
   - classification globale de l'entreprise ;
   - INFC d'une certification ;
   - classement SNCC d'une certification.
2. Aucun passage FUCCS -> INFC n'est automatique.
3. Les seuils, pondérations, arrondis et règles de calcul sont versionnés
   dans `modeles_scoring` + `ponderations_scoring`.
4. Aucune valeur métier provisoire n'est codée en dur dans ce module.
5. Le MPD physique reste inchangé.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================
# MODÈLES DE SCORING / PONDÉRATIONS
# ============================================================

class ScoringModelCreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=255)
    libelle: str = Field(min_length=1, max_length=255)
    version: str = Field(min_length=1, max_length=255)
    objet_evalue: str = Field(min_length=1, max_length=255)
    description: str | None = None
    date_debut_validite: date | None = None
    date_fin_validite: date | None = None
    regle_calcul: dict[str, Any]


class ScoringModelUpdateRequest(BaseModel):
    libelle: str | None = Field(default=None, max_length=255)
    description: str | None = None
    date_debut_validite: date | None = None
    date_fin_validite: date | None = None
    regle_calcul: dict[str, Any] | None = None


class ScoringModelCloneRequest(BaseModel):
    code: str = Field(min_length=1, max_length=255)
    libelle: str = Field(min_length=1, max_length=255)
    version: str = Field(min_length=1, max_length=255)
    date_debut_validite: date | None = None


class ScoringModelPublishRequest(BaseModel):
    reference_approbation: str = Field(min_length=1, max_length=255)
    date_debut_validite: date


class ScoringModelRetireRequest(BaseModel):
    date_fin_validite: date
    motif: str = Field(min_length=1, max_length=2000)


class ScoringWeightCreateRequest(BaseModel):
    domaine: str = Field(min_length=1, max_length=255)
    valeur: Decimal = Field(gt=0)
    periode_debut: str | None = Field(default=None, max_length=255)
    periode_fin: str | None = Field(default=None, max_length=255)
    statut: str | None = Field(default="ACTIF", max_length=255)


class ScoringWeightUpdateRequest(BaseModel):
    domaine: str | None = Field(default=None, max_length=255)
    valeur: Decimal | None = Field(default=None, gt=0)
    periode_debut: str | None = Field(default=None, max_length=255)
    periode_fin: str | None = Field(default=None, max_length=255)
    statut: str | None = Field(default=None, max_length=255)


class ScoringWeightResponse(BaseModel):
    id: UUID
    modele_scoring_id: UUID
    domaine: str | None = None
    valeur: Decimal | None = None
    periode_debut: str | None = None
    periode_fin: str | None = None
    statut: str | None = None
    created_at: datetime
    updated_at: datetime


class ScoringModelResponse(BaseModel):
    id: UUID
    code: str | None = None
    libelle: str | None = None
    version: str | None = None
    objet_evalue: str | None = None
    description: str | None = None
    date_debut_validite: date | None = None
    date_fin_validite: date | None = None
    regle_calcul: dict[str, Any] | None = None
    reference_approbation: str | None = None
    statut: str | None = None
    ponderations_count: int = 0
    total_ponderation: Decimal = Decimal("0")
    created_at: datetime
    updated_at: datetime


# ============================================================
# ENTRÉE GÉNÉRIQUE DE CALCUL
# ============================================================

class ScoreEvaluationInput(BaseModel):
    modele_scoring_id: UUID | None = None

    # Utilisé uniquement si la règle publiée est DIRECT_SCORE.
    score_direct: Decimal | None = None

    # Utilisé pour les règles pondérées.
    scores_domaines: dict[str, Decimal] = Field(default_factory=dict)

    # Snapshot des références métier ayant permis le calcul.
    # Les valeurs restent libres pour ne pas figer la structure trop tôt.
    sources: dict[str, Any] = Field(default_factory=dict)


class ScoreComputationPreviewResponse(BaseModel):
    modele_scoring_id: UUID
    modele_code: str
    modele_version: str
    objet_evalue: str
    mode_calcul: str
    score: Decimal
    contributions: dict[str, Any] = Field(default_factory=dict)
    classe: str | None = None
    niveau: int | None = None


# ============================================================
# CLASSIFICATION ENTREPRISE
# ============================================================

class EnterpriseClassificationResponse(BaseModel):
    id: UUID
    entreprise_id: UUID
    modele_scoring_id: UUID
    score: Decimal | None = None
    classe: str | None = None
    date_calcul: date | None = None
    date_validation: date | None = None
    sources: dict[str, Any] | None = None
    valide_par_id: UUID
    statut: str | None = None
    created_at: datetime
    updated_at: datetime


class EnterpriseClassificationListResponse(BaseModel):
    total: int
    items: list[EnterpriseClassificationResponse] = Field(default_factory=list)


# ============================================================
# INFC
# ============================================================

class InfcResultResponse(BaseModel):
    id: UUID
    certification_id: UUID
    modele_scoring_id: UUID
    score_global: Decimal | None = None
    niveau: int | None = None
    scores_domaines: dict[str, Any] | None = None
    date_calcul: date | None = None
    date_validation: date | None = None
    sources: dict[str, Any] | None = None
    statut: str | None = None
    created_at: datetime
    updated_at: datetime


class InfcResultListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[InfcResultResponse] = Field(default_factory=list)


class InfcValidateRequest(BaseModel):
    commentaire: str | None = Field(default=None, max_length=2000)


# ============================================================
# SNCC
# ============================================================

class SnccCreateRequest(BaseModel):
    classe: str = Field(min_length=1, max_length=255)
    statut_administratif: str = Field(min_length=1, max_length=255)
    niveau_risque: str = Field(min_length=1, max_length=255)
    justification: str = Field(min_length=1)
    date_effet: date


class SnccReclassifyRequest(SnccCreateRequest):
    motif_reclassement: str = Field(min_length=1, max_length=2000)


class SnccCloseRequest(BaseModel):
    date_fin: date
    motif: str = Field(min_length=1, max_length=2000)


class SnccResponse(BaseModel):
    id: UUID
    certification_id: UUID
    classe: str | None = None
    statut_administratif: str | None = None
    niveau_risque: str | None = None
    justification: str | None = None
    date_effet: date | None = None
    date_fin: date | None = None
    valide_par_id: UUID
    statut: str | None = None
    created_at: datetime
    updated_at: datetime


class SnccListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[SnccResponse] = Field(default_factory=list)
