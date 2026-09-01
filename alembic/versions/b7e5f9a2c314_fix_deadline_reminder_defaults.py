"""Corrige les valeurs par défaut techniques du journal des rappels."""

from alembic import op
import sqlalchemy as sa


revision = "b7e5f9a2c314"
down_revision = "a6d4e8f1b203"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "rappels_echeances",
        "id",
        server_default=sa.text("gen_random_uuid()"),
    )
    op.alter_column(
        "rappels_echeances",
        "created_at",
        server_default=sa.text("now()"),
    )
    op.alter_column(
        "rappels_echeances",
        "updated_at",
        server_default=sa.text("now()"),
    )


def downgrade():
    op.alter_column("rappels_echeances", "updated_at", server_default=None)
    op.alter_column("rappels_echeances", "created_at", server_default=None)
    op.alter_column("rappels_echeances", "id", server_default=None)
