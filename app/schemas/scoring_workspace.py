from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ScoringWorkspaceFilters(BaseModel):
    classification_classes: list[str] = Field(default_factory=list)
    classification_statuses: list[str] = Field(default_factory=list)
    infc_statuses: list[str] = Field(default_factory=list)
    sncc_classes: list[str] = Field(default_factory=list)
    sncc_admin_statuses: list[str] = Field(default_factory=list)
    sncc_risk_levels: list[str] = Field(default_factory=list)


class ClassificationWorkspaceFilters(BaseModel):
    classes: list[str] = Field(default_factory=list)
    statuses: list[str] = Field(default_factory=list)


class InfcWorkspaceFilters(BaseModel):
    statuses: list[str] = Field(default_factory=list)


class SnccWorkspaceFilters(BaseModel):
    classes: list[str] = Field(default_factory=list)
    admin_statuses: list[str] = Field(default_factory=list)
    risk_levels: list[str] = Field(default_factory=list)


class ClassificationWorkspaceItem(BaseModel):
    id: UUID
    enterprise_id: UUID
    enterprise_name: str | None = None
    enterprise_identifier: str | None = None
    enterprise_status: str | None = None
    score: Decimal | None = None
    class_code: str | None = None
    calculated_on: date | None = None
    validated_on: date | None = None
    status: str | None = None
    model_id: UUID
    model_code: str | None = None
    model_version: str | None = None
    validator_id: UUID
    validator_name: str | None = None


class ClassificationWorkspaceSummary(BaseModel):
    total: int = 0
    enterprises_classified: int = 0
    distinct_classes: int = 0


class ClassificationWorkspaceResponse(BaseModel):
    total: int
    limit: int
    offset: int
    summary: ClassificationWorkspaceSummary
    items: list[ClassificationWorkspaceItem] = Field(default_factory=list)


class EnterpriseScoringWorkspaceItem(BaseModel):
    enterprise_id: UUID
    enterprise_name: str | None = None
    enterprise_identifier: str | None = None
    enterprise_status: str | None = None
    activity: str | None = None
    latest_classification_id: UUID | None = None
    latest_score: Decimal | None = None
    latest_class: str | None = None
    latest_classification_date: date | None = None
    latest_model_code: str | None = None
    latest_model_version: str | None = None


class EnterpriseScoringWorkspaceResponse(BaseModel):
    total: int
    items: list[EnterpriseScoringWorkspaceItem] = Field(default_factory=list)


class CertificationWorkspaceBase(BaseModel):
    certification_id: UUID
    certification_identifier: str
    certificate_number: str | None = None
    certification_status: str | None = None
    expiry_date: date | None = None
    enterprise_id: UUID
    enterprise_name: str | None = None
    enterprise_identifier: str | None = None
    organization_name: str | None = None
    standard_code: str | None = None
    standard_name: str | None = None


class CertificationInfcWorkspaceItem(CertificationWorkspaceBase):
    latest_infc_id: UUID | None = None
    latest_infc_score: Decimal | None = None
    latest_infc_level: int | None = None
    latest_infc_status: str | None = None
    latest_infc_date: date | None = None


class CertificationSnccWorkspaceItem(CertificationWorkspaceBase):
    eligible: bool = False
    eligibility_reasons: list[str] = Field(default_factory=list)
    latest_infc_id: UUID | None = None
    latest_infc_score: Decimal | None = None
    latest_infc_level: int | None = None
    latest_infc_status: str | None = None
    latest_infc_date: date | None = None
    current_sncc_id: UUID | None = None
    current_sncc_class: str | None = None
    current_admin_status: str | None = None
    current_risk_level: str | None = None
    current_effective_date: date | None = None


class CertificationInfcWorkspaceResponse(BaseModel):
    total: int
    items: list[CertificationInfcWorkspaceItem] = Field(default_factory=list)


class CertificationSnccWorkspaceResponse(BaseModel):
    total: int
    items: list[CertificationSnccWorkspaceItem] = Field(default_factory=list)


class InfcWorkspaceItem(CertificationWorkspaceBase):
    result_id: UUID
    model_id: UUID
    model_code: str | None = None
    model_version: str | None = None
    score_global: Decimal | None = None
    level: int | None = None
    calculated_on: date | None = None
    validated_on: date | None = None
    status: str | None = None
    domain_scores: dict[str, Any] | list[Any] | None = None


class InfcWorkspaceSummary(BaseModel):
    total: int = 0
    calculated: int = 0
    validated: int = 0
    certifications_evaluated: int = 0


class InfcWorkspaceResponse(BaseModel):
    total: int
    limit: int
    offset: int
    summary: InfcWorkspaceSummary
    items: list[InfcWorkspaceItem] = Field(default_factory=list)


class SnccWorkspaceItem(CertificationWorkspaceBase):
    sncc_id: UUID
    class_code: str | None = None
    administrative_status: str | None = None
    risk_level: str | None = None
    justification: str | None = None
    effective_on: date | None = None
    ended_on: date | None = None
    validated_by_id: UUID
    validator_name: str | None = None
    status: str | None = None


class SnccWorkspaceSummary(BaseModel):
    total: int = 0
    current: int = 0
    closed: int = 0
    certifications_ranked: int = 0


class SnccWorkspaceResponse(BaseModel):
    total: int
    limit: int
    offset: int
    summary: SnccWorkspaceSummary
    items: list[SnccWorkspaceItem] = Field(default_factory=list)
