"""Structured logging bootstrap."""

import logging
import sys

from backend.app.core.config import Settings


def configure_logging(settings: Settings) -> None:
    """Configure root logger with a simple key=value friendly format."""
    level = getattr(logging, settings.log_level, logging.INFO)
    logging.basicConfig(
        level=level,
        format="level=%(levelname)s logger=%(name)s message=%(message)s",
        stream=sys.stdout,
        force=True,
    )
