from __future__ import annotations

from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.models.renouvellement_certification import RenouvellementCertification
from app.services.veille_service import WatchService


def deadline(resource_type: str, resource_id, due: date):
    return SimpleNamespace(
        id=uuid4(), ressource_type=resource_type, ressource_id=resource_id,
        type_echeance=("EXPIRATION_CERTIFICATION" if resource_type == "CERTIFICATION"
                       else "RENOUVELLEMENT_CERTIFICATION"),
        date_echeance=due, rappels_email_actifs=True,
        escalade_administrateurs_jour_j=True, rappel_jours_avant=2,
        responsable_id=None,
    )


@pytest.mark.asyncio
async def test_custom_certificate_milestone_notifies_three_roles_once():
    due = date.today() + timedelta(days=45)
    certificate = SimpleNamespace(id=uuid4(), seuils_alerte_expiration_jours=[120, 45, 0])
    item = deadline("CERTIFICATION", certificate.id, due)
    users = [SimpleNamespace(id=uuid4()) for _ in range(3)]
    queued = []

    async def recipients(_db, roles):
        if roles == {"ADMIN_HAUQE"}:
            return {users[1].id: users[1]}
        assert roles == {"CELLULE_VEILLE", "ADMIN_HAUQE", "POINT_FOCAL_BNEC"}
        return {user.id: user for user in users}

    async def queue(_db, **kwargs):
        queued.append(kwargs)
        return True

    db = SimpleNamespace(get=AsyncMock(return_value=certificate))
    with patch("app.services.veille_service.WatchRepository.active_deadlines_for_reminders",
               new=AsyncMock(return_value=[item])), \
         patch("app.services.veille_service.WatchRepository.milestone_reminder_already_recorded",
               new=AsyncMock(return_value=False)), \
         patch("app.services.veille_service.WatchRepository.deadline_reminder_admin_exclusions",
               new=AsyncMock(return_value=[])), \
         patch("app.services.veille_service.WatchRepository.find_active_alert_for_rule",
               new=AsyncMock(return_value=SimpleNamespace(id=uuid4()))), \
         patch("app.services.veille_service.WorkflowCommunicationService.recipients_for_roles",
               new=recipients), \
         patch.object(WatchService, "ensure_threshold_alert", new=AsyncMock(return_value=False)), \
         patch.object(WatchService, "_queue_deadline_reminder", new=queue):
        count = await WatchService.dispatch_deadline_reminders(db)

    assert count == 3
    assert {row["recipient"].id for row in queued} == {user.id for user in users}
    assert all(row["milestone_days"] == 45 for row in queued)
    assert all(row["certification_id"] == certificate.id for row in queued)
    assert all(row["reminder_type"] == f"CERT_RENEWAL_45_{due:%Y%m%d}" for row in queued)


@pytest.mark.asyncio
async def test_renewal_on_certificate_expiry_does_not_duplicate_mail():
    due = date.today() + timedelta(days=30)
    certificate = SimpleNamespace(id=uuid4(), date_expiration=due)
    renewal = SimpleNamespace(id=uuid4(), certification_id=certificate.id,
                              date_decision=None, decision=None, statut="PLANIFIE")
    item = deadline("RENOUVELLEMENT_CERTIFICATION", renewal.id, due)

    async def get(model, _id):
        return renewal if model is RenouvellementCertification else certificate

    db = SimpleNamespace(get=get)
    with patch("app.services.veille_service.WatchRepository.active_deadlines_for_reminders",
               new=AsyncMock(return_value=[item])), \
         patch("app.services.veille_service.WatchRepository.find_active_deadline_for_resource",
               new=AsyncMock(return_value=deadline("CERTIFICATION", certificate.id, due))), \
         patch("app.services.veille_service.WorkflowCommunicationService.recipients_for_roles",
               new=AsyncMock()) as recipients:
        count = await WatchService.dispatch_deadline_reminders(db)
    assert count == 0
    recipients.assert_not_awaited()


@pytest.mark.asyncio
async def test_missed_milestone_is_not_emailed_again_on_following_day():
    due = date.today() + timedelta(days=44)
    certificate = SimpleNamespace(id=uuid4(), seuils_alerte_expiration_jours=[120, 45, 0])
    item = deadline("CERTIFICATION", certificate.id, due)
    recipient = SimpleNamespace(id=uuid4())
    db = SimpleNamespace(get=AsyncMock(return_value=certificate))

    async def recipients(_db, roles):
        return {recipient.id: recipient} if roles != {"ADMIN_HAUQE"} else {}

    with patch("app.services.veille_service.WatchRepository.active_deadlines_for_reminders",
               new=AsyncMock(return_value=[item])), \
         patch("app.services.veille_service.WatchRepository.milestone_reminder_already_recorded",
               new=AsyncMock(return_value=True)), \
         patch("app.services.veille_service.WatchRepository.deadline_reminder_admin_exclusions",
               new=AsyncMock(return_value=[])), \
         patch("app.services.veille_service.WatchRepository.find_active_alert_for_rule",
               new=AsyncMock(return_value=SimpleNamespace(id=uuid4()))), \
         patch("app.services.veille_service.WorkflowCommunicationService.recipients_for_roles",
               new=recipients), \
         patch.object(WatchService, "ensure_threshold_alert", new=AsyncMock()), \
         patch.object(WatchService, "_queue_deadline_reminder", new=AsyncMock()) as queue:
        count = await WatchService.dispatch_deadline_reminders(db)
    assert count == 0
    queue.assert_not_awaited()


@pytest.mark.asyncio
async def test_decided_renewal_deadline_is_closed_and_queued_mail_cancelled():
    item = SimpleNamespace(id=uuid4(), statut="PLANIFIEE", motif_cloture=None)
    alert = SimpleNamespace(id=uuid4(), statut="NOUVELLE", date_resolution=None)
    message = SimpleNamespace(statut="EN_ATTENTE", resultat=None)
    results = iter([
        SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [alert])),
        SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [message])),
    ])
    db = SimpleNamespace(execute=AsyncMock(side_effect=lambda _query: next(results)))
    with patch("app.services.veille_service.WatchRepository.active_deadlines_for_decided_renewals",
               new=AsyncMock(return_value=[item])):
        count = await WatchService.close_decided_renewal_deadlines(db)
    assert count == 1
    assert item.statut == "TERMINEE"
    assert alert.statut == "RESOLUE"
    assert message.statut == "ANNULEE"


@pytest.mark.asyncio
async def test_updating_certificate_jalons_refreshes_pending_renewal_too():
    expiry = date.today() + timedelta(days=45)
    certificate = SimpleNamespace(id=uuid4(), date_expiration=expiry,
                                  identifiant_national="CERT-EXEMPLE", numero_certificat=None)
    renewal = SimpleNamespace(id=uuid4(), date_limite=expiry,
                              date_ouverture=None,
                              justification="Cycle de renouvellement généré automatiquement lors de l'intégration BNEC.")
    thresholds = WatchService.certification_expiration_thresholds([120, 45, 0])
    due = []

    async def ensure(_db, **kwargs):
        due.append(kwargs)
        return SimpleNamespace(id=uuid4()), True

    with patch.object(WatchService, "certification_expiration_thresholds_for",
                      new=AsyncMock(return_value=thresholds)), \
         patch.object(WatchService, "ensure_generated_deadline", new=ensure), \
         patch.object(WatchService, "ensure_threshold_alert", new=AsyncMock(return_value=True)), \
         patch("app.services.veille_service.WatchRepository.cancel_active_expiration_alerts_for_deadline",
               new=AsyncMock()), \
         patch("app.services.veille_service.WatchRepository.pending_renewals_for_certification",
               new=AsyncMock(return_value=[renewal])):
        await WatchService.refresh_certification_expiration_alert(
            SimpleNamespace(), certification=certificate
        )

    assert renewal.date_ouverture == expiry - timedelta(days=120)
    assert {item["resource_type"] for item in due} == {
        "CERTIFICATION", "RENOUVELLEMENT_CERTIFICATION"
    }
