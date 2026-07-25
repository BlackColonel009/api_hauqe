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

    examine_par_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
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
