from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ValidationWorkspaceFiltersResponse(BaseModel):
    decisions: list[str] = Field(default_factory=list)
    stages: list[str] = Field(default_factory=lambda: [
        "READY_N1",
        "N1_REVIEW",
        "READY_N2",
        "N2_REVIEW",
        "CORRECTION_PENDING",
        "COMPLETE",
    ])


class ValidationLevelSummary(BaseModel):
    validation_id: UUID | None = None
    level: str
    validator_id: UUID | None = None
    validator_name: str | None = None
    decision: str | None = None
    validation_date: date | None = None
    reserves: str | None = None
    justification: str | None = None
    status: str | None = None
    corrections_count: int = 0
    pending_corrections_count: int = 0
    resubmitted_corrections_count: int = 0


class ValidationWorkspaceItem(BaseModel):
    fiche_id: UUID
    fiche_revision: int | None = None
    fiche_status: str | None = None
    completeness: float | None = None
    submitted_at: datetime | None = None

    entreprise_id: UUID | None = None
    entreprise_name: str | None = None
    entreprise_identifiant: str | None = None

    mission_id: UUID
    mission_code: str | None = None
    campaign_code: str | None = None
    campaign_name: str | None = None
    zone_name: str | None = None

    verification_id: UUID
    verification_opinion: str | None = None
    verification_risk: str | None = None

    control_id: UUID
    control_status: str | None = None
    control_score: str | None = None
    control_maximum: str | None = None
    control_rate: str | None = None
    control_ended_on: date | None = None
    controller_name: str | None = None

    level_1: ValidationLevelSummary
    level_2: ValidationLevelSummary

    stage: str
    integration_possible: bool = False
    pending_corrections_count: int = 0


class ValidationWorkspaceSummary(BaseModel):
    total: int = 0
    ready_n1: int = 0
    ready_n2: int = 0
    correction_pending: int = 0
    complete: int = 0


class ValidationWorkspaceRegistryResponse(BaseModel):
    total: int
    limit: int
    offset: int
    summary: ValidationWorkspaceSummary
    items: list[ValidationWorkspaceItem] = Field(default_factory=list)
