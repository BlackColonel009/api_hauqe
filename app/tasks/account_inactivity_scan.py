"""
Tâche quotidienne — cycle d'inactivité des comptes.

Commande :
    python -m app.tasks.account_inactivity_scan

À planifier une fois par jour.

Cette tâche :
- envoie le préavis RM-33 ;
- désactive les comptes à 180 jours ;
- révoque leurs sessions ;
- nettoie les anciens jetons éphémères.
"""

from __future__ import annotations

import asyncio
import logging
import sys

from app.config.logging import configure_logging
from app.database.session import AsyncSessionLocal
from app.services.account_inactivity_service import AccountInactivityService

logger = logging.getLogger(__name__)
configure_logging()


async def run() -> None:
    async with AsyncSessionLocal() as db:
        result = await AccountInactivityService.run(db)
        logger.info(
            "Scan comptes terminé : "
            "%s préavis, %s désactivation(s), %s session(s) révoquée(s).",
            result.warnings_queued,
            result.users_deactivated,
            result.sessions_revoked,
        )


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.run(run(), loop_factory=asyncio.SelectorEventLoop)
    else:
        asyncio.run(run())
