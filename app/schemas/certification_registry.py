from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class CertificationFilterItem(BaseModel):
    id: UUID
    code: str | None = None
    label: str


class CertificationFiltersResponse(BaseModel):
    statuses: list[str] = Field(default_factory=list)
    norms: list[CertificationFilterItem] = Field(default_factory=list)
    organisms: list[CertificationFilterItem] = Field(default_factory=list)


class CertificationRegistryItem(BaseModel):
    id: UUID
    identifiant_national: str
    numero_certificat: str | None = None

    entreprise_id: UUID
    entreprise_name: str

    organisme_id: UUID
    organisme_name: str
    organisme_sigle: str | None = None

    norme_id: UUID
    norme_code: str | None = None
    norme_name: str | None = None
    norme_version: str | None = None

    accreditation_id: UUID | None = None
    accrediteur: str | None = None

    portee: str | None = None
    date_obtention: date | None = None
    date_effet: date | None = None
    date_expiration: date | None = None
    days_remaining: int | None = None

    statut: str | None = None
    authenticite_verifiee: bool | None = None
    certification_strategique: bool | None = None

    document_count: int = 0
    renewal_open: bool = False


class CertificationRegistrySummary(BaseModel):
    total: int = 0
    active_status: int = 0
    verified: int = 0
    to_verify: int = 0
    expired: int = 0
    expiring_30: int = 0
    expiring_90: int = 0
    expiring_180: int = 0
    suspended: int = 0
    renewals_open: int = 0


class CertificationRegistryResponse(BaseModel):
    total: int
    limit: int
    offset: int
    summary: CertificationRegistrySummary
    items: list[CertificationRegistryItem] = Field(default_factory=list)
