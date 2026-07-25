from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class NoteCritere(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "notes_criteres"

    controle_fuccs_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("controles_fuccs.id"),
        nullable=False,
    )

    critere_fuccs_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("criteres_fuccs.id"),
        nullable=False,
    )

    score: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
    )

    commentaire: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    preuve_document_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=True,
    )

    note_par_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("utilisateurs.id"),
        nullable=False,
    )

    controle_fuccs = relationship(
        "ControleFuccs",
        back_populates="notes",
    )

    critere_fuccs = relationship(
        "CritereFuccs",
        back_populates="notes",
    )

    preuve_document = relationship(
        "Document",
        foreign_keys=[preuve_document_id],
    )

    note_par = relationship(
        "Utilisateur",
        foreign_keys=[note_par_id],
    )
