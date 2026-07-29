from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class WatchOption(BaseModel):
    id: UUID
    label: str
    subtitle: str | None = None


class WatchFilters(BaseModel):
    deadline_types: list[str] = Field(default_factory=list)
    deadline_statuses: list[str] = Field(default_factory=list)
    alert_types: list[str] = Field(default_factory=list)
    alert_statuses: list[str] = Field(default_factory=list)
    watch_case_statuses: list[str] = Field(default_factory=list)
    watch_case_priorities: list[str] = Field(default_factory=list)
    report_types: list[str] = Field(default_factory=list)
    report_statuses: list[str] = Field(default_factory=list)


class WatchFormOptions(BaseModel):
    users: list[WatchOption] = Field(default_factory=list)
    certifications: list[WatchOption] = Field(default_factory=list)


class DeadlineWorkspaceItem(BaseModel):
    id: UUID
    ressource_type: str | None = None
    ressource_id: UUID | None = None
    resource_label: str | None = None
    resource_subtitle: str | None = None
    resource_route: str | None = None
    type_echeance: str | None = None
    titre: str | None = None
    description: str | None = None
    date_echeance: date | None = None
    responsable_id: UUID | None = None
    responsable_name: str | None = None
    priorite: str | None = None
    statut: str | None = None
    jours_restants: int | None = None
    alertes_actives_count: int = 0
    created_at: datetime
    updated_at: datetime


class DeadlineWorkspaceSummary(BaseModel):
    total: int = 0
    active: int = 0
    overdue: int = 0
    due_30: int = 0
    due_90: int = 0
    due_180: int = 0
    completed: int = 0


class DeadlineWorkspaceResponse(BaseModel):
    total: int
    limit: int
    offset: int
    summary: DeadlineWorkspaceSummary
    items: list[DeadlineWorkspaceItem] = Field(default_factory=list)


class AlertWorkspaceItem(BaseModel):
    id: UUID
    echeance_id: UUID | None = None
    type_alerte: str | None = None
    niveau: int | None = None
    level_label: str | None = None
    titre: str | None = None
    message: str | None = None
    ressource_type: str | None = None
    ressource_id: UUID | None = None
    resource_label: str | None = None
    resource_subtitle: str | None = None
    resource_route: str | None = None
    responsable_id: UUID | None = None
    responsable_name: str | None = None
    date_detection: date | None = None
    date_resolution: date | None = None
    regle_notification: str | None = None
    statut: str | None = None
    notifications_count: int = 0
    notifications_non_lues_count: int = 0
    created_at: datetime
    updated_at: datetime


class AlertWorkspaceSummary(BaseModel):
    total: int = 0
    active: int = 0
    level_1: int = 0
    level_2: int = 0
    level_3: int = 0
    level_4: int = 0
    resolved: int = 0


class AlertWorkspaceResponse(BaseModel):
    total: int
    limit: int
    offset: int
    summary: AlertWorkspaceSummary
    items: list[AlertWorkspaceItem] = Field(default_factory=list)


class WatchCaseWorkspaceItem(BaseModel):
    id: UUID
    certification_id: UUID
    certification_identifier: str | None = None
    certificate_number: str | None = None
    expiry_date: date | None = None
    enterprise_name: str | None = None
    standard_code: str | None = None
    organization_name: str | None = None
    type_evenement: str | None = None
    priorite: str | None = None
    date_ouverture: date | None = None
    responsable_id: UUID
    responsable_name: str | None = None
    prochaine_action_at: datetime | None = None
    date_cloture: date | None = None
    statut: str | None = None
    relances_count: int = 0
    relances_en_attente_count: int = 0
    created_at: datetime
    updated_at: datetime


class WatchCaseWorkspaceResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[WatchCaseWorkspaceItem] = Field(default_factory=list)


class WatchReportWorkspaceItem(BaseModel):
    id: UUID
    type_rapport: str | None = None
    periode_debut: str | None = None
    periode_fin: str | None = None
    nombre_certifications_suivies: int | None = None
    nombre_alertes: int | None = None
    nombre_renouvellements: int | None = None
    delai_moyen_traitement: float | None = None
    indicateurs: dict[str, Any] | None = None
    prepare_par_id: UUID
    prepare_par_name: str | None = None
    valide_par_id: UUID | None = None
    valide_par_name: str | None = None
    date_validation: date | None = None
    statut: str | None = None
    created_at: datetime
    updated_at: datetime


class WatchReportWorkspaceResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[WatchReportWorkspaceItem] = Field(default_factory=list)
