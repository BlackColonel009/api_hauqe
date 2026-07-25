from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class SiteEntreprise(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sites_entreprise"

    entreprise_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("entreprises.id"),
        nullable=False,
    )

    nom: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    type_site: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    adresse: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    zone_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("zones_administratives.id"),
        nullable=False,
    )

    latitude: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    longitude: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    date_ouverture: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    effectif: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    entreprise = relationship(
        "Entreprise",
        back_populates="sites",
    )

    zone = relationship(
        "ZoneAdministrative",
        foreign_keys=[zone_id],
    )
