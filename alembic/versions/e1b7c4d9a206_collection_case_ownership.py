"""Dossiers de collecte par entreprise et responsable stable."""

from alembic import op
import sqlalchemy as sa


revision = "e1b7c4d9a206"
down_revision = "b4c8d1e2f3a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("fiches_collecte", sa.Column("dossier_id", sa.UUID(), nullable=True))
    op.add_column("fiches_collecte", sa.Column("responsable_id", sa.UUID(), nullable=True))
    op.execute("UPDATE fiches_collecte SET dossier_id = id, responsable_id = collecte_par_id")
    # Les doublons historiques d'une même entreprise dans une même mission ne
    # sont pas supprimés : ils deviennent des révisions du dossier le plus
    # ancien. Cela permet ensuite de garantir une seule fiche racine.
    op.execute("""
        WITH groupes AS (
            SELECT id,
                   first_value(id) OVER (
                       PARTITION BY mission_id, entreprise_id
                       ORDER BY created_at, id
                   ) AS dossier_racine,
                   row_number() OVER (
                       PARTITION BY mission_id, entreprise_id
                       ORDER BY created_at, id
                   ) AS position
            FROM fiches_collecte
            WHERE entreprise_id IS NOT NULL
        )
        UPDATE fiches_collecte AS fiche
        SET dossier_id = groupes.dossier_racine
        FROM groupes
        WHERE fiche.id = groupes.id AND groupes.position > 1
    """)
    op.alter_column("fiches_collecte", "responsable_id", nullable=False)
    op.create_foreign_key("fk_fiches_collecte_dossier", "fiches_collecte", "fiches_collecte", ["dossier_id"], ["id"])
    op.create_foreign_key("fk_fiches_collecte_responsable", "fiches_collecte", "utilisateurs", ["responsable_id"], ["id"])
    op.create_index("ix_fiches_collecte_mission_dossier", "fiches_collecte", ["mission_id", "dossier_id"])
    op.execute("CREATE UNIQUE INDEX uq_fiches_collecte_mission_entreprise_root ON fiches_collecte (mission_id, entreprise_id) WHERE entreprise_id IS NOT NULL AND dossier_id = id")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_fiches_collecte_mission_entreprise_root")
    op.drop_index("ix_fiches_collecte_mission_dossier", table_name="fiches_collecte")
    op.drop_constraint("fk_fiches_collecte_responsable", "fiches_collecte", type_="foreignkey")
    op.drop_constraint("fk_fiches_collecte_dossier", "fiches_collecte", type_="foreignkey")
    op.drop_column("fiches_collecte", "responsable_id")
    op.drop_column("fiches_collecte", "dossier_id")
