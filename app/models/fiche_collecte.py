from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class FicheCollecte(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "fiches_collecte"

    mission_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("missions_collecte.id"),
        nullable=False,
    )

    entreprise_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("entreprises.id"),
        nullable=True,
    )

    version_formulaire: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    numero_revision: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    taux_completude: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    consentement_obtenu: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    nom_declarant: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    fonction_declarant: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    telephone_declarant: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    email_declarant: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    signature_declarant: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    observations: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    collecte_par_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    collecte_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    soumise_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    mission = relationship(
        "MissionCollecte",
        back_populates="fiches",
    )

    entreprise = relationship(
        "Entreprise",
        foreign_keys=[entreprise_id],
    )

    collecte_par = relationship(
        "Utilisateur",
        foreign_keys=[collecte_par_id],
    )

    offres_declarees: Mapped[list["OffreDeclaree"]] = relationship(
        "OffreDeclaree",
        back_populates="fiche_collecte",
    )

    certifications_declarees: Mapped[list["CertificationDeclaree"]] = relationship(
        "CertificationDeclaree",
        back_populates="fiche_collecte",
    )

    evenements: Mapped[list["EvenementCollecte"]] = relationship(
        "EvenementCollecte",
        back_populates="fiche_collecte",
    )
