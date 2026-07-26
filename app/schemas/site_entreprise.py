"""
Schémas API du sous-module Sites entreprise.

RÔLE DU FICHIER
---------------
Définir les données acceptées et retournées par l'API
pour les sites physiques rattachés à une entreprise.

IMPORTANT
---------
- entreprise_id vient de l'URL ;
- il n'est jamais accepté depuis le JSON ;
- zone_id doit correspondre à une zone administrative réelle ;
- aucun DELETE physique n'est utilisé ;
- un site désactivé reste conservé pour la traçabilité.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================
# CRÉATION
# ============================================================

class SiteEntrepriseCreateRequest(BaseModel):
    """
    Données autorisées lors de la création d'un site.
    """

    nom: str | None = Field(
        default=None,
        max_length=255,
    )

    type_site: str | None = Field(
        default=None,
        max_length=255,
    )

    adresse: str | None = None

    zone_id: UUID

    latitude: Decimal | None = None
    longitude: Decimal | None = None

    date_ouverture: date | None = None

    effectif: int | None = Field(
        default=None,
        ge=0,
    )


# ============================================================
# MODIFICATION
# ============================================================

class SiteEntrepriseUpdateRequest(BaseModel):
    """
    Modification partielle.

    entreprise_id reste volontairement non modifiable.
    """

    nom: str | None = Field(
        default=None,
        max_length=255,
    )

    type_site: str | None = Field(
        default=None,
        max_length=255,
    )

    adresse: str | None = None

    zone_id: UUID | None = None

    latitude: Decimal | None = None
    longitude: Decimal | None = None

    date_ouverture: date | None = None

    effectif: int | None = Field(
        default=None,
        ge=0,
    )


# ============================================================
# DÉSACTIVATION / RESTAURATION
# ============================================================

class SiteEntrepriseStatusRequest(BaseModel):
    """
    Le motif est enregistré dans le journal d'audit.
    """

    motif: str | None = Field(
        default=None,
        max_length=2000,
    )


# ============================================================
# RÉPONSE
# ============================================================

class SiteEntrepriseResponse(BaseModel):

    id: UUID
    entreprise_id: UUID

    nom: str | None = None
    type_site: str | None = None

    adresse: str | None = None
    zone_id: UUID

    latitude: Decimal | None = None
    longitude: Decimal | None = None

    date_ouverture: date | None = None
    effectif: int | None = None

    statut: str | None = None

    created_at: datetime
    updated_at: datetime