from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class CouvertureCertification(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "couvertures_certification"

    certification_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("certifications.id"),
        nullable=False,
    )

    type_couverture: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    offre_entreprise_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("offres_entreprise.id"),
        nullable=True,
    )

    site_entreprise_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sites_entreprise.id"),
        nullable=True,
    )

    libelle_couverture: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    details: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    certification = relationship(
        "Certification",
        back_populates="couvertures",
    )

    offre_entreprise = relationship(
        "OffreEntreprise",
        foreign_keys=[offre_entreprise_id],
    )

    site_entreprise = relationship(
        "SiteEntreprise",
        foreign_keys=[site_entreprise_id],
    )
