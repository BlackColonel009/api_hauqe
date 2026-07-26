"""
Modèle SQLAlchemy — jetons de sécurité à durée limitée.

Le token BRUT n'est jamais stocké.
PostgreSQL conserve uniquement SHA-256(token).

Types actuellement utilisés :
- PASSWORD_RESET
- MFA_LOGIN

La table est volontairement générique pour permettre plus tard un flux
d'invitation/activation sans ajouter une nouvelle famille de jetons.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class JetonSecuriteUtilisateur(Base):
    __tablename__ = "jetons_securite_utilisateur"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    utilisateur_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("utilisateurs.id", ondelete="CASCADE"),
        nullable=False,
    )
    type_jeton: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    jeton_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
    )
    expiration_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    utilise_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    adresse_ip: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    user_agent: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    contexte: Mapped[dict | None] = mapped_column(
        JSONB,
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
