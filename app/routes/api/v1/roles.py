"""
Routes API des rôles et permissions.

Sécurité :
- consulter les rôles       → ROLES.LIRE
- consulter les permissions → PERMISSIONS.LIRE
- modifier rôle/permission  → PERMISSIONS.ATTRIBUER

Le frontend ne décide jamais si une opération est autorisée.
Toutes les permissions sont vérifiées côté FastAPI.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Request,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.permissions.auth import require_permission
from app.repositories.role_repository import (
    RoleRepository,
)
from app.schemas.role import (
    PermissionResponse,
    RolePermissionAssignmentRequest,
    RolePermissionsResponse,
    RoleResponse,
)
from app.services.auth_service import AuthContext
from app.services.role_permission_service import (
    RolePermissionService,
)


router = APIRouter(
    tags=["Rôles et permissions"],
)


# ============================================================
# CATALOGUE DES ROLES
# ============================================================

@router.get(
    "/roles",
    response_model=list[RoleResponse],
)
async def list_roles(
    db: AsyncSession = Depends(get_db),

    actor: AuthContext = Depends(
        require_permission(
            "ROLES.LIRE"
        )
    ),
):
    roles = await RoleRepository.list_roles(
        db
    )

    return [
        RoleResponse(
            id=role.id,
            code=role.code,
            libelle=role.libelle,
            description=role.description,
            niveau=role.niveau,
            statut=role.statut,
        )
        for role in roles
    ]


# ============================================================
# CATALOGUE DES PERMISSIONS
# ============================================================

@router.get(
    "/permissions",
    response_model=list[PermissionResponse],
)
async def list_permissions(
    db: AsyncSession = Depends(get_db),

    actor: AuthContext = Depends(
        require_permission(
            "PERMISSIONS.LIRE"
        )
    ),
):
    permissions = (
        await RoleRepository.list_permissions(
            db
        )
    )

    return [
        PermissionResponse(
            id=permission.id,
            code=permission.code,
            domaine=permission.domaine,
            action=permission.action,
            description=permission.description,
        )
        for permission in permissions
    ]


# ============================================================
# PERMISSIONS D'UN ROLE
# ============================================================

@router.get(
    "/roles/{role_id}/permissions",
    response_model=RolePermissionsResponse,
)
async def get_role_permissions(
    role_id: UUID,

    db: AsyncSession = Depends(get_db),

    actor: AuthContext = Depends(
        require_permission(
            "PERMISSIONS.LIRE"
        )
    ),
):
    return await (
        RolePermissionService
        .get_role_permissions(
            db,
            role_id=role_id,
        )
    )


# ============================================================
# ATTRIBUER UNE PERMISSION A UN ROLE
# ============================================================

@router.post(
    "/roles/{role_id}/permissions",
    response_model=RolePermissionsResponse,
    status_code=status.HTTP_201_CREATED,
)
async def assign_role_permission(
    role_id: UUID,
    payload: RolePermissionAssignmentRequest,
    request: Request,

    db: AsyncSession = Depends(get_db),

    actor: AuthContext = Depends(
        require_permission(
            "PERMISSIONS.ATTRIBUER"
        )
    ),
):
    return await (
        RolePermissionService
        .assign_permission(
            db,
            role_id=role_id,
            permission_id=payload.permission_id,
            actor=actor,
            request=request,
        )
    )


# ============================================================
# RETIRER UNE PERMISSION D'UN ROLE
# ============================================================

@router.delete(
    "/roles/{role_id}/permissions/{permission_id}",
    response_model=RolePermissionsResponse,
)
async def remove_role_permission(
    role_id: UUID,
    permission_id: UUID,
    request: Request,

    db: AsyncSession = Depends(get_db),

    actor: AuthContext = Depends(
        require_permission(
            "PERMISSIONS.ATTRIBUER"
        )
    ),
):
    return await (
        RolePermissionService
        .remove_permission(
            db,
            role_id=role_id,
            permission_id=permission_id,
            actor=actor,
            request=request,
        )
    )