from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Entreprise(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "entreprises"

    identifiant_national: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    raison_sociale: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    nom_commercial: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    forme_juridique: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    rccm: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    nif: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    ifu: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    date_creation: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    nationalite: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    capital_social: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    effectif: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # Conservé dans la base conformément au MPD.
    # Il ne sera simplement pas exposé dans le frontend actuel.
    chiffre_affaires: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    email_principal: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    telephone_principal: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    site_web: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    adresse_siege: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    zone_siege_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("zones_administratives.id"),
        nullable=False,
    )

    activite_principale: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    secteurs_secondaires: Mapped[list[Any] | dict[str, Any] | None] = (
        mapped_column(
            JSONB,
            nullable=True,
        )
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    niveau_risque: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    source_donnee: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    date_derniere_verification: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    zone_siege = relationship(
        "ZoneAdministrative",
        foreign_keys=[zone_siege_id],
    )

    contacts: Mapped[list["ContactEntreprise"]] = relationship(
        "ContactEntreprise",
        back_populates="entreprise",
    )

    sites: Mapped[list["SiteEntreprise"]] = relationship(
        "SiteEntreprise",
        back_populates="entreprise",
    )

    offres: Mapped[list["OffreEntreprise"]] = relationship(
        "OffreEntreprise",
        back_populates="entreprise",
    )

    candidats_doublon_source: Mapped[list["CandidatDoublon"]] = relationship(
        "CandidatDoublon",
        foreign_keys="CandidatDoublon.entreprise_source_id",
        back_populates="entreprise_source",
    )

    candidats_doublon_cible: Mapped[list["CandidatDoublon"]] = relationship(
        "CandidatDoublon",
        foreign_keys="CandidatDoublon.entreprise_cible_id",
        back_populates="entreprise_cible",
    )
