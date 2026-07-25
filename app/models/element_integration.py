from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class ElementIntegration(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "elements_integration"

    integration_bnec_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("integrations_bnec.id"),
        nullable=False,
    )

    type_objet: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # UUID générique volontairement sans FK dans le MPD
    ressource_source_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )

    # UUID générique volontairement sans FK dans le MPD
    ressource_cible_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )

    revision_source: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    action: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    code_genere: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    statut: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    message_erreur: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    integration_bnec = relationship(
        "IntegrationBnec",
        back_populates="elements",
    )
