from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from app.models.alerte import Alerte
from app.models.notification import Notification
from app.repositories.veille_repository import WatchRepository
from app.services.workflow_communication_service import WorkflowCommunicationService


@pytest.mark.asyncio
async def test_one_person_with_two_roles_receives_one_in_app_and_one_email():
    user = SimpleNamespace(
        id=uuid4(), statut="ACTIF", email="agent@example.test",
        prenoms="Awa", nom="Kossi",
    )
    db = SimpleNamespace(
        add=Mock(),
        flush=AsyncMock(),
        execute=AsyncMock(return_value=SimpleNamespace(scalar_one=lambda: 0)),
        get=AsyncMock(),
    )
    with patch.object(
        WorkflowCommunicationService, "recipients_for_roles", new=AsyncMock(
            side_effect=[{user.id: user}, {user.id: user}]
        )
    ):
        count = await WorkflowCommunicationService.emit(
            db, event="COLLECTE_SOUMISE", resource_type="FICHE_COLLECTE",
            resource_id=uuid4(), title="Collecte soumise — Atelier Exemple",
            context="Entreprise : Atelier Exemple\nMission : HAUQE-MIS-2026-0001",
            action="Commencer la vérification documentaire.",
            route="#/verifications",
            action_roles={"VERIFICATEUR"},
            information_roles={"POINT_FOCAL_BNEC"},
        )
    created = [call.args[0] for call in db.add.call_args_list]
    assert count == 1
    assert len([item for item in created if isinstance(item, Alerte)]) == 1
    notifications = [item for item in created if isinstance(item, Notification)]
    assert [item.canal for item in notifications] == ["IN_APP", "EMAIL"]
    assert all(item.destinataire_utilisateur_id == user.id for item in notifications)
    assert "Atelier Exemple" in notifications[1].contenu
    assert "Action attendue" in notifications[1].contenu


@pytest.mark.asyncio
async def test_no_active_recipient_creates_no_alert():
    db = SimpleNamespace(add=Mock())
    with patch.object(
        WorkflowCommunicationService, "recipients_for_roles", new=AsyncMock(return_value={})
    ):
        count = await WorkflowCommunicationService.emit(
            db, event="BNEC_INTEGREE", resource_type="INTEGRATION_BNEC",
            resource_id=uuid4(), title="Intégration effectuée", context="Entreprise : Test",
            action="Suivre le dossier.", route="#/veille",
            action_roles={"CELLULE_VEILLE"},
        )
    assert count == 0
    db.add.assert_not_called()


@pytest.mark.asyncio
async def test_personal_alert_query_filters_by_account_not_all_alerts():
    user_id = uuid4()
    db = SimpleNamespace(execute=AsyncMock(side_effect=[
        SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [])),
        SimpleNamespace(scalar_one=lambda: 0),
    ]))
    rows, total = await WatchRepository.list_alerts(
        db, type_alerte=None, niveau=None, responsable_id=None,
        statut=None, ressource_type=None, ressource_id=None,
        limit=20, offset=0, current_user_id=user_id,
    )
    statement = str(db.execute.call_args_list[0].args[0].compile(
        compile_kwargs={"literal_binds": True}
    ))
    assert rows == [] and total == 0
    assert user_id.hex in statement
    assert "IN_APP" in statement
    assert "destinataire_utilisateur_id" in statement
