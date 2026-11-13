"""Genre des contacts entreprise, nullable et sans reprise déduite des noms."""
import sqlalchemy as sa
from alembic import op

revision = "l7b1d5f9a304"
down_revision = "k6a0c4e8f2b3"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("contacts_entreprise", sa.Column("genre", sa.String(20), nullable=True))
    op.create_check_constraint("ck_contacts_entreprise_genre", "contacts_entreprise",
                               "genre IS NULL OR genre IN ('FEMME', 'HOMME', 'AUTRE')")

def downgrade():
    op.drop_constraint("ck_contacts_entreprise_genre", "contacts_entreprise", type_="check")
    op.drop_column("contacts_entreprise", "genre")
