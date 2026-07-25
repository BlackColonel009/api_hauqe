from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class PointVerification(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "points_verification"

    dossier_verification_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("dossiers_verification.id"),
        nullable=False,
    )

    code: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    libelle: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    categorie: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    resultat: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    observation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    date_verification: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    preuve_document_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=True,
    )

    verifie_par_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    dossier_verification = relationship(
        "DossierVerification",
        back_populates="points",
    )

    preuve_document = relationship(
        "Document",
        foreign_keys=[preuve_document_id],
    )

    verifie_par = relationship(
        "Utilisateur",
        foreign_keys=[verifie_par_id],
    )

    anomalies: Mapped[list["AnomalieVerification"]] = relationship(
        "AnomalieVerification",
        back_populates="point_verification",
    )
