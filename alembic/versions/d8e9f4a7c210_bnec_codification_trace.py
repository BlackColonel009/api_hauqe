"""Codification institutionnelle BNEC et traçabilité des codes.

Revision ID: d8e9f4a7c210
Revises: c5b7a8f2d901
Create Date: 2026-07-29
"""

from alembic import op


revision = "d8e9f4a7c210"
down_revision = "c5b7a8f2d901"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Reprend aussi la correction 2.0 afin que la reconstruction Alembic soit
    # complète sur un nouveau serveur. Toutes les instructions sont idempotentes.
    op.execute(
        """
        ALTER TABLE certifications_declarees
        ADD COLUMN IF NOT EXISTS situation_declaree VARCHAR(255)
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
          IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'ck_certifications_declarees_situation'
          ) THEN
            ALTER TABLE certifications_declarees
            ADD CONSTRAINT ck_certifications_declarees_situation
            CHECK (
              situation_declaree IS NULL OR situation_declaree IN (
                'PRESENTE','ABSENTE','AUDIT_SURVEILLANCE_1',
                'AUDIT_SURVEILLANCE_2','AUDIT_SURVEILLANCE_3','RENOUVELLEMENT'
              )
            );
          END IF;
        END $$;
        """
    )

    op.execute(
        """
        ALTER TABLE elements_integration
          ADD COLUMN IF NOT EXISTS codification_regle_id UUID,
          ADD COLUMN IF NOT EXISTS codification_logical_code VARCHAR(255),
          ADD COLUMN IF NOT EXISTS codification_version VARCHAR(100),
          ADD COLUMN IF NOT EXISTS codification_format VARCHAR(255),
          ADD COLUMN IF NOT EXISTS codification_scope_key VARCHAR(500),
          ADD COLUMN IF NOT EXISTS codification_sequence BIGINT,
          ADD COLUMN IF NOT EXISTS codification_segments JSONB
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
          IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'fk_elements_integration_codification_regle'
          ) THEN
            ALTER TABLE elements_integration
            ADD CONSTRAINT fk_elements_integration_codification_regle
            FOREIGN KEY (codification_regle_id)
            REFERENCES regles_metier(id);
          END IF;
        END $$;
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS
          uq_elements_integration_codification_scope_sequence
        ON elements_integration (
          codification_regle_id,
          codification_scope_key,
          codification_sequence
        )
        WHERE codification_regle_id IS NOT NULL
          AND codification_scope_key IS NOT NULL
          AND codification_sequence IS NOT NULL
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS
          ix_elements_integration_codification_logical_code
        ON elements_integration (codification_logical_code)
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP INDEX IF EXISTS ix_elements_integration_codification_logical_code"
    )
    op.execute(
        "DROP INDEX IF EXISTS uq_elements_integration_codification_scope_sequence"
    )
    op.execute(
        """
        ALTER TABLE elements_integration
        DROP CONSTRAINT IF EXISTS fk_elements_integration_codification_regle
        """
    )
    op.execute(
        """
        ALTER TABLE elements_integration
          DROP COLUMN IF EXISTS codification_segments,
          DROP COLUMN IF EXISTS codification_sequence,
          DROP COLUMN IF EXISTS codification_scope_key,
          DROP COLUMN IF EXISTS codification_format,
          DROP COLUMN IF EXISTS codification_version,
          DROP COLUMN IF EXISTS codification_logical_code,
          DROP COLUMN IF EXISTS codification_regle_id
        """
    )
    # situation_declaree appartient à la correction 2.0 antérieure : elle n'est
    # volontairement pas supprimée par ce downgrade.
