from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class RapportVeille(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "rapports_veille"

    type_rapport: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # IMPORTANT :
    # le MPD actuel utilise VARCHAR(255), pas DATE.
    periode_debut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    periode_fin: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    nombre_certifications_suivies: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    nombre_alertes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    nombre_renouvellements: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    delai_moyen_traitement: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    indicateurs: Mapped[
        dict[str, Any] | list[Any] | None
    ] = mapped_column(
        JSONB,
        nullable=True,
    )

    prepare_par_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    valide_par_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=True,
    )

    date_validation: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    prepare_par = relationship(
        "Utilisateur",
        foreign_keys=[prepare_par_id],
    )

    valide_par = relationship(
        "Utilisateur",
        foreign_keys=[valide_par_id],
    )
