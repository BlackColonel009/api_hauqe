from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class DossierVeille(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "dossiers_veille"

    certification_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("certifications.id"),
        nullable=False,
    )

    type_evenement: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    priorite: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    date_ouverture: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    responsable_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    prochaine_action_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    date_cloture: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    certification = relationship(
        "Certification",
        foreign_keys=[certification_id],
    )

    responsable = relationship(
        "Utilisateur",
        foreign_keys=[responsable_id],
    )

    relances: Mapped[list["RelanceVeille"]] = relationship(
        "RelanceVeille",
        back_populates="dossier_veille",
    )
