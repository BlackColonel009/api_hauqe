from __future__ import annotations

from datetime import date

from sqlalchemy import Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class ModeleScoring(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "modeles_scoring"

    code: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    libelle: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    version: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    objet_evalue: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    date_debut_validite: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_fin_validite: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    regle_calcul: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    reference_approbation: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    ponderations: Mapped[list["PonderationScoring"]] = relationship(
        "PonderationScoring",
        back_populates="modele_scoring",
    )

    classifications_entreprise: Mapped[
        list["ClassificationEntreprise"]
    ] = relationship(
        "ClassificationEntreprise",
        back_populates="modele_scoring",
    )

    resultats_infc: Mapped[list["ResultatInfc"]] = relationship(
        "ResultatInfc",
        back_populates="modele_scoring",
    )
