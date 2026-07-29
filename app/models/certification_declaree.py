from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class CertificationDeclaree(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "certifications_declarees"

    fiche_collecte_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("fiches_collecte.id"),
        nullable=False,
    )

    nom_certification: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    numero: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    organisme_declare: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    norme_declaree: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    portee: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    date_obtention: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_expiration: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    copie_disponible: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    situation_declaree: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    certification_officielle_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("certifications.id"),
        nullable=True,
    )

    score_rapprochement: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    statut_rapprochement: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    fiche_collecte = relationship(
        "FicheCollecte",
        back_populates="certifications_declarees",
    )

    certification_officielle = relationship(
        "Certification",
        foreign_keys=[certification_officielle_id],
    )
