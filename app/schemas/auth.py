from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    email: str = Field(
        min_length=3,
        max_length=255,
    )

    password: str = Field(
        min_length=1,
        max_length=1024,
    )


class CurrentUserResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: UUID
    email: str
    nom: str | None = None
    prenoms: str | None = None
    fonction: str | None = None
    statut: str | None = None
    mfa_active: bool | None = None

    roles: list[str] = []
    permissions: list[str] = []


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user: CurrentUserResponse


class LogoutResponse(BaseModel):
    message: str = "Session révoquée."