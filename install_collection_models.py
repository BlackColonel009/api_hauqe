from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent


FILES = {

    # ============================================================
    # 24. CAMPAGNES
    # ============================================================

    "app/models/campagne.py": r'''
from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Campagne(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "campagnes"

    code: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    nom: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    objet: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    objectif: Mapped[str | None] = mapped_column(
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

    responsable_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    responsable = relationship(
        "Utilisateur",
        foreign_keys=[responsable_id],
    )

    missions: Mapped[list["MissionCollecte"]] = relationship(
        "MissionCollecte",
        back_populates="campagne",
    )
''',

    # ============================================================
    # 25. MISSIONS DE COLLECTE
    # ============================================================

    "app/models/mission_collecte.py": r'''
from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class MissionCollecte(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "missions_collecte"

    campagne_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("campagnes.id"),
        nullable=False,
    )

    code: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    objet: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    zone_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("zones_administratives.id"),
        nullable=False,
    )

    date_debut_prevue: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_fin_prevue: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_debut_reelle: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_fin_reelle: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    priorite: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    progression: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    campagne = relationship(
        "Campagne",
        back_populates="missions",
    )

    zone = relationship(
        "ZoneAdministrative",
        foreign_keys=[zone_id],
    )

    affectations: Mapped[list["AffectationMission"]] = relationship(
        "AffectationMission",
        back_populates="mission",
    )

    fiches: Mapped[list["FicheCollecte"]] = relationship(
        "FicheCollecte",
        back_populates="mission",
    )
''',

    # ============================================================
    # 26. AFFECTATIONS MISSION
    # ============================================================

    "app/models/affectation_mission.py": r'''
from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class AffectationMission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "affectations_mission"

    mission_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("missions_collecte.id"),
        nullable=False,
    )

    utilisateur_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    role_mission: Mapped[str | None] = mapped_column(
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

    attribue_par_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    motif: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    mission = relationship(
        "MissionCollecte",
        back_populates="affectations",
    )

    utilisateur = relationship(
        "Utilisateur",
        foreign_keys=[utilisateur_id],
    )

    attribue_par = relationship(
        "Utilisateur",
        foreign_keys=[attribue_par_id],
    )
''',

    # ============================================================
    # 27. FICHES DE COLLECTE
    # ============================================================

    "app/models/fiche_collecte.py": r'''
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class FicheCollecte(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "fiches_collecte"

    mission_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("missions_collecte.id"),
        nullable=False,
    )

    entreprise_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("entreprises.id"),
        nullable=True,
    )

    version_formulaire: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    numero_revision: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    taux_completude: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    consentement_obtenu: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    nom_declarant: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    fonction_declarant: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    telephone_declarant: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    email_declarant: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    signature_declarant: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    observations: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    collecte_par_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    collecte_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    soumise_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    mission = relationship(
        "MissionCollecte",
        back_populates="fiches",
    )

    entreprise = relationship(
        "Entreprise",
        foreign_keys=[entreprise_id],
    )

    collecte_par = relationship(
        "Utilisateur",
        foreign_keys=[collecte_par_id],
    )

    offres_declarees: Mapped[list["OffreDeclaree"]] = relationship(
        "OffreDeclaree",
        back_populates="fiche_collecte",
    )

    certifications_declarees: Mapped[list["CertificationDeclaree"]] = relationship(
        "CertificationDeclaree",
        back_populates="fiche_collecte",
    )

    evenements: Mapped[list["EvenementCollecte"]] = relationship(
        "EvenementCollecte",
        back_populates="fiche_collecte",
    )
''',

    # ============================================================
    # 28. OFFRES DECLAREES
    # ============================================================

    "app/models/offre_declaree.py": r'''
from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class OffreDeclaree(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "offres_declarees"

    fiche_collecte_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("fiches_collecte.id"),
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

    volume: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    unite: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    capacite: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    # Conservé tel quel : VARCHAR(255), pas JSONB.
    marches_vises: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    fiche_collecte = relationship(
        "FicheCollecte",
        back_populates="offres_declarees",
    )
''',

    # ============================================================
    # 29. CERTIFICATIONS DECLAREES
    # ============================================================

    "app/models/certification_declaree.py": r'''
from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class CertificationDeclaree(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "certifications_declarees"

    fiche_collecte_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("fiches_collecte.id"),
        nullable=False,
    )

    nom_certification: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    numero: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    organisme_declare: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    norme_declaree: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    portee: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    date_obtention: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_expiration: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    copie_disponible: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    certification_officielle_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("certifications.id"),
        nullable=True,
    )

    score_rapprochement: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    statut_rapprochement: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    fiche_collecte = relationship(
        "FicheCollecte",
        back_populates="certifications_declarees",
    )

    certification_officielle = relationship(
        "Certification",
        foreign_keys=[certification_officielle_id],
    )
''',

    # ============================================================
    # 30. EVENEMENTS DE COLLECTE
    # ============================================================

    "app/models/evenement_collecte.py": r'''
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class EvenementCollecte(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "evenements_collecte"

    fiche_collecte_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("fiches_collecte.id"),
        nullable=False,
    )

    type_evenement: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    ancien_statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    nouveau_statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    commentaire: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    acteur_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    date_evenement: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    fiche_collecte = relationship(
        "FicheCollecte",
        back_populates="evenements",
    )

    acteur = relationship(
        "Utilisateur",
        foreign_keys=[acteur_id],
    )
''',

    # ============================================================
    # __INIT__ BLOCS 1 A 5
    # ============================================================

    "app/models/__init__.py": r'''
from app.models.accreditation import Accreditation
from app.models.affectation_mission import AffectationMission
from app.models.audit import EvenementAudit
from app.models.audit_certification import AuditCertification
from app.models.campagne import Campagne
from app.models.candidat_doublon import CandidatDoublon
from app.models.certification import Certification
from app.models.certification_declaree import CertificationDeclaree
from app.models.contact_entreprise import ContactEntreprise
from app.models.couverture_certification import CouvertureCertification
from app.models.document import Document
from app.models.entreprise import Entreprise
from app.models.evenement_certification import EvenementCertification
from app.models.evenement_collecte import EvenementCollecte
from app.models.fiche_collecte import FicheCollecte
from app.models.mission_collecte import MissionCollecte
from app.models.norme import Norme
from app.models.offre_declaree import OffreDeclaree
from app.models.offre_entreprise import OffreEntreprise
from app.models.organisme import Organisme
from app.models.permission import Permission
from app.models.referentiel import Referentiel, ValeurReferentiel
from app.models.renouvellement_certification import RenouvellementCertification
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.session_utilisateur import SessionUtilisateur
from app.models.site_entreprise import SiteEntreprise
from app.models.utilisateur import Utilisateur
from app.models.utilisateur_role import UtilisateurRole
from app.models.zone_administrative import ZoneAdministrative


__all__ = [
    "Accreditation",
    "AffectationMission",
    "AuditCertification",
    "Campagne",
    "CandidatDoublon",
    "Certification",
    "CertificationDeclaree",
    "ContactEntreprise",
    "CouvertureCertification",
    "Document",
    "Entreprise",
    "EvenementAudit",
    "EvenementCertification",
    "EvenementCollecte",
    "FicheCollecte",
    "MissionCollecte",
    "Norme",
    "OffreDeclaree",
    "OffreEntreprise",
    "Organisme",
    "Permission",
    "Referentiel",
    "RenouvellementCertification",
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

    print("=" * 72)
    print("HAUQE CERTIF — MODELES COLLECTE")
    print("=" * 72)

    required = [
        ROOT / "app/models/common.py",
        ROOT / "app/models/utilisateur.py",
        ROOT / "app/models/entreprise.py",
        ROOT / "app/models/certification.py",
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
    print("Modèles ajoutés :")
    print("- campagnes")
    print("- missions_collecte")
    print("- affectations_mission")
    print("- fiches_collecte")
    print("- offres_declarees")
    print("- certifications_declarees")
    print("- evenements_collecte")
    print()
    print("Aucune migration Alembic générée.")
    print("Aucune modification PostgreSQL effectuée.")


if __name__ == "__main__":
    main()