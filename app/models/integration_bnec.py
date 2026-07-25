from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class IntegrationBnec(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "integrations_bnec"

    validation_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("validations.id"),
        nullable=False,
    )

    administrateur_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    date_debut: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_fin: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    precontrole: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    postcontrole: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    sauvegarde_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    resume: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    validation = relationship(
        "Validation",
        back_populates="integrations_bnec",
    )

    administrateur = relationship(
        "Utilisateur",
        foreign_keys=[administrateur_id],
    )

    elements: Mapped[list["ElementIntegration"]] = relationship(
        "ElementIntegration",
        back_populates="integration_bnec",
    )
