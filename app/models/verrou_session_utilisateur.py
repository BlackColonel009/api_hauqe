"""
Modèle SQLAlchemy — verrou de reprise d'une session utilisateur.

Le verrouillage de reprise est distinct :
- du timeout absolu de la session ;
- du timeout serveur d'inactivité ;
- du blocage du compte après échecs de connexion.

Il s'applique à UNE session précise et évite qu'une erreur de code privé sur
un appareil affecte les autres sessions de l'utilisateur.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class VerrouSessionUtilisateur(Base):
    __tablename__ = "verrous_session_utilisateur"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    session_utilisateur_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sessions_utilisateur.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    verrouillee_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    deverrouillee_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    tentatives_code_prive: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )
    derniere_tentative_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    motif: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
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
