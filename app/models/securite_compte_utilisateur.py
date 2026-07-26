"""
Modèle SQLAlchemy — sécurité avancée du compte.

Les secrets ne sont jamais stockés en clair :
- secret TOTP : chiffré avec Fernet ;
- codes de récupération : empreintes Argon2 ;
- code privé de reprise : empreinte Argon2.

`utilisateurs.mfa_active` reste le drapeau officiel d'activation MFA.
Cette table contient les détails techniques nécessaires à son fonctionnement.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class SecuriteCompteUtilisateur(Base):
    __tablename__ = "securite_compte_utilisateur"
    __table_args__ = (
        CheckConstraint(
            "delai_verrouillage_minutes IN (5, 10, 15, 30)",
            name="ck_security_lock_timeout_allowed",
        ),
    )

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

    mfa_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        server_default=text("'TOTP'"),
    )
    mfa_secret_chiffre: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    mfa_secret_pending_chiffre: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    mfa_recovery_codes_hash: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    mfa_verifie_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    code_prive_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    verrouillage_auto_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )
    delai_verrouillage_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("15"),
    )
    code_prive_configure_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # RM-33 : permet de ne pas renvoyer le préavis 30 jours à chaque scan.
    inactivite_warning_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    reactivation_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    derniere_modification_mot_de_passe_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
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
