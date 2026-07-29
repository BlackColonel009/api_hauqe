"""
Schémas des offres et certifications déclarées pendant la collecte.

IMPORTANT
---------
Les données déclarées sont conservées séparément des données officielles.

Une `certification_declaree` n'est donc jamais transformée silencieusement
en `certification`. Le rapprochement officiel sera réalisé dans la phase
Vérification.

Les champs `certification_officielle_id`, `score_rapprochement` et
`statut_rapprochement` sont exposés en lecture mais ne sont pas modifiables
par les endpoints de saisie de collecte.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class OffreDeclareeCreateRequest(BaseModel):
    type_offre: str | None = Field(default=None, max_length=255)
    nom: str | None = Field(default=None, max_length=255)
    description: str | None = None
    categorie: str | None = Field(default=None, max_length=255)
    volume: Decimal | None = Field(default=None, ge=0)
    unite: str | None = Field(default=None, max_length=255)
    capacite: Decimal | None = Field(default=None, ge=0)
    marches_vises: str | None = Field(default=None, max_length=255)
    statut: str | None = Field(default="ACTIF", max_length=255)


class OffreDeclareeUpdateRequest(BaseModel):
    type_offre: str | None = Field(default=None, max_length=255)
    nom: str | None = Field(default=None, max_length=255)
    description: str | None = None
    categorie: str | None = Field(default=None, max_length=255)
    volume: Decimal | None = Field(default=None, ge=0)
    unite: str | None = Field(default=None, max_length=255)
    capacite: Decimal | None = Field(default=None, ge=0)
    marches_vises: str | None = Field(default=None, max_length=255)
    statut: str | None = Field(default=None, max_length=255)


class OffreDeclareeResponse(BaseModel):
    id: UUID
    fiche_collecte_id: UUID
    type_offre: str | None = None
    nom: str | None = None
    description: str | None = None
    categorie: str | None = None
    volume: Decimal | None = None
    unite: str | None = None
    capacite: Decimal | None = None
    marches_vises: str | None = None
    statut: str | None = None
    created_at: datetime
    updated_at: datetime


class CertificationDeclareeCreateRequest(BaseModel):
    nom_certification: str | None = Field(default=None, max_length=255)
    numero: str | None = Field(default=None, max_length=255)
    organisme_declare: str | None = Field(default=None, max_length=255)
    norme_declaree: str | None = Field(default=None, max_length=255)
    portee: str | None = None
    date_obtention: date | None = None
    date_expiration: date | None = None
    copie_disponible: bool | None = None
    situation_declaree: str | None = Field(default=None, max_length=255)


class CertificationDeclareeUpdateRequest(BaseModel):
    nom_certification: str | None = Field(default=None, max_length=255)
    numero: str | None = Field(default=None, max_length=255)
    organisme_declare: str | None = Field(default=None, max_length=255)
    norme_declaree: str | None = Field(default=None, max_length=255)
    portee: str | None = None
    date_obtention: date | None = None
    date_expiration: date | None = None
    copie_disponible: bool | None = None
    situation_declaree: str | None = Field(default=None, max_length=255)


class CertificationDeclareeResponse(BaseModel):
    id: UUID
    fiche_collecte_id: UUID
    nom_certification: str | None = None
    numero: str | None = None
    organisme_declare: str | None = None
    norme_declaree: str | None = None
    portee: str | None = None
    date_obtention: date | None = None
    date_expiration: date | None = None
    copie_disponible: bool | None = None
    situation_declaree: str | None = None
    certification_officielle_id: UUID | None = None
    score_rapprochement: Decimal | None = None
    statut_rapprochement: str | None = None
    created_at: datetime
    updated_at: datetime
