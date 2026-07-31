"""
Service métier — changement et réinitialisation du mot de passe.

POLITIQUE
---------
La politique institutionnelle peut être publiée via la règle métier :

    ACCOUNT_PASSWORD_POLICY

Paramètres supportés :
- min_length
- require_upper
- require_lower
- require_digit
- require_special

En absence de règle publiée, le backend applique seulement un plancher
technique de 8 caractères afin de ne pas inventer une politique HAUQE
plus contraignante que les documents disponibles.

RÉINITIALISATION
----------------
- réponse toujours neutre sur `/forgot` ;
- token brut transmis uniquement par email ;
- SHA-256(token) stocké ;
- expiration : 30 minutes, conformément au frontend ;
- usage unique ;
- toutes les sessions sont révoquées après reset.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit_event
from app.config.settings import settings
from app.models.jeton_securite_utilisateur import JetonSecuriteUtilisateur
from app.repositories.account_repository import AccountRepository
from app.rules.business_rule_resolver import resolve_business_rule
from app.schemas.account import (
    ChangePasswordRequest,
    NeutralPasswordResetResponse,
    PasswordForgotRequest,
    PasswordResetRequest,
)
from app.services.account_service import AccountService
from app.services.auth_service import AuthContext
from app.utils.account_security import (
    generate_opaque_token,
    token_hash,
)


_password_hasher = PasswordHasher()


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


class PasswordService:

    @staticmethod
    async def password_policy(
        db: AsyncSession,
    ) -> dict:
        rule = await resolve_business_rule(
            db,
            "ACCOUNT_PASSWORD_POLICY",
        )
        if rule is None or not isinstance(rule.parametres, dict):
            return {
                "min_length": 8,
                "require_upper": False,
                "require_lower": False,
                "require_digit": False,
                "require_special": False,
                "_source": "TECHNICAL_FLOOR",
            }

        params = rule.parametres
        return {
            "min_length": max(8, int(params.get("min_length", 8))),
            "require_upper": bool(params.get("require_upper", False)),
            "require_lower": bool(params.get("require_lower", False)),
            "require_digit": bool(params.get("require_digit", False)),
            "require_special": bool(params.get("require_special", False)),
            "_source": f"RULE:{rule.id}",
        }

    @staticmethod
    async def validate_new_password(
        db: AsyncSession,
        *,
        password: str,
        confirmation: str,
    ) -> None:
        if password != confirmation:
            raise HTTPException(
                422,
                "Les deux nouveaux mots de passe ne correspondent pas.",
            )

        policy = await PasswordService.password_policy(db)

        if len(password) < policy["min_length"]:
            raise HTTPException(
                422,
                (
                    f"Le mot de passe doit contenir au moins "
                    f"{policy['min_length']} caractères."
                ),
            )
        if policy["require_upper"] and not re.search(r"[A-Z]", password):
            raise HTTPException(422, "Une majuscule est requise.")
        if policy["require_lower"] and not re.search(r"[a-z]", password):
            raise HTTPException(422, "Une minuscule est requise.")
        if policy["require_digit"] and not re.search(r"\d", password):
            raise HTTPException(422, "Un chiffre est requis.")
        if policy["require_special"] and not re.search(
            r"[^A-Za-z0-9]",
            password,
        ):
            raise HTTPException(
                422,
                "Un caractère spécial est requis.",
            )

    @staticmethod
    async def queue_security_notice(
        db: AsyncSession,
        *,
        user_id,
        email: str,
        subject: str,
        body: str,
    ) -> None:
        await AccountRepository.create_notification(
            db,
            user_id=user_id,
            channel="IN_APP",
            subject=subject,
            body=body,
            immediate=True,
        )
        await AccountRepository.create_notification(
            db,
            user_id=user_id,
            channel="EMAIL",
            subject=subject,
            body=body,
            external_address=None,
            immediate=False,
        )

    @staticmethod
    async def change_password(
        db: AsyncSession,
        *,
        payload: ChangePasswordRequest,
        actor: AuthContext,
        request: Request,
    ) -> dict:
        user = await AccountRepository.get_user(db, actor.user.id)
        if user is None:
            raise HTTPException(404, "Utilisateur introuvable.")

        try:
            _password_hasher.verify(
                user.mot_de_passe_hash or "",
                payload.current_password,
            )
        except VerifyMismatchError:
            await write_audit_event(
                db,
                action="ACCOUNT_PASSWORD_CHANGE_FAILED",
                categorie="SECURITE",
                resultat="ECHEC",
                utilisateur_id=user.id,
                ressource_type="utilisateur",
                ressource_id=user.id,
                adresse_ip=client_ip(request),
                contexte={"reason": "CURRENT_PASSWORD_INVALID"},
            )
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Mot de passe actuel incorrect.",
            )

        await PasswordService.validate_new_password(
            db,
            password=payload.new_password,
            confirmation=payload.confirm_password,
        )

        same_as_current = False
        try:
            same_as_current = _password_hasher.verify(
                user.mot_de_passe_hash or "",
                payload.new_password,
            )
        except VerifyMismatchError:
            same_as_current = False

        if same_as_current:
            raise HTTPException(
                422,
                "Le nouveau mot de passe doit être différent de l'ancien.",
            )

        user.mot_de_passe_hash = _password_hasher.hash(
            payload.new_password
        )

        security = await AccountRepository.get_or_create_security(
            db,
            user.id,
        )
        security.derniere_modification_mot_de_passe_at = datetime.now(
            timezone.utc
        )

        # Le compte conserve la session courante mais révoque les autres.
        current = await AccountService.resolve_current_session(
            db,
            request=request,
            actor=actor,
        )
        now = datetime.now(timezone.utc)
        revoked = 0
        for session in await AccountRepository.active_user_sessions(
            db,
            user.id,
        ):
            if session.id == current.id:
                continue
            session.revoquee_at = now
            revoked += 1

        await PasswordService.queue_security_notice(
            db,
            user_id=user.id,
            email=user.email,
            subject="Votre mot de passe HAUQE Certif a été modifié",
            body=(
                "Votre mot de passe a été modifié depuis votre espace "
                "Mon compte. Si vous n'êtes pas à l'origine de cette action, "
                "contactez immédiatement l'administrateur HAUQE."
            ),
        )

        await write_audit_event(
            db,
            action="ACCOUNT_PASSWORD_CHANGE",
            categorie="SECURITE",
            resultat="SUCCES",
            utilisateur_id=user.id,
            ressource_type="utilisateur",
            ressource_id=user.id,
            adresse_ip=client_ip(request),
            valeurs_apres={"other_sessions_revoked": revoked},
        )

        await db.commit()
        return {
            "detail": "Mot de passe modifié.",
            "other_sessions_revoked": revoked,
        }

    @staticmethod
    async def forgot_password(
        db: AsyncSession,
        *,
        payload: PasswordForgotRequest,
        request: Request,
    ) -> NeutralPasswordResetResponse:
        neutral = NeutralPasswordResetResponse()
        user = await AccountRepository.get_user_by_email(
            db,
            payload.email,
        )

        # Réponse identique si le compte n'existe pas / n'est pas actif.
        if user is None or (user.statut or "").upper() != "ACTIF":
            await write_audit_event(
                db,
                action="AUTH_PASSWORD_RESET_REQUEST",
                categorie="SECURITE",
                resultat="NEUTRE",
                utilisateur_id=None,
                ressource_type="utilisateur",
                adresse_ip=client_ip(request),
                contexte={"account_matched": False},
            )
            await db.commit()
            return neutral

        now = datetime.now(timezone.utc)

        # Invalider les précédents tokens reset encore actifs.
        for previous in await AccountRepository.active_security_tokens(
            db,
            user_id=user.id,
            token_type="PASSWORD_RESET",
        ):
            previous.utilise_at = now

        raw_token = generate_opaque_token(40)
        item = JetonSecuriteUtilisateur(
            utilisateur_id=user.id,
            type_jeton="PASSWORD_RESET",
            jeton_hash=token_hash(raw_token),
            expiration_at=now + timedelta(minutes=30),
            utilise_at=None,
            adresse_ip=client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            contexte={"purpose": "SELF_SERVICE_PASSWORD_RESET"},
        )
        db.add(item)
        await db.flush()

        template = settings.password_reset_url_template
        if template:
            link = str(template).replace("{token}", raw_token)
            await AccountRepository.create_notification(
                db,
                user_id=user.id,
                channel="EMAIL",
                subject="Réinitialisation de votre mot de passe HAUQE Certif",
                body=(
                    "Un changement de mot de passe a été demandé. "
                    "Le lien suivant est valable 30 minutes et une seule fois : "
                    f"{link}"
                ),
                immediate=False,
            )

        await write_audit_event(
            db,
            action="AUTH_PASSWORD_RESET_REQUEST",
            categorie="SECURITE",
            resultat="SUCCES",
            utilisateur_id=user.id,
            ressource_type="jeton_securite_utilisateur",
            ressource_id=item.id,
            adresse_ip=client_ip(request),
            contexte={
                "account_matched": True,
                "email_queued": bool(template),
            },
        )

        await db.commit()
        return neutral

    @staticmethod
    async def reset_password(
        db: AsyncSession,
        *,
        payload: PasswordResetRequest,
        request: Request,
    ) -> dict:
        await PasswordService.validate_new_password(
            db,
            password=payload.new_password,
            confirmation=payload.confirm_password,
        )

        item = await AccountRepository.get_security_token_by_hash(
            db,
            token_hash(payload.token),
        )
        now = datetime.now(timezone.utc)

        if (
            item is None
            or item.type_jeton != "PASSWORD_RESET"
            or item.utilise_at is not None
            or item.expiration_at <= now
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lien de réinitialisation invalide ou expiré.",
            )

        user = await AccountRepository.get_user(
            db,
            item.utilisateur_id,
        )
        if user is None or (user.statut or "").upper() != "ACTIF":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lien de réinitialisation invalide ou expiré.",
            )

        user.mot_de_passe_hash = _password_hasher.hash(
            payload.new_password
        )
        item.utilise_at = now

        security = await AccountRepository.get_or_create_security(
            db,
            user.id,
        )
        security.derniere_modification_mot_de_passe_at = now

        revoked = 0
        for session in await AccountRepository.active_user_sessions(
            db,
            user.id,
        ):
            session.revoquee_at = now
            revoked += 1

        await PasswordService.queue_security_notice(
            db,
            user_id=user.id,
            email=user.email,
            subject="Votre mot de passe HAUQE Certif a été réinitialisé",
            body=(
                "Votre mot de passe a été réinitialisé et toutes vos "
                "sessions précédentes ont été révoquées."
            ),
        )

        await write_audit_event(
            db,
            action="AUTH_PASSWORD_RESET_COMPLETE",
            categorie="SECURITE",
            resultat="SUCCES",
            utilisateur_id=user.id,
            ressource_type="utilisateur",
            ressource_id=user.id,
            adresse_ip=client_ip(request),
            valeurs_apres={"sessions_revoked": revoked},
        )

        await db.commit()
        return {
            "detail": "Mot de passe réinitialisé. Reconnectez-vous.",
            "sessions_revoked": revoked,
        }
