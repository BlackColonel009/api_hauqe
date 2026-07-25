from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent


FILES = {

    # ============================================================
    # ENTREPRISE
    # ============================================================

    "app/models/entreprise.py": r'''
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


class Entreprise(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "entreprises"

    identifiant_national: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    raison_sociale: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    nom_commercial: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    forme_juridique: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    rccm: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    nif: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    ifu: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    date_creation: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    nationalite: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    capital_social: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    effectif: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # Conservé dans la base conformément au MPD.
    # Il ne sera simplement pas exposé dans le frontend actuel.
    chiffre_affaires: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    email_principal: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    telephone_principal: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    site_web: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    adresse_siege: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    zone_siege_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("zones_administratives.id"),
        nullable=False,
    )

    activite_principale: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    secteurs_secondaires: Mapped[list[Any] | dict[str, Any] | None] = (
        mapped_column(
            JSONB,
            nullable=True,
        )
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    niveau_risque: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    source_donnee: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    date_derniere_verification: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    zone_siege = relationship(
        "ZoneAdministrative",
        foreign_keys=[zone_siege_id],
    )

    contacts: Mapped[list["ContactEntreprise"]] = relationship(
        "ContactEntreprise",
        back_populates="entreprise",
    )

    sites: Mapped[list["SiteEntreprise"]] = relationship(
        "SiteEntreprise",
        back_populates="entreprise",
    )

    offres: Mapped[list["OffreEntreprise"]] = relationship(
        "OffreEntreprise",
        back_populates="entreprise",
    )

    candidats_doublon_source: Mapped[list["CandidatDoublon"]] = relationship(
        "CandidatDoublon",
        foreign_keys="CandidatDoublon.entreprise_source_id",
        back_populates="entreprise_source",
    )

    candidats_doublon_cible: Mapped[list["CandidatDoublon"]] = relationship(
        "CandidatDoublon",
        foreign_keys="CandidatDoublon.entreprise_cible_id",
        back_populates="entreprise_cible",
    )
''',

    # ============================================================
    # CONTACT ENTREPRISE
    # ============================================================

    "app/models/contact_entreprise.py": r'''
from __future__ import annotations

from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class ContactEntreprise(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "contacts_entreprise"

    entreprise_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("entreprises.id"),
        nullable=False,
    )

    nom: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    prenoms: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    fonction: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    telephone: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    type_contact: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    contact_principal: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    entreprise = relationship(
        "Entreprise",
        back_populates="contacts",
    )
''',

    # ============================================================
    # SITE ENTREPRISE
    # ============================================================

    "app/models/site_entreprise.py": r'''
from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class SiteEntreprise(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sites_entreprise"

    entreprise_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("entreprises.id"),
        nullable=False,
    )

    nom: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    type_site: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    adresse: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    zone_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("zones_administratives.id"),
        nullable=False,
    )

    latitude: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    longitude: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    date_ouverture: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    effectif: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    entreprise = relationship(
        "Entreprise",
        back_populates="sites",
    )

    zone = relationship(
        "ZoneAdministrative",
        foreign_keys=[zone_id],
    )
''',

    # ============================================================
    # OFFRE ENTREPRISE
    # ============================================================

    "app/models/offre_entreprise.py": r'''
from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class OffreEntreprise(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "offres_entreprise"

    entreprise_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("entreprises.id"),
        nullable=False,
    )

    type_offre: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    nom: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    categorie: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    volume_annuel: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    unite: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    capacite_production: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    marches_cibles: Mapped[list[Any] | dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    destinations: Mapped[list[Any] | dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    entreprise = relationship(
        "Entreprise",
        back_populates="offres",
    )
''',

    # ============================================================
    # CANDIDAT DOUBLON
    # ============================================================

    "app/models/candidat_doublon.py": r'''
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class CandidatDoublon(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "candidats_doublon"

    entreprise_source_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("entreprises.id"),
        nullable=False,
    )

    entreprise_cible_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("entreprises.id"),
        nullable=False,
    )

    criteres_concordants: Mapped[
        list[Any] | dict[str, Any] | None
    ] = mapped_column(
        JSONB,
        nullable=True,
    )

    score_similarite: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    statut_examen: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    decision: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    motif_decision: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    examine_par_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=True,
    )

    examine_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    entreprise_source = relationship(
        "Entreprise",
        foreign_keys=[entreprise_source_id],
        back_populates="candidats_doublon_source",
    )

    entreprise_cible = relationship(
        "Entreprise",
        foreign_keys=[entreprise_cible_id],
        back_populates="candidats_doublon_cible",
    )

    examine_par = relationship(
        "Utilisateur",
        foreign_keys=[examine_par_id],
    )
''',

    # ============================================================
    # __INIT__ - BLOCS 1 + 2 + 3
    # ============================================================

    "app/models/__init__.py": r'''
from app.models.audit import EvenementAudit
from app.models.candidat_doublon import CandidatDoublon
from app.models.contact_entreprise import ContactEntreprise
from app.models.entreprise import Entreprise
from app.models.norme import Norme
from app.models.offre_entreprise import OffreEntreprise
from app.models.permission import Permission
from app.models.referentiel import Referentiel, ValeurReferentiel
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.session_utilisateur import SessionUtilisateur
from app.models.site_entreprise import SiteEntreprise
from app.models.utilisateur import Utilisateur
from app.models.utilisateur_role import UtilisateurRole
from app.models.zone_administrative import ZoneAdministrative


__all__ = [
    "CandidatDoublon",
    "ContactEntreprise",
    "Entreprise",
    "EvenementAudit",
    "Norme",
    "OffreEntreprise",
    "Permission",
    "Referentiel",
    "Role",
    "RolePermission",
    "SessionUtilisateur",
    "SiteEntreprise",
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
    print("HAUQE CERTIF — MODELES ENTREPRISES")
    print("=" * 70)

    required = [
        ROOT / "app/models/common.py",
        ROOT / "app/models/utilisateur.py",
        ROOT / "app/models/zone_administrative.py",
        ROOT / "app/models/referentiel.py",
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
    print("- entreprises")
    print("- contacts_entreprise")
    print("- sites_entreprise")
    print("- offres_entreprise")
    print("- candidats_doublon")
    print()
    print("Aucune migration Alembic générée.")
    print("Aucune table PostgreSQL modifiée.")


if __name__ == "__main__":
    main()