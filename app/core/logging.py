"""Structured logging setup with Rich handler."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

from rich.logging import RichHandler

_LOG_FORMAT = "%(message)s"
_DATE_FORMAT = "[%X]"

_configured = False


def configure_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    force: bool = False,
) -> None:
    """Configure the root logger with a Rich console handler.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to write log output.
        force: Re-configure even if already configured.
    """
    global _configured
    if _configured and not force:
        return

    numeric_level = getattr(logging, level.upper(), logging.INFO)

    handlers: list[logging.Handler] = [
        RichHandler(
            rich_tracebacks=True,
            markup=True,
            show_path=False,
            log_time_format=_DATE_FORMAT,
        )
    ]

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s  %(levelname)-8s  %(name)s  %(message)s")
        )
        handlers.append(file_handler)

    logging.basicConfig(
        level=numeric_level,
        format=_LOG_FORMAT,
        datefmt=_DATE_FORMAT,
        handlers=handlers,
        force=True,
    )
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a named logger.  Call configure_logging() first."""
    return logging.getLogger(name)


def set_level(level: str) -> None:
    """Dynamically change the root log level."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.getLogger().setLevel(numeric_level)
