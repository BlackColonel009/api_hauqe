"""Schémas API des zones administratives HAUQE Certif."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


ZONE_TYPES = {
    "REGION",
    "PREFECTURE",
    "COMMUNE",
    "LOCALITE",
    "AUTRE",
}


class ZoneAdministrativeCreateRequest(BaseModel):
    parent_id: UUID | None = None
    type_zone: str = Field(min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=255)
    nom: str = Field(min_length=1, max_length=255)
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)
    statut: str = Field(default="ACTIF", max_length=255)

    @field_validator("type_zone")
    @classmethod
    def normalize_type(cls, value: str) -> str:
        normalized = value.strip().upper().replace("É", "E")
        if normalized not in ZONE_TYPES:
            raise ValueError(
                "Type de zone invalide. Valeurs : REGION, PREFECTURE, "
                "COMMUNE, LOCALITE ou AUTRE."
            )
        return normalized


class ZoneAdministrativeUpdateRequest(BaseModel):
    parent_id: UUID | None = None
    type_zone: str | None = Field(default=None, max_length=255)
    code: str | None = Field(default=None, max_length=255)
    nom: str | None = Field(default=None, max_length=255)
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)
    statut: str | None = Field(default=None, max_length=255)

    @field_validator("type_zone")
    @classmethod
    def normalize_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper().replace("É", "E")
        if normalized not in ZONE_TYPES:
            raise ValueError(
                "Type de zone invalide. Valeurs : REGION, PREFECTURE, "
                "COMMUNE, LOCALITE ou AUTRE."
            )
        return normalized


class ZoneAdministrativeStatusRequest(BaseModel):
    statut: str = Field(min_length=1, max_length=255)
    motif: str | None = Field(default=None, max_length=2000)


class ZoneAdministrativeQuickCreateRequest(BaseModel):
    """Création contrôlée depuis une fiche de collecte."""

    parent_id: UUID | None = None
    type_zone: str = Field(default="LOCALITE", max_length=255)
    code: str | None = Field(default=None, max_length=255)
    nom: str = Field(min_length=2, max_length=255)
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)

    @field_validator("type_zone")
    @classmethod
    def normalize_type(cls, value: str) -> str:
        normalized = value.strip().upper().replace("É", "E")
        if normalized not in ZONE_TYPES:
            raise ValueError("Type de zone invalide.")
        return normalized


class ZoneAdministrativeResponse(BaseModel):
    id: UUID
    parent_id: UUID | None = None
    parent_nom: str | None = None
    type_zone: str | None = None
    code: str | None = None
    nom: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    statut: str | None = None
    enfants_count: int = 0
    chemin: str | None = None
    created_at: datetime
    updated_at: datetime


class ZoneAdministrativeListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[ZoneAdministrativeResponse] = Field(default_factory=list)
