from __future__ import annotations

from datetime import datetime
from uuid import UUID
 
from sqlalchemy import Boolean, ForeignKey, String, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Utilisateur(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "utilisateurs"

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    mot_de_passe_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    nom: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    prenoms: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    telephone: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    fonction: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    region_affectation_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("zones_administratives.id"),
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    mfa_active: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    derniere_connexion_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    region_affectation = relationship(
        "ZoneAdministrative",
        foreign_keys=[region_affectation_id],
    )

    attributions_roles = relationship(
        "UtilisateurRole",
        foreign_keys="UtilisateurRole.utilisateur_id",
        back_populates="utilisateur",
    )

    attributions_effectuees = relationship(
        "UtilisateurRole",
        foreign_keys="UtilisateurRole.attribue_par_id",
        back_populates="attribue_par",
    )

    sessions = relationship(
        "SessionUtilisateur",
        back_populates="utilisateur",
    )

    evenements_audit = relationship(
        "EvenementAudit",
        back_populates="utilisateur",
    )
