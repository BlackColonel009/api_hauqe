from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class CritereFuccs(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "criteres_fuccs"

    rubrique_fuccs_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("rubriques_fuccs.id"),
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

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    score_maximal: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    poids: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    ordre_affichage: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    commentaire_obligatoire: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    preuve_obligatoire: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    rubrique_fuccs = relationship(
        "RubriqueFuccs",
        back_populates="criteres",
    )

    notes: Mapped[list["NoteCritere"]] = relationship(
        "NoteCritere",
        back_populates="critere_fuccs",
    )
