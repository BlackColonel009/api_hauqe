"""
Service métier — présence des utilisateurs.

Définitions :
- ONLINE : activité d'une session encore vivante dans les 2 dernières minutes ;
- RECENT : dernière activité dans la fenêtre demandée (15 min par défaut).

Le polling GET ne met jamais à jour `derniere_activite_at`.
Seul le heartbeat provenant d'une activité réelle du navigateur le fait.
Ainsi le menu de présence ne maintient pas artificiellement les sessions actives.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.presence_repository import PresenceRepository
from app.schemas.presence import (
    PresenceListResponse,
    PresenceRoleResponse,
    PresenceUserResponse,
)
from app.services.auth_service import AuthContext
from app.utils.account_security import token_hash


ONLINE_WINDOW = timedelta(minutes=2)


def _bearer_token(request: Request) -> str:
    authorization = request.headers.get(
        "Authorization",
        "",
    ).strip()

    if not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session Bearer absente.",
        )

    raw = authorization[7:].strip()

    if not raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session Bearer absente.",
        )

    return raw


def _is_live_session(session, now: datetime) -> bool:
    if session.revoquee_at is not None:
        return False

    if (
        session.expiration_at is not None
        and session.expiration_at <= now
    ):
        return False

    return True


class PresenceService:

    @staticmethod
    async def list_users(
        db: AsyncSession,
        *,
        actor: AuthContext,
        minutes: int,
        limit: int,
    ) -> PresenceListResponse:
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=minutes)
        online_cutoff = now - ONLINE_WINDOW

        rows = await PresenceRepository.recent_session_rows(
            db,
            cutoff=cutoff,
        )

        by_user = {}

        for session, user, activity_at in rows:
            item = by_user.setdefault(
                user.id,
                {
                    "user": user,
                    "last_activity_at": activity_at,
                    "latest_live_activity_at": None,
                },
            )

            if activity_at > item["last_activity_at"]:
                item["last_activity_at"] = activity_at

            if _is_live_session(session, now):
                current_live = item[
                    "latest_live_activity_at"
                ]

                if (
                    current_live is None
                    or activity_at > current_live
                ):
                    item[
                        "latest_live_activity_at"
                    ] = activity_at

        user_ids = list(by_user.keys())

        roles_map = await PresenceRepository.roles_for_users(
            db,
            user_ids,
        )

        avatar_user_ids = await PresenceRepository.avatar_users(
            db,
            user_ids,
        )

        users: list[PresenceUserResponse] = []

        for user_id, data in by_user.items():
            user = data["user"]
            last_activity_at = data["last_activity_at"]
            live_activity_at = data["latest_live_activity_at"]

            presence = (
                "ONLINE"
                if (
                    live_activity_at is not None
                    and live_activity_at >= online_cutoff
                )
                else "RECENT"
            )

            roles = [
                PresenceRoleResponse(
                    code=code,
                    libelle=libelle,
                )
                for code, libelle
                in roles_map.get(user_id, [])
            ]

            full_name = " ".join(
                part.strip()
                for part in [
                    getattr(user, "prenoms", None),
                    getattr(user, "nom", None),
                ]
                if part and part.strip()
            )

            if not full_name:
                full_name = (
                    getattr(user, "email", None)
                    or "Utilisateur"
                )

            has_avatar = user_id in avatar_user_ids

            users.append(
                PresenceUserResponse(
                    user_id=user_id,
                    nom_complet=full_name,
                    fonction=getattr(
                        user,
                        "fonction",
                        None,
                    ),
                    roles=roles,
                    presence=presence,
                    last_activity_at=last_activity_at,
                    has_avatar=has_avatar,
                    avatar_url=(
                        f"/api/v1/presence/users/{user_id}/avatar"
                        if has_avatar
                        else None
                    ),
                    is_current_user=(
                        user_id == actor.user.id
                    ),
                )
            )

        users.sort(
            key=lambda item: (
                0 if item.presence == "ONLINE" else 1,
                -item.last_activity_at.timestamp(),
            )
        )

        online_count = sum(
            1
            for item in users
            if item.presence == "ONLINE"
        )

        recent_count = len(users) - online_count
        total_count = len(users)

        return PresenceListResponse(
            window_minutes=minutes,
            online_count=online_count,
            recent_count=recent_count,
            total_count=total_count,
            users=users[:limit],
        )

    @staticmethod
    async def heartbeat(
        db: AsyncSession,
        *,
        request: Request,
        actor: AuthContext,
    ) -> None:
        now = datetime.now(timezone.utc)
        raw_token = _bearer_token(request)

        session = (
            await PresenceRepository.get_session_by_token_hash(
                db,
                token_hash=token_hash(raw_token),
            )
        )

        if (
            session is None
            or session.utilisateur_id != actor.user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session courante introuvable.",
            )

        if not _is_live_session(session, now):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expirée ou révoquée.",
            )

        session.derniere_activite_at = now
        await db.commit()

    @staticmethod
    async def avatar_path(
        db: AsyncSession,
        *,
        user_id: UUID,
    ):
        document = (
            await PresenceRepository.avatar_document_for_user(
                db,
                user_id=user_id,
            )
        )

        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Avatar introuvable.",
            )

        path = Path(document.chemin_stockage)

        if not path.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fichier avatar introuvable.",
            )

        return document, path
