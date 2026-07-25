from __future__ import annotations

from datetime import date

from sqlalchemy import Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Norme(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "normes"

    code: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    nom: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    version: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    autorite_emettrice: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    domaine: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    portee: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    date_debut_application: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_fin_application: Mapped[date | None] = mapped_column(
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
