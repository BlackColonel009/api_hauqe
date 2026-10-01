from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.rapport_genere import RapportGenere
from app.schemas.governance import ReportConfigurationSaveRequest
from app.services import governance_service as module


class FakeSession:
    def __init__(self):
        self.added = []
        self.commits = 0

    def add(self, item):
        self.added.append(item)

    async def flush(self):
        for item in self.added:
            if item.id is None:
                item.id = uuid4()
            if item.created_at is None:
                item.created_at = datetime.now(timezone.utc)
            if item.updated_at is None:
                item.updated_at = item.created_at

    async def commit(self):
        self.commits += 1

    async def refresh(self, _item):
        pass


@pytest.mark.asyncio
async def test_report_configurations_are_scoped_to_current_user(monkeypatch):
    user_id = uuid4()
    received = {}

    async def list_reports(_db, **filters):
        received.update(filters)
        return {"total": 0, "items": []}

    monkeypatch.setattr(module.GovernanceService, "list_reports", list_reports)
    result = await module.GovernanceService.list_report_configurations(
        object(), actor=SimpleNamespace(user=SimpleNamespace(id=user_id))
    )
    assert result["total"] == 0
    assert received == {
        "categorie": "EXPORT_CONFIG", "statut": "CONFIGURATION",
        "demandeur_id": user_id, "limit": 100, "offset": 0,
    }


@pytest.mark.asyncio
async def test_save_report_configuration_writes_existing_table_and_audit(monkeypatch):
    db = FakeSession()
    actor = SimpleNamespace(user=SimpleNamespace(id=uuid4()))
    events = []

    async def no_existing(_db, *, actor):
        return {"total": 0, "items": []}

    async def audit(_db, **kwargs):
        events.append(kwargs)

    monkeypatch.setattr(module.GovernanceService, "list_report_configurations", no_existing)
    monkeypatch.setattr(module, "write_audit_event", audit)
    payload = ReportConfigurationSaveRequest(
        model_id="companies", filtres={"status": "ACTIF", "region": "zone-1"},
        sections={"selected": ["identifiers", "statuses"]}, format="CSV",
    )
    result = await module.GovernanceService.save_report_configuration(
        db, payload=payload, actor=actor, request=None,
    )
    assert isinstance(db.added[0], RapportGenere)
    assert result.code_modele == "EXPORT_CONFIG_COMPANIES"
    assert result.demandeur_id == actor.user.id
    assert result.filtres == payload.filtres
    assert result.sections == payload.sections
    assert result.format == "CSV"
    assert result.statut == "CONFIGURATION"
    assert db.commits == 1
    assert events[0]["action"] == "REPORT_CONFIG_SAVE"
