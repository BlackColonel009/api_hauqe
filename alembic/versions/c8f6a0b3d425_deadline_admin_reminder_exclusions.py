"""Ajoute les exclusions individuelles d'administrateurs aux rappels."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "c8f6a0b3d425"
down_revision = "b7e5f9a2c314"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "exclusions_rappels_echeances",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("echeance_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("administrateur_id", postgresql.UUID(as_uuid=True), nullable=False),
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
        sa.ForeignKeyConstraint(["echeance_id"], ["echeances.id"]),
        sa.ForeignKeyConstraint(["administrateur_id"], ["utilisateurs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "echeance_id",
            "administrateur_id",
            name="uq_exclusion_rappel_echeance_administrateur",
        ),
    )


def downgrade():
    op.drop_table("exclusions_rappels_echeances")
