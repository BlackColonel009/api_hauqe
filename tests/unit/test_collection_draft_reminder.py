import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from app.routes.api.v1.collecte_workspace import my_collection_drafts


def test_draft_query_is_personal_and_read_only():
    user_id = uuid4()
    fiche_id, mission_id = uuid4(), uuid4()
    rows = [SimpleNamespace(id=fiche_id, mission_id=mission_id,
                            code="MISSION-2026-001", raison_sociale="Entreprise test")]
    db = SimpleNamespace(execute=AsyncMock(return_value=SimpleNamespace(all=lambda: rows)))
    result = asyncio.run(my_collection_drafts(db, SimpleNamespace(user=SimpleNamespace(id=user_id))))
    query = db.execute.call_args.args[0]
    values = query.compile().params
    assert user_id in values.values()
    assert "BROUILLON" in values.values()
    assert "fiches_collecte.responsable_id" in str(query)
    assert result["total"] == 1
    assert result["items"][0]["fiche_id"] == str(fiche_id)
