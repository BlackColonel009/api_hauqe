"""Ajoute les préférences d'actualisation automatique par utilisateur."""

from alembic import op
import sqlalchemy as sa


revision = "b3c4d5e6f7a8"
down_revision = "a2b3c4d5e6f7"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "preferences_utilisateur",
        sa.Column(
            "actualisation_automatique_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
    )
    op.add_column(
        "preferences_utilisateur",
        sa.Column(
            "actualisation_intervalle_secondes",
            sa.Integer(),
            server_default=sa.text("30"),
            nullable=False,
        ),
    )
    op.add_column(
        "preferences_utilisateur",
        sa.Column(
            "actualisation_au_retour",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
    )


def downgrade():
    op.drop_column(
        "preferences_utilisateur",
        "actualisation_au_retour",
    )
    op.drop_column(
        "preferences_utilisateur",
        "actualisation_intervalle_secondes",
    )
    op.drop_column(
        "preferences_utilisateur",
        "actualisation_automatique_active",
    )
