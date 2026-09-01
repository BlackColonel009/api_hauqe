from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class ExclusionRappelEcheance(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Administrateur exclu des rappels d'une échéance donnée."""

    __tablename__ = "exclusions_rappels_echeances"
    __table_args__ = (
        UniqueConstraint(
            "echeance_id",
            "administrateur_id",
            name="uq_exclusion_rappel_echeance_administrateur",
        ),
    )

    echeance_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("echeances.id"), nullable=False
    )
    administrateur_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("utilisateurs.id"), nullable=False
    )
