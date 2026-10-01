"""Lier les courriels programmés à leur relance de veille.

Revision ID: k6a0c4e8f2b3
Revises: j5f9b3d7e1a2
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "k6a0c4e8f2b3"
down_revision = "j5f9b3d7e1a2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("notifications", sa.Column("relance_veille_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_notifications_relance_veille", "notifications", "relances_veille", ["relance_veille_id"], ["id"])
    op.create_index("ix_notifications_relance_veille_id", "notifications", ["relance_veille_id"])
    # Rattacher uniquement les anciens messages dont le rapprochement est
    # unique (contenu, destinataire et proximité de création identiques).
    op.execute("""
        UPDATE notifications AS n
        SET relance_veille_id = r.id
        FROM relances_veille AS r
        WHERE n.relance_veille_id IS NULL
          AND n.canal = 'EMAIL'
          AND n.destinataire_utilisateur_id IS NULL
          AND n.adresse_externe = r.adresse_email
          AND n.objet = r.objet
          AND n.contenu = r.contenu
          AND n.created_at BETWEEN r.created_at - INTERVAL '5 minutes'
                               AND r.created_at + INTERVAL '5 minutes'
          AND (SELECT count(*) FROM relances_veille AS candidate
               WHERE candidate.adresse_email = n.adresse_externe
                 AND candidate.objet = n.objet
                 AND candidate.contenu = n.contenu
                 AND n.created_at BETWEEN candidate.created_at - INTERVAL '5 minutes'
                                      AND candidate.created_at + INTERVAL '5 minutes') = 1
    """)


def downgrade() -> None:
    op.drop_index("ix_notifications_relance_veille_id", table_name="notifications")
    op.drop_constraint("fk_notifications_relance_veille", "notifications", type_="foreignkey")
    op.drop_column("notifications", "relance_veille_id")
