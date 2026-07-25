from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent


FILES = {

    # ============================================================
    # 51. ECHEANCES
    # ============================================================

    "app/models/echeance.py": r'''
from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Echeance(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "echeances"

    ressource_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Relation générique : volontairement sans FK.
    ressource_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )

    type_echeance: Mapped[str | None] = mapped_column(
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

    date_echeance: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    responsable_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
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

    responsable = relationship(
        "Utilisateur",
        foreign_keys=[responsable_id],
    )

    alertes: Mapped[list["Alerte"]] = relationship(
        "Alerte",
        back_populates="echeance",
    )
''',

    # ============================================================
    # 52. ALERTES
    # ============================================================

    "app/models/alerte.py": r'''
from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Alerte(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "alertes"

    echeance_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("echeances.id"),
        nullable=True,
    )

    type_alerte: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Niveau 1, 2, 3, 4...
    niveau: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    titre: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    ressource_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Relation générique, sans FK dans le MPD.
    ressource_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )

    responsable_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=True,
    )

    date_detection: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_resolution: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    regle_notification: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    echeance = relationship(
        "Echeance",
        back_populates="alertes",
    )

    responsable = relationship(
        "Utilisateur",
        foreign_keys=[responsable_id],
    )

    notifications: Mapped[list["Notification"]] = relationship(
        "Notification",
        back_populates="alerte",
    )
''',

    # ============================================================
    # 53. NOTIFICATIONS
    # ============================================================

    "app/models/notification.py": r'''
from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Notification(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "notifications"

    alerte_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("alertes.id"),
        nullable=True,
    )

    destinataire_utilisateur_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=True,
    )

    adresse_externe: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    canal: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    objet: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    contenu: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Conservé en DATE car c'est le type du MPD actuel.
    date_envoi: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_lecture: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    resultat: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    nombre_tentatives: Mapped[int | None] = mapped_column(
        Integer,
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

    alerte = relationship(
        "Alerte",
        back_populates="notifications",
    )

    destinataire_utilisateur = relationship(
        "Utilisateur",
        foreign_keys=[destinataire_utilisateur_id],
    )
''',

    # ============================================================
    # 54. DOSSIERS DE VEILLE
    # ============================================================

    "app/models/dossier_veille.py": r'''
from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class DossierVeille(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "dossiers_veille"

    certification_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("certifications.id"),
        nullable=False,
    )

    type_evenement: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    priorite: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    date_ouverture: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    responsable_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    prochaine_action_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
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

    certification = relationship(
        "Certification",
        foreign_keys=[certification_id],
    )

    responsable = relationship(
        "Utilisateur",
        foreign_keys=[responsable_id],
    )

    relances: Mapped[list["RelanceVeille"]] = relationship(
        "RelanceVeille",
        back_populates="dossier_veille",
    )
''',

    # ============================================================
    # 55. RELANCES DE VEILLE
    # ============================================================

    "app/models/relance_veille.py": r'''
from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class RelanceVeille(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "relances_veille"

    dossier_veille_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("dossiers_veille.id"),
        nullable=False,
    )

    destinataire: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    canal: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    objet: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    date_envoi: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_echeance: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_reponse: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    reponse: Mapped[str | None] = mapped_column(
        Text,
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

    dossier_veille = relationship(
        "DossierVeille",
        back_populates="relances",
    )
''',

    # ============================================================
    # 56. RAPPORTS DE VEILLE
    # ============================================================

    "app/models/rapport_veille.py": r'''
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


class RapportVeille(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "rapports_veille"

    type_rapport: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # IMPORTANT :
    # le MPD actuel utilise VARCHAR(255), pas DATE.
    periode_debut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    periode_fin: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    nombre_certifications_suivies: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    nombre_alertes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    nombre_renouvellements: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    delai_moyen_traitement: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    indicateurs: Mapped[
        dict[str, Any] | list[Any] | None
    ] = mapped_column(
        JSONB,
        nullable=True,
    )

    prepare_par_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    valide_par_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=True,
    )

    date_validation: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    prepare_par = relationship(
        "Utilisateur",
        foreign_keys=[prepare_par_id],
    )

    valide_par = relationship(
        "Utilisateur",
        foreign_keys=[valide_par_id],
    )
''',
}


IMPORTS = [
    "from app.models.alerte import Alerte",
    "from app.models.dossier_veille import DossierVeille",
    "from app.models.echeance import Echeance",
    "from app.models.notification import Notification",
    "from app.models.rapport_veille import RapportVeille",
    "from app.models.relance_veille import RelanceVeille",
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
    Ajoute les imports sans supprimer ceux
    des blocs 1 à 9.
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
        "app/models/certification.py",
        "app/models/classement_sncc.py",
        "app/models/resultat_infc.py",
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
    print("HAUQE CERTIF — ECHEANCES / ALERTES / VEILLE")
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
    print("BLOC ECHEANCES / ALERTES / VEILLE CREE")
    print("=" * 72)

    print(
        """
Tables ajoutées :

- echeances
- alertes
- notifications
- dossiers_veille
- relances_veille
- rapports_veille

Aucune migration Alembic générée.
Aucune table PostgreSQL modifiée.
"""
    )


if __name__ == "__main__":
    main()