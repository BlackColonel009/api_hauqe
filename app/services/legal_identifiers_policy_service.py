"""Politique versionnée de collecte des identifiants juridiques."""
from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.regle_metier import RegleMetier


LEGAL_IDENTIFIERS_POLICY_CODE = "COLLECTE_IDENTIFIANTS_JURIDIQUES"


async def legal_identifiers_collection_enabled(db: AsyncSession) -> bool:
    """Retourne False tant qu'aucune règle HAUQE publiée ne l'active."""
    rows = (
        await db.execute(
            select(RegleMetier)
            .where(RegleMetier.statut == "PUBLIE")
            .order_by(RegleMetier.date_debut_effet.desc().nullslast())
        )
    ).scalars().all()
    today = date.today()
    for rule in rows:
        params = rule.parametres if isinstance(rule.parametres, dict) else {}
        logical_code = str(params.get("_logical_code", rule.code or "")).strip().upper()
        if logical_code != LEGAL_IDENTIFIERS_POLICY_CODE:
            continue
        if rule.date_debut_effet and rule.date_debut_effet > today:
            continue
        if rule.date_fin_effet and rule.date_fin_effet < today:
            continue
        return bool(params.get("enabled", False))
    return False
