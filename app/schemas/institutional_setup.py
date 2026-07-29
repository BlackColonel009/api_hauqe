from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class InstitutionalFieldOption(BaseModel):
    name: str
    label: str
    nullable: bool
    type: str


class InstitutionalCountOption(BaseModel):
    code: str
    label: str
    description: str


class CompletenessCatalogResponse(BaseModel):
    fields: list[InstitutionalFieldOption] = Field(default_factory=list)
    count_resources: list[InstitutionalCountOption] = Field(default_factory=list)


class CompletenessValidateRequest(BaseModel):
    parametres: dict[str, Any]


class CompletenessValidateResponse(BaseModel):
    valid: bool
    normalized: dict[str, Any]
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ReadinessRule(BaseModel):
    ready: bool
    id: UUID | None = None
    version: str | None = None
    effective_from: date | None = None
    approval_reference: str | None = None
    status: str | None = None


class ReadinessModel(BaseModel):
    ready: bool
    id: UUID | None = None
    code: str | None = None
    version: str | None = None
    object_type: str
    calculation_mode: str | None = None
    active_weights: int = 0
    total_weight: float = 0
    approval_reference: str | None = None
    status: str | None = None


class InstitutionalReadinessResponse(BaseModel):
    collecte_completude: ReadinessRule
    classification_entreprise: ReadinessModel
    infc: ReadinessModel
    ready_for_collecte_submission: bool
    ready_for_classification_tests: bool
    ready_for_infc_score_tests: bool
    blockers: list[str] = Field(default_factory=list)
