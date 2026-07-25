from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class DossierVerification(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "dossiers_verification"

    fiche_collecte_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("fiches_collecte.id"),
        nullable=False,
    )

    date_ouverture: Mapped[date | None] = mapped_column(
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

    avis: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    synthese: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    niveau_risque: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    priorite: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    fiche_collecte = relationship(
        "FicheCollecte",
        foreign_keys=[fiche_collecte_id],
    )

    affectations: Mapped[list["AffectationVerification"]] = relationship(
        "AffectationVerification",
        back_populates="dossier_verification",
    )

    points: Mapped[list["PointVerification"]] = relationship(
        "PointVerification",
        back_populates="dossier_verification",
    )

    anomalies: Mapped[list["AnomalieVerification"]] = relationship(
        "AnomalieVerification",
        back_populates="dossier_verification",
    )

    confirmations_externes: Mapped[list["ConfirmationExterne"]] = relationship(
        "ConfirmationExterne",
        back_populates="dossier_verification",
    )
