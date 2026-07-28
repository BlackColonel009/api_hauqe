from __future__ import annotations
from datetime import date
from uuid import UUID
from pydantic import BaseModel, Field

class IntegrationWorkspaceFiltersResponse(BaseModel):
    statuses: list[str] = Field(default_factory=list)

class IntegrationWorkspaceItem(BaseModel):
    integration_id: UUID
    integration_status: str | None = None
    started_on: date | None = None
    ended_on: date | None = None
    precontrol: str | None = None
    postcontrol: str | None = None
    backup_reference: str | None = None
    summary_text: str | None = None
    administrator_id: UUID
    administrator_name: str | None = None
    validation_id: UUID
    validation_decision: str | None = None
    validation_date: date | None = None
    validator_id: UUID | None = None
    validator_name: str | None = None
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
    control_id: UUID | None = None
    control_score: str | None = None
    control_maximum: str | None = None
    control_rate: str | None = None
    control_ended_on: date | None = None
    elements_count: int = 0
    elements_success_count: int = 0
    elements_error_count: int = 0

class IntegrationWorkspaceSummary(BaseModel):
    total: int = 0
    waiting: int = 0
    precontrolled: int = 0
    in_progress: int = 0
    postcontrolled: int = 0
    integrated: int = 0
    failed: int = 0

class IntegrationWorkspaceRegistryResponse(BaseModel):
    total: int
    limit: int
    offset: int
    summary: IntegrationWorkspaceSummary
    items: list[IntegrationWorkspaceItem] = Field(default_factory=list)

class IntegrationQueueWorkspaceItem(BaseModel):
    validation_id: UUID
    validation_decision: str
    validation_date: date | None = None
    validator_name: str | None = None
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
    control_id: UUID | None = None
    control_rate: str | None = None
    existing_integration_id: UUID | None = None
    existing_integration_status: str | None = None
    existing_integration_closed: bool = False
    eligible: bool = True

class IntegrationQueueWorkspaceResponse(BaseModel):
    total: int
    items: list[IntegrationQueueWorkspaceItem] = Field(default_factory=list)
