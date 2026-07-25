from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Organisme(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "organismes"

    identifiant_national: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    nom_officiel: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    sigle: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    type_organisme: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    pays: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    numero_enregistrement: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    telephone: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    adresse: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    zone_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("zones_administratives.id"),
        nullable=True,
    )

    site_web: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    date_derniere_verification: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    zone = relationship(
        "ZoneAdministrative",
        foreign_keys=[zone_id],
    )

    accreditations = relationship(
        "Accreditation",
        back_populates="organisme",
    )

    certifications = relationship(
        "Certification",
        back_populates="organisme",
    )
