from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class EvenementCollecte(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "evenements_collecte"

    fiche_collecte_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("fiches_collecte.id"),
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

    commentaire: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    acteur_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    date_evenement: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    fiche_collecte = relationship(
        "FicheCollecte",
        back_populates="evenements",
    )

    acteur = relationship(
        "Utilisateur",
        foreign_keys=[acteur_id],
    )
