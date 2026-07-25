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


class DecisionInstitutionnelle(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "decisions_institutionnelles"

    ressource_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Relation polymorphe : pas de FK dans le MPD actuel.
    ressource_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )

    type_decision: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    titre: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    contexte: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    constats: Mapped[
        dict[str, Any] | list[Any] | None
    ] = mapped_column(
        JSONB,
        nullable=True,
    )

    risques: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    options: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    decision: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    recommandation: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    autorite: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    decide_par_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=True,
    )

    date_decision: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    priorite: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    decide_par = relationship(
        "Utilisateur",
        foreign_keys=[decide_par_id],
    )
