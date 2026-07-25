from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Alerte(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "alertes"

    echeance_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("echeances.id"),
        nullable=True,
    )

    type_alerte: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Niveau 1, 2, 3, 4...
    niveau: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    titre: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    ressource_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Relation générique, sans FK dans le MPD.
    ressource_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )

    responsable_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=True,
    )

    date_detection: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_resolution: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    regle_notification: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    echeance = relationship(
        "Echeance",
        back_populates="alertes",
    )

    responsable = relationship(
        "Utilisateur",
        foreign_keys=[responsable_id],
    )

    notifications: Mapped[list["Notification"]] = relationship(
        "Notification",
        back_populates="alerte",
    )
