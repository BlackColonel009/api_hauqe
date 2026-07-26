"""
Routes API — Mon compte / Sécurité utilisateur.

PAGES FRONTEND
--------------
- `profil.html`
- `connexion.html`
- `mot-de-passe-oublie.html`

Toutes les routes `/me/*` exigent seulement une session authentifiée :
un utilisateur n'a pas besoin d'une permission RBAC supplémentaire pour
consulter/modifier SON propre compte.

Les routes sensibles continuent néanmoins à vérifier :
- propriété de la session ;
- mot de passe actuel ;
- MFA ;
- état du compte ;
- audit.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.permissions.auth import get_current_auth
from app.schemas.account import (
    ChangePasswordRequest,
    MfaDisableRequest,
    MfaEnableResponse,
    MfaLoginVerifyRequest,
    MfaLoginVerifyResponse,
    MfaStatusResponse,
    MfaVerifyEnrollmentRequest,
    MfaVerifyEnrollmentResponse,
    MyProfileResponse,
    MyProfileUpdateRequest,
    MySessionResponse,
    NeutralPasswordResetResponse,
    NotificationPreferencesResponse,
    NotificationPreferencesUpdateRequest,
    PasswordForgotRequest,
    PasswordResetRequest,
    SecurityLockStateResponse,
    SecurityLockUpdateRequest,
    SessionRevokeResponse,
    SessionsRevokeOthersResponse,
    LockSessionRequest,
    UnlockSessionRequest,
    UnlockSessionResponse,
)
from app.services.account_service import AccountService
from app.services.auth_service import AuthContext
from app.services.mfa_service import MfaService
from app.services.password_service import PasswordService


account_router = APIRouter(
    prefix="/me",
    tags=["Mon compte"],
)

account_auth_router = APIRouter(
    prefix="/auth",
    tags=["Authentification - compte"],
)


# ============================================================
# PROFIL
# ============================================================

@account_router.get(
    "/profile",
    response_model=MyProfileResponse,
)
async def my_profile(
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(get_current_auth),
):
    return await AccountService.profile(db, actor)


@account_router.patch(
    "/profile",
    response_model=MyProfileResponse,
)
async def update_my_profile(
    payload: MyProfileUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(get_current_auth),
):
    return await AccountService.update_profile(
        db,
        payload=payload,
        actor=actor,
        request=request,
    )


# ============================================================
# MOT DE PASSE
# ============================================================

@account_router.post("/password/change")
async def change_my_password(
    payload: ChangePasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(get_current_auth),
):
    return await PasswordService.change_password(
        db,
        payload=payload,
        actor=actor,
        request=request,
    )


@account_auth_router.post(
    "/password/forgot",
    response_model=NeutralPasswordResetResponse,
)
async def forgot_password(
    payload: PasswordForgotRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    return await PasswordService.forgot_password(
        db,
        payload=payload,
        request=request,
    )


@account_auth_router.post("/password/reset")
async def reset_password(
    payload: PasswordResetRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    return await PasswordService.reset_password(
        db,
        payload=payload,
        request=request,
    )


# ============================================================
# SESSIONS
# ============================================================

@account_router.get(
    "/sessions",
    response_model=list[MySessionResponse],
)
async def my_sessions(
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(get_current_auth),
):
    return await AccountService.list_sessions(
        db,
        request=request,
        actor=actor,
    )


@account_router.post(
    "/sessions/revoke-others",
    response_model=SessionsRevokeOthersResponse,
)
async def revoke_my_other_sessions(
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(get_current_auth),
):
    return await AccountService.revoke_other_sessions(
        db,
        actor=actor,
        request=request,
    )


@account_router.post(
    "/sessions/{session_id}/revoke",
    response_model=SessionRevokeResponse,
)
async def revoke_my_session(
    session_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(get_current_auth),
):
    return await AccountService.revoke_session(
        db,
        session_id=session_id,
        actor=actor,
        request=request,
    )


# ============================================================
# MFA
# ============================================================

@account_router.get(
    "/mfa",
    response_model=MfaStatusResponse,
)
async def my_mfa_status(
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(get_current_auth),
):
    return await MfaService.status(db, actor)


@account_router.post(
    "/mfa/enable",
    response_model=MfaEnableResponse,
)
async def enable_my_mfa(
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(get_current_auth),
):
    return await MfaService.enable(
        db,
        actor=actor,
        request=request,
    )


@account_router.post(
    "/mfa/verify",
    response_model=MfaVerifyEnrollmentResponse,
)
async def verify_my_mfa_enrollment(
    payload: MfaVerifyEnrollmentRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(get_current_auth),
):
    return await MfaService.verify_enrollment(
        db,
        payload=payload,
        actor=actor,
        request=request,
    )


@account_router.post(
    "/mfa/disable",
    response_model=MfaStatusResponse,
)
async def disable_my_mfa(
    payload: MfaDisableRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(get_current_auth),
):
    return await MfaService.disable(
        db,
        payload=payload,
        actor=actor,
        request=request,
    )


@account_auth_router.post(
    "/mfa/verify",
    response_model=MfaLoginVerifyResponse,
)
async def verify_login_mfa(
    payload: MfaLoginVerifyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    return await MfaService.verify_login_challenge(
        db,
        payload=payload,
        request=request,
    )


# ============================================================
# PRÉFÉRENCES DE NOTIFICATION
# ============================================================

@account_router.get(
    "/notification-preferences",
    response_model=NotificationPreferencesResponse,
)
async def my_notification_preferences(
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(get_current_auth),
):
    return await AccountService.notification_preferences(
        db,
        actor,
    )


@account_router.patch(
    "/notification-preferences",
    response_model=NotificationPreferencesResponse,
)
async def update_my_notification_preferences(
    payload: NotificationPreferencesUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(get_current_auth),
):
    return await AccountService.update_notification_preferences(
        db,
        payload=payload,
        actor=actor,
        request=request,
    )


# ============================================================
# VERROUILLAGE AUTOMATIQUE / CODE PRIVÉ
# ============================================================

@account_router.get(
    "/security-lock",
    response_model=SecurityLockStateResponse,
)
async def my_security_lock(
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(get_current_auth),
):
    return await AccountService.security_lock_state(
        db,
        actor=actor,
        request=request,
    )


@account_router.patch(
    "/security-lock",
    response_model=SecurityLockStateResponse,
)
async def update_my_security_lock(
    payload: SecurityLockUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(get_current_auth),
):
    return await AccountService.update_security_lock(
        db,
        payload=payload,
        actor=actor,
        request=request,
    )


@account_router.post(
    "/security-lock/lock",
    response_model=SecurityLockStateResponse,
)
async def lock_my_current_session(
    payload: LockSessionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(get_current_auth),
):
    return await AccountService.lock_current_session(
        db,
        reason=payload.reason,
        actor=actor,
        request=request,
    )


@account_router.post(
    "/security-lock/verify",
    response_model=UnlockSessionResponse,
)
async def unlock_my_current_session(
    payload: UnlockSessionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(get_current_auth),
):
    return await AccountService.unlock_current_session(
        db,
        payload=payload,
        actor=actor,
        request=request,
    )
