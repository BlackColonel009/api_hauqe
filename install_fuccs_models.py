from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent


FILES = {

    # ============================================================
    # 36. GRILLES FUCCS
    # ============================================================

    "app/models/grille_fuccs.py": r'''
from __future__ import annotations

from datetime import date

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class GrilleFuccs(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "grilles_fuccs"

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

    date_effet: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_fin: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    reference_approbation: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    statut_publication: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    rubriques: Mapped[list["RubriqueFuccs"]] = relationship(
        "RubriqueFuccs",
        back_populates="grille_fuccs",
    )

    controles: Mapped[list["ControleFuccs"]] = relationship(
        "ControleFuccs",
        back_populates="grille_fuccs",
    )
''',

    # ============================================================
    # 37. RUBRIQUES FUCCS
    # ============================================================

    "app/models/rubrique_fuccs.py": r'''
from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class RubriqueFuccs(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "rubriques_fuccs"

    grille_fuccs_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("grilles_fuccs.id"),
        nullable=False,
    )

    code: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    libelle: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    ordre_affichage: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    grille_fuccs = relationship(
        "GrilleFuccs",
        back_populates="rubriques",
    )

    criteres: Mapped[list["CritereFuccs"]] = relationship(
        "CritereFuccs",
        back_populates="rubrique_fuccs",
    )
''',

    # ============================================================
    # 38. CRITERES FUCCS
    # ============================================================

    "app/models/critere_fuccs.py": r'''
from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class CritereFuccs(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "criteres_fuccs"

    rubrique_fuccs_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("rubriques_fuccs.id"),
        nullable=False,
    )

    code: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    libelle: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    score_maximal: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    poids: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    ordre_affichage: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    commentaire_obligatoire: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    preuve_obligatoire: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    rubrique_fuccs = relationship(
        "RubriqueFuccs",
        back_populates="criteres",
    )

    notes: Mapped[list["NoteCritere"]] = relationship(
        "NoteCritere",
        back_populates="critere_fuccs",
    )
''',

    # ============================================================
    # 39. CONTROLES FUCCS
    # ============================================================

    "app/models/controle_fuccs.py": r'''
from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class ControleFuccs(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "controles_fuccs"

    dossier_verification_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("dossiers_verification.id"),
        nullable=False,
    )

    grille_fuccs_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("grilles_fuccs.id"),
        nullable=False,
    )

    controleur_id: Mapped[UUID] = mapped_column(
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

    score_brut: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    score_maximal: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    # IMPORTANT :
    # Le MPD actuel définit taux comme VARCHAR(255).
    # On le respecte strictement ici.
    taux: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    synthese: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    dossier_verification = relationship(
        "DossierVerification",
        foreign_keys=[dossier_verification_id],
    )

    grille_fuccs = relationship(
        "GrilleFuccs",
        back_populates="controles",
    )

    controleur = relationship(
        "Utilisateur",
        foreign_keys=[controleur_id],
    )

    notes: Mapped[list["NoteCritere"]] = relationship(
        "NoteCritere",
        back_populates="controle_fuccs",
    )

    constats: Mapped[list["ConstatControle"]] = relationship(
        "ConstatControle",
        back_populates="controle_fuccs",
    )
''',

    # ============================================================
    # 40. NOTES CRITERES
    # ============================================================

    "app/models/note_critere.py": r'''
from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class NoteCritere(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "notes_criteres"

    controle_fuccs_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("controles_fuccs.id"),
        nullable=False,
    )

    critere_fuccs_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("criteres_fuccs.id"),
        nullable=False,
    )

    score: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    commentaire: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    preuve_document_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=True,
    )

    note_par_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    controle_fuccs = relationship(
        "ControleFuccs",
        back_populates="notes",
    )

    critere_fuccs = relationship(
        "CritereFuccs",
        back_populates="notes",
    )

    preuve_document = relationship(
        "Document",
        foreign_keys=[preuve_document_id],
    )

    note_par = relationship(
        "Utilisateur",
        foreign_keys=[note_par_id],
    )
''',

    # ============================================================
    # 41. CONSTATS DE CONTROLE
    # ============================================================

    "app/models/constat_controle.py": r'''
from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class ConstatControle(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "constats_controle"

    controle_fuccs_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("controles_fuccs.id"),
        nullable=False,
    )

    type_constat: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    gravite: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    titre: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    controle_fuccs = relationship(
        "ControleFuccs",
        back_populates="constats",
    )
''',
}


IMPORTS = [
    "from app.models.constat_controle import ConstatControle",
    "from app.models.controle_fuccs import ControleFuccs",
    "from app.models.critere_fuccs import CritereFuccs",
    "from app.models.grille_fuccs import GrilleFuccs",
    "from app.models.note_critere import NoteCritere",
    "from app.models.rubrique_fuccs import RubriqueFuccs",
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
    Ajoute les imports du bloc FUCCS sans supprimer
    ceux des blocs précédents.
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


def verify_previous_block() -> None:
    required = [
        "app/models/common.py",
        "app/models/dossier_verification.py",
        "app/models/utilisateur.py",
        "app/models/document.py",
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
    print("HAUQE CERTIF — MODELES GRILLE DE CONTROLE")
    print("=" * 72)

    if not (ROOT / "app").exists():
        raise SystemExit(
            "ERREUR : dossier app/ introuvable."
        )

    verify_previous_block()

    for relative_path, content in FILES.items():
        write_file(
            relative_path,
            content,
        )

    update_models_init()

    print()
    print("=" * 72)
    print("BLOC GRILLE DE CONTROLE CREE")
    print("=" * 72)

    print(
        """
Tables ajoutées :

- grilles_fuccs
- rubriques_fuccs
- criteres_fuccs
- controles_fuccs
- notes_criteres
- constats_controle

Aucune migration Alembic générée.
Aucune table PostgreSQL modifiée.
Aucun nombre de critères n'a été codé en dur.
"""
    )


if __name__ == "__main__":
    main()