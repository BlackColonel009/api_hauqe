from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class ConfirmationExterne(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "confirmations_externes"

    dossier_verification_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("dossiers_verification.id"),
        nullable=False,
    )

    organisme_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organismes.id"),
        nullable=True,
    )

    canal: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    destinataire: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    objet: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    date_envoi: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_echeance: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_reponse: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    contenu_reponse: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    resultat: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    document_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    dossier_verification = relationship(
        "DossierVerification",
        back_populates="confirmations_externes",
    )

    organisme = relationship(
        "Organisme",
        foreign_keys=[organisme_id],
    )

    document = relationship(
        "Document",
        foreign_keys=[document_id],
    )
