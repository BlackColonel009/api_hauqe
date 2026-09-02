"""Empêche les doublons d'entreprises par raison sociale normalisée.

Revision ID: d9f2a7c4e318
Revises: c8f6a0b3d425
"""

from alembic import op


revision = "d9f2a7c4e318"
down_revision = "c8f6a0b3d425"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ne pas masquer un historique incohérent : l'administrateur doit traiter
    # les doublons préexistants avant d'activer la garantie d'unicité.
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (
            SELECT 1
            FROM entreprises
            WHERE raison_sociale IS NOT NULL
              AND btrim(raison_sociale) <> ''
            GROUP BY lower(
              regexp_replace(
                btrim(raison_sociale),
                '[[:space:][:punct:]]+',
                '',
                'g'
              )
            )
            HAVING count(*) > 1
          ) THEN
            RAISE EXCEPTION
              'Doublons de raisons sociales existants : corrigez-les avant la migration d9f2a7c4e318.';
          END IF;
        END $$;
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_entreprises_raison_sociale_normalisee
        ON entreprises (
          lower(
            regexp_replace(
              btrim(raison_sociale),
              '[[:space:][:punct:]]+',
              '',
              'g'
            )
          )
        )
        WHERE raison_sociale IS NOT NULL
          AND btrim(raison_sociale) <> '';
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_entreprises_raison_sociale_normalisee")
