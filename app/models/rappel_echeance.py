from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class RappelEcheance(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Trace un envoi automatique et empêche tout doublon pour une journée."""

    __tablename__ = "rappels_echeances"
    __table_args__ = (
        UniqueConstraint(
            "echeance_id",
            "destinataire_utilisateur_id",
            "type_rappel",
            "date_rappel",
            name="uq_rappel_echeance_destinataire_type_date",
        ),
    )

    echeance_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("echeances.id"), nullable=False
    )
    destinataire_utilisateur_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("utilisateurs.id"), nullable=False
    )
    notification_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("notifications.id"), nullable=True
    )
    type_rappel: Mapped[str] = mapped_column(String(64), nullable=False)
    date_rappel: Mapped[date] = mapped_column(Date, nullable=False)
