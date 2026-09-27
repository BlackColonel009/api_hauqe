"""Lie explicitement une certification déclarée à son organisme."""

from alembic import op
import sqlalchemy as sa


revision = "g2c8d4e1f509"
down_revision = "e1b7c4d9a206"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("certifications_declarees", sa.Column("organisme_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_certifications_declarees_organisme",
        "certifications_declarees", "organismes", ["organisme_id"], ["id"],
    )
    op.create_index("ix_certifications_declarees_organisme_id", "certifications_declarees", ["organisme_id"])


def downgrade() -> None:
    op.drop_index("ix_certifications_declarees_organisme_id", table_name="certifications_declarees")
    op.drop_constraint("fk_certifications_declarees_organisme", "certifications_declarees", type_="foreignkey")
    op.drop_column("certifications_declarees", "organisme_id")
