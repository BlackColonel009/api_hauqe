"""Journalisation HAUQE : terminal concis, détails dans un fichier rotatif."""

from __future__ import annotations

import logging
import re
from logging.config import dictConfig
from pathlib import Path


LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
LOG_FILE = LOG_DIR / "hauqe.log"

RESET = "\033[0m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"


class HauqeTerminalFormatter(logging.Formatter):
    """Colorise le terminal selon le niveau ou le statut HTTP."""

    status_pattern = re.compile(r'HTTP/\d(?:\.\d)?"\s+(\d{3})')

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        color = GREEN
        match = self.status_pattern.search(message)

        if match:
            status = int(match.group(1))
            if status >= 500:
                color = RED
            elif status >= 400:
                color = YELLOW
            else:
                color = GREEN
        elif record.levelno >= logging.ERROR:
            color = RED
        elif record.levelno >= logging.WARNING:
            color = YELLOW

        return f"{color}{message}{RESET}"


def configure_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "terminal": {
                    "()": "app.config.logging.HauqeTerminalFormatter",
                    "format": "%(levelname)s: %(message)s",
                },
                "detailed": {
                    "format": (
                        "%(asctime)s | %(levelname)-8s | %(name)s | "
                        "%(message)s"
                    ),
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
            },
            "handlers": {
                "terminal_errors": {
                    "class": "logging.StreamHandler",
                    "level": "ERROR",
                    "formatter": "terminal",
                    "stream": "ext://sys.stderr",
                },
                "terminal_endpoints": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "terminal",
                    "stream": "ext://sys.stdout",
                },
                "application_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "INFO",
                    "formatter": "detailed",
                    "filename": str(LOG_FILE),
                    "maxBytes": 5_000_000,
                    "backupCount": 5,
                    "encoding": "utf-8",
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["terminal_errors", "application_file"],
            },
            "loggers": {
                "uvicorn.access": {
                    "level": "INFO",
                    "handlers": ["terminal_endpoints", "application_file"],
                    "propagate": False,
                },
                "uvicorn.error": {
                    "level": "ERROR",
                    "handlers": ["terminal_errors", "application_file"],
                    "propagate": False,
                },
                "sqlalchemy.engine": {
                    "level": "WARNING",
                    "handlers": ["application_file"],
                    "propagate": False,
                },
            },
        }
    )
