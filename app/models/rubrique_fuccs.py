from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class RubriqueFuccs(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "rubriques_fuccs"

    grille_fuccs_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("grilles_fuccs.id"),
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

    ordre_affichage: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    grille_fuccs = relationship(
        "GrilleFuccs",
        back_populates="rubriques",
    )

    criteres: Mapped[list["CritereFuccs"]] = relationship(
        "CritereFuccs",
        back_populates="rubrique_fuccs",
    )
