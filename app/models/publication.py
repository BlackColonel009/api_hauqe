from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Publication(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "publications"

    ressource_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Ressource générique : pas de FK physique.
    ressource_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )

    objet: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    perimetre: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    niveau_confidentialite: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    demande_par_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    date_demande: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    decision: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    autorite_approbation: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    approuve_par_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=True,
    )

    date_approbation: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    reserve: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    date_publication: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    demande_par = relationship(
        "Utilisateur",
        foreign_keys=[demande_par_id],
    )

    approuve_par = relationship(
        "Utilisateur",
        foreign_keys=[approuve_par_id],
    )
