from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Validation(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "validations"

    fiche_collecte_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("fiches_collecte.id"),
        nullable=False,
    )

    controle_fuccs_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("controles_fuccs.id"),
        nullable=True,
    )

    niveau_validation: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    validateur_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    decision: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    date_validation: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Le MPD actuel définit reserves en VARCHAR(255)
    reserves: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    justification: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    fiche_collecte = relationship(
        "FicheCollecte",
        foreign_keys=[fiche_collecte_id],
    )

    controle_fuccs = relationship(
        "ControleFuccs",
        foreign_keys=[controle_fuccs_id],
    )

    validateur = relationship(
        "Utilisateur",
        foreign_keys=[validateur_id],
    )

    corrections: Mapped[list["Correction"]] = relationship(
        "Correction",
        back_populates="validation",
    )

    integrations_bnec: Mapped[list["IntegrationBnec"]] = relationship(
        "IntegrationBnec",
        back_populates="validation",
    )
