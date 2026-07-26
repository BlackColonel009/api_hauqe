"""
Schémas API du sous-module Contacts entreprise.

RÔLE DU FICHIER
---------------
Définir les données acceptées et retournées par l'API pour
les contacts rattachés à une entreprise.

IMPORTANT
---------
Un contact appartient obligatoirement à une entreprise.

La suppression physique n'est pas utilisée :
    ACTIF   → contact utilisable
    INACTIF → contact désactivé

La relation entreprise_id est déterminée par l'URL et non par
le corps JSON afin d'éviter qu'un client puisse déplacer
arbitrairement un contact vers une autre entreprise.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================
# CRÉATION
# ============================================================

class ContactEntrepriseCreateRequest(BaseModel):
    """
    Données autorisées lors de la création d'un contact.
    """

    nom: str | None = Field(
        default=None,
        max_length=255,
    )

    prenoms: str | None = Field(
        default=None,
        max_length=255,
    )

    fonction: str | None = Field(
        default=None,
        max_length=255,
    )

    telephone: str | None = Field(
        default=None,
        max_length=255,
    )

    email: str | None = Field(
        default=None,
        max_length=255,
    )

    type_contact: str | None = Field(
        default=None,
        max_length=255,
    )

    contact_principal: bool = False


# ============================================================
# MODIFICATION
# ============================================================

class ContactEntrepriseUpdateRequest(BaseModel):
    """
    Mise à jour partielle.

    entreprise_id n'est volontairement pas modifiable ici.
    """

    nom: str | None = Field(
        default=None,
        max_length=255,
    )

    prenoms: str | None = Field(
        default=None,
        max_length=255,
    )

    fonction: str | None = Field(
        default=None,
        max_length=255,
    )

    telephone: str | None = Field(
        default=None,
        max_length=255,
    )

    email: str | None = Field(
        default=None,
        max_length=255,
    )

    type_contact: str | None = Field(
        default=None,
        max_length=255,
    )

    contact_principal: bool | None = None


# ============================================================
# DÉSACTIVATION / RESTAURATION
# ============================================================

class ContactStatusRequest(BaseModel):
    """
    Motif facultatif conservé dans le journal d'audit.
    """

    motif: str | None = Field(
        default=None,
        max_length=2000,
    )


# ============================================================
# RÉPONSE
# ============================================================

class ContactEntrepriseResponse(BaseModel):

    id: UUID
    entreprise_id: UUID

    nom: str | None = None
    prenoms: str | None = None
    fonction: str | None = None

    telephone: str | None = None
    email: str | None = None

    type_contact: str | None = None
    contact_principal: bool | None = None

    statut: str | None = None

    created_at: datetime
    updated_at: datetime