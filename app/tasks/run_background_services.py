"""Worker serveur permanent : courriels et sauvegardes planifiées."""
from __future__ import annotations
import asyncio
import logging
import sys
from contextlib import suppress
from datetime import date
from time import monotonic
from app.config.logging import configure_logging
from app.tasks.process_notification_queue import run as process_emails
from app.tasks.process_scheduled_backups import run as process_backups
from app.tasks.watch_daily_scan import run as run_watch_scan
from app.tasks.account_inactivity_scan import run as run_inactivity_scan
from app.tasks.account_weekly_digest import run as run_weekly_digest

logger = logging.getLogger(__name__)
configure_logging()


async def run_worker(coro) -> None:
    """Exécute les tâches DB asynchrones sur une boucle compatible Windows."""
    if sys.platform != "win32":
        await coro
        return

    await asyncio.to_thread(
        lambda: asyncio.run(
            coro,
            loop_factory=asyncio.SelectorEventLoop,
        )
    )


async def serve() -> None:
    """Traite les courriels, les sauvegardes et le scan de veille quotidien."""
    next_backup_at = 0.0
    last_watch_scan_date = None
    last_inactivity_scan_date = None
    last_weekly_digest_date = None
    while True:
        try: await run_worker(process_emails(limit=100))
        except Exception:
            logger.exception("Échec du traitement de la file SMTP.")
        if monotonic() >= next_backup_at:
            try: await run_worker(process_backups())
            except Exception:
                logger.exception("Échec du planificateur de sauvegarde.")
            next_backup_at = monotonic() + 3600
        today = date.today()
        if last_watch_scan_date != today:
            try:
                await run_worker(run_watch_scan())
                last_watch_scan_date = today
            except Exception:
                logger.exception("Échec du scan quotidien des échéances.")
        if last_inactivity_scan_date != today:
            try:
                await run_worker(run_inactivity_scan())
                last_inactivity_scan_date = today
            except Exception:
                logger.exception("Échec du scan quotidien d'inactivité des comptes.")
        if today.weekday() == 0 and last_weekly_digest_date != today:
            try:
                await run_worker(run_weekly_digest())
                last_weekly_digest_date = today
            except Exception:
                logger.exception("Échec du résumé hebdomadaire des comptes.")
        await asyncio.sleep(10)


async def stop(task: asyncio.Task | None) -> None:
    if task is None:
        return
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task

if __name__=="__main__": asyncio.run(serve())
