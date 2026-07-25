from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Sauvegarde(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "sauvegardes"

    type_enregistrement: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    parent_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sauvegardes.id"),
        nullable=True,
    )

    frequence: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    retention: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    perimetre: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    emplacement_stockage: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    date_debut: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_fin: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    taille_octets: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    integrite_validee: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    resultat: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    preuve_document_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=True,
    )

    message_erreur: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    parent: Mapped["Sauvegarde | None"] = relationship(
        "Sauvegarde",
        remote_side="Sauvegarde.id",
        back_populates="enfants",
        foreign_keys=[parent_id],
    )

    enfants: Mapped[list["Sauvegarde"]] = relationship(
        "Sauvegarde",
        back_populates="parent",
        foreign_keys=[parent_id],
    )

    preuve_document = relationship(
        "Document",
        foreign_keys=[preuve_document_id],
    )
