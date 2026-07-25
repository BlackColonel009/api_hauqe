from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Accreditation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "accreditations"

    organisme_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organismes.id"),
        nullable=False,
    )

    numero: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    accrediteur: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    domaine_technique: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    perimetre: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    date_delivrance: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_expiration: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    reference_officielle: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    decision_hauqe: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    date_decision: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    organisme = relationship(
        "Organisme",
        back_populates="accreditations",
    )

    certifications = relationship(
        "Certification",
        back_populates="accreditation",
    )
