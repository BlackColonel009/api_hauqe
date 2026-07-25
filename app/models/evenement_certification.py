from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class EvenementCertification(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "evenements_certification"

    certification_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("certifications.id"),
        nullable=False,
    )

    type_evenement: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    ancien_statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    nouveau_statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    date_evenement: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    motif: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    source: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    acteur_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=True,
    )

    certification = relationship(
        "Certification",
        back_populates="evenements",
    )

    acteur = relationship(
        "Utilisateur",
        foreign_keys=[acteur_id],
    )
