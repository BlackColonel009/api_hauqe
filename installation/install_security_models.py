from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent


FILES = {

    # ============================================================
    # COMMON
    # ============================================================

    "app/models/common.py": r'''
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, func, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column


class UUIDPrimaryKeyMixin:
    """
    Identifiant technique correspondant au MPD :
    UUID PK NOT NULL DEFAULT gen_random_uuid()
    """

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )


class TimestampMixin:
    """
    Champs transversaux présents dans le MPD.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
''',

    # ============================================================
    # ZONE ADMINISTRATIVE
    # Nécessaire car utilisateurs.region_affectation_id -> zones...
    # ============================================================

    "app/models/zone_administrative.py": r'''
from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class ZoneAdministrative(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "zones_administratives"

    parent_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("zones_administratives.id"),
        nullable=True,
    )

    type_zone: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    code: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    nom: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    latitude: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    longitude: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    parent: Mapped["ZoneAdministrative | None"] = relationship(
        "ZoneAdministrative",
        remote_side="ZoneAdministrative.id",
        back_populates="enfants",
    )

    enfants: Mapped[list["ZoneAdministrative"]] = relationship(
        "ZoneAdministrative",
        back_populates="parent",
    )
''',

    # ============================================================
    # UTILISATEURS
    # ============================================================

    "app/models/utilisateur.py": r'''
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Utilisateur(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "utilisateurs"

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    mot_de_passe_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    nom: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    prenoms: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    telephone: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    fonction: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    region_affectation_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("zones_administratives.id"),
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    mfa_active: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    derniere_connexion_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )

    region_affectation = relationship(
        "ZoneAdministrative",
        foreign_keys=[region_affectation_id],
    )

    attributions_roles = relationship(
        "UtilisateurRole",
        foreign_keys="UtilisateurRole.utilisateur_id",
        back_populates="utilisateur",
    )

    attributions_effectuees = relationship(
        "UtilisateurRole",
        foreign_keys="UtilisateurRole.attribue_par_id",
        back_populates="attribue_par",
    )

    sessions = relationship(
        "SessionUtilisateur",
        back_populates="utilisateur",
    )

    evenements_audit = relationship(
        "EvenementAudit",
        back_populates="utilisateur",
    )
''',

    # ============================================================
    # ROLES
    # ============================================================

    "app/models/role.py": r'''
from __future__ import annotations

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Role(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "roles"

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

    niveau: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    attributions = relationship(
        "UtilisateurRole",
        back_populates="role",
    )

    autorisations = relationship(
        "RolePermission",
        back_populates="role",
    )
''',

    # ============================================================
    # PERMISSIONS
    # ============================================================

    "app/models/permission.py": r'''
from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Permission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    domaine: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    action: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    roles = relationship(
        "RolePermission",
        back_populates="permission",
    )
''',

    # ============================================================
    # UTILISATEUR_ROLE
    # ============================================================

    "app/models/utilisateur_role.py": r'''
from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class UtilisateurRole(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "utilisateur_role"

    utilisateur_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    role_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("roles.id"),
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

    utilisateur = relationship(
        "Utilisateur",
        foreign_keys=[utilisateur_id],
        back_populates="attributions_roles",
    )

    attribue_par = relationship(
        "Utilisateur",
        foreign_keys=[attribue_par_id],
        back_populates="attributions_effectuees",
    )

    role = relationship(
        "Role",
        back_populates="attributions",
    )
''',

    # ============================================================
    # ROLE_PERMISSION
    # ============================================================

    "app/models/role_permission.py": r'''
from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class RolePermission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "role_permission"

    role_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("roles.id"),
        nullable=False,
    )

    permission_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("permissions.id"),
        nullable=False,
    )

    role = relationship(
        "Role",
        back_populates="autorisations",
    )

    permission = relationship(
        "Permission",
        back_populates="roles",
    )
''',

    # ============================================================
    # SESSIONS
    # ============================================================

    "app/models/session_utilisateur.py": r'''
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class SessionUtilisateur(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sessions_utilisateur"

    utilisateur_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    jeton_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    adresse_ip: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    user_agent: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    debut_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    derniere_activite_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    expiration_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    revoquee_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    utilisateur = relationship(
        "Utilisateur",
        back_populates="sessions",
    )
''',

    # ============================================================
    # JOURNAL D'AUDIT
    # ============================================================

    "app/models/audit.py": r'''
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class EvenementAudit(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "evenements_audit"

    utilisateur_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=True,
    )

    action: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    categorie: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    ressource_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    ressource_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )

    adresse_ip: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    contexte: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    valeurs_avant: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    valeurs_apres: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    empreinte: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    resultat: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    date_evenement: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    utilisateur = relationship(
        "Utilisateur",
        back_populates="evenements_audit",
    )
''',

    # ============================================================
    # MODELS __INIT__
    # ============================================================

    "app/models/__init__.py": r'''
from app.models.audit import EvenementAudit
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.session_utilisateur import SessionUtilisateur
from app.models.utilisateur import Utilisateur
from app.models.utilisateur_role import UtilisateurRole
from app.models.zone_administrative import ZoneAdministrative

__all__ = [
    "EvenementAudit",
    "Permission",
    "Role",
    "RolePermission",
    "SessionUtilisateur",
    "Utilisateur",
    "UtilisateurRole",
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
    print("HAUQE CERTIF — INSTALLATION MODELES SECURITE")
    print("=" * 70)

    app_dir = ROOT / "app"

    if not app_dir.exists():
        raise SystemExit(
            "ERREUR : app/ introuvable. "
            "Place le script à la racine du projet."
        )

    for relative_path, content in FILES.items():
        write_file(relative_path, content)

    print()
    print("=" * 70)
    print("MODELES CREES")
    print("=" * 70)
    print()
    print("Aucune migration Alembic n'a été générée.")
    print("Aucune table PostgreSQL n'a été modifiée.")


if __name__ == "__main__":
    main()