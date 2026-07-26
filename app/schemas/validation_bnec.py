"""
Schémas API — Validation hiérarchisée, corrections et intégration BNEC.

DOCTRINE
--------
Le workflow suit la procédure HAUQE :
    Vérification -> FUCCS -> Revue N1 -> Validation N2 -> Intégration BNEC.

Les validations sont des décisions historisées : une décision déjà créée
n'est pas écrasée silencieusement. Une nouvelle décision produit une nouvelle
ligne `validations`.

Les valeurs techniques `NIVEAU_1` et `NIVEAU_2` représentent respectivement :
- revue technique de premier niveau ;
- validation définitive de second niveau.

L'autorité réelle n'est pas déterminée uniquement par cette chaîne :
elle est imposée par les permissions serveur.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


ValidationDecision = Literal[
    "VALIDE",
    "VALIDE_SOUS_RESERVE",
    "AJOURNE",
    "REJETE",
]


class ValidationDecisionRequest(BaseModel):
    decision: ValidationDecision
    reserves: str | None = Field(default=None, max_length=255)
    justification: str = Field(min_length=1)


class ValidationResponse(BaseModel):
    id: UUID
    fiche_collecte_id: UUID
    controle_fuccs_id: UUID | None = None
    niveau_validation: str | None = None
    validateur_id: UUID
    decision: str | None = None
    date_validation: date | None = None
    reserves: str | None = None
    justification: str | None = None
    statut: str | None = None
    created_at: datetime
    updated_at: datetime


class ValidationListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[ValidationResponse] = Field(default_factory=list)


class ValidationQueueItem(BaseModel):
    fiche_collecte_id: UUID
    controle_fuccs_id: UUID
    controle_statut: str | None = None
    score_brut: str | None = None
    score_maximal: str | None = None
    taux: str | None = None
    niveau_1_decision: str | None = None
    niveau_1_validation_id: UUID | None = None
    niveau_2_decision: str | None = None
    niveau_2_validation_id: UUID | None = None
    integration_possible: bool = False


class CorrectionCreateRequest(BaseModel):
    motif: str = Field(min_length=1)
    instructions: str = Field(min_length=1)
    date_echeance: date | None = None


class CorrectionUpdateRequest(BaseModel):
    motif: str | None = None
    instructions: str | None = None
    date_echeance: date | None = None


class CorrectionResubmitRequest(BaseModel):
    reponse: str = Field(min_length=1)
    date_resoumission: date | None = None


class CorrectionResponse(BaseModel):
    id: UUID
    validation_id: UUID
    motif: str | None = None
    instructions: str | None = None
    date_demande: date | None = None
    date_echeance: date | None = None
    date_resoumission: date | None = None
    reponse: str | None = None
    statut: str | None = None
    created_at: datetime
    updated_at: datetime


# ============================================================
# SCHEMAS — INTEGRATION BNEC
# ============================================================

IntegrationCheckResult = Literal["OK", "ECHEC"]
IntegrationElementResult = Literal["INTEGRE", "ECHEC"]


class IntegrationOpenRequest(BaseModel):
    resume: str | None = None


class IntegrationCheckRequest(BaseModel):
    resultat: IntegrationCheckResult
    resume: str = Field(min_length=1)
    sauvegarde_reference: str | None = Field(default=None, max_length=255)


class IntegrationStartRequest(BaseModel):
    resume: str | None = None


class IntegrationElementCreateRequest(BaseModel):
    type_objet: str = Field(min_length=1, max_length=255)
    ressource_source_id: UUID | None = None
    ressource_cible_id: UUID | None = None
    revision_source: str | None = Field(default=None, max_length=255)
    action: str = Field(min_length=1, max_length=255)
    code_genere: str | None = Field(default=None, max_length=255)


class IntegrationElementUpdateRequest(BaseModel):
    ressource_source_id: UUID | None = None
    ressource_cible_id: UUID | None = None
    revision_source: str | None = Field(default=None, max_length=255)
    action: str | None = Field(default=None, max_length=255)
    code_genere: str | None = Field(default=None, max_length=255)


class IntegrationElementResultRequest(BaseModel):
    resultat: IntegrationElementResult
    ressource_cible_id: UUID | None = None
    code_genere: str | None = Field(default=None, max_length=255)
    message_erreur: str | None = Field(default=None, max_length=255)


class IntegrationElementResponse(BaseModel):
    id: UUID
    integration_bnec_id: UUID
    type_objet: str | None = None
    ressource_source_id: UUID | None = None
    ressource_cible_id: UUID | None = None
    revision_source: str | None = None
    action: str | None = None
    code_genere: str | None = None
    statut: str | None = None
    message_erreur: str | None = None
    created_at: datetime
    updated_at: datetime


class IntegrationResponse(BaseModel):
    id: UUID
    validation_id: UUID
    administrateur_id: UUID
    date_debut: date | None = None
    date_fin: date | None = None
    statut: str | None = None
    precontrole: str | None = None
    postcontrole: str | None = None
    sauvegarde_reference: str | None = None
    resume: str | None = None
    elements_count: int = 0
    elements_success_count: int = 0
    elements_error_count: int = 0
    created_at: datetime
    updated_at: datetime


class IntegrationListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[IntegrationResponse] = Field(default_factory=list)


class IntegrationQueueItem(BaseModel):
    validation_id: UUID
    fiche_collecte_id: UUID
    controle_fuccs_id: UUID | None = None
    decision: str
    date_validation: date | None = None
    existing_integration_id: UUID | None = None
    existing_integration_status: str | None = None
    eligible: bool = True
