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
