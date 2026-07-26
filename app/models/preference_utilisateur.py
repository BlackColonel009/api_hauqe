"""
Modèle SQLAlchemy — préférences utilisateur.

Cette table complète `utilisateurs` sans déplacer les attributs d'identité
déjà présents dans le MPD.

Elle persiste uniquement les préférences réellement attendues par
`profil.html` :
- langue ;
- fuseau horaire ;
- avatar privé éventuel ;
- cinq catégories de notification.

L'adresse professionnelle, la fonction, les rôles et permissions restent
administrés ailleurs et ne sont pas stockés ici.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class PreferenceUtilisateur(Base):
    __tablename__ = "preferences_utilisateur"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    utilisateur_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("utilisateurs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    langue: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'fr'"),
    )
    fuseau_horaire: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        server_default=text("'Africa/Lome'"),
    )
    avatar_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
    )

    notifications_alertes_critiques: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )
    notifications_affectations: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )
    notifications_corrections: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )
    notifications_rapports_planifies: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )
    notifications_resume_hebdomadaire: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=text("now()"),
    )
