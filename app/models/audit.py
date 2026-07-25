from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class EvenementAudit(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "evenements_audit"

    utilisateur_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=True,
    )

    action: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    categorie: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    ressource_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    ressource_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )

    adresse_ip: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    contexte: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    valeurs_avant: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    valeurs_apres: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    empreinte: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    resultat: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    date_evenement: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    utilisateur = relationship(
        "Utilisateur",
        back_populates="evenements_audit",
    )
