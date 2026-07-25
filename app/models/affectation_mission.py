from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class AffectationMission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "affectations_mission"

    mission_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("missions_collecte.id"),
        nullable=False,
    )

    utilisateur_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    role_mission: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    date_debut: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_fin: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    attribue_par_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    motif: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    mission = relationship(
        "MissionCollecte",
        back_populates="affectations",
    )

    utilisateur = relationship(
        "Utilisateur",
        foreign_keys=[utilisateur_id],
    )

    attribue_par = relationship(
        "Utilisateur",
        foreign_keys=[attribue_par_id],
    )
