"""Étend les situations déclarées des certifications collectées."""

from alembic import op


revision = "c4d5e6f7a8b9"
down_revision = "b3c4d5e6f7a8"
branch_labels = None
depends_on = None


CONSTRAINT_NAME = "ck_certifications_declarees_situation"


def _replace_constraint(values: str) -> None:
    op.execute(
        f"""
        ALTER TABLE certifications_declarees
        DROP CONSTRAINT IF EXISTS {CONSTRAINT_NAME}
        """
    )
    op.execute(
        f"""
        ALTER TABLE certifications_declarees
        ADD CONSTRAINT {CONSTRAINT_NAME}
        CHECK (
            situation_declaree IS NULL
            OR situation_declaree IN ({values})
        )
        """
    )


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE certifications_declarees
        ADD COLUMN IF NOT EXISTS situation_declaree VARCHAR(255)
        """
    )
    _replace_constraint(
        "'PRESENTE','ABSENTE','AUDIT_SURVEILLANCE_1',"
        "'AUDIT_SURVEILLANCE_2','AUDIT_SURVEILLANCE_3',"
        "'RENOUVELLEMENT','EXPIREE','AUDIT_INITIAL'"
    )


def downgrade() -> None:
    _replace_constraint(
        "'PRESENTE','ABSENTE','AUDIT_SURVEILLANCE_1',"
        "'AUDIT_SURVEILLANCE_2','AUDIT_SURVEILLANCE_3','RENOUVELLEMENT'"
    )
