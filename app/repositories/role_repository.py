"""
Repository des rôles et permissions.

Ce fichier contient uniquement les opérations PostgreSQL
nécessaires à la gestion du RBAC (Role Based Access Control).

Il ne décide PAS si l'utilisateur courant possède le droit
de modifier un rôle.

Cette décision appartient à la couche d'autorisation/service.

Tables utilisées :
- roles
- permissions
- role_permission
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission


class RoleRepository:

    # ========================================================
    # ROLES
    # ========================================================

    @staticmethod
    async def list_roles(
        db: AsyncSession,
    ) -> list[Role]:
        """
        Retourne tous les rôles.
        """

        result = await db.execute(
            select(Role)
            .order_by(
                Role.niveau.desc(),
                Role.code,
            )
        )

        return list(
            result.scalars().all()
        )


    @staticmethod
    async def get_role_by_id(
        db: AsyncSession,
        role_id: UUID,
    ) -> Role | None:
        """
        Recherche un rôle par son UUID.
        """

        result = await db.execute(
            select(Role).where(
                Role.id == role_id
            )
        )

        return result.scalar_one_or_none()


    # ========================================================
    # PERMISSIONS
    # ========================================================

    @staticmethod
    async def list_permissions(
        db: AsyncSession,
    ) -> list[Permission]:
        """
        Retourne le catalogue complet des permissions.
        """

        result = await db.execute(
            select(Permission)
            .order_by(
                Permission.domaine,
                Permission.action,
                Permission.code,
            )
        )

        return list(
            result.scalars().all()
        )


    @staticmethod
    async def get_permission_by_id(
        db: AsyncSession,
        permission_id: UUID,
    ) -> Permission | None:
        """
        Recherche une permission par son UUID.
        """

        result = await db.execute(
            select(Permission).where(
                Permission.id == permission_id
            )
        )

        return result.scalar_one_or_none()


    # ========================================================
    # PERMISSIONS D'UN ROLE
    # ========================================================

    @staticmethod
    async def get_permissions_for_role(
        db: AsyncSession,
        role_id: UUID,
    ) -> list[Permission]:
        """
        Retourne toutes les permissions actuellement
        attribuées à un rôle.
        """

        result = await db.execute(
            select(Permission)
            .join(
                RolePermission,
                RolePermission.permission_id
                == Permission.id,
            )
            .where(
                RolePermission.role_id == role_id
            )
            .distinct()
            .order_by(
                Permission.domaine,
                Permission.action,
                Permission.code,
            )
        )

        return list(
            result.scalars().all()
        )


    # ========================================================
    # LIEN ROLE ↔ PERMISSION
    # ========================================================

    @staticmethod
    async def get_role_permission(
        db: AsyncSession,
        *,
        role_id: UUID,
        permission_id: UUID,
    ) -> RolePermission | None:
        """
        Recherche l'association technique entre un rôle
        et une permission.

        La table role_permission ne possède pas de colonne
        de statut dans le MPD actuel.
        """

        result = await db.execute(
            select(RolePermission).where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id
                == permission_id,
            )
        )

        return result.scalar_one_or_none()