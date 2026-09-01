"""Ajoute la politique et le journal des rappels d'échéance."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "a6d4e8f1b203"
down_revision = "c4d5e6f7a8b9"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "echeances",
        sa.Column(
            "rappels_email_actifs",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.add_column(
        "echeances",
        sa.Column(
            "rappel_jours_avant",
            sa.Integer(),
            nullable=False,
            server_default="2",
        ),
    )
    op.add_column(
        "echeances",
        sa.Column(
            "escalade_administrateurs_jour_j",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.create_table(
        "rappels_echeances",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("echeance_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "destinataire_utilisateur_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("notification_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("type_rappel", sa.String(length=64), nullable=False),
        sa.Column("date_rappel", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["echeance_id"], ["echeances.id"]),
        sa.ForeignKeyConstraint(["destinataire_utilisateur_id"], ["utilisateurs.id"]),
        sa.ForeignKeyConstraint(["notification_id"], ["notifications.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "echeance_id",
            "destinataire_utilisateur_id",
            "type_rappel",
            "date_rappel",
            name="uq_rappel_echeance_destinataire_type_date",
        ),
    )


def downgrade():
    op.drop_table("rappels_echeances")
    op.drop_column("echeances", "escalade_administrateurs_jour_j")
    op.drop_column("echeances", "rappel_jours_avant")
    op.drop_column("echeances", "rappels_email_actifs")
