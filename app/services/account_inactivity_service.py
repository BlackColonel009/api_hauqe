"""
Service RM-33 — cycle d'inactivité des comptes.

Règle validée du projet :
- préavis 30 jours avant désactivation ;
- désactivation après 180 jours consécutifs d'inactivité ;
- réactivation uniquement par l'administration existante.

Le scan utilise comme dernière activité la date la plus récente parmi :
- `utilisateurs.derniere_connexion_at` ;
- `sessions_utilisateur.derniere_activite_at` ;
- `utilisateurs.created_at` en dernier recours.

Le scan ne supprime aucun compte.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit_event
from app.repositories.account_repository import AccountRepository
from app.schemas.account import AccountInactivityScanResponse


class AccountInactivityService:

    WARNING_AFTER_DAYS = 150
    DEACTIVATE_AFTER_DAYS = 180

    @staticmethod
    async def run(
        db: AsyncSession,
    ) -> AccountInactivityScanResponse:
        now = datetime.now(timezone.utc)
        users = await AccountRepository.active_users(db)

        warnings = 0
        deactivated = 0
        revoked_sessions = 0

        for user in users:
            security = await AccountRepository.get_or_create_security(
                db,
                user.id,
            )
            session_activity = await AccountRepository.last_session_activity(
                db,
                user.id,
            )

            candidates = [
                dt
                for dt in (
                    user.derniere_connexion_at,
                    session_activity,
                    security.reactivation_at,
                    user.created_at,
                )
                if dt is not None
            ]
            if not candidates:
                continue

            last_activity = max(candidates)
            inactive_days = (now - last_activity).days

            if inactive_days >= AccountInactivityService.DEACTIVATE_AFTER_DAYS:
                user.statut = "INACTIF"

                for session in await AccountRepository.active_user_sessions(
                    db,
                    user.id,
                ):
                    session.revoquee_at = now
                    revoked_sessions += 1

                await write_audit_event(
                    db,
                    action="ACCOUNT_INACTIVITY_DEACTIVATE",
                    categorie="SECURITE",
                    resultat="SUCCES",
                    utilisateur_id=user.id,
                    ressource_type="utilisateur",
                    ressource_id=user.id,
                    valeurs_apres={
                        "statut": "INACTIF",
                        "inactive_days": inactive_days,
                    },
                    contexte={
                        "rule": "RM-33",
                        "threshold_days": 180,
                    },
                )
                deactivated += 1
                continue

            if (
                inactive_days
                >= AccountInactivityService.WARNING_AFTER_DAYS
                and security.inactivite_warning_sent_at is None
            ):
                remaining = max(
                    0,
                    AccountInactivityService.DEACTIVATE_AFTER_DAYS
                    - inactive_days,
                )
                subject = (
                    "Préavis d'inactivité de votre compte HAUQE Certif"
                )
                body = (
                    "Votre compte n'a pas enregistré d'activité récente. "
                    f"Sans nouvelle connexion, il sera désactivé dans "
                    f"environ {remaining} jour(s), conformément à la règle "
                    "de sécurité du système."
                )

                await AccountRepository.create_notification(
                    db,
                    user_id=user.id,
                    channel="IN_APP",
                    subject=subject,
                    body=body,
                    immediate=True,
                )
                await AccountRepository.create_notification(
                    db,
                    user_id=user.id,
                    channel="EMAIL",
                    subject=subject,
                    body=body,
                    immediate=False,
                )

                security.inactivite_warning_sent_at = now

                await write_audit_event(
                    db,
                    action="ACCOUNT_INACTIVITY_WARNING",
                    categorie="SECURITE",
                    resultat="SUCCES",
                    utilisateur_id=user.id,
                    ressource_type="utilisateur",
                    ressource_id=user.id,
                    valeurs_apres={
                        "inactive_days": inactive_days,
                        "days_before_deactivation": remaining,
                    },
                    contexte={
                        "rule": "RM-33",
                        "warning_days_before": 30,
                    },
                )
                warnings += 1

        # Nettoyage technique des jetons éphémères utilisés/expirés.
        expired_deleted = 0
        cleanup_before = now - timedelta(days=7)
        for token in await AccountRepository.expired_or_used_tokens(
            db,
            before=cleanup_before,
        ):
            await db.delete(token)
            expired_deleted += 1

        await write_audit_event(
            db,
            action="ACCOUNT_INACTIVITY_SCAN",
            categorie="SECURITE",
            resultat="SUCCES",
            utilisateur_id=None,
            ressource_type="utilisateur",
            valeurs_apres={
                "users_scanned": len(users),
                "warnings_queued": warnings,
                "users_deactivated": deactivated,
                "sessions_revoked": revoked_sessions,
                "expired_tokens_deleted": expired_deleted,
            },
        )

        await db.commit()

        return AccountInactivityScanResponse(
            scanned_at=now,
            users_scanned=len(users),
            warnings_queued=warnings,
            users_deactivated=deactivated,
            sessions_revoked=revoked_sessions,
            expired_tokens_deleted=expired_deleted,
        )
