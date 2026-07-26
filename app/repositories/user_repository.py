"""
Accès PostgreSQL pour l'administration des utilisateurs.

Responsabilités :
- rechercher et lister les utilisateurs ;
- créer les associations utilisateur ↔ rôle ;
- récupérer les rôles ;
- révoquer les sessions actives.

IMPORTANT :
Ce repository ne décide pas qui a le droit d'effectuer
ces opérations. Les permissions sont contrôlées dans
les routes/services.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permission import Permission
from app.models.role import Role
from app.models.session_utilisateur import (
    SessionUtilisateur,
)
from app.models.utilisateur import Utilisateur
from app.models.utilisateur_role import UtilisateurRole


class UserRepository:

    # ========================================================
    # UTILISATEURS
    # ========================================================

    @staticmethod
    async def list_users(
        db: AsyncSession,
    ) -> list[Utilisateur]:
        """
        Retourne tous les utilisateurs.

        La pagination sera ajoutée ensuite lorsque les modules
        métier commenceront à produire davantage de données.
        """

        result = await db.execute(
            select(Utilisateur)
            .order_by(
                Utilisateur.nom,
                Utilisateur.prenoms,
                Utilisateur.email,
            )
        )

        return list(
            result.scalars().all()
        )


    @staticmethod
    async def get_user_by_id(
        db: AsyncSession,
        user_id: UUID,
    ) -> Utilisateur | None:

        result = await db.execute(
            select(Utilisateur).where(
                Utilisateur.id == user_id
            )
        )

        return result.scalar_one_or_none()


    @staticmethod
    async def get_user_by_email(
        db: AsyncSession,
        email: str,
    ) -> Utilisateur | None:

        result = await db.execute(
            select(Utilisateur).where(
                Utilisateur.email == email
            )
        )

        return result.scalar_one_or_none()


    # ========================================================
    # ROLES
    # ========================================================

    @staticmethod
    async def list_roles(
        db: AsyncSession,
    ) -> list[Role]:

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

        result = await db.execute(
            select(Role).where(
                Role.id == role_id
            )
        )

        return result.scalar_one_or_none()


    @staticmethod
    async def get_role_assignment(
        db: AsyncSession,
        *,
        user_id: UUID,
        role_id: UUID,
    ) -> UtilisateurRole | None:

        result = await db.execute(
            select(UtilisateurRole).where(
                UtilisateurRole.utilisateur_id
                == user_id,

                UtilisateurRole.role_id
                == role_id,

                UtilisateurRole.statut
                == "ACTIF",
            )
        )

        return result.scalar_one_or_none()


    @staticmethod
    async def get_role_codes_for_user(
        db: AsyncSession,
        user_id: UUID,
    ) -> list[str]:

        result = await db.execute(
            select(Role.code)
            .join(
                UtilisateurRole,
                UtilisateurRole.role_id
                == Role.id,
            )
            .where(
                UtilisateurRole.utilisateur_id
                == user_id,

                UtilisateurRole.statut
                == "ACTIF",
            )
            .distinct()
            .order_by(Role.code)
        )

        return list(
            result.scalars().all()
        )


    # ========================================================
    # PERMISSIONS
    # ========================================================

    @staticmethod
    async def list_permissions(
        db: AsyncSession,
    ) -> list[Permission]:

        result = await db.execute(
            select(Permission)
            .order_by(
                Permission.domaine,
                Permission.action,
            )
        )

        return list(
            result.scalars().all()
        )


    # ========================================================
    # SESSIONS
    # ========================================================

    @staticmethod
    async def revoke_active_sessions(
        db: AsyncSession,
        *,
        user_id: UUID,
        revoked_at: datetime,
    ) -> int:
        """
        Révoque toutes les sessions encore ouvertes.

        Cette méthode est appelée lorsqu'un compte est
        désactivé par un administrateur.
        """

        result = await db.execute(
            select(SessionUtilisateur).where(
                SessionUtilisateur.utilisateur_id
                == user_id,

                SessionUtilisateur.revoquee_at.is_(
                    None
                ),
            )
        )

        sessions = list(
            result.scalars().all()
        )

        for db_session in sessions:
            db_session.revoquee_at = revoked_at

        return len(sessions)