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
import html
import logging
import smtplib
import sys
from email.message import EmailMessage

from app.config.logging import configure_logging
from app.config.settings import settings
from app.database.session import AsyncSessionLocal
from app.repositories.veille_repository import WatchRepository
from app.schemas.veille import NotificationResultRequest
from app.services.veille_service import WatchService

logger = logging.getLogger(__name__)
configure_logging()

MAIL_BRAND = "HAUQE — Haute Autorité de la Qualité et de l'Environnement"


def hauqe_contact_lines() -> list[str]:
    """Construit la signature à partir des seules coordonnées configurées."""
    return [
        value.strip()
        for value in (
            settings.hauqe_contact_service,
            settings.hauqe_contact_email,
            settings.hauqe_contact_phone,
        )
        if value and value.strip()
    ]


def hauqe_plain_signature() -> str:
    contact = hauqe_contact_lines()
    if not contact:
        return (
            "Message automatique du SNGSC / HAUQE. "
            "Merci de ne pas répondre à ce message si aucun contact n'est indiqué."
        )
    return "Pour toute précision, contactez :\n" + "\n".join(contact)


def hauqe_html_signature() -> str:
    contact = hauqe_contact_lines()
    if not contact:
        return (
            "Message automatique du SNGSC / HAUQE. Merci de ne pas répondre à ce "
            "courriel si aucun contact n'est indiqué."
        )
    safe_contact = "<br>".join(html.escape(value) for value in contact)
    return f"Pour toute précision, contactez :<br>{safe_contact}"


def hauqe_subject(subject: str) -> str:
    """Préfixe uniforme, sans répéter HAUQE lorsque l'objet le contient déjà."""
    clean_subject = (subject or "Notification").strip()
    if clean_subject.upper().startswith("HAUQE"):
        return clean_subject
    return f"HAUQE | {clean_subject}"


def hauqe_plain_message(body: str) -> str:
    """Version lisible dans les clients qui ne prennent pas en charge le HTML."""
    return (
        f"{MAIL_BRAND}\n"
        "Communication officielle du SNGSC\n"
        f"{'=' * 52}"
        f"\n\n{(body or '').strip()}\n\n"
        "—\n"
        f"{hauqe_plain_signature()}"
    )


def hauqe_html_message(body: str) -> str:
    """Habillage sobre et compatible pour les courriels émis par le worker."""
    safe_body = html.escape((body or "").strip()).replace("\n", "<br>")
    return f"""\
<!doctype html>
<html lang="fr"><body style="margin:0;background:#f3f7f5;font-family:Arial,sans-serif;color:#163d32;">
  <div style="max-width:640px;margin:24px auto;background:#ffffff;border:1px solid #d7e6df;border-radius:14px;overflow:hidden;">
    <div style="padding:24px 28px;background:#087659;color:#ffffff;">
      <div style="font-size:12px;font-weight:700;letter-spacing:1.1px;opacity:.85;">HAUQE · SNGSC</div>
      <div style="margin-top:7px;font-size:20px;font-weight:700;">Communication officielle</div>
      <div style="margin-top:4px;font-size:13px;opacity:.9;">Haute Autorité de la Qualité et de l'Environnement</div>
    </div>
    <div style="padding:28px;font-size:15px;line-height:1.65;">{safe_body}</div>
    <div style="padding:16px 28px;background:#eef6f2;border-top:1px solid #d7e6df;font-size:12px;line-height:1.5;color:#527067;">
      {hauqe_html_signature()}
    </div>
  </div>
</body></html>"""


def send_smtp(
    *,
    recipient: str,
    subject: str,
    body: str,
) -> str:
    host = settings.hauqe_smtp_host
    sender = settings.hauqe_smtp_from

    if not host or not sender:
        raise RuntimeError(
            "Transport SMTP non configuré : "
            "HAUQE_SMTP_HOST / HAUQE_SMTP_FROM requis."
        )

    port = settings.hauqe_smtp_port
    user = settings.hauqe_smtp_user
    password = settings.hauqe_smtp_password
    use_tls = settings.hauqe_smtp_use_tls

    message = EmailMessage()
    message["From"] = f"HAUQE <{sender}>"
    message["To"] = recipient
    message["Subject"] = hauqe_subject(subject)
    message["X-HAUQE-Message"] = "SNGSC"
    message.set_content(hauqe_plain_message(body))
    message.add_alternative(hauqe_html_message(body), subtype="html")

    with smtplib.SMTP(host, port, timeout=30) as smtp:
        if use_tls:
            smtp.starttls()
        if user:
            smtp.login(user, password or "")
        smtp.send_message(message)

    return f"ACCEPTE_PAR_RELAIS_SMTP:{host}"


async def run(limit: int = 100) -> None:
    if not settings.hauqe_smtp_host or not settings.hauqe_smtp_from:
        logger.warning("SMTP non configuré. La file EMAIL reste intacte.")
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
                if (item.objet or "") == "Création de votre compte HAUQE":
                    item.contenu = (
                        "Contenu sensible effacé automatiquement après "
                        "l’envoi des identifiants temporaires."
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
                logger.exception(
                    "Échec SMTP pour la notification %s.",
                    item.id,
                )
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

        logger.info("File EMAIL traitée : %s notification(s).", len(rows))


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.run(run(), loop_factory=asyncio.SelectorEventLoop)
    else:
        asyncio.run(run())
