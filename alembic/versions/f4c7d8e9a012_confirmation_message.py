"""Ajoute le contenu du message aux confirmations externes."""

from alembic import op
import sqlalchemy as sa

revision = "f4c7d8e9a012"
down_revision = "e1f0a2b3c4d5"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "confirmations_externes",
        sa.Column("contenu_demande", sa.Text(), nullable=True),
    )


def downgrade():
    op.drop_column("confirmations_externes", "contenu_demande")
