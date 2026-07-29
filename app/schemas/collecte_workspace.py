from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class CollecteOption(BaseModel):
    id: UUID
    label: str
    code: str | None = None
    type: str | None = None


class CollecteWorkspaceFiltersResponse(BaseModel):
    campaigns: list[CollecteOption] = Field(default_factory=list)
    zones: list[CollecteOption] = Field(default_factory=list)
    collectors: list[CollecteOption] = Field(default_factory=list)
    mission_statuses: list[str] = Field(default_factory=list)
    fiche_statuses: list[str] = Field(default_factory=list)


class CollecteRegistryItem(BaseModel):
    mission_id: UUID
    mission_code: str | None = None
    mission_object: str | None = None
    mission_status: str | None = None
    priority: str | None = None
    progression: int | None = None
    planned_start: date | None = None
    planned_end: date | None = None

    campaign_id: UUID
    campaign_code: str
    campaign_name: str | None = None

    zone_id: UUID
    zone_name: str | None = None
    zone_type: str | None = None

    assigned_names: str | None = None

    fiche_id: UUID | None = None
    fiche_status: str | None = None
    completeness: Decimal | None = None
    revision_number: int | None = None
    collected_at: datetime | None = None
    submitted_at: datetime | None = None

    entreprise_id: UUID | None = None
    entreprise_name: str | None = None


class CollecteRegistrySummary(BaseModel):
    total_missions: int = 0
    without_fiche: int = 0
    drafts: int = 0
    submitted: int = 0
    corrections: int = 0
    average_completeness: Decimal | None = None


class CollecteRegistryResponse(BaseModel):
    total: int
    limit: int
    offset: int
    summary: CollecteRegistrySummary
    items: list[CollecteRegistryItem] = Field(default_factory=list)

class CollecteQuickEnterpriseCreateRequest(BaseModel):
    raison_sociale: str = Field(min_length=2, max_length=255)
    zone_siege_id: UUID
    adresse_siege: str | None = Field(default=None, max_length=255)
    telephone_principal: str | None = Field(default=None, max_length=255)
    email_principal: str | None = Field(default=None, max_length=255)


class CollecteQuickEnterpriseResponse(BaseModel):
    id: UUID
    identifiant_national: str
    raison_sociale: str
    zone_siege_id: UUID
    adresse_siege: str | None = None
    telephone_principal: str | None = None
    email_principal: str | None = None
    statut: str
    source_donnee: str

