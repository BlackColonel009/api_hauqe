"""
Schémas API de la gestion documentaire.

Le chemin physique du fichier est volontairement absent des réponses API.
Tous les fichiers privés sont servis uniquement par une route authentifiée.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentVerificationRequest(BaseModel):
    statut_verification: str = Field(min_length=1, max_length=255)
    motif: str | None = Field(default=None, max_length=2000)


class DocumentStatusRequest(BaseModel):
    motif: str | None = Field(default=None, max_length=2000)


class DocumentResponse(BaseModel):
    id: UUID
    type_document: str | None = None
    nom_original: str | None = None
    nom_stockage: str | None = None
    format: str | None = None
    taille_octets: int | None = None
    checksum: str | None = None
    version: str | None = None
    ressource_type: str | None = None
    ressource_id: UUID | None = None
    confidentialite: str | None = None
    source: str | None = None
    date_document: date | None = None
    depose_par_id: UUID | None = None
    date_depot: datetime | None = None
    statut_verification: str | None = None
    statut: str | None = None
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[DocumentResponse] = Field(default_factory=list)
