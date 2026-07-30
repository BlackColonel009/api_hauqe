"""
Tâche quotidienne de génération des échéances et alertes de veille.

Usage manuel :
    python -m app.tasks.watch_daily_scan

Planification :
    - Windows Task Scheduler ;
    - cron/systemd timer ;
    - ordonnanceur applicatif ultérieur.

La tâche est idempotente :
- elle déduplique les échéances actives ;
- elle déduplique les alertes actives pour une même règle + échéance.

Elle ne dépend pas du frontend.
"""

from __future__ import annotations

import asyncio
import logging
import sys

from app.config.logging import configure_logging
from app.database.session import AsyncSessionLocal
from app.services.veille_service import WatchService

logger = logging.getLogger(__name__)
configure_logging()


async def run() -> None:
    async with AsyncSessionLocal() as db:
        result = await WatchService.run_daily_scan(
            db,
            actor=None,
            request=None,
        )
        logger.info(
            "Scan veille terminé : "
            "%s échéance(s) créée(s), %s alerte(s) créée(s).",
            result.deadlines_created,
            result.alerts_created,
        )


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.run(run(), loop_factory=asyncio.SelectorEventLoop)
    else:
        asyncio.run(run())
