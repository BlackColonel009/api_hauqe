"""
Sécurité et cycle de vie des sessions utilisateur.

Responsabilités :
- vérifier l'expiration absolue d'une session ;
- détecter une période d'inactivité trop longue ;
- révoquer automatiquement une session devenue invalide ;
- journaliser les révocations de sécurité ;
- mettre à jour la dernière activité d'une session valide.

IMPORTANT :
Ce service ne crée pas les sessions.
La création reste gérée par AuthService.login().
"""

from __future__ import annotations

from app.config.settings import settings
from datetime import datetime, timedelta, timezone

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit_event
from app.models.session_utilisateur import SessionUtilisateur


# ============================================================
# TEMPS UTC
# ============================================================
# Tous les événements techniques sont manipulés en UTC.
# PostgreSQL utilise TIMESTAMPTZ pour ces colonnes.
# ============================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ============================================================
# CONFIGURATION DU VERROUILLAGE PAR INACTIVITE
# ============================================================

def idle_timeout_minutes() -> int:
    """
    Retourne la durée maximale d'inactivité autorisée.

    La valeur provient exclusivement de Settings, qui charge
    le fichier .env au démarrage de l'application.

    Exemple :
        AUTH_IDLE_TIMEOUT_MINUTES=30

    Une valeur inférieure à 1 minute est refusée afin d'éviter
    une configuration accidentellement invalide.
    """

    return max(
        settings.auth_idle_timeout_minutes,
        1,
    )


# ============================================================
# IP CLIENT
# ============================================================

def get_client_ip(
    request: Request,
) -> str | None:
    """
    Retourne l'adresse IP connue par FastAPI.

    Plus tard, si l'application est placée derrière Nginx,
    nous traiterons proprement les proxys de confiance et
    X-Forwarded-For.
    """

    if request.client is None:
        return None

    return request.client.host


# ============================================================
# SERVICE DE SECURITE DES SESSIONS
# ============================================================

class SessionSecurityService:
    """
    Centralise toutes les règles de sécurité appliquées
    à une session déjà créée.
    """

    @staticmethod
    def is_absolute_expired(
        session: SessionUtilisateur,
        *,
        now: datetime,
    ) -> bool:
        """
        Vérifie l'expiration absolue.

        Une session dont expiration_at est absente est
        considérée invalide par sécurité.
        """

        if session.expiration_at is None:
            return True

        return session.expiration_at <= now

    @staticmethod
    def is_idle_expired(
        session: SessionUtilisateur,
        *,
        now: datetime,
    ) -> bool:
        """
        Vérifie si l'utilisateur est resté inactif
        trop longtemps.

        Si derniere_activite_at est absente, debut_at
        sert de référence.
        """

        last_activity = (
            session.derniere_activite_at
            or session.debut_at
        )

        if last_activity is None:
            # Une session sans aucune référence temporelle
            # est considérée invalide.
            return True

        idle_limit = timedelta(
            minutes=idle_timeout_minutes()
        )

        return (
            now - last_activity
        ) >= idle_limit

    @staticmethod
    async def revoke_session(
        db: AsyncSession,
        *,
        session: SessionUtilisateur,
        request: Request,
        reason: str,
        audit_action: str,
    ) -> None:
        """
        Révoque définitivement une session.

        Le token brut n'est jamais enregistré dans l'audit.
        """

        now = utc_now()

        if session.revoquee_at is None:
            session.revoquee_at = now

        await write_audit_event(
            db,
            action=audit_action,
            categorie="SECURITE",
            resultat="REVOQUEE",
            utilisateur_id=session.utilisateur_id,
            ressource_type="session",
            ressource_id=session.id,
            adresse_ip=get_client_ip(request),
            contexte={
                "motif": reason,
                "user_agent": request.headers.get(
                    "user-agent"
                ),
                "expiration_at": (
                    session.expiration_at.isoformat()
                    if session.expiration_at
                    else None
                ),
                "derniere_activite_at": (
                    session.derniere_activite_at.isoformat()
                    if session.derniere_activite_at
                    else None
                ),
            },
        )

        await db.commit()

    @staticmethod
    async def touch(
        db: AsyncSession,
        *,
        session: SessionUtilisateur,
    ) -> None:
        """
        Enregistre une activité valide de l'utilisateur.

        Cette date servira au prochain contrôle du délai
        d'inactivité.
        """

        session.derniere_activite_at = utc_now()

        await db.commit()