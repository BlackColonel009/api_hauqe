"""
Schémas API du module Campagnes de collecte.

Une campagne constitue le parent organisationnel des missions.
Le responsable est un utilisateur existant du système.

Le vocabulaire des statuts de campagne n'est pas figé ici :
la liste institutionnelle pourra être administrée via les référentiels.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CampagneCreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=255)
    nom: str | None = Field(default=None, max_length=255)
    objet: str | None = Field(default=None, max_length=255)
    objectif: str | None = Field(default=None, max_length=255)
    date_debut: date | None = None
    date_fin: date | None = None
    responsable_id: UUID
    statut: str | None = Field(default=None, max_length=255)


class CampagneUpdateRequest(BaseModel):
    nom: str | None = Field(default=None, max_length=255)
    objet: str | None = Field(default=None, max_length=255)
    objectif: str | None = Field(default=None, max_length=255)
    date_debut: date | None = None
    date_fin: date | None = None
    responsable_id: UUID | None = None
    statut: str | None = Field(default=None, max_length=255)


class CampagneResponse(BaseModel):
    id: UUID
    code: str
    nom: str | None = None
    objet: str | None = None
    objectif: str | None = None
    date_debut: date | None = None
    date_fin: date | None = None
    responsable_id: UUID
    statut: str | None = None
    created_at: datetime
    updated_at: datetime


class CampagneListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[CampagneResponse] = Field(default_factory=list)
