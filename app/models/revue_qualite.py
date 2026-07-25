from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class RevueQualite(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "revues_qualite"

    # MPD actuel : VARCHAR(255), pas DATE.
    periode_debut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    periode_fin: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    perimetre: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    resultat_global: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    constats: Mapped[
        dict[str, Any] | list[Any] | None
    ] = mapped_column(
        JSONB,
        nullable=True,
    )

    preuves: Mapped[
        dict[str, Any] | list[Any] | None
    ] = mapped_column(
        JSONB,
        nullable=True,
    )

    responsable_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    date_validation: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    responsable = relationship(
        "Utilisateur",
        foreign_keys=[responsable_id],
    )

    plans_action: Mapped[list["PlanAction"]] = relationship(
        "PlanAction",
        back_populates="revue_qualite",
    )
