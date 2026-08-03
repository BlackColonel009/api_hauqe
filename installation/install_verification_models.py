from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent


FILES = {

    # ============================================================
    # 31. DOSSIERS DE VERIFICATION
    # ============================================================

    "app/models/dossier_verification.py": r'''
from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class DossierVerification(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "dossiers_verification"

    fiche_collecte_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("fiches_collecte.id"),
        nullable=False,
    )

    date_ouverture: Mapped[date | None] = mapped_column(
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

    avis: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    synthese: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    niveau_risque: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    priorite: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    fiche_collecte = relationship(
        "FicheCollecte",
        foreign_keys=[fiche_collecte_id],
    )

    affectations: Mapped[list["AffectationVerification"]] = relationship(
        "AffectationVerification",
        back_populates="dossier_verification",
    )

    points: Mapped[list["PointVerification"]] = relationship(
        "PointVerification",
        back_populates="dossier_verification",
    )

    anomalies: Mapped[list["AnomalieVerification"]] = relationship(
        "AnomalieVerification",
        back_populates="dossier_verification",
    )

    confirmations_externes: Mapped[list["ConfirmationExterne"]] = relationship(
        "ConfirmationExterne",
        back_populates="dossier_verification",
    )
''',

    # ============================================================
    # 32. AFFECTATIONS VERIFICATION
    # ============================================================

    "app/models/affectation_verification.py": r'''
from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class AffectationVerification(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "affectations_verification"

    dossier_verification_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("dossiers_verification.id"),
        nullable=False,
    )

    verificateur_id: Mapped[UUID] = mapped_column(
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

    date_echeance: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    motif: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    dossier_verification = relationship(
        "DossierVerification",
        back_populates="affectations",
    )

    verificateur = relationship(
        "Utilisateur",
        foreign_keys=[verificateur_id],
    )
''',

    # ============================================================
    # 33. POINTS DE VERIFICATION
    # ============================================================

    "app/models/point_verification.py": r'''
from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class PointVerification(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "points_verification"

    dossier_verification_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("dossiers_verification.id"),
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

    categorie: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    resultat: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    observation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    date_verification: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    preuve_document_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=True,
    )

    verifie_par_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    dossier_verification = relationship(
        "DossierVerification",
        back_populates="points",
    )

    preuve_document = relationship(
        "Document",
        foreign_keys=[preuve_document_id],
    )

    verifie_par = relationship(
        "Utilisateur",
        foreign_keys=[verifie_par_id],
    )

    anomalies: Mapped[list["AnomalieVerification"]] = relationship(
        "AnomalieVerification",
        back_populates="point_verification",
    )
''',

    # ============================================================
    # 34. ANOMALIES DE VERIFICATION
    # ============================================================

    "app/models/anomalie_verification.py": r'''
from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class AnomalieVerification(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "anomalies_verification"

    dossier_verification_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("dossiers_verification.id"),
        nullable=False,
    )

    point_verification_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("points_verification.id"),
        nullable=True,
    )

    categorie: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    gravite: Mapped[str | None] = mapped_column(
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

    resolution: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    date_resolution: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    escalade: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    dossier_verification = relationship(
        "DossierVerification",
        back_populates="anomalies",
    )

    point_verification = relationship(
        "PointVerification",
        back_populates="anomalies",
    )
''',

    # ============================================================
    # 35. CONFIRMATIONS EXTERNES
    # ============================================================

    "app/models/confirmation_externe.py": r'''
from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class ConfirmationExterne(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "confirmations_externes"

    dossier_verification_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("dossiers_verification.id"),
        nullable=False,
    )

    organisme_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organismes.id"),
        nullable=True,
    )

    canal: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    destinataire: Mapped[str | None] = mapped_column(
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

    contenu_reponse: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    resultat: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    document_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    dossier_verification = relationship(
        "DossierVerification",
        back_populates="confirmations_externes",
    )

    organisme = relationship(
        "Organisme",
        foreign_keys=[organisme_id],
    )

    document = relationship(
        "Document",
        foreign_keys=[document_id],
    )
''',
}


NEW_IMPORTS = '''
from app.models.affectation_verification import AffectationVerification
from app.models.anomalie_verification import AnomalieVerification
from app.models.confirmation_externe import ConfirmationExterne
from app.models.dossier_verification import DossierVerification
from app.models.point_verification import PointVerification
'''


def write_file(relative_path: str, content: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        dedent(content).lstrip(),
        encoding="utf-8",
    )

    print(f"[OK] {relative_path}")


def update_models_init() -> None:
    """
    Ajoute les nouveaux imports sans écraser les imports
    des blocs précédents.
    """

    init_path = ROOT / "app/models/__init__.py"

    if not init_path.exists():
        init_path.write_text("", encoding="utf-8")

    current = init_path.read_text(encoding="utf-8")

    imports = [
        "from app.models.affectation_verification import AffectationVerification",
        "from app.models.anomalie_verification import AnomalieVerification",
        "from app.models.confirmation_externe import ConfirmationExterne",
        "from app.models.dossier_verification import DossierVerification",
        "from app.models.point_verification import PointVerification",
    ]

    missing = [
        item
        for item in imports
        if item not in current
    ]

    if missing:
        current = current.rstrip() + "\n\n" + "\n".join(missing) + "\n"
        init_path.write_text(current, encoding="utf-8")

    print("[OK] app/models/__init__.py")


def main() -> None:

    print("=" * 72)
    print("HAUQE CERTIF — MODELES VERIFICATION")
    print("=" * 72)

    required = [
        ROOT / "app/models/common.py",
        ROOT / "app/models/fiche_collecte.py",
        ROOT / "app/models/utilisateur.py",
        ROOT / "app/models/document.py",
        ROOT / "app/models/organisme.py",
    ]

    for path in required:
        if not path.exists():
            raise SystemExit(
                f"ERREUR : fichier requis absent : {path}"
            )

    for relative_path, content in FILES.items():
        write_file(relative_path, content)

    update_models_init()

    print()
    print("Modèles ajoutés :")
    print("- dossiers_verification")
    print("- affectations_verification")
    print("- points_verification")
    print("- anomalies_verification")
    print("- confirmations_externes")
    print()
    print("Aucune migration Alembic générée.")
    print("Aucune table PostgreSQL modifiée.")


if __name__ == "__main__":
    main()