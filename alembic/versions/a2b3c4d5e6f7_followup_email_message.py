"""Ajoute l'adresse e-mail et le message aux relances de veille."""

from alembic import op
import sqlalchemy as sa

revision = "a2b3c4d5e6f7"
down_revision = "f4c7d8e9a012"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "relances_veille",
        sa.Column("adresse_email", sa.String(length=320), nullable=True),
    )
    op.add_column(
        "relances_veille",
        sa.Column("contenu", sa.Text(), nullable=True),
    )


def downgrade():
    op.drop_column("relances_veille", "contenu")
    op.drop_column("relances_veille", "adresse_email")
