from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.alerte import Alerte
from app.models.correction import Correction
from app.models.echeance import Echeance
from app.schemas.validation_bnec import CorrectionCreateRequest, CorrectionResubmitRequest, IntegrationOpenRequest, IntegrationStartRequest
from app.services.validation_bnec_service import ValidationBnecService
from app.services.veille_service import WatchService


def result(value):
    return SimpleNamespace(scalar_one_or_none=lambda: value,
                           scalars=lambda: SimpleNamespace(all=lambda: value))


@pytest.mark.asyncio
@pytest.mark.parametrize("decision,confirm", [("AJOURNE", False), ("VALIDE_SOUS_RESERVE", False)])
async def test_integration_never_opens_without_favorable_or_explicit_reserve_confirmation(decision, confirm):
    validation = SimpleNamespace(niveau_validation="NIVEAU_2", decision=decision, statut="TERMINE")
    with patch.object(ValidationBnecService, "get_validation", new=AsyncMock(return_value=validation)):
        with pytest.raises(HTTPException) as error:
            await ValidationBnecService.open_integration(
                SimpleNamespace(), validation_id=uuid4(),
                payload=IntegrationOpenRequest(confirmer_reserve=confirm),
                actor=SimpleNamespace(), request=SimpleNamespace(),
            )
    assert error.value.status_code == 409


@pytest.mark.asyncio
@pytest.mark.parametrize("decision,latest_is_same", [("VALIDE_SOUS_RESERVE", True), ("VALIDE", False)])
async def test_final_integration_requires_reserve_acknowledgement_and_current_n2(decision, latest_is_same):
    validation = SimpleNamespace(id=uuid4(), decision=decision, statut="TERMINE")
    integration = SimpleNamespace(statut="EN_ATTENTE")
    fiche = SimpleNamespace(id=uuid4())
    latest = validation if latest_is_same else SimpleNamespace(id=uuid4())
    actor = SimpleNamespace(permissions={
        "INTEGRATION.EXECUTER", "INTEGRATION.PRECONTROLER",
        "INTEGRATION.POSTCONTROLER", "INTEGRATION.CLOTURER",
    })
    with patch.object(ValidationBnecService, "_source_context",
                      new=AsyncMock(return_value=(integration, validation, fiche, None))), \
         patch("app.services.validation_bnec_service.ValidationBnecRepository.latest_validation_for_level",
               new=AsyncMock(return_value=latest)):
        with pytest.raises(HTTPException) as error:
            await ValidationBnecService.start(
                SimpleNamespace(), integration_id=uuid4(),
                payload=IntegrationStartRequest(), actor=actor, request=SimpleNamespace(),
            )
    assert error.value.status_code == 409


@pytest.mark.asyncio
async def test_request_creates_one_linked_deadline_and_contextual_notifications():
    fiche_id, validation_id, collector_id, validator_id = (uuid4() for _ in range(4))
    validation = SimpleNamespace(id=validation_id, fiche_collecte_id=fiche_id,
                                 validateur_id=validator_id, decision="AJOURNE")
    fiche = SimpleNamespace(id=fiche_id, collecte_par_id=collector_id)
    validator = SimpleNamespace(prenoms="Awa", nom="Kossi", email="awa@example.test")
    added = []

    async def flush():
        for item in added:
            if getattr(item, "id", None) is None:
                item.id = uuid4()
            if isinstance(item, Correction):
                item.created_at = item.updated_at = datetime.now(timezone.utc)

    async def get(model, item_id):
        return fiche if item_id == fiche_id else validator

    db = SimpleNamespace(add=added.append, flush=flush, get=get,
                         execute=AsyncMock(return_value=result(None)),
                         commit=AsyncMock(), refresh=AsyncMock())
    actor = SimpleNamespace(user=SimpleNamespace(id=uuid4()))
    due = date.today() + timedelta(days=5)
    with patch.object(ValidationBnecService, "get_validation", new=AsyncMock(return_value=validation)), \
         patch("app.services.validation_bnec_service.WorkflowCommunicationService.fiche_context",
               new=AsyncMock(return_value=("Entreprise Exemple", "Mission : M-001"))), \
         patch("app.services.validation_bnec_service.WorkflowCommunicationService.emit",
               new=AsyncMock(return_value=3)) as emit, \
         patch("app.services.validation_bnec_service.write_audit_event", new=AsyncMock()):
        created = await ValidationBnecService.create_correction(
            db, validation_id=validation_id,
            payload=CorrectionCreateRequest(motif="Preuve absente", instructions="Déposer la preuve", date_echeance=due),
            actor=actor, request=SimpleNamespace(client=None),
        )

    deadline = next(item for item in added if isinstance(item, Echeance))
    assert deadline.ressource_type == "CORRECTION"
    assert deadline.ressource_id == created.id
    assert deadline.responsable_id == collector_id
    assert deadline.date_echeance == due
    assert "Awa Kossi" in emit.await_args.kwargs["context"]
    assert "Preuve absente" in emit.await_args.kwargs["context"]
    assert emit.await_args.kwargs["deadline_id"] == deadline.id
    assert emit.await_args.kwargs["action_roles"] == {"ADMIN_HAUQE", "POINT_FOCAL_BNEC"}
    assert emit.await_args.kwargs["action_user_ids"] == {collector_id}
    assert str(created.id) in emit.await_args.kwargs["route"]
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_resubmission_completes_only_its_deadline_and_cancels_queued_emails():
    validation_id, fiche_id, correction_id, collector_id = (uuid4() for _ in range(4))
    correction = SimpleNamespace(id=correction_id, validation_id=validation_id,
                                 date_resoumission=None, reponse=None, statut="DEMANDEE",
                                 motif="Preuve absente", instructions="Déposer la preuve",
                                 date_demande=date.today(), date_echeance=date.today(),
                                 created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
    deadline = SimpleNamespace(id=uuid4(), statut="PLANIFIEE", motif_cloture=None)
    alert = SimpleNamespace(id=uuid4(), statut="NOUVELLE", date_resolution=None)
    pending = SimpleNamespace(statut="EN_ATTENTE", resultat=None)
    sent = SimpleNamespace(statut="ENVOYEE", resultat="SMTP")
    queue = [result(deadline), result([alert]), result([pending])]
    db = SimpleNamespace(execute=AsyncMock(side_effect=queue),
                         get=AsyncMock(return_value=SimpleNamespace(id=fiche_id, collecte_par_id=collector_id)),
                         commit=AsyncMock(), refresh=AsyncMock())
    validation = SimpleNamespace(fiche_collecte_id=fiche_id)
    actor = SimpleNamespace(user=SimpleNamespace(id=collector_id), roles=["AGENT_COLLECTE"])
    with patch("app.services.validation_bnec_service.ValidationBnecRepository.get_correction",
               new=AsyncMock(return_value=correction)), \
         patch.object(ValidationBnecService, "get_validation", new=AsyncMock(return_value=validation)), \
         patch("app.services.validation_bnec_service.write_audit_event", new=AsyncMock()):
        response = await ValidationBnecService.resubmit_correction(
            db, validation_id=validation_id, correction_id=correction_id,
            payload=CorrectionResubmitRequest(reponse="Document fourni"),
            actor=actor, request=SimpleNamespace(client=None),
        )

    assert response.statut == "RESOUMISE"
    assert deadline.statut == "TERMINEE"
    assert alert.statut == "RESOLUE"
    assert pending.statut == "ANNULEE"
    assert sent.statut == "ENVOYEE"
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_correction_reminder_targets_collector_point_focal_and_admin_once():
    collector = SimpleNamespace(id=uuid4(), statut="ACTIF")
    admin = SimpleNamespace(id=uuid4(), statut="ACTIF")
    focal = SimpleNamespace(id=uuid4(), statut="ACTIF")
    deadline = SimpleNamespace(id=uuid4(), ressource_type="CORRECTION", date_echeance=date.today() - timedelta(days=1),
                               rappels_email_actifs=True, escalade_administrateurs_jour_j=True,
                               rappel_jours_avant=2, responsable_id=collector.id)
    async def recipients(_db, codes):
        if codes == {"ADMIN_HAUQE"}:
            return {admin.id: admin}
        return {admin.id: admin, focal.id: focal}
    queued = []
    async def queue(_db, **kwargs):
        queued.append(kwargs["recipient"].id)
        return True
    with patch("app.services.veille_service.WatchRepository.active_deadlines_for_reminders",
               new=AsyncMock(return_value=[deadline])), \
         patch("app.services.veille_service.WatchRepository.get_user", new=AsyncMock(return_value=collector)), \
         patch("app.services.veille_service.WatchRepository.deadline_reminder_admin_exclusions",
               new=AsyncMock(return_value=[])), \
         patch("app.services.veille_service.WorkflowCommunicationService.recipients_for_roles", new=recipients), \
         patch.object(WatchService, "_ensure_deadline_reminder_alert", new=AsyncMock(return_value=SimpleNamespace(id=uuid4()))), \
         patch.object(WatchService, "_queue_deadline_reminder", new=queue):
        total = await WatchService.dispatch_deadline_reminders(SimpleNamespace())
    assert total == 3
    assert set(queued) == {collector.id, admin.id, focal.id}
