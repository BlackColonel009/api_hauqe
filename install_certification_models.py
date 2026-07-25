from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent


FILES = {

    # ============================================================
    # ORGANISMES
    # ============================================================

    "app/models/organisme.py": r'''
from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Organisme(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "organismes"

    identifiant_national: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    nom_officiel: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    sigle: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    type_organisme: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    pays: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    numero_enregistrement: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    telephone: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    adresse: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    zone_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("zones_administratives.id"),
        nullable=True,
    )

    site_web: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    date_derniere_verification: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    zone = relationship(
        "ZoneAdministrative",
        foreign_keys=[zone_id],
    )

    accreditations = relationship(
        "Accreditation",
        back_populates="organisme",
    )

    certifications = relationship(
        "Certification",
        back_populates="organisme",
    )
''',

    # ============================================================
    # ACCREDITATIONS
    # ============================================================

    "app/models/accreditation.py": r'''
from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Accreditation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "accreditations"

    organisme_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organismes.id"),
        nullable=False,
    )

    numero: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    accrediteur: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    domaine_technique: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    perimetre: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    date_delivrance: Mapped[date | None] = mapped_column(
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

    reference_officielle: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    decision_hauqe: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    date_decision: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    organisme = relationship(
        "Organisme",
        back_populates="accreditations",
    )

    certifications = relationship(
        "Certification",
        back_populates="accreditation",
    )
''',

    # ============================================================
    # CERTIFICATIONS
    # ============================================================

    "app/models/certification.py": r'''
from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Certification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "certifications"

    identifiant_national: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    entreprise_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("entreprises.id"),
        nullable=False,
    )

    organisme_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organismes.id"),
        nullable=False,
    )

    accreditation_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("accreditations.id"),
        nullable=True,
    )

    norme_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("normes.id"),
        nullable=False,
    )

    numero_certificat: Mapped[str | None] = mapped_column(
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

    date_effet: Mapped[date | None] = mapped_column(
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

    motif_statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Conservée car elle existe dans la base actuelle.
    classification: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    authenticite_verifiee: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    certification_strategique: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    source_donnee: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    entreprise = relationship(
        "Entreprise",
        foreign_keys=[entreprise_id],
    )

    organisme = relationship(
        "Organisme",
        back_populates="certifications",
    )

    accreditation = relationship(
        "Accreditation",
        back_populates="certifications",
    )

    norme = relationship(
        "Norme",
        foreign_keys=[norme_id],
    )

    couvertures = relationship(
        "CouvertureCertification",
        back_populates="certification",
    )

    audits = relationship(
        "AuditCertification",
        back_populates="certification",
    )

    evenements = relationship(
        "EvenementCertification",
        back_populates="certification",
    )

    renouvellements = relationship(
        "RenouvellementCertification",
        back_populates="certification",
    )
''',

    # ============================================================
    # COUVERTURES
    # ============================================================

    "app/models/couverture_certification.py": r'''
from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class CouvertureCertification(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "couvertures_certification"

    certification_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("certifications.id"),
        nullable=False,
    )

    type_couverture: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    offre_entreprise_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("offres_entreprise.id"),
        nullable=True,
    )

    site_entreprise_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sites_entreprise.id"),
        nullable=True,
    )

    libelle_couverture: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    details: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    certification = relationship(
        "Certification",
        back_populates="couvertures",
    )

    offre_entreprise = relationship(
        "OffreEntreprise",
        foreign_keys=[offre_entreprise_id],
    )

    site_entreprise = relationship(
        "SiteEntreprise",
        foreign_keys=[site_entreprise_id],
    )
''',

    # ============================================================
    # AUDITS DE CERTIFICATION
    # ============================================================

    "app/models/audit_certification.py": r'''
from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class AuditCertification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "audits_certification"

    certification_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("certifications.id"),
        nullable=False,
    )

    type_audit: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    date_prevue: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_realisee: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    auditeur: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    resultat: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    prochain_audit_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    observations: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    certification = relationship(
        "Certification",
        back_populates="audits",
    )
''',

    # ============================================================
    # HISTORIQUE CERTIFICATION
    # ============================================================

    "app/models/evenement_certification.py": r'''
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class EvenementCertification(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "evenements_certification"

    certification_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("certifications.id"),
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

    date_evenement: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    motif: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    source: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    acteur_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=True,
    )

    certification = relationship(
        "Certification",
        back_populates="evenements",
    )

    acteur = relationship(
        "Utilisateur",
        foreign_keys=[acteur_id],
    )
''',

    # ============================================================
    # RENOUVELLEMENTS
    # ============================================================

    "app/models/renouvellement_certification.py": r'''
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


class RenouvellementCertification(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "renouvellements_certification"

    certification_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("certifications.id"),
        nullable=False,
    )

    date_ouverture: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_limite: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    date_decision: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    decision: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    resultat: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    justification: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    preuves: Mapped[
        list[Any] | dict[str, Any] | None
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
        back_populates="renouvellements",
    )
''',

    # ============================================================
    # DOCUMENTS
    # ============================================================

    "app/models/document.py": r'''
from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Document(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "documents"

    type_document: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    nom_original: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    nom_stockage: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    chemin_stockage: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    format: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    taille_octets: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    checksum: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    version: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    ressource_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Relation polymorphe volontairement conservée telle que
    # définie dans le MPD actuel : pas de ForeignKey SQL.
    ressource_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )

    confidentialite: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    source: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    date_document: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    depose_par_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=True,
    )

    date_depot: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    statut_verification: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    depose_par = relationship(
        "Utilisateur",
        foreign_keys=[depose_par_id],
    )
''',

    # ============================================================
    # __INIT__ BLOCS 1 A 4
    # ============================================================

    "app/models/__init__.py": r'''
from app.models.accreditation import Accreditation
from app.models.audit import EvenementAudit
from app.models.audit_certification import AuditCertification
from app.models.candidat_doublon import CandidatDoublon
from app.models.certification import Certification
from app.models.contact_entreprise import ContactEntreprise
from app.models.couverture_certification import CouvertureCertification
from app.models.document import Document
from app.models.entreprise import Entreprise
from app.models.evenement_certification import EvenementCertification
from app.models.norme import Norme
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
    "AuditCertification",
    "CandidatDoublon",
    "Certification",
    "ContactEntreprise",
    "CouvertureCertification",
    "Document",
    "Entreprise",
    "EvenementAudit",
    "EvenementCertification",
    "Norme",
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
    print("HAUQE CERTIF — ORGANISMES / CERTIFICATIONS / DOCUMENTS")
    print("=" * 72)

    required = [
        ROOT / "app/models/common.py",
        ROOT / "app/models/entreprise.py",
        ROOT / "app/models/offre_entreprise.py",
        ROOT / "app/models/site_entreprise.py",
        ROOT / "app/models/norme.py",
        ROOT / "app/models/utilisateur.py",
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
    print("- organismes")
    print("- accreditations")
    print("- certifications")
    print("- couvertures_certification")
    print("- audits_certification")
    print("- evenements_certification")
    print("- renouvellements_certification")
    print("- documents")
    print()
    print("Aucune migration Alembic générée.")
    print("Aucune modification PostgreSQL effectuée.")


if __name__ == "__main__":
    main()