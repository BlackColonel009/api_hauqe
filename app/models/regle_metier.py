from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class RegleMetier(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "regles_metier"

    code: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    famille: Mapped[str | None] = mapped_column(
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

    version: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    parametres: Mapped[
        dict[str, Any] | list[Any] | None
    ] = mapped_column(
        JSONB,
        nullable=True,
    )

    date_debut_effet: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_fin_effet: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    reference_approbation: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    approuve_par_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    approuve_par = relationship(
        "Utilisateur",
        foreign_keys=[approuve_par_id],
    )
