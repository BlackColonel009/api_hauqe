from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class MissionCollecte(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "missions_collecte"

    campagne_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("campagnes.id"),
        nullable=False,
    )

    code: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    objet: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    zone_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("zones_administratives.id"),
        nullable=False,
    )

    date_debut_prevue: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_fin_prevue: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_debut_reelle: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_fin_reelle: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    priorite: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    progression: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    campagne = relationship(
        "Campagne",
        back_populates="missions",
    )

    zone = relationship(
        "ZoneAdministrative",
        foreign_keys=[zone_id],
    )

    affectations: Mapped[list["AffectationMission"]] = relationship(
        "AffectationMission",
        back_populates="mission",
    )

    fiches: Mapped[list["FicheCollecte"]] = relationship(
        "FicheCollecte",
        back_populates="mission",
    )
