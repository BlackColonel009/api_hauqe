from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Referentiel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "referentiels"

    code: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    libelle: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    type_valeur: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    valeurs: Mapped[list["ValeurReferentiel"]] = relationship(
        "ValeurReferentiel",
        back_populates="referentiel",
        foreign_keys="ValeurReferentiel.referentiel_id",
    )


class ValeurReferentiel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "valeurs_referentiel"

    referentiel_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("referentiels.id"),
        nullable=False,
    )

    parent_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("valeurs_referentiel.id"),
        nullable=True,
    )

    code: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    libelle: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    ordre_affichage: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    date_debut_validite: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_fin_validite: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    referentiel: Mapped["Referentiel"] = relationship(
        "Referentiel",
        back_populates="valeurs",
        foreign_keys=[referentiel_id],
    )

    parent: Mapped["ValeurReferentiel | None"] = relationship(
        "ValeurReferentiel",
        remote_side="ValeurReferentiel.id",
        back_populates="enfants",
        foreign_keys=[parent_id],
    )

    enfants: Mapped[list["ValeurReferentiel"]] = relationship(
        "ValeurReferentiel",
        back_populates="parent",
        foreign_keys=[parent_id],
    )
