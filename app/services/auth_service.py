from __future__ import annotations

from app.config.settings import settings
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit_event
from app.models.session_utilisateur import SessionUtilisateur
from app.models.utilisateur import Utilisateur
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth import (
    CurrentUserResponse,
    LoginResponse,
)
from app.utils.security import (
    generate_access_token,
    hash_access_token,
    verify_password,
)

from app.services.login_guard_service import (
    LoginGuardService,
)

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ============================================================
# DUREE ABSOLUE D'UNE SESSION
# ============================================================

def session_duration_minutes() -> int:
    """
    Durée maximale absolue d'une session authentifiée.

    La valeur est centralisée dans Settings et provient
    normalement de AUTH_SESSION_MINUTES dans .env.
    """

    return max(
        settings.auth_session_minutes,
        1,
    )


def client_ip(request: Request) -> str | None:
    if request.client is None:
        return None

    return request.client.host


@dataclass
class AuthContext:
    user: Utilisateur
    db_session: SessionUtilisateur
    roles: list[str]
    permissions: list[str]


class AuthService:

    @staticmethod
    async def login(
        db: AsyncSession,
        *,
        email: str,
        password: str,
        request: Request,
    ) -> LoginResponse:

        normalized_email = (
            email.strip().lower()
        )

        ip = client_ip(request)

        user = (
            await AuthRepository.get_user_by_email(
                db,
                normalized_email,
            )
        )
        
        # ====================================================
        # PROTECTION ANTI-BRUTEFORCE
        # ====================================================
        #
        # Ce contrôle intervient AVANT la vérification du mot
        # de passe.
        #
        # Il analyse :
        # - les échecs récents du compte ;
        # - les échecs récents de l'adresse IP.
        # ====================================================

        guard_result = (
            await LoginGuardService.check(
                db,
                user=user,
                ip_address=ip,
            )
        )

        if guard_result.blocked:

            await (
                LoginGuardService
                .audit_blocked_attempt(
                    db,
                    request=request,
                    user=user,
                    result=guard_result,
                )
            )

            raise HTTPException(
                status_code=(
                    status.HTTP_429_TOO_MANY_REQUESTS
                ),
                detail=(
                    "Trop de tentatives de connexion. "
                    "Réessayez plus tard."
                ),
                headers={
                    "Retry-After": str(
                        guard_result
                        .retry_after_seconds
                    )
                },
            )

        # Même réponse pour compte inexistant
        # et mauvais mot de passe.
        if (
            user is None
            or not verify_password(
                password,
                user.mot_de_passe_hash,
            )
        ):
            await write_audit_event(
                db,
                action="AUTH_LOGIN",
                categorie="SECURITE",
                resultat="ECHEC",
                utilisateur_id=(
                    user.id if user else None
                ),
                ressource_type="utilisateur",
                ressource_id=(
                    user.id if user else None
                ),
                adresse_ip=ip,
                contexte={
                    "motif":
                        "IDENTIFIANTS_INVALIDES",
                    "email":
                        normalized_email,
                    "user_agent":
                        request.headers.get(
                            "user-agent"
                        ),
                },
            )

            await db.commit()

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=(
                    "Identifiants invalides."
                ),
                headers={
                    "WWW-Authenticate": "Bearer"
                },
            )

        if (
            user.statut or ""
        ).strip().upper() != "ACTIF":

            await write_audit_event(
                db,
                action="AUTH_LOGIN",
                categorie="SECURITE",
                resultat="REFUSE",
                utilisateur_id=user.id,
                ressource_type="utilisateur",
                ressource_id=user.id,
                adresse_ip=ip,
                contexte={
                    "motif":
                        "COMPTE_NON_ACTIF",
                    "statut":
                        user.statut,
                    "user_agent":
                        request.headers.get(
                            "user-agent"
                        ),
                },
            )

            await db.commit()

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Compte utilisateur non actif."
                ),
            )

        roles = (
            await AuthRepository.get_roles(
                db,
                user.id,
            )
        )

        permissions = (
            await AuthRepository.get_permissions(
                db,
                user.id,
            )
        )

        token = generate_access_token()
        token_hash = hash_access_token(token)

        now = utc_now()

        expires_at = (
            now
            + timedelta(
                minutes=session_duration_minutes()
            )
        )

        db_session = SessionUtilisateur(
            utilisateur_id=user.id,
            jeton_hash=token_hash,
            adresse_ip=ip,
            user_agent=request.headers.get(
                "user-agent"
            ),
            debut_at=now,
            derniere_activite_at=now,
            expiration_at=expires_at,
            revoquee_at=None,
        )

        db.add(db_session)

        user.derniere_connexion_at = now

        await db.flush()

        await write_audit_event(
            db,
            action="AUTH_LOGIN",
            categorie="SECURITE",
            resultat="SUCCES",
            utilisateur_id=user.id,
            ressource_type="session",
            ressource_id=db_session.id,
            adresse_ip=ip,
            contexte={
                "roles": roles,
                "nombre_permissions":
                    len(permissions),
                "user_agent":
                    request.headers.get(
                        "user-agent"
                    ),
                "expiration_at":
                    expires_at.isoformat(),
            },
        )

        await db.commit()

        return LoginResponse(
            access_token=token,
            token_type="bearer",
            expires_at=expires_at,
            user=CurrentUserResponse(
                id=user.id,
                email=user.email,
                nom=user.nom,
                prenoms=user.prenoms,
                fonction=user.fonction,
                statut=user.statut,
                mfa_active=user.mfa_active,
                roles=roles,
                permissions=permissions,
            ),
        )

    @staticmethod
    async def logout(
        db: AsyncSession,
        *,
        context: AuthContext,
        request: Request,
    ) -> None:

        now = utc_now()

        context.db_session.revoquee_at = now
        context.db_session.derniere_activite_at = now

        await write_audit_event(
            db,
            action="AUTH_LOGOUT",
            categorie="SECURITE",
            resultat="SUCCES",
            utilisateur_id=context.user.id,
            ressource_type="session",
            ressource_id=context.db_session.id,
            adresse_ip=client_ip(request),
            contexte={
                "user_agent":
                    request.headers.get(
                        "user-agent"
                    ),
            },
        )

        await db.commit()