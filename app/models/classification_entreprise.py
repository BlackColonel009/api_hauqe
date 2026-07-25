from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class ClassificationEntreprise(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "classifications_entreprise"

    entreprise_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("entreprises.id"),
        nullable=False,
    )

    modele_scoring_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("modeles_scoring.id"),
        nullable=False,
    )

    score: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    classe: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    date_calcul: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_validation: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    sources: Mapped[
        dict[str, Any] | list[Any] | None
    ] = mapped_column(
        JSONB,
        nullable=True,
    )

    valide_par_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    entreprise = relationship(
        "Entreprise",
        foreign_keys=[entreprise_id],
    )

    modele_scoring = relationship(
        "ModeleScoring",
        back_populates="classifications_entreprise",
    )

    valide_par = relationship(
        "Utilisateur",
        foreign_keys=[valide_par_id],
    )
