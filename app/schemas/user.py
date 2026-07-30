"""
Schémas API liés à l'administration des utilisateurs.

Ce fichier définit uniquement les données exposées par l'API.
Il ne contient aucune logique métier ni accès PostgreSQL.

IMPORTANT :
- le hash du mot de passe n'est jamais exposé ;
- le mot de passe initial n'apparaît que dans la requête
  de création ;
- les rôles sont exposés par leur code fonctionnel.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================
# CREATION D'UN UTILISATEUR
# ============================================================

class UserCreateRequest(BaseModel):
    """
    Données nécessaires pour créer un compte.

    Pour le moment, l'administrateur fournit un mot de passe
    initial. Il est immédiatement transformé en hash Argon2id.
    """

    email: str = Field(
        min_length=3,
        max_length=255,
    )

    password: str = Field(
        min_length=12,
        max_length=1024,
    )

    nom: str | None = Field(
        default=None,
        max_length=255,
    )

    prenoms: str | None = Field(
        default=None,
        max_length=255,
    )

    telephone: str | None = Field(
        default=None,
        max_length=255,
    )

    fonction: str | None = Field(
        default=None,
        max_length=255,
    )

    statut: str = Field(
        default="ACTIF",
        max_length=255,
    )

    role_ids: list[UUID] = Field(default_factory=list)

    envoyer_identifiants_email: bool = False


# ============================================================
# MODIFICATION D'UN UTILISATEUR
# ============================================================

class UserUpdateRequest(BaseModel):
    """
    Mise à jour partielle.

    Tous les champs sont optionnels.
    Le mot de passe n'est volontairement pas modifié ici :
    une route dédiée sera créée pour cela.
    """

    nom: str | None = Field(
        default=None,
        max_length=255,
    )

    prenoms: str | None = Field(
        default=None,
        max_length=255,
    )

    telephone: str | None = Field(
        default=None,
        max_length=255,
    )

    fonction: str | None = Field(
        default=None,
        max_length=255,
    )


# ============================================================
# CHANGEMENT DE STATUT
# ============================================================

class UserStatusRequest(BaseModel):
    """
    Active ou désactive un compte.

    Valeurs actuellement supportées :
    - ACTIF
    - INACTIF
    """

    statut: str = Field(
        min_length=1,
        max_length=255,
    )

    motif: str | None = Field(
        default=None,
        max_length=1000,
    )


# ============================================================
# ATTRIBUTION D'UN ROLE
# ============================================================

class UserRoleAssignmentRequest(BaseModel):
    """
    Associe un rôle existant à un utilisateur.
    """

    role_id: UUID

    motif: str | None = Field(
        default=None,
        max_length=1000,
    )


# ============================================================
# REPONSE UTILISATEUR
# ============================================================

class UserResponse(BaseModel):

    id: UUID
    email: str

    nom: str | None = None
    prenoms: str | None = None
    telephone: str | None = None
    fonction: str | None = None

    statut: str | None = None
    mfa_active: bool | None = None

    derniere_connexion_at: datetime | None = None

    roles: list[str] = []
