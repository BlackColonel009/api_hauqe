from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.repositories.mission_collecte_repository import (
    MissionCollecteRepository,
)
from app.services.fiche_collecte_service import FicheCollecteService
from app.services.mission_collecte_service import MissionCollecteService


def make_actor(*permissions: str):
    return SimpleNamespace(
        user=SimpleNamespace(id=uuid4()),
        permissions=list(permissions),
    )


@pytest.mark.asyncio
async def test_unassigned_collector_cannot_write_a_mission(monkeypatch):
    actor = make_actor("COLLECTE.CREER")
    mission_id = uuid4()
    monkeypatch.setattr(
        MissionCollecteService,
        "get",
        AsyncMock(return_value=SimpleNamespace(id=mission_id)),
    )
    monkeypatch.setattr(
        MissionCollecteRepository,
        "get_active_assignment_for_user",
        AsyncMock(return_value=None),
    )

    with pytest.raises(HTTPException) as exc:
        await FicheCollecteService.ensure_actor_can_write_mission(
            AsyncMock(),
            mission_id=mission_id,
            actor=actor,
        )

    assert exc.value.status_code == 403
    assert "affectation active" in exc.value.detail


@pytest.mark.asyncio
async def test_assigned_collector_can_write_a_mission(monkeypatch):
    actor = make_actor("COLLECTE.MODIFIER")
    mission_id = uuid4()
    assignment = SimpleNamespace(mission_id=mission_id)
    monkeypatch.setattr(
        MissionCollecteService,
        "get",
        AsyncMock(return_value=SimpleNamespace(id=mission_id)),
    )
    active_assignment = AsyncMock(return_value=assignment)
    monkeypatch.setattr(
        MissionCollecteRepository,
        "get_active_assignment_for_user",
        active_assignment,
    )

    await FicheCollecteService.ensure_actor_can_write_mission(
        AsyncMock(),
        mission_id=mission_id,
        actor=actor,
    )

    active_assignment.assert_awaited_once()


@pytest.mark.asyncio
async def test_collecte_manager_can_write_without_assignment(monkeypatch):
    actor = make_actor("COLLECTE.AFFECTER")
    mission_id = uuid4()
    monkeypatch.setattr(
        MissionCollecteService,
        "get",
        AsyncMock(return_value=SimpleNamespace(id=mission_id)),
    )
    active_assignment = AsyncMock()
    monkeypatch.setattr(
        MissionCollecteRepository,
        "get_active_assignment_for_user",
        active_assignment,
    )

    await FicheCollecteService.ensure_actor_can_write_mission(
        AsyncMock(),
        mission_id=mission_id,
        actor=actor,
    )

    active_assignment.assert_not_awaited()
