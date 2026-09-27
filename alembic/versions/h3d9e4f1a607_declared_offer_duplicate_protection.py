"""Protège les offres déclarées contre les doublons d'une même collecte."""

from alembic import op


revision = "h3d9e4f1a607"
down_revision = "g2c8d4e1f509"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Préserver les anciennes lignes dans l'historique, mais n'en laisser
    # qu'une seule active par fiche/type/nom/catégorie avant la contrainte.
    op.execute("""
        WITH classees AS (
            SELECT id,
                   row_number() OVER (
                       PARTITION BY fiche_collecte_id,
                                    upper(trim(coalesce(type_offre, ''))),
                                    upper(trim(nom)),
                                    upper(trim(coalesce(categorie, '')))
                       ORDER BY created_at, id
                   ) AS position
            FROM offres_declarees
            WHERE nullif(trim(nom), '') IS NOT NULL
              AND coalesce(statut, 'ACTIF') <> 'DOUBLON_ANNULE'
        )
        UPDATE offres_declarees AS offre
        SET statut = 'DOUBLON_ANNULE'
        FROM classees
        WHERE offre.id = classees.id
          AND classees.position > 1
    """)
    op.execute("""
        CREATE UNIQUE INDEX uq_offres_declarees_fiche_business_key
        ON offres_declarees (
            fiche_collecte_id,
            upper(trim(coalesce(type_offre, ''))),
            upper(trim(nom)),
            upper(trim(coalesce(categorie, '')))
        )
        WHERE nullif(trim(nom), '') IS NOT NULL
          AND coalesce(statut, 'ACTIF') <> 'DOUBLON_ANNULE'
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_offres_declarees_fiche_business_key")
