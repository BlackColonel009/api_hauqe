"""Ajoute le plan d'alerte d'expiration propre à chaque certification."""

from alembic import op
from sqlalchemy.dialects import postgresql
import sqlalchemy as sa


revision = "b4c8d1e2f3a6"
down_revision = "f7a1e2c3d4b5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "certifications",
        sa.Column(
            "seuils_alerte_expiration_jours",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("certifications", "seuils_alerte_expiration_jours")
