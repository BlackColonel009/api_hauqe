from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Archive(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "archives"

    ressource_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Ressource générique : pas de FK.
    ressource_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )

    categorie_donnees: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    date_archivage: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    motif: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    auteur_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    duree_conservation: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    date_suppression_prevue: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    emplacement: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    auteur = relationship(
        "Utilisateur",
        foreign_keys=[auteur_id],
    )
