from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class FuccsWorkspaceGrid(BaseModel):
    id: UUID
    code: str | None = None
    label: str | None = None
    version: str | None = None
    effective_date: date | None = None
    publication_status: str | None = None
    rubrics_count: int = 0
    criteria_count: int = 0
    maximum_score: Decimal = Decimal("0")


class FuccsWorkspaceFiltersResponse(BaseModel):
    statuses: list[str] = Field(default_factory=list)
    active_grid: FuccsWorkspaceGrid | None = None


class FuccsControlRegistryItem(BaseModel):
    control_id: UUID
    control_status: str | None = None
    started_on: date | None = None
    ended_on: date | None = None
    raw_score: Decimal | None = None
    maximum_score: Decimal | None = None
    rate: str | None = None
    synthesis: str | None = None

    grid_id: UUID
    grid_code: str | None = None
    grid_label: str | None = None
    grid_version: str | None = None
    criteria_count: int = 0

    dossier_id: UUID
    verification_opinion: str | None = None
    verification_risk: str | None = None
    verification_closed_on: date | None = None

    fiche_id: UUID
    fiche_revision: int | None = None

    mission_id: UUID
    mission_code: str | None = None
    campaign_code: str | None = None
    campaign_name: str | None = None
    zone_name: str | None = None

    entreprise_id: UUID | None = None
    entreprise_name: str | None = None
    entreprise_identifiant: str | None = None

    controller_id: UUID
    controller_name: str | None = None

    notes_count: int = 0
    findings_count: int = 0
    documents_count: int = 0


class FuccsControlRegistrySummary(BaseModel):
    total: int = 0
    drafts: int = 0
    finalized: int = 0
    complete_notes: int = 0
    incomplete_notes: int = 0


class FuccsControlRegistryResponse(BaseModel):
    total: int
    limit: int
    offset: int
    summary: FuccsControlRegistrySummary
    items: list[FuccsControlRegistryItem] = Field(default_factory=list)


class FuccsEligibleVerificationItem(BaseModel):
    dossier_id: UUID
    verification_opinion: str | None = None
    verification_risk: str | None = None
    verification_closed_on: date | None = None

    fiche_id: UUID
    fiche_revision: int | None = None

    mission_id: UUID
    mission_code: str | None = None
    campaign_code: str | None = None
    campaign_name: str | None = None
    zone_name: str | None = None

    entreprise_id: UUID | None = None
    entreprise_name: str | None = None
    entreprise_identifiant: str | None = None

    controls_count: int = 0
    latest_control_id: UUID | None = None
    latest_control_status: str | None = None


class FuccsEligibleVerificationsResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[FuccsEligibleVerificationItem] = Field(default_factory=list)
