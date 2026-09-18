"""Logging configuration for the pipeline.

Provides a structured logger that works consistently in local
development and in Databricks notebooks.
"""

import logging
import sys
from typing import Optional


DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Return a configured logger with a consistent format.

    Args:
        name: Logger name, typically __name__ of the calling module.
        level: Optional log level (DEBUG, INFO, WARNING, ERROR).
               Defaults to INFO.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    log_level = getattr(logging, (level or "INFO").upper(), logging.INFO)
    logger.setLevel(log_level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    handler.setFormatter(logging.Formatter(DEFAULT_FORMAT, DEFAULT_DATE_FORMAT))

    logger.addHandler(handler)
    logger.propagate = False

    return logger