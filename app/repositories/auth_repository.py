from __future__ import annotations

from datetime import date
from datetime import datetime
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.session_utilisateur import SessionUtilisateur
from app.models.utilisateur import Utilisateur
from app.models.utilisateur_role import UtilisateurRole
from app.models.audit import EvenementAudit


class AuthRepository:

    @staticmethod
    async def get_user_by_email(
        session: AsyncSession,
        email: str,
    ) -> Utilisateur | None:

        result = await session.execute(
            select(Utilisateur).where(
                Utilisateur.email == email
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_id(
        session: AsyncSession,
        user_id: UUID,
    ) -> Utilisateur | None:

        result = await session.execute(
            select(Utilisateur).where(
                Utilisateur.id == user_id
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def get_session_by_token_hash(
        session: AsyncSession,
        token_hash: str,
    ) -> SessionUtilisateur | None:

        result = await session.execute(
            select(SessionUtilisateur).where(
                SessionUtilisateur.jeton_hash
                == token_hash
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def get_roles(
        session: AsyncSession,
        user_id: UUID,
    ) -> list[str]:

        today = date.today()

        result = await session.execute(
            select(Role.code)
            .join(
                UtilisateurRole,
                UtilisateurRole.role_id == Role.id,
            )
            .where(
                UtilisateurRole.utilisateur_id
                == user_id,

                or_(
                    UtilisateurRole.statut.is_(None),
                    UtilisateurRole.statut == "ACTIF",
                ),

                or_(
                    UtilisateurRole.date_debut.is_(None),
                    UtilisateurRole.date_debut <= today,
                ),

                or_(
                    UtilisateurRole.date_fin.is_(None),
                    UtilisateurRole.date_fin >= today,
                ),

                or_(
                    Role.statut.is_(None),
                    Role.statut == "ACTIF",
                ),
            )
            .distinct()
            .order_by(Role.code)
        )

        return list(result.scalars().all())

    @staticmethod
    async def get_permissions(
        session: AsyncSession,
        user_id: UUID,
    ) -> list[str]:

        today = date.today()

        result = await session.execute(
            select(Permission.code)
            .join(
                RolePermission,
                RolePermission.permission_id
                == Permission.id,
            )
            .join(
                Role,
                Role.id == RolePermission.role_id,
            )
            .join(
                UtilisateurRole,
                UtilisateurRole.role_id
                == Role.id,
            )
            .where(
                UtilisateurRole.utilisateur_id
                == user_id,

                or_(
                    UtilisateurRole.statut.is_(None),
                    UtilisateurRole.statut == "ACTIF",
                ),

                or_(
                    UtilisateurRole.date_debut.is_(None),
                    UtilisateurRole.date_debut <= today,
                ),

                or_(
                    UtilisateurRole.date_fin.is_(None),
                    UtilisateurRole.date_fin >= today,
                ),

                or_(
                    Role.statut.is_(None),
                    Role.statut == "ACTIF",
                ),
            )
            .distinct()
            .order_by(Permission.code)
        )

        return list(result.scalars().all())
    
    # ========================================================
    # SECURITE - ECHECS DE CONNEXION
    # ========================================================

    @staticmethod
    async def get_recent_failed_logins_for_user(
        session: AsyncSession,
        *,
        user_id: UUID,
        since: datetime,
    ) -> list[EvenementAudit]:
        """
        Retourne les échecs de connexion récents associés
        à un utilisateur connu.

        Cette méthode permet le verrouillage logique du compte
        sans ajouter de colonne locked_until dans utilisateurs.
        """

        result = await session.execute(
            select(EvenementAudit)
            .where(
                EvenementAudit.action == "AUTH_LOGIN",
                EvenementAudit.resultat == "ECHEC",
                EvenementAudit.utilisateur_id == user_id,
                EvenementAudit.date_evenement >= since,
            )
            .order_by(
                EvenementAudit.date_evenement.desc()
            )
        )

        return list(
            result.scalars().all()
        )


    @staticmethod
    async def get_recent_failed_logins_for_ip(
        session: AsyncSession,
        *,
        ip_address: str,
        since: datetime,
    ) -> list[EvenementAudit]:
        """
        Retourne les échecs récents provenant d'une IP.

        Cette protection complète le verrouillage par compte :
        elle limite les attaques utilisant plusieurs emails.
        """

        result = await session.execute(
            select(EvenementAudit)
            .where(
                EvenementAudit.action == "AUTH_LOGIN",
                EvenementAudit.resultat == "ECHEC",
                EvenementAudit.adresse_ip == ip_address,
                EvenementAudit.date_evenement >= since,
            )
            .order_by(
                EvenementAudit.date_evenement.desc()
            )
        )

        return list(
            result.scalars().all()
        )