"""
Politique de notification personnelle.

Les préférences `profil.html` sont consommables par les autres domaines via
une seule fonction afin d'éviter des `if` dispersés.

Événements supportés :
- ALERTE_CRITIQUE
- AFFECTATION
- CORRECTION
- RAPPORT_PLANIFIE
- RESUME_HEBDOMADAIRE

Les notifications de sécurité du compte (reset, mot de passe, inactivité,
MFA) sont toujours envoyées et ne passent pas par cette préférence.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.account_repository import AccountRepository


EVENT_TO_FIELD = {
    "ALERTE_CRITIQUE": "notifications_alertes_critiques",
    "AFFECTATION": "notifications_affectations",
    "CORRECTION": "notifications_corrections",
    "RAPPORT_PLANIFIE": "notifications_rapports_planifies",
    "RESUME_HEBDOMADAIRE": "notifications_resume_hebdomadaire",
}


async def user_wants_notification(
    db: AsyncSession,
    *,
    user_id,
    event_code: str,
) -> bool:
    field = EVENT_TO_FIELD.get(event_code.strip().upper())
    if field is None:
        # Événement non paramétré par le profil : ne pas le supprimer
        # silencieusement.
        return True

    prefs = await AccountRepository.get_or_create_preferences(
        db,
        user_id,
    )
    return bool(getattr(prefs, field))
