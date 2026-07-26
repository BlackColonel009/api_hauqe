"""
Repository PostgreSQL — Mon compte / Sécurité utilisateur.

Le repository ne contient aucune décision métier.
Il centralise :
- profil + préférences ;
- rôles et permissions ;
- sessions ;
- MFA et verrou de session ;
- jetons temporaires ;
- notifications de sécurité ;
- lecture des comptes actifs pour le scan RM-33.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.jeton_securite_utilisateur import JetonSecuriteUtilisateur
from app.models.notification import Notification
from app.models.permission import Permission
from app.models.preference_utilisateur import PreferenceUtilisateur
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.securite_compte_utilisateur import SecuriteCompteUtilisateur
from app.models.session_utilisateur import SessionUtilisateur
from app.models.utilisateur import Utilisateur
from app.models.utilisateur_role import UtilisateurRole
from app.models.verrou_session_utilisateur import VerrouSessionUtilisateur
from app.models.zone_administrative import ZoneAdministrative


class AccountRepository:

    # ========================================================
    # UTILISATEUR / PROFIL
    # ========================================================

    @staticmethod
    async def get_user(
        db: AsyncSession,
        user_id: UUID,
    ) -> Utilisateur | None:
        result = await db.execute(
            select(Utilisateur).where(Utilisateur.id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_email(
        db: AsyncSession,
        email: str,
    ) -> Utilisateur | None:
        result = await db.execute(
            select(Utilisateur).where(
                func.lower(Utilisateur.email) == email.strip().lower()
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_region_name(
        db: AsyncSession,
        zone_id: UUID | None,
    ) -> str | None:
        if zone_id is None:
            return None
        result = await db.execute(
            select(ZoneAdministrative.nom).where(
                ZoneAdministrative.id == zone_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_preferences(
        db: AsyncSession,
        user_id: UUID,
    ) -> PreferenceUtilisateur | None:
        result = await db.execute(
            select(PreferenceUtilisateur).where(
                PreferenceUtilisateur.utilisateur_id == user_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_or_create_preferences(
        db: AsyncSession,
        user_id: UUID,
    ) -> PreferenceUtilisateur:
        item = await AccountRepository.get_preferences(db, user_id)
        if item is None:
            item = PreferenceUtilisateur(utilisateur_id=user_id)
            db.add(item)
            await db.flush()
        return item

    @staticmethod
    async def active_avatar_document(
        db: AsyncSession,
        document_id: UUID,
    ) -> Document | None:
        result = await db.execute(
            select(Document).where(
                Document.id == document_id,
                func.upper(func.coalesce(Document.statut, "ACTIF"))
                == "ACTIF",
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def roles_and_permissions(
        db: AsyncSession,
        user_id: UUID,
    ) -> tuple[list[str], list[str]]:
        roles_result = await db.execute(
            select(Role.code)
            .join(
                UtilisateurRole,
                UtilisateurRole.role_id == Role.id,
            )
            .where(
                UtilisateurRole.utilisateur_id == user_id,
                func.upper(
                    func.coalesce(UtilisateurRole.statut, "ACTIF")
                ) == "ACTIF",
            )
            .distinct()
            .order_by(Role.code)
        )
        roles = [row[0] for row in roles_result.all()]

        permissions_result = await db.execute(
            select(Permission.code)
            .join(
                RolePermission,
                RolePermission.permission_id == Permission.id,
            )
            .join(
                UtilisateurRole,
                UtilisateurRole.role_id == RolePermission.role_id,
            )
            .where(
                UtilisateurRole.utilisateur_id == user_id,
                func.upper(
                    func.coalesce(UtilisateurRole.statut, "ACTIF")
                ) == "ACTIF",
            )
            .distinct()
            .order_by(Permission.code)
        )
        permissions = [row[0] for row in permissions_result.all()]
        return roles, permissions

    # ========================================================
    # SÉCURITÉ DU COMPTE
    # ========================================================

    @staticmethod
    async def get_security(
        db: AsyncSession,
        user_id: UUID,
    ) -> SecuriteCompteUtilisateur | None:
        result = await db.execute(
            select(SecuriteCompteUtilisateur).where(
                SecuriteCompteUtilisateur.utilisateur_id == user_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_or_create_security(
        db: AsyncSession,
        user_id: UUID,
    ) -> SecuriteCompteUtilisateur:
        item = await AccountRepository.get_security(db, user_id)
        if item is None:
            item = SecuriteCompteUtilisateur(utilisateur_id=user_id)
            db.add(item)
            await db.flush()
        return item

    # ========================================================
    # SESSIONS
    # ========================================================

    @staticmethod
    async def get_session(
        db: AsyncSession,
        session_id: UUID,
    ) -> SessionUtilisateur | None:
        result = await db.execute(
            select(SessionUtilisateur).where(
                SessionUtilisateur.id == session_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_session_by_token_hash(
        db: AsyncSession,
        token_hash: str,
    ) -> SessionUtilisateur | None:
        result = await db.execute(
            select(SessionUtilisateur).where(
                SessionUtilisateur.jeton_hash == token_hash
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_user_sessions(
        db: AsyncSession,
        user_id: UUID,
    ) -> list[SessionUtilisateur]:
        result = await db.execute(
            select(SessionUtilisateur)
            .where(SessionUtilisateur.utilisateur_id == user_id)
            .order_by(
                SessionUtilisateur.debut_at.desc().nullslast(),
                SessionUtilisateur.created_at.desc(),
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def active_user_sessions(
        db: AsyncSession,
        user_id: UUID,
    ) -> list[SessionUtilisateur]:
        now = datetime.now().astimezone()
        result = await db.execute(
            select(SessionUtilisateur).where(
                SessionUtilisateur.utilisateur_id == user_id,
                SessionUtilisateur.revoquee_at.is_(None),
                (
                    SessionUtilisateur.expiration_at.is_(None)
                    | (SessionUtilisateur.expiration_at > now)
                ),
            )
        )
        return list(result.scalars().all())

    # ========================================================
    # VERROUS DE SESSION
    # ========================================================

    @staticmethod
    async def get_session_lock(
        db: AsyncSession,
        session_id: UUID,
    ) -> VerrouSessionUtilisateur | None:
        result = await db.execute(
            select(VerrouSessionUtilisateur).where(
                VerrouSessionUtilisateur.session_utilisateur_id
                == session_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_or_create_session_lock(
        db: AsyncSession,
        session_id: UUID,
    ) -> VerrouSessionUtilisateur:
        item = await AccountRepository.get_session_lock(
            db,
            session_id,
        )
        if item is None:
            item = VerrouSessionUtilisateur(
                session_utilisateur_id=session_id,
            )
            db.add(item)
            await db.flush()
        return item

    @staticmethod
    async def lock_rows_for_sessions(
        db: AsyncSession,
        session_ids: list[UUID],
    ) -> dict[UUID, VerrouSessionUtilisateur]:
        if not session_ids:
            return {}
        result = await db.execute(
            select(VerrouSessionUtilisateur).where(
                VerrouSessionUtilisateur.session_utilisateur_id.in_(
                    session_ids
                )
            )
        )
        return {
            row.session_utilisateur_id: row
            for row in result.scalars().all()
        }

    # ========================================================
    # JETONS DE SÉCURITÉ
    # ========================================================

    @staticmethod
    async def get_security_token_by_hash(
        db: AsyncSession,
        token_hash: str,
    ) -> JetonSecuriteUtilisateur | None:
        result = await db.execute(
            select(JetonSecuriteUtilisateur).where(
                JetonSecuriteUtilisateur.jeton_hash == token_hash
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def active_security_tokens(
        db: AsyncSession,
        *,
        user_id: UUID,
        token_type: str,
    ) -> list[JetonSecuriteUtilisateur]:
        now = datetime.now().astimezone()
        result = await db.execute(
            select(JetonSecuriteUtilisateur).where(
                JetonSecuriteUtilisateur.utilisateur_id == user_id,
                JetonSecuriteUtilisateur.type_jeton == token_type,
                JetonSecuriteUtilisateur.utilise_at.is_(None),
                JetonSecuriteUtilisateur.expiration_at > now,
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def expired_or_used_tokens(
        db: AsyncSession,
        *,
        before: datetime,
    ) -> list[JetonSecuriteUtilisateur]:
        result = await db.execute(
            select(JetonSecuriteUtilisateur).where(
                (
                    JetonSecuriteUtilisateur.expiration_at < before
                )
                | (
                    JetonSecuriteUtilisateur.utilise_at.is_not(None)
                )
            )
        )
        return list(result.scalars().all())

    # ========================================================
    # NOTIFICATIONS DE SÉCURITÉ
    # ========================================================

    @staticmethod
    async def create_notification(
        db: AsyncSession,
        *,
        user_id: UUID,
        channel: str,
        subject: str,
        body: str,
        external_address: str | None = None,
        immediate: bool = False,
    ) -> Notification:
        item = Notification(
            alerte_id=None,
            destinataire_utilisateur_id=user_id,
            adresse_externe=external_address,
            canal=channel,
            objet=subject,
            contenu=body,
            date_envoi=(
                datetime.now().date()
                if immediate else None
            ),
            date_lecture=None,
            resultat=(
                "Disponible dans l'application"
                if immediate else None
            ),
            nombre_tentatives=0,
            message_erreur=None,
            statut="ENVOYEE" if immediate else "EN_ATTENTE",
        )
        db.add(item)
        await db.flush()
        return item

    # ========================================================
    # SCAN D'INACTIVITÉ RM-33
    # ========================================================

    @staticmethod
    async def active_users(
        db: AsyncSession,
    ) -> list[Utilisateur]:
        result = await db.execute(
            select(Utilisateur).where(
                func.upper(Utilisateur.statut) == "ACTIF"
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def last_session_activity(
        db: AsyncSession,
        user_id: UUID,
    ) -> datetime | None:
        result = await db.execute(
            select(func.max(SessionUtilisateur.derniere_activite_at)).where(
                SessionUtilisateur.utilisateur_id == user_id
            )
        )
        return result.scalar_one_or_none()
