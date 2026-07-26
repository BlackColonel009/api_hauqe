"""
Schémas API du module Entreprises.

RÔLE DU FICHIER
---------------
Définir précisément ce que l'API accepte et retourne pour une entreprise.

IMPORTANT
---------
Le modèle PostgreSQL contient davantage de colonnes que celles exposées
ici.

C'est volontaire.

Par exemple :
    - chiffre_affaires reste présent dans PostgreSQL ;
    - niveau_risque reste présent dans PostgreSQL ;
    - date_derniere_verification reste présente dans PostgreSQL.

Ces données seront pilotées par les modules métier appropriés et ne sont
pas modifiables depuis le formulaire Entreprises courant.

Aucune logique métier ni requête SQL ne doit être placée ici.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================
# CRÉATION D'UNE ENTREPRISE
# ============================================================

class EntrepriseCreateRequest(BaseModel):
    """
    Données autorisées lors de la création d'une entreprise.

    identifiant_national :
        identifiant métier unique de l'entreprise.

    zone_siege_id :
        doit correspondre à une zone_administrative existante.
    """

    identifiant_national: str = Field(
        min_length=1,
        max_length=255,
    )

    raison_sociale: str | None = Field(
        default=None,
        max_length=255,
    )

    nom_commercial: str | None = Field(
        default=None,
        max_length=255,
    )

    forme_juridique: str | None = Field(
        default=None,
        max_length=255,
    )

    rccm: str | None = Field(
        default=None,
        max_length=255,
    )

    nif: str | None = Field(
        default=None,
        max_length=255,
    )

    ifu: str | None = Field(
        default=None,
        max_length=255,
    )

    date_creation: date | None = None

    nationalite: str | None = Field(
        default=None,
        max_length=255,
    )

    capital_social: Decimal | None = None

    effectif: int | None = Field(
        default=None,
        ge=0,
    )

    email_principal: str | None = Field(
        default=None,
        max_length=255,
    )

    telephone_principal: str | None = Field(
        default=None,
        max_length=255,
    )

    site_web: str | None = Field(
        default=None,
        max_length=255,
    )

    adresse_siege: str | None = Field(
        default=None,
        max_length=255,
    )

    zone_siege_id: UUID

    activite_principale: str | None = Field(
        default=None,
        max_length=255,
    )

    secteurs_secondaires: list[str] | None = None


# ============================================================
# MODIFICATION D'UNE ENTREPRISE
# ============================================================

class EntrepriseUpdateRequest(BaseModel):
    """
    Modification partielle.

    L'identifiant national n'est volontairement pas modifiable
    dans cette route.

    Une modification d'un identifiant métier critique devra,
    si elle devient nécessaire, passer par une procédure dédiée
    et fortement auditée.
    """

    raison_sociale: str | None = Field(
        default=None,
        max_length=255,
    )

    nom_commercial: str | None = Field(
        default=None,
        max_length=255,
    )

    forme_juridique: str | None = Field(
        default=None,
        max_length=255,
    )

    rccm: str | None = Field(
        default=None,
        max_length=255,
    )

    nif: str | None = Field(
        default=None,
        max_length=255,
    )

    ifu: str | None = Field(
        default=None,
        max_length=255,
    )

    date_creation: date | None = None

    nationalite: str | None = Field(
        default=None,
        max_length=255,
    )

    capital_social: Decimal | None = None

    effectif: int | None = Field(
        default=None,
        ge=0,
    )

    email_principal: str | None = Field(
        default=None,
        max_length=255,
    )

    telephone_principal: str | None = Field(
        default=None,
        max_length=255,
    )

    site_web: str | None = Field(
        default=None,
        max_length=255,
    )

    adresse_siege: str | None = Field(
        default=None,
        max_length=255,
    )

    zone_siege_id: UUID | None = None

    activite_principale: str | None = Field(
        default=None,
        max_length=255,
    )

    secteurs_secondaires: list[str] | None = None


# ============================================================
# ARCHIVAGE LOGIQUE
# ============================================================

class EntrepriseArchiveRequest(BaseModel):
    """
    L'entreprise n'est jamais supprimée physiquement ici.

    Le motif est conservé dans le journal d'audit.
    """

    motif: str | None = Field(
        default=None,
        max_length=2000,
    )


# ============================================================
# RÉPONSE API
# ============================================================

class EntrepriseResponse(BaseModel):
    """
    Vue publique actuelle d'une entreprise.

    Les colonnes internes non utilisées actuellement ne sont
    volontairement pas exposées.
    """

    id: UUID

    identifiant_national: str

    raison_sociale: str | None = None
    nom_commercial: str | None = None
    forme_juridique: str | None = None

    rccm: str | None = None
    nif: str | None = None
    ifu: str | None = None

    date_creation: date | None = None
    nationalite: str | None = None

    capital_social: Decimal | None = None
    effectif: int | None = None

    email_principal: str | None = None
    telephone_principal: str | None = None
    site_web: str | None = None

    adresse_siege: str | None = None
    zone_siege_id: UUID

    activite_principale: str | None = None

    secteurs_secondaires: list[str] | None = None

    statut: str | None = None

    created_at: datetime
    updated_at: datetime


# ============================================================
# LISTE PAGINÉE
# ============================================================

class EntrepriseListResponse(BaseModel):
    """
    Réponse utilisée par la page de liste.

    Cela évite de retourner plusieurs milliers d'entreprises
    en une seule requête lorsque la BNEC grandira.
    """

    total: int
    limit: int
    offset: int

    items: list[EntrepriseResponse] = Field(
        default_factory=list
    )