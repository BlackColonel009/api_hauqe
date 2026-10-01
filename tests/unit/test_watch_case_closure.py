from __future__ import annotations

from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.schemas.veille import WatchCaseCloseRequest
from app.services.account_service import AccountService
from app.services.veille_service import WatchService


def row(**values):
    return SimpleNamespace(**values)


@pytest.mark.asyncio
async def test_close_stops_only_pending_items_and_preserves_replied_history():
    case_id = uuid4()
    cert_id = uuid4()
    pending = row(id=uuid4(), statut="EN_ATTENTE", date_envoi=date.today() + timedelta(days=2))
    sent = row(id=uuid4(), statut="EN_ATTENTE", date_envoi=date.today() - timedelta(days=1))
    replied = row(id=uuid4(), statut="REPONDU", date_envoi=date.today() - timedelta(days=3))
    deadline = row(statut="PLANIFIEE", motif_cloture=None)
    alert = row(statut="NOUVELLE", date_resolution=None)
    mail = row(relance_veille_id=pending.id, statut="PLANIFIEE", resultat=None, message_erreur=None)
    case = row(id=case_id, certification_id=cert_id, type_evenement="RENOUVELLEMENT",
               responsable_id=uuid4(), statut="OUVERT", date_cloture=None)
    actor = row(user=row(id=uuid4(), prenoms="Awa", nom="Kossi", email="awa@example.test"))
    db = row(commit=AsyncMock(), refresh=AsyncMock())
    targets = {"followups": [pending, sent, replied], "deadlines": [deadline],
               "alerts": [alert], "emails": [mail], "alert_emails": []}
    with patch.object(WatchService, "require_watch_case", new=AsyncMock(return_value=case)), \
         patch.object(WatchService, "close_watch_case_targets", new=AsyncMock(return_value=targets)), \
         patch.object(WatchService, "watch_case_response", new=AsyncMock(return_value=case)), \
         patch("app.services.veille_service.WatchRepository.certification_context", new=AsyncMock(return_value="Entreprise : Exemple\nCertification : ISO 9001")), \
         patch("app.services.veille_service.WorkflowCommunicationService.emit", new=AsyncMock(return_value=2)) as notify, \
         patch("app.services.veille_service.write_audit_event", new=AsyncMock()):
        result = await WatchService.close_watch_case(
            db, case_id=case_id, payload=WatchCaseCloseRequest(motif="Suivi achevé"),
            actor=actor, request=row(client=None),
        )
        assert result is case
        assert (pending.statut, sent.statut, replied.statut) == (
            "ANNULEE", "CLOTUREE_SANS_REPONSE", "REPONDU")
        assert deadline.statut == "ANNULEE" and alert.statut == "ANNULEE"
        assert mail.statut == "ANNULEE" and case.statut == "CLOTURE"
        assert "Entreprise : Exemple" in notify.await_args.kwargs["context"]
        assert "Suivi achevé" in notify.await_args.kwargs["context"]

        await WatchService.close_watch_case(
            db, case_id=case_id, payload=WatchCaseCloseRequest(motif="Suivi achevé"),
            actor=actor, request=row(client=None),
        )
        assert notify.await_count == 1
        db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_close_preview_counts_only_selected_case_targets():
    case_id = uuid4()
    selected = {"followups": [row(statut="EN_ATTENTE"), row(statut="REPONDU")],
                "deadlines": [row()], "alerts": [row()],
                "emails": [row()], "alert_emails": []}
    db = row()
    with patch.object(WatchService, "require_watch_case", new=AsyncMock()), \
         patch.object(WatchService, "close_watch_case_targets", new=AsyncMock(return_value=selected)) as targets:
        preview = await WatchService.close_watch_case_preview(db, case_id)
    targets.assert_awaited_once_with(db, case_id)
    assert (preview.relances_total, preview.relances_en_attente,
            preview.echeances_actives, preview.alertes_actives,
            preview.courriels_planifies) == (2, 1, 1, 1, 1)


@pytest.mark.asyncio
async def test_close_target_queries_never_select_other_case_or_certificate_deadlines():
    case_id, other_case_id, followup_id = uuid4(), uuid4(), uuid4()
    statements = []

    async def execute(statement):
        statements.append(str(statement.compile(compile_kwargs={"literal_binds": True})))
        return row(scalars=lambda: row(all=lambda: []))

    db = row(execute=execute)
    with patch("app.services.veille_service.WatchRepository.list_followups",
               new=AsyncMock(return_value=[row(id=followup_id, statut="REPONDU")])):
        targets = await WatchService.close_watch_case_targets(db, case_id)

    assert targets["deadlines"] == []
    assert case_id.hex in statements[0]
    assert followup_id.hex in statements[0]
    assert other_case_id.hex not in "\n".join(statements)
    assert "DOSSIER_VEILLE" in statements[0] and "RELANCE_VEILLE" in statements[0]
    assert "relance_veille_id" in statements[-1] or "relance_veille_id" in "\n".join(statements)


def test_point_focal_can_manage_system_email_policies():
    AccountService.require_email_policy_admin(row(roles=["POINT_FOCAL_BNEC"]))
    with pytest.raises(HTTPException) as error:
        AccountService.require_email_policy_admin(row(roles=["CELLULE_VEILLE"]))
    assert error.value.status_code == 403
