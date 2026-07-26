"""account_security_extension

Revision ID: c5b7a8f2d901
Revises: 9f89b5d85b6a
Create Date: 2026-07-26

Extension explicitement introduite pour couvrir les fonctions déjà présentes
dans le frontend `profil.html` mais absentes du MPD initial :
- préférences utilisateur ;
- MFA réel ;
- verrouillage de reprise par session ;
- jetons temporaires de sécurité.

Le schéma métier passe de 66 à 70 tables.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c5b7a8f2d901"
down_revision: Union[str, Sequence[str], None] = "9f89b5d85b6a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "preferences_utilisateur",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("utilisateur_id", sa.UUID(), nullable=False),
        sa.Column(
            "langue",
            sa.String(length=20),
            server_default=sa.text("'fr'"),
            nullable=False,
        ),
        sa.Column(
            "fuseau_horaire",
            sa.String(length=100),
            server_default=sa.text("'Africa/Lome'"),
            nullable=False,
        ),
        sa.Column("avatar_document_id", sa.UUID(), nullable=True),
        sa.Column(
            "notifications_alertes_critiques",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "notifications_affectations",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "notifications_corrections",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "notifications_rapports_planifies",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "notifications_resume_hebdomadaire",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["utilisateur_id"],
            ["utilisateurs.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["avatar_document_id"],
            ["documents.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("utilisateur_id"),
    )

    op.create_table(
        "securite_compte_utilisateur",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("utilisateur_id", sa.UUID(), nullable=False),
        sa.Column(
            "mfa_type",
            sa.String(length=30),
            server_default=sa.text("'TOTP'"),
            nullable=False,
        ),
        sa.Column("mfa_secret_chiffre", sa.Text(), nullable=True),
        sa.Column("mfa_secret_pending_chiffre", sa.Text(), nullable=True),
        sa.Column(
            "mfa_recovery_codes_hash",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "mfa_verifie_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "code_prive_hash",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "verrouillage_auto_active",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "delai_verrouillage_minutes",
            sa.Integer(),
            server_default=sa.text("15"),
            nullable=False,
        ),
        sa.Column(
            "code_prive_configure_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "inactivite_warning_sent_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "reactivation_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "derniere_modification_mot_de_passe_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "delai_verrouillage_minutes IN (5, 10, 15, 30)",
            name="ck_security_lock_timeout_allowed",
        ),
        sa.ForeignKeyConstraint(
            ["utilisateur_id"],
            ["utilisateurs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("utilisateur_id"),
    )

    op.create_table(
        "verrous_session_utilisateur",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "session_utilisateur_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "verrouillee_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "deverrouillee_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "tentatives_code_prive",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "derniere_tentative_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "motif",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["session_utilisateur_id"],
            ["sessions_utilisateur.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_utilisateur_id"),
    )

    op.create_table(
        "jetons_securite_utilisateur",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("utilisateur_id", sa.UUID(), nullable=False),
        sa.Column(
            "type_jeton",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "jeton_hash",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "expiration_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "utilise_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "adresse_ip",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "user_agent",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "contexte",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["utilisateur_id"],
            ["utilisateurs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("jeton_hash"),
    )

    op.create_index(
        "ix_security_tokens_user_type",
        "jetons_securite_utilisateur",
        ["utilisateur_id", "type_jeton"],
        unique=False,
    )
    op.create_index(
        "ix_security_tokens_expiration",
        "jetons_securite_utilisateur",
        ["expiration_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_security_tokens_expiration",
        table_name="jetons_securite_utilisateur",
    )
    op.drop_index(
        "ix_security_tokens_user_type",
        table_name="jetons_securite_utilisateur",
    )
    op.drop_table("jetons_securite_utilisateur")
    op.drop_table("verrous_session_utilisateur")
    op.drop_table("securite_compte_utilisateur")
    op.drop_table("preferences_utilisateur")
