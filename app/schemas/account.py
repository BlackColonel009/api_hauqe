"""
Schémas API — Mon compte / Sécurité utilisateur.

Le frontend `profil.html` est découpé en quatre onglets :
- informations personnelles ;
- sécurité ;
- notifications ;
- sessions.

Les schémas n'exposent jamais :
- mot_de_passe_hash ;
- secret TOTP chiffré ;
- hash du code privé ;
- hash des jetons ;
- hash des codes de récupération.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================
# PROFIL
# ============================================================

class MyProfileUpdateRequest(BaseModel):
    prenoms: str | None = Field(default=None, max_length=255)
    nom: str | None = Field(default=None, max_length=255)
    telephone: str | None = Field(default=None, max_length=255)
    langue: Literal["fr", "en"] | None = None
    fuseau_horaire: str | None = Field(default=None, max_length=100)
    avatar_document_id: UUID | None = None


class MyProfileResponse(BaseModel):
    id: UUID
    email: str
    prenoms: str | None = None
    nom: str | None = None
    telephone: str | None = None
    fonction: str | None = None
    region_affectation_id: UUID | None = None
    region_affectation_nom: str | None = None
    statut: str | None = None
    mfa_active: bool
    derniere_connexion_at: datetime | None = None
    created_at: datetime
    langue: str
    fuseau_horaire: str
    avatar_document_id: UUID | None = None
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)


# ============================================================
# MOT DE PASSE
# ============================================================

class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=8, max_length=256)
    confirm_password: str = Field(min_length=8, max_length=256)


class PasswordForgotRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)


class PasswordResetRequest(BaseModel):
    token: str = Field(min_length=20, max_length=512)
    new_password: str = Field(min_length=8, max_length=256)
    confirm_password: str = Field(min_length=8, max_length=256)


class NeutralPasswordResetResponse(BaseModel):
    detail: str = (
        "Si un compte correspond à cette adresse, "
        "les instructions ont été envoyées."
    )


# ============================================================
# SESSIONS
# ============================================================

class MySessionResponse(BaseModel):
    id: UUID
    current: bool
    adresse_ip: str | None = None
    user_agent: str | None = None
    debut_at: datetime | None = None
    derniere_activite_at: datetime | None = None
    expiration_at: datetime | None = None
    revoquee_at: datetime | None = None
    locked: bool = False
    locked_at: datetime | None = None


class SessionRevokeResponse(BaseModel):
    session_id: UUID
    revoked: bool


class SessionsRevokeOthersResponse(BaseModel):
    revoked_count: int


# ============================================================
# MFA
# ============================================================

class MfaStatusResponse(BaseModel):
    active: bool
    type: str = "TOTP"
    verified_at: datetime | None = None
    recovery_codes_remaining: int = 0


class MfaEnableResponse(BaseModel):
    secret: str
    otpauth_uri: str
    detail: str = (
        "Scannez ou saisissez cette clé dans l'application MFA, "
        "puis confirmez avec un code à 6 chiffres."
    )


class MfaVerifyEnrollmentRequest(BaseModel):
    code: str = Field(min_length=6, max_length=20)


class MfaVerifyEnrollmentResponse(BaseModel):
    active: bool
    recovery_codes: list[str] = Field(default_factory=list)


class MfaDisableRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=256)
    code_or_recovery: str = Field(min_length=4, max_length=128)


class MfaLoginVerifyRequest(BaseModel):
    challenge_token: str = Field(min_length=20, max_length=512)
    code_or_recovery: str = Field(min_length=4, max_length=128)


class MfaLoginVerifyResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user_id: UUID


class MfaChallengeResponse(BaseModel):
    mfa_required: bool = True
    challenge_token: str
    expires_at: datetime


# ============================================================
# PRÉFÉRENCES DE NOTIFICATION
# ============================================================

class NotificationPreferencesUpdateRequest(BaseModel):
    alertes_critiques: bool | None = None
    affectations: bool | None = None
    corrections: bool | None = None
    rapports_planifies: bool | None = None
    resume_hebdomadaire: bool | None = None


class NotificationPreferencesResponse(BaseModel):
    alertes_critiques: bool
    affectations: bool
    corrections: bool
    rapports_planifies: bool
    resume_hebdomadaire: bool


# ============================================================
# VERROUILLAGE DE REPRISE
# ============================================================

class SecurityLockUpdateRequest(BaseModel):
    enabled: bool
    timeout_minutes: Literal[5, 10, 15, 30]
    current_password: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
    )
    new_code: str | None = Field(
        default=None,
        min_length=5,
        max_length=128,
    )
    confirm_code: str | None = Field(
        default=None,
        min_length=5,
        max_length=128,
    )


class SecurityLockStateResponse(BaseModel):
    enabled: bool
    timeout_minutes: int
    code_configured: bool
    current_session_locked: bool
    current_session_locked_at: datetime | None = None
    attempts_remaining: int


class LockSessionRequest(BaseModel):
    reason: Literal["INACTIVITY", "MANUAL_TEST", "USER_REQUEST"] = "USER_REQUEST"


class UnlockSessionRequest(BaseModel):
    code: str = Field(min_length=1, max_length=128)


class UnlockSessionResponse(BaseModel):
    unlocked: bool
    attempts_remaining: int
    session_revoked: bool = False


# ============================================================
# ADMIN / CYCLE D'INACTIVITÉ
# ============================================================

class AccountInactivityScanResponse(BaseModel):
    scanned_at: datetime
    users_scanned: int
    warnings_queued: int
    users_deactivated: int
    sessions_revoked: int
    expired_tokens_deleted: int


# ============================================================
# AIDE D'INTÉGRATION AUTH
# ============================================================

class PostPasswordAuthenticationResult(BaseModel):
    """
    Contrat du hook appelé après validation email/mot de passe.

    Si `mfa_required` est vrai, la route `/auth/login` NE DOIT PAS créer
    de session définitive. Elle renvoie le challenge MFA.
    """
    mfa_required: bool
    challenge_token: str | None = None
    challenge_expires_at: datetime | None = None
