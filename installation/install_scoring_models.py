from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent


FILES = {

    # ============================================================
    # 46. MODELES DE SCORING
    # ============================================================

    "app/models/modele_scoring.py": r'''
from __future__ import annotations

from datetime import date

from sqlalchemy import Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class ModeleScoring(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "modeles_scoring"

    code: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    libelle: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    version: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    objet_evalue: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    date_debut_validite: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_fin_validite: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    regle_calcul: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    reference_approbation: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    ponderations: Mapped[list["PonderationScoring"]] = relationship(
        "PonderationScoring",
        back_populates="modele_scoring",
    )

    classifications_entreprise: Mapped[
        list["ClassificationEntreprise"]
    ] = relationship(
        "ClassificationEntreprise",
        back_populates="modele_scoring",
    )

    resultats_infc: Mapped[list["ResultatInfc"]] = relationship(
        "ResultatInfc",
        back_populates="modele_scoring",
    )
''',

    # ============================================================
    # 47. PONDERATIONS SCORING
    # ============================================================

    "app/models/ponderation_scoring.py": r'''
from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class PonderationScoring(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "ponderations_scoring"

    modele_scoring_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("modeles_scoring.id"),
        nullable=False,
    )

    domaine: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    valeur: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    # IMPORTANT :
    # Le MPD actuel les définit comme VARCHAR(255).
    periode_debut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    periode_fin: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    modele_scoring = relationship(
        "ModeleScoring",
        back_populates="ponderations",
    )
''',

    # ============================================================
    # 48. CLASSIFICATIONS ENTREPRISE
    # ============================================================

    "app/models/classification_entreprise.py": r'''
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class ClassificationEntreprise(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "classifications_entreprise"

    entreprise_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("entreprises.id"),
        nullable=False,
    )

    modele_scoring_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("modeles_scoring.id"),
        nullable=False,
    )

    score: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    classe: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    date_calcul: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_validation: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    sources: Mapped[
        dict[str, Any] | list[Any] | None
    ] = mapped_column(
        JSONB,
        nullable=True,
    )

    valide_par_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    entreprise = relationship(
        "Entreprise",
        foreign_keys=[entreprise_id],
    )

    modele_scoring = relationship(
        "ModeleScoring",
        back_populates="classifications_entreprise",
    )

    valide_par = relationship(
        "Utilisateur",
        foreign_keys=[valide_par_id],
    )
''',

    # ============================================================
    # 49. RESULTATS INFC
    # ============================================================

    "app/models/resultat_infc.py": r'''
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class ResultatInfc(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "resultats_infc"

    certification_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("certifications.id"),
        nullable=False,
    )

    modele_scoring_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("modeles_scoring.id"),
        nullable=False,
    )

    score_global: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    niveau: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    scores_domaines: Mapped[
        dict[str, Any] | list[Any] | None
    ] = mapped_column(
        JSONB,
        nullable=True,
    )

    date_calcul: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_validation: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    sources: Mapped[
        dict[str, Any] | list[Any] | None
    ] = mapped_column(
        JSONB,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    certification = relationship(
        "Certification",
        foreign_keys=[certification_id],
    )

    modele_scoring = relationship(
        "ModeleScoring",
        back_populates="resultats_infc",
    )
''',

    # ============================================================
    # 50. CLASSEMENTS SNCC
    # ============================================================

    "app/models/classement_sncc.py": r'''
from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class ClassementSncc(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "classements_sncc"

    certification_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("certifications.id"),
        nullable=False,
    )

    classe: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    statut_administratif: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    niveau_risque: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    justification: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    date_effet: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_fin: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    valide_par_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    certification = relationship(
        "Certification",
        foreign_keys=[certification_id],
    )

    valide_par = relationship(
        "Utilisateur",
        foreign_keys=[valide_par_id],
    )
''',
}


IMPORTS = [
    "from app.models.classement_sncc import ClassementSncc",
    "from app.models.classification_entreprise import ClassificationEntreprise",
    "from app.models.modele_scoring import ModeleScoring",
    "from app.models.ponderation_scoring import PonderationScoring",
    "from app.models.resultat_infc import ResultatInfc",
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
        "app/models/entreprise.py",
        "app/models/certification.py",
        "app/models/utilisateur.py",
        "app/models/integration_bnec.py",
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
    print("HAUQE CERTIF — SCORING / CLASSIFICATION / INFC / SNCC")
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
    print("BLOC SCORING CREE")
    print("=" * 72)

    print(
        """
Tables ajoutées :

- modeles_scoring
- ponderations_scoring
- classifications_entreprise
- resultats_infc
- classements_sncc

Aucune migration Alembic générée.
Aucune table PostgreSQL modifiée.
"""
    )


if __name__ == "__main__":
    main()