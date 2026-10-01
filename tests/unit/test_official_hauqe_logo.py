from __future__ import annotations

from io import BytesIO
from unittest.mock import patch
from zipfile import ZipFile

from app.services.bnec_report_service import render_pdf, render_xlsx
from app.tasks.process_notification_queue import send_smtp


def test_bnec_pdf_and_xlsx_embed_official_logo():
    pdf = render_pdf("Bilan BNEC", "Septembre 2026", [("Certificats", "2")])
    assert b"/Subtype /Image" in pdf and b"/XObject" in pdf
    xlsx = render_xlsx("Bilan BNEC", "Septembre 2026", [("Certificats", "2")])
    with ZipFile(BytesIO(xlsx)) as archive:
        assert any(name.startswith("xl/media/image") for name in archive.namelist())


def test_smtp_message_embeds_logo_inline():
    with patch("app.tasks.process_notification_queue.settings") as settings, \
         patch("app.tasks.process_notification_queue.smtplib.SMTP") as smtp:
        settings.hauqe_smtp_host = "smtp.example.test"
        settings.hauqe_smtp_from = "notifications@example.test"
        settings.hauqe_smtp_port = 587
        settings.hauqe_smtp_user = None
        settings.hauqe_smtp_password = None
        settings.hauqe_smtp_use_tls = True
        settings.hauqe_contact_service = None
        settings.hauqe_contact_email = None
        settings.hauqe_contact_phone = None
        send_smtp(recipient="agent@example.test", subject="Dossier de veille", body="Bonjour")
    message = smtp.return_value.__enter__.return_value.send_message.call_args.args[0]
    html_body = message.get_body(preferencelist=("html",)).get_content()
    assert "cid:hauqe-official-logo" in html_body
    images = [part for part in message.walk() if part.get_content_type() == "image/jpeg"]
    assert len(images) == 1
    assert images[0]["Content-ID"] == "<hauqe-official-logo>"
