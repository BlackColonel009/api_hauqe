from __future__ import annotations

from datetime import date

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class GrilleFuccs(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "grilles_fuccs"

    code: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    libelle: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    version: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    date_effet: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_fin: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    reference_approbation: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    statut_publication: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    rubriques: Mapped[list["RubriqueFuccs"]] = relationship(
        "RubriqueFuccs",
        back_populates="grille_fuccs",
    )

    controles: Mapped[list["ControleFuccs"]] = relationship(
        "ControleFuccs",
        back_populates="grille_fuccs",
    )
