from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent


FILES = {

    # ============================================================
    # 57. REGLES METIER
    # ============================================================

    "app/models/regle_metier.py": r'''
from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class RegleMetier(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "regles_metier"

    code: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    famille: Mapped[str | None] = mapped_column(
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

    version: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    parametres: Mapped[
        dict[str, Any] | list[Any] | None
    ] = mapped_column(
        JSONB,
        nullable=True,
    )

    date_debut_effet: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_fin_effet: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    reference_approbation: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    approuve_par_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    approuve_par = relationship(
        "Utilisateur",
        foreign_keys=[approuve_par_id],
    )
''',

    # ============================================================
    # 58. REVUES QUALITE
    # ============================================================

    "app/models/revue_qualite.py": r'''
from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class RevueQualite(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "revues_qualite"

    # MPD actuel : VARCHAR(255), pas DATE.
    periode_debut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    periode_fin: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    perimetre: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    resultat_global: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    constats: Mapped[
        dict[str, Any] | list[Any] | None
    ] = mapped_column(
        JSONB,
        nullable=True,
    )

    preuves: Mapped[
        dict[str, Any] | list[Any] | None
    ] = mapped_column(
        JSONB,
        nullable=True,
    )

    responsable_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    date_validation: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    responsable = relationship(
        "Utilisateur",
        foreign_keys=[responsable_id],
    )

    plans_action: Mapped[list["PlanAction"]] = relationship(
        "PlanAction",
        back_populates="revue_qualite",
    )
''',

    # ============================================================
    # 59. PLANS D'ACTION
    # ============================================================

    "app/models/plan_action.py": r'''
from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class PlanAction(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "plans_action"

    revue_qualite_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("revues_qualite.id"),
        nullable=True,
    )

    titre: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    objectif: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    responsable_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    date_debut: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_echeance: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    priorite: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    indicateur: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    progression: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    date_cloture: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    revue_qualite = relationship(
        "RevueQualite",
        back_populates="plans_action",
    )

    responsable = relationship(
        "Utilisateur",
        foreign_keys=[responsable_id],
    )
''',

    # ============================================================
    # 60. DECISIONS INSTITUTIONNELLES
    # ============================================================

    "app/models/decision_institutionnelle.py": r'''
from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class DecisionInstitutionnelle(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "decisions_institutionnelles"

    ressource_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Relation polymorphe : pas de FK dans le MPD actuel.
    ressource_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )

    type_decision: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    titre: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    contexte: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    constats: Mapped[
        dict[str, Any] | list[Any] | None
    ] = mapped_column(
        JSONB,
        nullable=True,
    )

    risques: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    options: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    decision: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    recommandation: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    autorite: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    decide_par_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=True,
    )

    date_decision: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    priorite: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    decide_par = relationship(
        "Utilisateur",
        foreign_keys=[decide_par_id],
    )
''',

    # ============================================================
    # 61. PUBLICATIONS
    # ============================================================

    "app/models/publication.py": r'''
from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Publication(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "publications"

    ressource_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Ressource générique : pas de FK physique.
    ressource_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )

    objet: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    perimetre: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    niveau_confidentialite: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    demande_par_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    date_demande: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    decision: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    autorite_approbation: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    approuve_par_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=True,
    )

    date_approbation: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    reserve: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    date_publication: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    demande_par = relationship(
        "Utilisateur",
        foreign_keys=[demande_par_id],
    )

    approuve_par = relationship(
        "Utilisateur",
        foreign_keys=[approuve_par_id],
    )
''',

    # ============================================================
    # 62. RAPPORTS GENERES
    # ============================================================

    "app/models/rapport_genere.py": r'''
from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class RapportGenere(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "rapports_generes"

    code_modele: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    nom_modele: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    categorie: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    demandeur_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    filtres: Mapped[
        dict[str, Any] | list[Any] | None
    ] = mapped_column(
        JSONB,
        nullable=True,
    )

    sections: Mapped[
        dict[str, Any] | list[Any] | None
    ] = mapped_column(
        JSONB,
        nullable=True,
    )

    format: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # MPD actuel : VARCHAR(255).
    periode_debut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    periode_fin: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    date_demande: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_generation: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    document_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=True,
    )

    resultat: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    demandeur = relationship(
        "Utilisateur",
        foreign_keys=[demandeur_id],
    )

    document = relationship(
        "Document",
        foreign_keys=[document_id],
    )
''',

    # ============================================================
    # 64. ARCHIVES
    # ============================================================

    "app/models/archive.py": r'''
from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Archive(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "archives"

    ressource_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Ressource générique : pas de FK.
    ressource_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )

    categorie_donnees: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    date_archivage: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    motif: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    auteur_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    duree_conservation: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    date_suppression_prevue: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    emplacement: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    auteur = relationship(
        "Utilisateur",
        foreign_keys=[auteur_id],
    )
''',

    # ============================================================
    # 65. SAUVEGARDES
    # ============================================================

    "app/models/sauvegarde.py": r'''
from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Sauvegarde(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "sauvegardes"

    type_enregistrement: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    parent_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sauvegardes.id"),
        nullable=True,
    )

    frequence: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    retention: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    perimetre: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    emplacement_stockage: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    date_debut: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_fin: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    taille_octets: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    integrite_validee: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    resultat: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    preuve_document_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=True,
    )

    message_erreur: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    parent: Mapped["Sauvegarde | None"] = relationship(
        "Sauvegarde",
        remote_side="Sauvegarde.id",
        back_populates="enfants",
        foreign_keys=[parent_id],
    )

    enfants: Mapped[list["Sauvegarde"]] = relationship(
        "Sauvegarde",
        back_populates="parent",
        foreign_keys=[parent_id],
    )

    preuve_document = relationship(
        "Document",
        foreign_keys=[preuve_document_id],
    )
''',

    # ============================================================
    # 66. INCIDENTS
    # ============================================================

    "app/models/incident.py": r'''
from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Incident(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "incidents"

    code: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    categorie: Mapped[str | None] = mapped_column(
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

    date_declaration: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    declare_par_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    responsable_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=True,
    )

    ressource_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Ressource générique : pas de FK physique.
    ressource_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )

    preuves: Mapped[
        dict[str, Any] | list[Any] | None
    ] = mapped_column(
        JSONB,
        nullable=True,
    )

    resolution: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    date_resolution: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_cloture: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    declare_par = relationship(
        "Utilisateur",
        foreign_keys=[declare_par_id],
    )

    responsable = relationship(
        "Utilisateur",
        foreign_keys=[responsable_id],
    )
''',
}


IMPORTS = [
    "from app.models.archive import Archive",
    "from app.models.decision_institutionnelle import DecisionInstitutionnelle",
    "from app.models.incident import Incident",
    "from app.models.plan_action import PlanAction",
    "from app.models.publication import Publication",
    "from app.models.rapport_genere import RapportGenere",
    "from app.models.regle_metier import RegleMetier",
    "from app.models.revue_qualite import RevueQualite",
    "from app.models.sauvegarde import Sauvegarde",
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
    Ajoute uniquement les imports du dernier bloc.
    Aucun import existant n'est supprimé.
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
        "app/models/utilisateur.py",
        "app/models/document.py",
        "app/models/audit.py",
        "app/models/rapport_veille.py",
        "app/models/classement_sncc.py",
    ]

    for relative_path in required:

        path = ROOT / relative_path

        if not path.exists():
            raise SystemExit(
                f"ERREUR : fichier requis absent : "
                f"{relative_path}"
            )


def main() -> None:

    print("=" * 74)
    print("HAUQE CERTIF — BLOC FINAL DES MODELES SQLALCHEMY")
    print("=" * 74)

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
    print("=" * 74)
    print("BLOC FINAL CREE")
    print("=" * 74)

    print(
        """
Tables ajoutées :

57 - regles_metier
58 - revues_qualite
59 - plans_action
60 - decisions_institutionnelles
61 - publications
62 - rapports_generes

63 - evenements_audit (déjà présent)

64 - archives
65 - sauvegardes
66 - incidents

Aucune migration Alembic générée.
Aucune modification PostgreSQL effectuée.
"""
    )


if __name__ == "__main__":
    main()