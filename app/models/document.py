from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Document(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "documents"

    type_document: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    nom_original: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    nom_stockage: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    chemin_stockage: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    format: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    taille_octets: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    checksum: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    version: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    ressource_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Relation polymorphe volontairement conservée telle que
    # définie dans le MPD actuel : pas de ForeignKey SQL.
    ressource_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )

    confidentialite: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    source: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    date_document: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    depose_par_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=True,
    )

    date_depot: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    statut_verification: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    depose_par = relationship(
        "Utilisateur",
        foreign_keys=[depose_par_id],
    )
