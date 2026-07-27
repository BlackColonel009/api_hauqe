"""Schémas API — présence des utilisateurs HAUQE."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class PresenceRoleResponse(BaseModel):
    code: str
    libelle: str | None = None


class PresenceUserResponse(BaseModel):
    user_id: UUID
    nom_complet: str
    fonction: str | None = None
    roles: list[PresenceRoleResponse] = Field(default_factory=list)
    presence: Literal["ONLINE", "RECENT"]
    last_activity_at: datetime
    has_avatar: bool = False
    avatar_url: str | None = None
    is_current_user: bool = False


class PresenceListResponse(BaseModel):
    window_minutes: int
    online_count: int
    recent_count: int
    total_count: int
    users: list[PresenceUserResponse]
