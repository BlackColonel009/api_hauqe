"""
Repository PostgreSQL — présence utilisateurs.

Aucune décision métier ici :
- sessions récentes ;
- rôles actifs ;
- avatars ;
- résolution de la session courante.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.preference_utilisateur import PreferenceUtilisateur
from app.models.role import Role
from app.models.session_utilisateur import SessionUtilisateur
from app.models.utilisateur import Utilisateur
from app.models.utilisateur_role import UtilisateurRole


class PresenceRepository:

    @staticmethod
    async def recent_session_rows(
        db: AsyncSession,
        *,
        cutoff: datetime,
    ):
        activity_at = func.coalesce(
            SessionUtilisateur.derniere_activite_at,
            SessionUtilisateur.debut_at,
            SessionUtilisateur.created_at,
        )

        result = await db.execute(
            select(
                SessionUtilisateur,
                Utilisateur,
                activity_at.label("activity_at"),
            )
            .join(
                Utilisateur,
                Utilisateur.id == SessionUtilisateur.utilisateur_id,
            )
            .where(activity_at >= cutoff)
            .order_by(activity_at.desc())
        )

        return list(result.all())

    @staticmethod
    async def roles_for_users(
        db: AsyncSession,
        user_ids: list[UUID],
    ) -> dict[UUID, list[tuple[str, str | None]]]:
        if not user_ids:
            return {}

        result = await db.execute(
            select(
                UtilisateurRole.utilisateur_id,
                Role.code,
                Role.libelle,
                Role.niveau,
            )
            .join(
                Role,
                Role.id == UtilisateurRole.role_id,
            )
            .where(
                UtilisateurRole.utilisateur_id.in_(user_ids),
                func.upper(
                    func.coalesce(UtilisateurRole.statut, "ACTIF")
                ) == "ACTIF",
            )
            .order_by(
                UtilisateurRole.utilisateur_id,
                Role.niveau.desc().nullslast(),
                Role.code,
            )
        )

        mapping: dict[
            UUID,
            list[tuple[str, str | None]],
        ] = {}

        for user_id, code, libelle, _niveau in result.all():
            mapping.setdefault(user_id, []).append(
                (code, libelle)
            )

        return mapping

    @staticmethod
    async def avatar_users(
        db: AsyncSession,
        user_ids: list[UUID],
    ) -> set[UUID]:
        if not user_ids:
            return set()

        result = await db.execute(
            select(
                PreferenceUtilisateur.utilisateur_id
            ).where(
                PreferenceUtilisateur.utilisateur_id.in_(user_ids),
                PreferenceUtilisateur.avatar_document_id.is_not(None),
            )
        )

        return {row[0] for row in result.all()}

    @staticmethod
    async def get_session_by_token_hash(
        db: AsyncSession,
        *,
        token_hash: str,
    ) -> SessionUtilisateur | None:
        result = await db.execute(
            select(SessionUtilisateur).where(
                SessionUtilisateur.jeton_hash == token_hash
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def avatar_document_for_user(
        db: AsyncSession,
        *,
        user_id: UUID,
    ) -> Document | None:
        result = await db.execute(
            select(Document)
            .join(
                PreferenceUtilisateur,
                PreferenceUtilisateur.avatar_document_id
                == Document.id,
            )
            .where(
                PreferenceUtilisateur.utilisateur_id == user_id,
                func.upper(
                    func.coalesce(Document.statut, "ACTIF")
                ) == "ACTIF",
            )
        )
        return result.scalar_one_or_none()
