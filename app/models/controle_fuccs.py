from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class ControleFuccs(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "controles_fuccs"

    dossier_verification_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("dossiers_verification.id"),
        nullable=False,
    )

    grille_fuccs_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("grilles_fuccs.id"),
        nullable=False,
    )

    controleur_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    date_debut: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_fin: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    score_brut: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    score_maximal: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    # IMPORTANT :
    # Le MPD actuel définit taux comme VARCHAR(255).
    # On le respecte strictement ici.
    taux: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    synthese: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    dossier_verification = relationship(
        "DossierVerification",
        foreign_keys=[dossier_verification_id],
    )

    grille_fuccs = relationship(
        "GrilleFuccs",
        back_populates="controles",
    )

    controleur = relationship(
        "Utilisateur",
        foreign_keys=[controleur_id],
    )

    notes: Mapped[list["NoteCritere"]] = relationship(
        "NoteCritere",
        back_populates="controle_fuccs",
    )

    constats: Mapped[list["ConstatControle"]] = relationship(
        "ConstatControle",
        back_populates="controle_fuccs",
    )
