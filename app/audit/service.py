from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import EvenementAudit


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def write_audit_event(
    session: AsyncSession,
    *,
    action: str,
    categorie: str,
    resultat: str,
    utilisateur_id: UUID | None = None,
    ressource_type: str | None = None,
    ressource_id: UUID | None = None,
    adresse_ip: str | None = None,
    contexte: dict | None = None,
    valeurs_avant: dict | None = None,
    valeurs_apres: dict | None = None,
) -> EvenementAudit:

    event = EvenementAudit(
        utilisateur_id=utilisateur_id,
        action=action,
        categorie=categorie,
        ressource_type=ressource_type,
        ressource_id=ressource_id,
        adresse_ip=adresse_ip,
        contexte=(
            json.dumps(
                contexte,
                ensure_ascii=False,
                default=str,
            )
            if contexte
            else None
        ),
        valeurs_avant=valeurs_avant,
        valeurs_apres=valeurs_apres,
        resultat=resultat,
        date_evenement=utc_now(),
    )

    session.add(event)

    await session.flush()

    return event