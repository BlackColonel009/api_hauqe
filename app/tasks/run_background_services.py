"""Worker serveur permanent : courriels et sauvegardes planifiées."""
from __future__ import annotations
import asyncio
import logging
from contextlib import suppress
from time import monotonic
from app.config.logging import configure_logging
from app.tasks.process_notification_queue import run as process_emails
from app.tasks.process_scheduled_backups import run as process_backups

logger = logging.getLogger(__name__)
configure_logging()

async def serve() -> None:
    """Traite les courriels rapidement et les sauvegardes chaque heure."""
    next_backup_at = 0.0
    while True:
        try: await process_emails(limit=100)
        except Exception:
            logger.exception("Échec du traitement de la file SMTP.")
        if monotonic() >= next_backup_at:
            try: await process_backups()
            except Exception:
                logger.exception("Échec du planificateur de sauvegarde.")
            next_backup_at = monotonic() + 3600
        await asyncio.sleep(10)


async def stop(task: asyncio.Task | None) -> None:
    if task is None:
        return
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task

if __name__=="__main__": asyncio.run(serve())
