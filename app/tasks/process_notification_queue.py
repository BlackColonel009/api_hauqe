"""
Worker minimal de transport EMAIL pour les notifications en attente.

IMPORTANT
---------
Le domaine métier ne stocke aucun secret SMTP.

Variables d'environnement attendues :
    HAUQE_SMTP_HOST
    HAUQE_SMTP_PORT          défaut 587
    HAUQE_SMTP_USER
    HAUQE_SMTP_PASSWORD
    HAUQE_SMTP_FROM
    HAUQE_SMTP_USE_TLS       défaut true

Si `HAUQE_SMTP_HOST` ou `HAUQE_SMTP_FROM` manque, le worker quitte sans
modifier la file.

Les notifications IN_APP ne passent pas par ce worker.
"""

from __future__ import annotations

import asyncio
import os
import smtplib
import sys
from email.message import EmailMessage

from app.database.session import AsyncSessionLocal
from app.repositories.veille_repository import WatchRepository
from app.schemas.veille import NotificationResultRequest
from app.services.veille_service import WatchService


def env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def send_smtp(
    *,
    recipient: str,
    subject: str,
    body: str,
) -> str:
    host = os.getenv("HAUQE_SMTP_HOST")
    sender = os.getenv("HAUQE_SMTP_FROM")

    if not host or not sender:
        raise RuntimeError(
            "Transport SMTP non configuré : "
            "HAUQE_SMTP_HOST / HAUQE_SMTP_FROM requis."
        )

    port = int(os.getenv("HAUQE_SMTP_PORT", "587"))
    user = os.getenv("HAUQE_SMTP_USER")
    password = os.getenv("HAUQE_SMTP_PASSWORD")
    use_tls = env_bool("HAUQE_SMTP_USE_TLS", True)

    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(host, port, timeout=30) as smtp:
        if use_tls:
            smtp.starttls()
        if user:
            smtp.login(user, password or "")
        smtp.send_message(message)

    return f"SMTP:{host}"


async def run(limit: int = 100) -> None:
    if not os.getenv("HAUQE_SMTP_HOST") or not os.getenv("HAUQE_SMTP_FROM"):
        print(
            "SMTP non configuré. La file EMAIL reste intacte."
        )
        return

    async with AsyncSessionLocal() as db:
        rows = await WatchRepository.pending_email_notifications(
            db,
            limit=limit,
        )

        for item in rows:
            recipient = item.adresse_externe

            if item.destinataire_utilisateur_id:
                user = await WatchRepository.get_user(
                    db,
                    item.destinataire_utilisateur_id,
                )
                if user is None or (user.statut or "").upper() != "ACTIF":
                    await WatchService.record_notification_delivery(
                        db,
                        notification_id=item.id,
                        payload=NotificationResultRequest(
                            success=False,
                            resultat="DESTINATAIRE_INACTIF",
                            message_erreur=(
                                "Utilisateur absent ou inactif au moment "
                                "de l'envoi."
                            ),
                        ),
                        actor=None,
                        request=None,
                    )
                    continue
                recipient = user.email

            if not recipient:
                await WatchService.record_notification_delivery(
                    db,
                    notification_id=item.id,
                    payload=NotificationResultRequest(
                        success=False,
                        resultat="DESTINATAIRE_ABSENT",
                        message_erreur="Aucune adresse email disponible.",
                    ),
                    actor=None,
                    request=None,
                )
                continue

            try:
                provider_result = send_smtp(
                    recipient=recipient,
                    subject=item.objet or "Notification HAUQE",
                    body=item.contenu or "",
                )
                await WatchService.record_notification_delivery(
                    db,
                    notification_id=item.id,
                    payload=NotificationResultRequest(
                        success=True,
                        resultat=provider_result,
                    ),
                    actor=None,
                    request=None,
                )
            except Exception as exc:
                await WatchService.record_notification_delivery(
                    db,
                    notification_id=item.id,
                    payload=NotificationResultRequest(
                        success=False,
                        resultat="ECHEC_SMTP",
                        message_erreur=str(exc)[:255],
                    ),
                    actor=None,
                    request=None,
                )

        print(f"File EMAIL traitée : {len(rows)} notification(s).")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.run(run(), loop_factory=asyncio.SelectorEventLoop)
    else:
        asyncio.run(run())
