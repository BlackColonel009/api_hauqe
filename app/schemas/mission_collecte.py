"""
Schémas API des missions de collecte et de leurs affectations.

RELATIONS
---------
campagnes -> missions_collecte -> affectations_mission -> utilisateurs

Le MPD impose `campagne_id` et `zone_id`.
L'auteur d'une affectation (`attribue_par_id`) n'est jamais fourni par le
client : le backend utilise l'utilisateur authentifié.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MissionCollecteCreateRequest(BaseModel):
    code: str | None = Field(default=None, max_length=255)
    objet: str | None = Field(default=None, max_length=255)
    zone_id: UUID
    date_debut_prevue: date | None = None
    date_fin_prevue: date | None = None
    date_debut_reelle: date | None = None
    date_fin_reelle: date | None = None
    priorite: str | None = Field(default=None, max_length=255)
    progression: int | None = Field(default=0, ge=0, le=100)
    statut: str | None = Field(default=None, max_length=255)


class MissionCollecteUpdateRequest(BaseModel):
    code: str | None = Field(default=None, max_length=255)
    objet: str | None = Field(default=None, max_length=255)
    zone_id: UUID | None = None
    date_debut_prevue: date | None = None
    date_fin_prevue: date | None = None
    date_debut_reelle: date | None = None
    date_fin_reelle: date | None = None
    priorite: str | None = Field(default=None, max_length=255)
    progression: int | None = Field(default=None, ge=0, le=100)
    statut: str | None = Field(default=None, max_length=255)


class MissionCollecteResponse(BaseModel):
    id: UUID
    campagne_id: UUID
    code: str | None = None
    objet: str | None = None
    zone_id: UUID
    date_debut_prevue: date | None = None
    date_fin_prevue: date | None = None
    date_debut_reelle: date | None = None
    date_fin_reelle: date | None = None
    priorite: str | None = None
    progression: int | None = None
    statut: str | None = None
    created_at: datetime
    updated_at: datetime


class MissionCollecteListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[MissionCollecteResponse] = Field(default_factory=list)


class AffectationMissionCreateRequest(BaseModel):
    utilisateur_id: UUID
    role_mission: str | None = Field(default=None, max_length=255)
    date_debut: date | None = None
    date_fin: date | None = None
    motif: str | None = None
    statut: str | None = Field(default="ACTIF", max_length=255)


class AffectationMissionUpdateRequest(BaseModel):
    role_mission: str | None = Field(default=None, max_length=255)
    date_debut: date | None = None
    date_fin: date | None = None
    motif: str | None = None
    statut: str | None = Field(default=None, max_length=255)


class AffectationMissionResponse(BaseModel):
    id: UUID
    mission_id: UUID
    utilisateur_id: UUID
    role_mission: str | None = None
    date_debut: date | None = None
    date_fin: date | None = None
    attribue_par_id: UUID
    motif: str | None = None
    statut: str | None = None
    created_at: datetime
    updated_at: datetime
