"""
Service métier — MFA TOTP.

ENRÔLEMENT
----------
1. `/me/mfa/enable` génère un secret temporaire chiffré.
2. Le frontend affiche la clé/QR.
3. `/me/mfa/verify` vérifie un premier TOTP.
4. Le secret devient actif, `utilisateurs.mfa_active = true`.
5. Huit codes de récupération sont retournés UNE SEULE FOIS.

LOGIN
-----
Le service expose `post_password_authentication()` pour être appelé depuis
l'actuel `POST /auth/login` juste après vérification email/mot de passe et
AVANT création de la session.

Si MFA est actif :
- aucune session définitive n'est créée ;
- un challenge opaque de 5 minutes est généré ;
- `/auth/mfa/verify` termine l'authentification et crée la session.

Cette intégration est obligatoire : sinon l'ancien `/auth/login` resterait un
contournement du MFA.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit_event
from app.config.settings import settings
from app.models.jeton_securite_utilisateur import JetonSecuriteUtilisateur
from app.models.session_utilisateur import SessionUtilisateur
from app.repositories.account_repository import AccountRepository
from app.schemas.account import (
    MfaChallengeResponse,
    MfaDisableRequest,
    MfaEnableResponse,
    MfaLoginVerifyRequest,
    MfaLoginVerifyResponse,
    MfaStatusResponse,
    MfaVerifyEnrollmentRequest,
    MfaVerifyEnrollmentResponse,
)
from app.services.auth_service import AuthContext
from app.utils.account_security import (
    decrypt_mfa_secret,
    encrypt_mfa_secret,
    generate_opaque_token,
    generate_recovery_codes,
    generate_totp_secret,
    hash_secret,
    provisioning_uri,
    token_hash,
    verify_secret,
    verify_totp_code,
)


_password_hasher = PasswordHasher()


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


class MfaService:

    @staticmethod
    async def status(
        db: AsyncSession,
        actor: AuthContext,
    ) -> MfaStatusResponse:
        security = await AccountRepository.get_or_create_security(
            db,
            actor.user.id,
        )
        return MfaStatusResponse(
            active=bool(actor.user.mfa_active),
            type=security.mfa_type or "TOTP",
            verified_at=security.mfa_verifie_at,
            recovery_codes_remaining=len(
                security.mfa_recovery_codes_hash or []
            ),
        )

    @staticmethod
    async def enable(
        db: AsyncSession,
        *,
        actor: AuthContext,
        request: Request,
    ) -> MfaEnableResponse:
        user = await AccountRepository.get_user(db, actor.user.id)
        if user is None:
            raise HTTPException(404, "Utilisateur introuvable.")
        if user.mfa_active:
            raise HTTPException(409, "Le MFA est déjà activé.")

        secret = generate_totp_secret()
        try:
            encrypted = encrypt_mfa_secret(secret)
        except RuntimeError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc

        security = await AccountRepository.get_or_create_security(
            db,
            user.id,
        )
        security.mfa_type = "TOTP"
        security.mfa_secret_pending_chiffre = encrypted

        await write_audit_event(
            db,
            action="ACCOUNT_MFA_ENROLLMENT_START",
            categorie="SECURITE",
            resultat="SUCCES",
            utilisateur_id=user.id,
            ressource_type="securite_compte_utilisateur",
            ressource_id=security.id,
            adresse_ip=client_ip(request),
        )

        await db.commit()

        return MfaEnableResponse(
            secret=secret,
            otpauth_uri=provisioning_uri(
                secret=secret,
                email=user.email,
            ),
        )

    @staticmethod
    async def verify_enrollment(
        db: AsyncSession,
        *,
        payload: MfaVerifyEnrollmentRequest,
        actor: AuthContext,
        request: Request,
    ) -> MfaVerifyEnrollmentResponse:
        user = await AccountRepository.get_user(db, actor.user.id)
        if user is None:
            raise HTTPException(404, "Utilisateur introuvable.")

        security = await AccountRepository.get_or_create_security(
            db,
            user.id,
        )
        if not security.mfa_secret_pending_chiffre:
            raise HTTPException(
                409,
                "Aucun enrôlement MFA en attente.",
            )

        try:
            secret = decrypt_mfa_secret(
                security.mfa_secret_pending_chiffre
            )
        except RuntimeError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc

        if not verify_totp_code(secret, payload.code):
            await write_audit_event(
                db,
                action="ACCOUNT_MFA_ENROLLMENT_VERIFY_FAILED",
                categorie="SECURITE",
                resultat="ECHEC",
                utilisateur_id=user.id,
                ressource_type="securite_compte_utilisateur",
                ressource_id=security.id,
                adresse_ip=client_ip(request),
            )
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Code MFA incorrect.",
            )

        recovery_codes = generate_recovery_codes(8)

        security.mfa_secret_chiffre = (
            security.mfa_secret_pending_chiffre
        )
        security.mfa_secret_pending_chiffre = None
        security.mfa_recovery_codes_hash = [
            hash_secret(code)
            for code in recovery_codes
        ]
        security.mfa_verifie_at = datetime.now(timezone.utc)
        user.mfa_active = True

        await write_audit_event(
            db,
            action="ACCOUNT_MFA_ENABLE",
            categorie="SECURITE",
            resultat="SUCCES",
            utilisateur_id=user.id,
            ressource_type="utilisateur",
            ressource_id=user.id,
            adresse_ip=client_ip(request),
        )

        await db.commit()

        return MfaVerifyEnrollmentResponse(
            active=True,
            recovery_codes=recovery_codes,
        )

    @staticmethod
    async def verify_mfa_or_recovery(
        db: AsyncSession,
        *,
        user,
        code_or_recovery: str,
        consume_recovery: bool,
    ) -> tuple[bool, bool]:
        """
        Retourne `(valid, recovery_code_used)`.
        """
        security = await AccountRepository.get_or_create_security(
            db,
            user.id,
        )
        if not security.mfa_secret_chiffre:
            return False, False

        try:
            secret = decrypt_mfa_secret(
                security.mfa_secret_chiffre
            )
        except RuntimeError:
            return False, False

        if verify_totp_code(secret, code_or_recovery):
            return True, False

        hashes = list(security.mfa_recovery_codes_hash or [])
        for index, stored_hash in enumerate(hashes):
            if verify_secret(stored_hash, code_or_recovery.strip()):
                if consume_recovery:
                    hashes.pop(index)
                    security.mfa_recovery_codes_hash = hashes
                return True, True

        return False, False

    @staticmethod
    async def disable(
        db: AsyncSession,
        *,
        payload: MfaDisableRequest,
        actor: AuthContext,
        request: Request,
    ) -> MfaStatusResponse:
        user = await AccountRepository.get_user(db, actor.user.id)
        if user is None:
            raise HTTPException(404, "Utilisateur introuvable.")
        if not user.mfa_active:
            return await MfaService.status(db, actor)

        try:
            _password_hasher.verify(
                user.mot_de_passe_hash or "",
                payload.current_password,
            )
        except VerifyMismatchError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Mot de passe actuel incorrect.",
            )

        valid, recovery_used = await MfaService.verify_mfa_or_recovery(
            db,
            user=user,
            code_or_recovery=payload.code_or_recovery,
            consume_recovery=True,
        )
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Code MFA ou code de récupération incorrect.",
            )

        security = await AccountRepository.get_or_create_security(
            db,
            user.id,
        )
        security.mfa_secret_chiffre = None
        security.mfa_secret_pending_chiffre = None
        security.mfa_recovery_codes_hash = None
        security.mfa_verifie_at = None
        user.mfa_active = False

        await write_audit_event(
            db,
            action="ACCOUNT_MFA_DISABLE",
            categorie="SECURITE",
            resultat="SUCCES",
            utilisateur_id=user.id,
            ressource_type="utilisateur",
            ressource_id=user.id,
            adresse_ip=client_ip(request),
            contexte={"recovery_code_used": recovery_used},
        )

        await db.commit()
        return MfaStatusResponse(
            active=False,
            type="TOTP",
            verified_at=None,
            recovery_codes_remaining=0,
        )

    # ========================================================
    # HOOK LOGIN : mot de passe déjà validé
    # ========================================================

    @staticmethod
    async def post_password_authentication(
        db: AsyncSession,
        *,
        user,
        request: Request,
    ) -> MfaChallengeResponse | None:
        """
        À appeler depuis `AuthService.login()` AVANT création de session.

        - MFA inactif -> None : AuthService poursuit son flux normal.
        - MFA actif   -> challenge : AuthService retourne ce challenge et
          n'émet PAS encore de Bearer token.
        """
        if not bool(user.mfa_active):
            return None

        security = await AccountRepository.get_or_create_security(
            db,
            user.id,
        )
        if not security.mfa_secret_chiffre:
            # Drapeau incohérent : ne jamais contourner silencieusement MFA.
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Configuration MFA du compte incohérente.",
            )

        now = datetime.now(timezone.utc)

        for previous in await AccountRepository.active_security_tokens(
            db,
            user_id=user.id,
            token_type="MFA_LOGIN",
        ):
            previous.utilise_at = now

        raw_token = generate_opaque_token(40)
        expires = now + timedelta(minutes=5)

        challenge = JetonSecuriteUtilisateur(
            utilisateur_id=user.id,
            type_jeton="MFA_LOGIN",
            jeton_hash=token_hash(raw_token),
            expiration_at=expires,
            utilise_at=None,
            adresse_ip=client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            contexte={"password_verified": True},
        )
        db.add(challenge)
        await db.flush()

        await write_audit_event(
            db,
            action="AUTH_MFA_CHALLENGE_CREATE",
            categorie="SECURITE",
            resultat="SUCCES",
            utilisateur_id=user.id,
            ressource_type="jeton_securite_utilisateur",
            ressource_id=challenge.id,
            adresse_ip=client_ip(request),
        )
        await db.commit()

        return MfaChallengeResponse(
            challenge_token=raw_token,
            expires_at=expires,
        )

    @staticmethod
    async def verify_login_challenge(
        db: AsyncSession,
        *,
        payload: MfaLoginVerifyRequest,
        request: Request,
    ) -> MfaLoginVerifyResponse:
        challenge = await AccountRepository.get_security_token_by_hash(
            db,
            token_hash(payload.challenge_token),
        )
        now = datetime.now(timezone.utc)

        if (
            challenge is None
            or challenge.type_jeton != "MFA_LOGIN"
            or challenge.utilise_at is not None
            or challenge.expiration_at <= now
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Challenge MFA invalide ou expiré.",
            )

        user = await AccountRepository.get_user(
            db,
            challenge.utilisateur_id,
        )
        if (
            user is None
            or (user.statut or "").upper() != "ACTIF"
            or not user.mfa_active
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Challenge MFA invalide ou expiré.",
            )

        valid, recovery_used = await MfaService.verify_mfa_or_recovery(
            db,
            user=user,
            code_or_recovery=payload.code_or_recovery,
            consume_recovery=True,
        )
        if not valid:
            await write_audit_event(
                db,
                action="AUTH_MFA_VERIFY",
                categorie="SECURITE",
                resultat="ECHEC",
                utilisateur_id=user.id,
                ressource_type="utilisateur",
                ressource_id=user.id,
                adresse_ip=client_ip(request),
            )
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Code MFA incorrect.",
            )

        challenge.utilise_at = now

        raw_access_token = generate_opaque_token(48)
        expiration = now + timedelta(
            minutes=int(
                getattr(settings, "AUTH_SESSION_MINUTES", 480)
            )
        )

        session = SessionUtilisateur(
            utilisateur_id=user.id,
            jeton_hash=token_hash(raw_access_token),
            adresse_ip=client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            debut_at=now,
            derniere_activite_at=now,
            expiration_at=expiration,
            revoquee_at=None,
        )
        db.add(session)

        user.derniere_connexion_at = now
        security = await AccountRepository.get_or_create_security(
            db,
            user.id,
        )
        security.inactivite_warning_sent_at = None

        await write_audit_event(
            db,
            action="AUTH_MFA_VERIFY",
            categorie="SECURITE",
            resultat="SUCCES",
            utilisateur_id=user.id,
            ressource_type="session_utilisateur",
            adresse_ip=client_ip(request),
            contexte={"recovery_code_used": recovery_used},
        )

        await db.commit()

        return MfaLoginVerifyResponse(
            access_token=raw_access_token,
            expires_at=expiration,
            user_id=user.id,
        )
