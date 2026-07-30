from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Echeance(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "echeances"

    ressource_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Relation générique : volontairement sans FK.
    ressource_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )

    type_echeance: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    titre: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    date_echeance: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    responsable_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
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

    motif_cloture: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    responsable = relationship(
        "Utilisateur",
        foreign_keys=[responsable_id],
    )

    alertes: Mapped[list["Alerte"]] = relationship(
        "Alerte",
        back_populates="echeance",
    )
