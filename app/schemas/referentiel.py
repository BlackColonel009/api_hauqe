from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReferentielCreate(BaseModel):
    code: str = Field(min_length=1, max_length=255)
    libelle: str = Field(min_length=1, max_length=255)
    description: str | None = None
    type_valeur: str | None = Field(default="LISTE", max_length=255)


class ReferentielUpdate(BaseModel):
    libelle: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    type_valeur: str | None = Field(default=None, max_length=255)
    statut: str | None = Field(default=None, max_length=255)


class ValeurReferentielCreate(BaseModel):
    code: str = Field(min_length=1, max_length=255)
    libelle: str = Field(min_length=1, max_length=255)
    description: str | None = None
    parent_id: UUID | None = None
    ordre_affichage: int | None = Field(default=None, ge=0)
    date_debut_validite: date | None = None
    date_fin_validite: date | None = None


class ValeurReferentielUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=255)
    libelle: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    parent_id: UUID | None = None
    ordre_affichage: int | None = Field(default=None, ge=0)
    date_debut_validite: date | None = None
    date_fin_validite: date | None = None
    statut: str | None = Field(default=None, max_length=255)


class ValeurReferentielResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    referentiel_id: UUID
    parent_id: UUID | None = None
    code: str | None = None
    libelle: str | None = None
    description: str | None = None
    ordre_affichage: int | None = None
    date_debut_validite: date | None = None
    date_fin_validite: date | None = None
    statut: str | None = None
    created_at: datetime
    updated_at: datetime


class ReferentielResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    libelle: str | None = None
    description: str | None = None
    type_valeur: str | None = None
    statut: str | None = None
    valeurs_count: int = 0
    created_at: datetime
    updated_at: datetime


class ReferentielListResponse(BaseModel):
    total: int
    items: list[ReferentielResponse] = Field(default_factory=list)
