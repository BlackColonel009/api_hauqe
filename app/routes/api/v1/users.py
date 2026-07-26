"""
Routes d'administration des utilisateurs.

Toutes les routes sont protégées par les permissions
créées lors du bootstrap sécurité.

Aucune confiance n'est accordée au frontend :
la permission est contrôlée côté serveur pour chaque action.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Request,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.permissions.auth import require_permission
from app.schemas.user import (
    UserCreateRequest,
    UserResponse,
    UserRoleAssignmentRequest,
    UserStatusRequest,
    UserUpdateRequest,
)
from app.services.auth_service import AuthContext
from app.services.user_service import UserService


router = APIRouter(
    prefix="/users",
    tags=["Utilisateurs"],
)


# ============================================================
# LISTE DES UTILISATEURS
# ============================================================

@router.get(
    "",
    response_model=list[UserResponse],
)
async def list_users(
    db: AsyncSession = Depends(get_db),

    actor: AuthContext = Depends(
        require_permission(
            "UTILISATEURS.LIRE"
        )
    ),
):
    return await UserService.list_users(
        db
    )


# ============================================================
# DETAIL UTILISATEUR
# ============================================================

@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
async def get_user(
    user_id: UUID,

    db: AsyncSession = Depends(get_db),

    actor: AuthContext = Depends(
        require_permission(
            "UTILISATEURS.LIRE"
        )
    ),
):
    return await UserService.get_user(
        db,
        user_id=user_id,
    )


# ============================================================
# CREATION
# ============================================================

@router.post(
    "",
    response_model=UserResponse,
    status_code=201,
)
async def create_user(
    payload: UserCreateRequest,
    request: Request,

    db: AsyncSession = Depends(get_db),

    actor: AuthContext = Depends(
        require_permission(
            "UTILISATEURS.CREER"
        )
    ),
):
    return await UserService.create_user(
        db,
        payload=payload,
        actor=actor,
        request=request,
    )


# ============================================================
# MODIFICATION
# ============================================================

@router.patch(
    "/{user_id}",
    response_model=UserResponse,
)
async def update_user(
    user_id: UUID,
    payload: UserUpdateRequest,
    request: Request,

    db: AsyncSession = Depends(get_db),

    actor: AuthContext = Depends(
        require_permission(
            "UTILISATEURS.MODIFIER"
        )
    ),
):
    return await UserService.update_user(
        db,
        user_id=user_id,
        payload=payload,
        actor=actor,
        request=request,
    )


# ============================================================
# ACTIVATION / DESACTIVATION
# ============================================================

@router.patch(
    "/{user_id}/status",
    response_model=UserResponse,
)
async def change_user_status(
    user_id: UUID,
    payload: UserStatusRequest,
    request: Request,

    db: AsyncSession = Depends(get_db),

    actor: AuthContext = Depends(
        require_permission(
            "UTILISATEURS.DESACTIVER"
        )
    ),
):
    return await UserService.change_status(
        db,
        user_id=user_id,
        new_status=payload.statut,
        motif=payload.motif,
        actor=actor,
        request=request,
    )


# ============================================================
# ATTRIBUTION D'UN ROLE
# ============================================================

@router.post(
    "/{user_id}/roles",
    response_model=UserResponse,
)
async def assign_role(
    user_id: UUID,
    payload: UserRoleAssignmentRequest,
    request: Request,

    db: AsyncSession = Depends(get_db),

    actor: AuthContext = Depends(
        require_permission(
            "UTILISATEURS.GERER_ROLES"
        )
    ),
):
    return await UserService.assign_role(
        db,
        user_id=user_id,
        role_id=payload.role_id,
        motif=payload.motif,
        actor=actor,
        request=request,
    )


# ============================================================
# RETRAIT D'UN ROLE
# ============================================================

@router.delete(
    "/{user_id}/roles/{role_id}",
    response_model=UserResponse,
)
async def remove_role(
    user_id: UUID,
    role_id: UUID,
    request: Request,

    db: AsyncSession = Depends(get_db),

    actor: AuthContext = Depends(
        require_permission(
            "UTILISATEURS.GERER_ROLES"
        )
    ),
):
    return await UserService.remove_role(
        db,
        user_id=user_id,
        role_id=role_id,
        actor=actor,
        request=request,
    )