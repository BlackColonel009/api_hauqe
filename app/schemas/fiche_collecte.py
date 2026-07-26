"""
Schémas API des fiches de collecte et de leurs révisions.

DOCTRINE
--------
- une mission peut conserver plusieurs révisions historiques ;
- la révision ayant le plus grand `numero_revision` est considérée comme
  courante dans le MPD actuel ;
- les anciennes révisions ne sont jamais écrasées ;
- BROUILLON et SOUMISE sont les deux états de collecte actuellement
  explicitement documentés ;
- le taux de complétude est calculé côté serveur depuis une règle métier
  publiée, jamais fourni par le client.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class FicheCollecteCreateRequest(BaseModel):
    entreprise_id: UUID | None = None
    version_formulaire: str | None = Field(default=None, max_length=255)

    consentement_obtenu: bool | None = None
    nom_declarant: str | None = Field(default=None, max_length=255)
    fonction_declarant: str | None = Field(default=None, max_length=255)
    telephone_declarant: str | None = Field(default=None, max_length=255)
    email_declarant: str | None = Field(default=None, max_length=255)
    signature_declarant: str | None = Field(default=None, max_length=255)
    observations: str | None = None


class FicheCollecteUpdateRequest(BaseModel):
    entreprise_id: UUID | None = None
    version_formulaire: str | None = Field(default=None, max_length=255)

    consentement_obtenu: bool | None = None
    nom_declarant: str | None = Field(default=None, max_length=255)
    fonction_declarant: str | None = Field(default=None, max_length=255)
    telephone_declarant: str | None = Field(default=None, max_length=255)
    email_declarant: str | None = Field(default=None, max_length=255)
    signature_declarant: str | None = Field(default=None, max_length=255)
    observations: str | None = None


class FicheCollecteRevisionRequest(BaseModel):
    """
    Commentaire expliquant pourquoi une nouvelle révision est ouverte.
    """

    commentaire: str = Field(min_length=1)


class FicheCollecteSubmitRequest(BaseModel):
    commentaire: str | None = None


class FicheCollecteResponse(BaseModel):
    id: UUID
    mission_id: UUID
    entreprise_id: UUID | None = None
    version_formulaire: str | None = None
    numero_revision: int | None = None
    statut: str | None = None
    taux_completude: Decimal | None = None
    consentement_obtenu: bool | None = None
    nom_declarant: str | None = None
    fonction_declarant: str | None = None
    telephone_declarant: str | None = None
    email_declarant: str | None = None
    signature_declarant: str | None = None
    observations: str | None = None
    collecte_par_id: UUID
    collecte_at: datetime | None = None
    soumise_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class EvenementCollecteResponse(BaseModel):
    id: UUID
    fiche_collecte_id: UUID
    type_evenement: str | None = None
    ancien_statut: str | None = None
    nouveau_statut: str | None = None
    commentaire: str | None = None
    acteur_id: UUID
    date_evenement: datetime | None = None
    created_at: datetime
    updated_at: datetime
