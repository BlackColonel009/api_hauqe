"""Conserver le motif de clôture des échéances.

Revision ID: e1f0a2b3c4d5
Revises: d8e9f4a7c210
"""

from alembic import op
import sqlalchemy as sa


revision = "e1f0a2b3c4d5"
down_revision = "d8e9f4a7c210"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("echeances", sa.Column("motif_cloture", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("echeances", "motif_cloture")
