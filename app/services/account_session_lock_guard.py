"""
Garde d'authentification pour le verrouillage de reprise.

À appeler depuis `get_current_auth()` APRÈS résolution de la session et AVANT
l'accès aux routes métier.

Routes exemptées quand la session est verrouillée :
- POST /api/v1/me/security-lock/verify
- POST /api/v1/auth/logout

Sans cette intégration, le frontend masquerait bien l'écran mais l'API
resterait techniquement accessible avec le Bearer token : ce serait
insuffisant.
"""

from __future__ import annotations

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.account_repository import AccountRepository


LOCK_EXEMPT_PATHS = {
    "/api/v1/me/security-lock/verify",
    "/api/v1/auth/logout",
}


async def ensure_session_not_screen_locked(
    db: AsyncSession,
    *,
    session,
    request: Request,
) -> None:
    if request.url.path in LOCK_EXEMPT_PATHS:
        return

    lock = await AccountRepository.get_session_lock(
        db,
        session.id,
    )
    if lock is None or lock.verrouillee_at is None:
        return

    currently_locked = (
        lock.deverrouillee_at is None
        or lock.deverrouillee_at < lock.verrouillee_at
    )
    if currently_locked:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail={
                "code": "SESSION_SCREEN_LOCKED",
                "message": "La session doit être déverrouillée.",
            },
        )
