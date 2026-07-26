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
import sys

from app.database.session import AsyncSessionLocal
from app.services.account_inactivity_service import AccountInactivityService


async def run() -> None:
    async with AsyncSessionLocal() as db:
        result = await AccountInactivityService.run(db)
        print(
            "Scan comptes terminé : "
            f"{result.warnings_queued} préavis, "
            f"{result.users_deactivated} désactivation(s), "
            f"{result.sessions_revoked} session(s) révoquée(s)."
        )


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.run(run(), loop_factory=asyncio.SelectorEventLoop)
    else:
        asyncio.run(run())
