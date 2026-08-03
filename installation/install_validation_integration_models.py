from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent


FILES = {

    # ============================================================
    # 42. VALIDATIONS
    # ============================================================

    "app/models/validation.py": r'''
from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Validation(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "validations"

    fiche_collecte_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("fiches_collecte.id"),
        nullable=False,
    )

    controle_fuccs_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("controles_fuccs.id"),
        nullable=True,
    )

    niveau_validation: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    validateur_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    decision: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    date_validation: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Le MPD actuel définit reserves en VARCHAR(255)
    reserves: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    justification: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    fiche_collecte = relationship(
        "FicheCollecte",
        foreign_keys=[fiche_collecte_id],
    )

    controle_fuccs = relationship(
        "ControleFuccs",
        foreign_keys=[controle_fuccs_id],
    )

    validateur = relationship(
        "Utilisateur",
        foreign_keys=[validateur_id],
    )

    corrections: Mapped[list["Correction"]] = relationship(
        "Correction",
        back_populates="validation",
    )

    integrations_bnec: Mapped[list["IntegrationBnec"]] = relationship(
        "IntegrationBnec",
        back_populates="validation",
    )
''',

    # ============================================================
    # 43. CORRECTIONS
    # ============================================================

    "app/models/correction.py": r'''
from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Correction(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "corrections"

    validation_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("validations.id"),
        nullable=False,
    )

    motif: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    instructions: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    date_demande: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_echeance: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_resoumission: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    reponse: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    validation = relationship(
        "Validation",
        back_populates="corrections",
    )
''',

    # ============================================================
    # 44. INTEGRATIONS BNEC
    # ============================================================

    "app/models/integration_bnec.py": r'''
from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class IntegrationBnec(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "integrations_bnec"

    validation_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("validations.id"),
        nullable=False,
    )

    administrateur_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    date_debut: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_fin: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    precontrole: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    postcontrole: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    sauvegarde_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    resume: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    validation = relationship(
        "Validation",
        back_populates="integrations_bnec",
    )

    administrateur = relationship(
        "Utilisateur",
        foreign_keys=[administrateur_id],
    )

    elements: Mapped[list["ElementIntegration"]] = relationship(
        "ElementIntegration",
        back_populates="integration_bnec",
    )
''',

    # ============================================================
    # 45. ELEMENTS D'INTEGRATION
    # ============================================================

    "app/models/element_integration.py": r'''
from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class ElementIntegration(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "elements_integration"

    integration_bnec_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("integrations_bnec.id"),
        nullable=False,
    )

    type_objet: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # UUID générique volontairement sans FK dans le MPD
    ressource_source_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )

    # UUID générique volontairement sans FK dans le MPD
    ressource_cible_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )

    revision_source: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    action: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    code_genere: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    message_erreur: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    integration_bnec = relationship(
        "IntegrationBnec",
        back_populates="elements",
    )
''',
}


IMPORTS = [
    "from app.models.correction import Correction",
    "from app.models.element_integration import ElementIntegration",
    "from app.models.integration_bnec import IntegrationBnec",
    "from app.models.validation import Validation",
]


def write_file(relative_path: str, content: str) -> None:
    path = ROOT / relative_path

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        dedent(content).lstrip(),
        encoding="utf-8",
    )

    print(f"[OK] {relative_path}")


def update_models_init() -> None:
    """
    Ajoute les imports du bloc sans écraser
    les modèles déjà installés.
    """

    init_path = ROOT / "app/models/__init__.py"

    if not init_path.exists():
        init_path.write_text(
            "",
            encoding="utf-8",
        )

    current = init_path.read_text(
        encoding="utf-8",
    )

    missing = [
        line
        for line in IMPORTS
        if line not in current
    ]

    if missing:
        current = (
            current.rstrip()
            + "\n\n"
            + "\n".join(missing)
            + "\n"
        )

        init_path.write_text(
            current,
            encoding="utf-8",
        )

    print("[OK] app/models/__init__.py")


def verify_previous_blocks() -> None:

    required = [
        "app/models/common.py",
        "app/models/fiche_collecte.py",
        "app/models/controle_fuccs.py",
        "app/models/utilisateur.py",
    ]

    for relative_path in required:

        path = ROOT / relative_path

        if not path.exists():
            raise SystemExit(
                f"ERREUR : fichier requis absent : "
                f"{relative_path}"
            )


def main() -> None:

    print("=" * 72)
    print("HAUQE CERTIF — VALIDATION ET INTEGRATION BNEC")
    print("=" * 72)

    if not (ROOT / "app").exists():
        raise SystemExit(
            "ERREUR : dossier app/ introuvable."
        )

    verify_previous_blocks()

    for relative_path, content in FILES.items():
        write_file(
            relative_path,
            content,
        )

    update_models_init()

    print()
    print("=" * 72)
    print("BLOC VALIDATION / INTEGRATION CREE")
    print("=" * 72)

    print(
        """
Tables ajoutées :

- validations
- corrections
- integrations_bnec
- elements_integration

Aucune migration Alembic générée.
Aucune modification PostgreSQL effectuée.
"""
    )


if __name__ == "__main__":
    main()