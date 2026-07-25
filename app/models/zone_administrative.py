from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class ZoneAdministrative(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "zones_administratives"

    parent_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("zones_administratives.id"),
        nullable=True,
    )

    type_zone: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    code: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    nom: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    latitude: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    longitude: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    parent: Mapped["ZoneAdministrative | None"] = relationship(
        "ZoneAdministrative",
        remote_side="ZoneAdministrative.id",
        back_populates="enfants",
    )

    enfants: Mapped[list["ZoneAdministrative"]] = relationship(
        "ZoneAdministrative",
        back_populates="parent",
    )
