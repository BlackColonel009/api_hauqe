from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Certification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "certifications"

    identifiant_national: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    entreprise_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("entreprises.id"),
        nullable=False,
    )

    organisme_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organismes.id"),
        nullable=False,
    )

    accreditation_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("accreditations.id"),
        nullable=True,
    )

    norme_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("normes.id"),
        nullable=False,
    )

    numero_certificat: Mapped[str | None] = mapped_column(
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

    date_effet: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_expiration: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    motif_statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Conservée car elle existe dans la base actuelle.
    classification: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    authenticite_verifiee: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    certification_strategique: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    source_donnee: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    entreprise = relationship(
        "Entreprise",
        foreign_keys=[entreprise_id],
    )

    organisme = relationship(
        "Organisme",
        back_populates="certifications",
    )

    accreditation = relationship(
        "Accreditation",
        back_populates="certifications",
    )

    norme = relationship(
        "Norme",
        foreign_keys=[norme_id],
    )

    couvertures = relationship(
        "CouvertureCertification",
        back_populates="certification",
    )

    audits = relationship(
        "AuditCertification",
        back_populates="certification",
    )

    evenements = relationship(
        "EvenementCertification",
        back_populates="certification",
    )

    renouvellements = relationship(
        "RenouvellementCertification",
        back_populates="certification",
    )
