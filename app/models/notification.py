from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Notification(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "notifications"

    alerte_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("alertes.id"),
        nullable=True,
    )

    destinataire_utilisateur_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=True,
    )

    adresse_externe: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    canal: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    objet: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    contenu: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Conservé en DATE car c'est le type du MPD actuel.
    date_envoi: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_lecture: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    resultat: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    nombre_tentatives: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    message_erreur: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    alerte = relationship(
        "Alerte",
        back_populates="notifications",
    )

    destinataire_utilisateur = relationship(
        "Utilisateur",
        foreign_keys=[destinataire_utilisateur_id],
    )
