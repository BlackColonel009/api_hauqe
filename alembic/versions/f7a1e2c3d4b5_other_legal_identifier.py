"""Ajoute un identifiant juridique complémentaire aux entreprises."""

from alembic import op
import sqlalchemy as sa


revision = "f7a1e2c3d4b5"
down_revision = "d9f2a7c4e318"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "entreprises",
        sa.Column(
            "autre_identifiant_juridique",
            sa.String(length=255),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("entreprises", "autre_identifiant_juridique")
