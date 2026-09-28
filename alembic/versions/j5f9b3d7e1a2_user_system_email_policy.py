"""Réglage administratif des courriels fonctionnels par utilisateur.

Revision ID: j5f9b3d7e1a2
Revises: i4e8a2c6d0b4
"""

import sqlalchemy as sa
from alembic import op

revision = "j5f9b3d7e1a2"
down_revision = "i4e8a2c6d0b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "preferences_utilisateur",
        sa.Column("courriels_systeme_actifs", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_column("preferences_utilisateur", "courriels_systeme_actifs")
