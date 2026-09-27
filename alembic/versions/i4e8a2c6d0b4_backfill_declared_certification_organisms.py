"""Rapproche les organismes des certifications déclarées historiques.

Revision ID: i4e8a2c6d0b4
Revises: h3d9e4f1a607
"""

from alembic import op


revision = "i4e8a2c6d0b4"
down_revision = "h3d9e4f1a607"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Une saisie de collecte historique peut contenir le libellé de
    # l'organisme sans sa clé de registre. Si aucun organisme n'existe sous ce
    # nom, nous le précréons en « À vérifier », sans inventer d'accréditation
    # ni d'information réglementaire, puis relions les certifications.
    op.execute(
        """
        INSERT INTO organismes (id, nom_officiel, type_organisme, statut)
        SELECT gen_random_uuid(), labels.libelle, 'CERTIFICATION', 'A_VERIFIER'
        FROM (
            SELECT DISTINCT btrim(organisme_declare) AS libelle
            FROM certifications_declarees
            WHERE organisme_id IS NULL
              AND nullif(btrim(organisme_declare), '') IS NOT NULL
        ) AS labels
        WHERE NOT EXISTS (
            SELECT 1
            FROM organismes AS organisme
            WHERE lower(btrim(coalesce(organisme.nom_officiel, '')))
                      = lower(labels.libelle)
               OR lower(btrim(coalesce(organisme.sigle, '')))
                      = lower(labels.libelle)
        )
        """
    )
    # Le comptage garantit qu'un éventuel registre déjà ambigu n'est jamais
    # choisi arbitrairement : ce cas reste à traiter par l'administrateur.
    op.execute(
        """
        UPDATE certifications_declarees AS certification
        SET organisme_id = (
                SELECT organisme.id
                FROM organismes AS organisme
                WHERE lower(btrim(coalesce(organisme.nom_officiel, '')))
                          = lower(btrim(certification.organisme_declare))
                   OR lower(btrim(coalesce(organisme.sigle, '')))
                          = lower(btrim(certification.organisme_declare))
                ORDER BY organisme.updated_at DESC
                LIMIT 1
            ),
            updated_at = now()
        WHERE certification.organisme_id IS NULL
          AND nullif(btrim(certification.organisme_declare), '') IS NOT NULL
          AND 1 = (
                SELECT count(*)
                FROM organismes AS organisme
                WHERE lower(btrim(coalesce(organisme.nom_officiel, '')))
                          = lower(btrim(certification.organisme_declare))
                   OR lower(btrim(coalesce(organisme.sigle, '')))
                          = lower(btrim(certification.organisme_declare))
            )
        """
    )


def downgrade() -> None:
    # Ne pas supprimer de données métier ni délier les historiques.
    pass
