from types import SimpleNamespace

from app.config.settings import settings
from app.tasks.process_notification_queue import (
    append_sngsc_application_link,
    application_url_for_internal_alert,
    hauqe_html_message,
)


def test_sngsc_link_is_reserved_for_internal_alerts(monkeypatch):
    monkeypatch.setattr(settings, "lien_vers_sngsc", "31.220.87.142/sngsc")

    internal_alert = SimpleNamespace(
        alerte_id="alert-id",
        destinataire_utilisateur_id="user-id",
    )
    external_alert = SimpleNamespace(
        alerte_id="alert-id",
        destinataire_utilisateur_id=None,
    )

    assert application_url_for_internal_alert(internal_alert) == (
        "https://31.220.87.142/sngsc"
    )
    assert application_url_for_internal_alert(external_alert) is None


def test_sngsc_link_is_added_once_to_plain_and_html_messages():
    url = "http://31.220.87.142/sngsc"
    body = append_sngsc_application_link("Bonjour,\nAlerte à traiter.", url)

    assert body.count(url) == 1
    assert append_sngsc_application_link(body, url) == body
    assert f'href="{url}"' in hauqe_html_message(body, application_url=url)
