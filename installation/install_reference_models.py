from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent


FILES = {

    # ============================================================
    # REFERENTIEL + VALEURS
    # ============================================================

    "app/models/referentiel.py": r'''
from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Referentiel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "referentiels"

    code: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    libelle: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    type_valeur: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    valeurs: Mapped[list["ValeurReferentiel"]] = relationship(
        "ValeurReferentiel",
        back_populates="referentiel",
        foreign_keys="ValeurReferentiel.referentiel_id",
    )


class ValeurReferentiel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "valeurs_referentiel"

    referentiel_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("referentiels.id"),
        nullable=False,
    )

    parent_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("valeurs_referentiel.id"),
        nullable=True,
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

    date_debut_validite: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_fin_validite: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    referentiel: Mapped["Referentiel"] = relationship(
        "Referentiel",
        back_populates="valeurs",
        foreign_keys=[referentiel_id],
    )

    parent: Mapped["ValeurReferentiel | None"] = relationship(
        "ValeurReferentiel",
        remote_side="ValeurReferentiel.id",
        back_populates="enfants",
        foreign_keys=[parent_id],
    )

    enfants: Mapped[list["ValeurReferentiel"]] = relationship(
        "ValeurReferentiel",
        back_populates="parent",
        foreign_keys=[parent_id],
    )
''',

    # ============================================================
    # NORMES
    # ============================================================

    "app/models/norme.py": r'''
from __future__ import annotations

from datetime import date

from sqlalchemy import Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Norme(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "normes"

    code: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    nom: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    version: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    autorite_emettrice: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    domaine: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    portee: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    date_debut_application: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_fin_application: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_expiration: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
''',

    # ============================================================
    # __INIT__ COMPLET BLOCS 1 + 2
    # ============================================================

    "app/models/__init__.py": r'''
from app.models.audit import EvenementAudit
from app.models.norme import Norme
from app.models.permission import Permission
from app.models.referentiel import Referentiel, ValeurReferentiel
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.session_utilisateur import SessionUtilisateur
from app.models.utilisateur import Utilisateur
from app.models.utilisateur_role import UtilisateurRole
from app.models.zone_administrative import ZoneAdministrative


__all__ = [
    "EvenementAudit",
    "Norme",
    "Permission",
    "Referentiel",
    "Role",
    "RolePermission",
    "SessionUtilisateur",
    "Utilisateur",
    "UtilisateurRole",
    "ValeurReferentiel",
    "ZoneAdministrative",
]
''',
}


def write_file(relative_path: str, content: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        dedent(content).lstrip(),
        encoding="utf-8",
    )

    print(f"[OK] {relative_path}")


def main() -> None:

    print("=" * 70)
    print("HAUQE CERTIF — MODELES REFERENTIELS")
    print("=" * 70)

    if not (ROOT / "app").exists():
        raise SystemExit(
            "ERREUR : dossier app/ introuvable."
        )

    required = [
        ROOT / "app/models/common.py",
        ROOT / "app/models/zone_administrative.py",
    ]

    for path in required:
        if not path.exists():
            raise SystemExit(
                f"ERREUR : fichier requis absent : {path}"
            )

    for relative_path, content in FILES.items():
        write_file(relative_path, content)

    print()
    print("Modèles créés :")
    print("- referentiels")
    print("- valeurs_referentiel")
    print("- normes")
    print()
    print("Aucune migration exécutée.")
    print("Aucune table PostgreSQL modifiée.")


if __name__ == "__main__":
    main()