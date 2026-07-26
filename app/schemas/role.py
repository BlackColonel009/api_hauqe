"""
Schémas API des rôles et permissions.

Responsabilités :
- exposer les rôles sans exposer les détails SQLAlchemy ;
- exposer le catalogue des permissions ;
- recevoir une demande d'attribution de permission ;
- retourner la matrice de permissions d'un rôle.

Aucune logique d'autorisation n'est exécutée ici.
Les contrôles de sécurité sont réalisés dans les services
et les dépendances FastAPI.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================
# PERMISSION
# ============================================================

class PermissionResponse(BaseModel):
    """
    Représentation publique d'une permission.
    """

    id: UUID
    code: str
    domaine: str | None = None
    action: str | None = None
    description: str | None = None


# ============================================================
# ROLE
# ============================================================

class RoleResponse(BaseModel):
    """
    Représentation publique d'un rôle.
    """

    id: UUID
    code: str
    libelle: str | None = None
    description: str | None = None
    niveau: int | None = None
    statut: str | None = None


# ============================================================
# ATTRIBUTION D'UNE PERMISSION
# ============================================================

class RolePermissionAssignmentRequest(BaseModel):
    """
    Corps envoyé à :

        POST /roles/{role_id}/permissions
    """

    permission_id: UUID


# ============================================================
# MATRICE D'UN ROLE
# ============================================================

class RolePermissionsResponse(BaseModel):
    """
    Retourne un rôle avec toutes ses permissions effectives.
    """

    role_id: UUID
    role_code: str
    role_libelle: str | None = None

    permissions: list[PermissionResponse] = Field(
        default_factory=list
    )