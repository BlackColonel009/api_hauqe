"""
Protection des connexions contre le bruteforce.

Rôle du fichier :
- compter les échecs récents ;
- contrôler le seuil par utilisateur ;
- contrôler le seuil par adresse IP ;
- déterminer la durée restante du verrouillage ;
- journaliser les tentatives bloquées.

Aucune nouvelle table n'est nécessaire.

La source de vérité utilisée est :
    evenements_audit

Les événements AUTH_LOGIN / ECHEC déjà enregistrés servent
donc directement au mécanisme de protection.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import (
    datetime,
    timedelta,
    timezone,
)

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit_event
from app.config.settings import settings
from app.models.utilisateur import Utilisateur
from app.repositories.auth_repository import (
    AuthRepository,
)


# ============================================================
# HORLOGE TECHNIQUE
# ============================================================

def utc_now() -> datetime:
    """
    Les contrôles de sécurité utilisent exclusivement UTC.
    """

    return datetime.now(timezone.utc)


# ============================================================
# RESULTAT DU CONTROLE
# ============================================================

@dataclass
class LoginGuardResult:
    """
    Résultat retourné par le moteur anti-bruteforce.
    """

    blocked: bool
    reason: str | None = None
    retry_after_seconds: int = 0


# ============================================================
# SERVICE ANTI-BRUTEFORCE
# ============================================================

class LoginGuardService:

    @staticmethod
    def max_attempts() -> int:
        """
        Nombre maximal d'échecs tolérés.
        """

        return max(
            settings.auth_max_failed_attempts,
            1,
        )


    @staticmethod
    def failure_window_minutes() -> int:
        """
        Fenêtre dans laquelle les échecs sont comptés.
        """

        return max(
            settings.auth_failure_window_minutes,
            1,
        )


    @staticmethod
    def lockout_minutes() -> int:
        """
        Durée du verrouillage temporaire.
        """

        return max(
            settings.auth_lockout_minutes,
            1,
        )


    # ========================================================
    # CALCUL DU VERROUILLAGE
    # ========================================================

    @classmethod
    def evaluate_events(
        cls,
        events,
        *,
        now: datetime,
        reason: str,
    ) -> LoginGuardResult:
        """
        Détermine si une série d'échecs entraîne
        actuellement un verrouillage.

        Le verrouillage commence au dernier échec enregistré.
        """

        if len(events) < cls.max_attempts():
            return LoginGuardResult(
                blocked=False
            )

        latest_failure = events[0]

        if latest_failure.date_evenement is None:
            return LoginGuardResult(
                blocked=False
            )

        locked_until = (
            latest_failure.date_evenement
            + timedelta(
                minutes=cls.lockout_minutes()
            )
        )

        # Le délai de blocage est déjà terminé.
        if now >= locked_until:
            return LoginGuardResult(
                blocked=False
            )

        remaining = int(
            (
                locked_until - now
            ).total_seconds()
        )

        return LoginGuardResult(
            blocked=True,
            reason=reason,
            retry_after_seconds=max(
                remaining,
                1,
            ),
        )


    # ========================================================
    # CONTROLE GLOBAL
    # ========================================================

    @classmethod
    async def check(
        cls,
        db: AsyncSession,
        *,
        user: Utilisateur | None,
        ip_address: str | None,
    ) -> LoginGuardResult:
        """
        Vérifie successivement :

        1. le nombre d'échecs sur le compte ;
        2. le nombre d'échecs provenant de l'adresse IP.

        La première règle déclenchée bloque la connexion.
        """

        now = utc_now()

        since = (
            now
            - timedelta(
                minutes=(
                    cls.failure_window_minutes()
                )
            )
        )

        # ----------------------------------------------------
        # Protection par compte
        # ----------------------------------------------------

        if user is not None:

            user_events = (
                await AuthRepository
                .get_recent_failed_logins_for_user(
                    db,
                    user_id=user.id,
                    since=since,
                )
            )

            result = cls.evaluate_events(
                user_events,
                now=now,
                reason="COMPTE_TEMPORAIREMENT_BLOQUE",
            )

            if result.blocked:
                return result

        # ----------------------------------------------------
        # Protection par adresse IP
        # ----------------------------------------------------

        if ip_address:

            ip_events = (
                await AuthRepository
                .get_recent_failed_logins_for_ip(
                    db,
                    ip_address=ip_address,
                    since=since,
                )
            )

            result = cls.evaluate_events(
                ip_events,
                now=now,
                reason="ADRESSE_IP_TEMPORAIREMENT_BLOQUEE",
            )

            if result.blocked:
                return result

        return LoginGuardResult(
            blocked=False
        )


    # ========================================================
    # JOURNALISATION DU BLOCAGE
    # ========================================================

    @staticmethod
    async def audit_blocked_attempt(
        db: AsyncSession,
        *,
        request: Request,
        user: Utilisateur | None,
        result: LoginGuardResult,
    ) -> None:
        """
        Journalise une tentative rejetée par le mécanisme
        anti-bruteforce.

        IMPORTANT :
        aucun mot de passe ni token n'est enregistré.
        """

        await write_audit_event(
            db,
            action="AUTH_LOGIN_BLOCKED",
            categorie="SECURITE",
            resultat="REFUSE",
            utilisateur_id=(
                user.id
                if user
                else None
            ),
            ressource_type="utilisateur",
            ressource_id=(
                user.id
                if user
                else None
            ),
            adresse_ip=(
                request.client.host
                if request.client
                else None
            ),
            contexte={
                "motif": result.reason,
                "retry_after_seconds":
                    result.retry_after_seconds,
                "user_agent":
                    request.headers.get(
                        "user-agent"
                    ),
            },
        )

        await db.commit()