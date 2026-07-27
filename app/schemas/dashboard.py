"""
Schémas API — Pilotage / Tableaux de bord / Baromètre / Public.

OBJECTIF
--------
Fournir six niveaux de lecture sans créer de nouvelle table :
- opérationnel ;
- tactique mensuel ;
- stratégique trimestriel ;
- annuel ;
- baromètre national périodique ;
- public agrégé autorisé.

PRINCIPES
---------
1. Les indicateurs sont calculés côté serveur.
2. Le frontend ne recalcule aucune formule institutionnelle.
3. Les données publiques sont strictement agrégées.
4. Le endpoint public n'est actif que si :
   - une règle métier publiée autorise explicitement les indicateurs ;
   - une publication approuvée et publiée vise cette règle.
5. Aucun score composite de baromètre n'est inventé.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class PeriodResponse(BaseModel):
    start: date
    end: date
    label: str


class KpiValue(BaseModel):
    key: str
    label: str
    value: int | Decimal | float | None
    unit: str | None = None
    previous_value: int | Decimal | float | None = None
    delta: int | Decimal | float | None = None
    definition: str | None = None


class DistributionItem(BaseModel):
    key: str
    label: str
    value: int | Decimal | float
    percentage: Decimal | None = None


class TimeSeriesPoint(BaseModel):
    period: str
    value: int | Decimal | float


class GeographicAggregate(BaseModel):
    zone_id: UUID | None = None
    zone_code: str | None = None
    zone_name: str
    zone_type: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    enterprises: int = 0
    certifications: int = 0
    active_certifications: int = 0
    average_infc: Decimal | None = None


class PriorityAction(BaseModel):
    type: str
    level: int | None = None
    title: str
    due_date: date | None = None
    resource_type: str | None = None
    resource_id: UUID | None = None


class ExpiringCertificationItem(BaseModel):
    certification_id: UUID
    enterprise_id: UUID
    certification_code: str | None = None
    enterprise_name: str
    norm: str | None = None
    certification_body: str | None = None
    expiration_date: date
    days_remaining: int


class DashboardFiltersResponse(BaseModel):
    zones: list[dict[str, Any]] = Field(default_factory=list)
    sectors: list[str] = Field(default_factory=list)
    norms: list[dict[str, Any]] = Field(default_factory=list)
    certification_bodies: list[dict[str, Any]] = Field(default_factory=list)


class IndicatorDefinition(BaseModel):
    key: str
    label: str
    description: str
    source_tables: list[str] = Field(default_factory=list)
    public_candidate: bool = False


class IndicatorDefinitionsResponse(BaseModel):
    items: list[IndicatorDefinition] = Field(default_factory=list)


class OperationalDashboardResponse(BaseModel):
    generated_at: datetime
    period: PeriodResponse
    kpis: list[KpiValue] = Field(default_factory=list)
    certification_statuses: list[DistributionItem] = Field(default_factory=list)
    deadline_buckets: list[DistributionItem] = Field(default_factory=list)
    expiring_certifications: list[ExpiringCertificationItem] = Field(
        default_factory=list
    )
    infc_national_average: Decimal | None = None
    priority_actions: list[PriorityAction] = Field(default_factory=list)
    recent_certifications: list[dict[str, Any]] = Field(default_factory=list)
    activity_series: list[TimeSeriesPoint] = Field(default_factory=list)


class TacticalDashboardResponse(BaseModel):
    generated_at: datetime
    period: PeriodResponse
    kpis: list[KpiValue] = Field(default_factory=list)
    collection: dict[str, Any] = Field(default_factory=dict)
    verification: dict[str, Any] = Field(default_factory=dict)
    fuccs: dict[str, Any] = Field(default_factory=dict)
    validation: dict[str, Any] = Field(default_factory=dict)
    integration: dict[str, Any] = Field(default_factory=dict)
    watch: dict[str, Any] = Field(default_factory=dict)
    quality: dict[str, Any] = Field(default_factory=dict)


class DecisionSynthesis(BaseModel):
    findings: list[str] = Field(default_factory=list)
    major_risks: list[str] = Field(default_factory=list)
    priority_recommendations: list[str] = Field(default_factory=list)


class StrategicDashboardResponse(BaseModel):
    generated_at: datetime
    period: PeriodResponse
    kpis: list[KpiValue] = Field(default_factory=list)
    certification_statuses: list[DistributionItem] = Field(default_factory=list)
    sncc_classes: list[DistributionItem] = Field(default_factory=list)
    sncc_risks: list[DistributionItem] = Field(default_factory=list)
    by_region: list[GeographicAggregate] = Field(default_factory=list)
    by_sector: list[DistributionItem] = Field(default_factory=list)
    by_norm: list[DistributionItem] = Field(default_factory=list)
    by_certification_body: list[DistributionItem] = Field(default_factory=list)
    infc_series: list[TimeSeriesPoint] = Field(default_factory=list)
    synthesis: DecisionSynthesis


class AnnualDashboardResponse(BaseModel):
    generated_at: datetime
    year: int
    period: PeriodResponse
    kpis: list[KpiValue] = Field(default_factory=list)
    quarterly_certifications: list[TimeSeriesPoint] = Field(default_factory=list)
    quarterly_infc: list[TimeSeriesPoint] = Field(default_factory=list)
    certification_statuses: list[DistributionItem] = Field(default_factory=list)
    sncc_classes: list[DistributionItem] = Field(default_factory=list)
    by_region: list[GeographicAggregate] = Field(default_factory=list)
    quality: dict[str, Any] = Field(default_factory=dict)
    governance: dict[str, Any] = Field(default_factory=dict)
    continuity: dict[str, Any] = Field(default_factory=dict)


class BarometerResponse(BaseModel):
    generated_at: datetime
    period: PeriodResponse
    scope: str = "NATIONAL"
    certifications_count: int
    active_certifications_count: int
    enterprises_count: int
    validated_infc_count: int
    national_infc_average: Decimal | None = None
    certification_statuses: list[DistributionItem] = Field(default_factory=list)
    sncc_classes: list[DistributionItem] = Field(default_factory=list)
    sncc_risks: list[DistributionItem] = Field(default_factory=list)
    by_region: list[GeographicAggregate] = Field(default_factory=list)
    by_sector: list[DistributionItem] = Field(default_factory=list)
    by_norm: list[DistributionItem] = Field(default_factory=list)
    by_certification_body: list[DistributionItem] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class PublicIndicatorItem(BaseModel):
    key: str
    label: str
    value: Any


class PublicIndicatorsResponse(BaseModel):
    generated_at: datetime
    publication_id: UUID
    publication_date: date
    rule_id: UUID
    rule_version: str | None = None
    period: PeriodResponse
    indicators: list[PublicIndicatorItem] = Field(default_factory=list)
    disclaimer: str
