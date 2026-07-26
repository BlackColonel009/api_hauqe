"""
Schémas API du sous-module Offres entreprise.

RÔLE DU FICHIER
---------------
Définir le contrat HTTP des produits/services proposés par une entreprise.

RELATION
--------
offres_entreprise.entreprise_id -> entreprises.id

Les champs `marches_cibles` et `destinations` sont stockés en JSONB dans
PostgreSQL. L'API courante les expose comme listes de chaînes ; cette
structure pourra être enrichie plus tard sans migration de la colonne JSONB.

Aucune logique SQL ou permission n'est placée ici.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class OffreEntrepriseCreateRequest(BaseModel):
    """Données autorisées pour créer une offre."""

    type_offre: str = Field(min_length=1, max_length=255)
    nom: str | None = Field(default=None, max_length=255)
    description: str | None = None
    categorie: str | None = Field(default=None, max_length=255)

    volume_annuel: Decimal | None = Field(default=None, ge=0)
    unite: str | None = Field(default=None, max_length=255)
    capacite_production: Decimal | None = Field(default=None, ge=0)

    marches_cibles: list[str] | None = None
    destinations: list[str] | None = None


class OffreEntrepriseUpdateRequest(BaseModel):
    """
    Mise à jour partielle.

    `entreprise_id` n'est jamais accepté depuis le JSON : l'entreprise
    propriétaire est déterminée par l'URL.
    """

    type_offre: str | None = Field(default=None, max_length=255)
    nom: str | None = Field(default=None, max_length=255)
    description: str | None = None
    categorie: str | None = Field(default=None, max_length=255)

    volume_annuel: Decimal | None = Field(default=None, ge=0)
    unite: str | None = Field(default=None, max_length=255)
    capacite_production: Decimal | None = Field(default=None, ge=0)

    marches_cibles: list[str] | None = None
    destinations: list[str] | None = None


class OffreEntrepriseStatusRequest(BaseModel):
    """Motif conservé dans le journal d'audit."""

    motif: str | None = Field(default=None, max_length=2000)


class OffreEntrepriseResponse(BaseModel):
    """Vue publique actuelle d'une offre d'entreprise."""

    id: UUID
    entreprise_id: UUID

    type_offre: str | None = None
    nom: str | None = None
    description: str | None = None
    categorie: str | None = None

    volume_annuel: Decimal | None = None
    unite: str | None = None
    capacite_production: Decimal | None = None

    marches_cibles: list[str] | None = None
    destinations: list[str] | None = None

    statut: str | None = None

    created_at: datetime
    updated_at: datetime
