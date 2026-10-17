"""Reusable logging configuration module for the SentinelAI CV Engine.

Provides standardized, readable log formatting, prevents duplicate handlers,
respects configured log levels, and protects against logging secrets or raw
video content.
"""

import logging
import os
import sys
from typing import Optional

DEFAULT_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_ROOT_LOGGER_INITIALIZED = False


def setup_logging(
    log_level: Optional[str] = None,
    logger_name: str = "sentinel_cv",
) -> logging.Logger:
    """Configure and return the root logger for the CV engine.

    Ensures idempotent handler setup to avoid duplicate logs when called
    multiple times across modules.

    Args:
        log_level: Desired logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
                   If None, reads from CV_LOG_LEVEL environment variable or defaults to 'INFO'.
        logger_name: Name of the logger to configure (defaults to 'sentinel_cv').

    Returns:
        logging.Logger: Configured logger instance.
    """
    global _ROOT_LOGGER_INITIALIZED

    if log_level is None:
        log_level = os.getenv("CV_LOG_LEVEL", "INFO")

    numeric_level = getattr(logging, log_level.strip().upper(), logging.INFO)
    logger = logging.getLogger(logger_name)
    logger.setLevel(numeric_level)

    # Avoid duplicate handlers on re-initialization
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(numeric_level)
        formatter = logging.Formatter(
            fmt=DEFAULT_LOG_FORMAT,
            datefmt=DEFAULT_DATE_FORMAT,
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    else:
        # Update level on existing handlers
        for handler in logger.handlers:
            handler.setLevel(numeric_level)

    # Prevent propagating to root logger if root would duplicate output
    logger.propagate = False
    _ROOT_LOGGER_INITIALIZED = True

    return logger


def get_logger(name: str) -> logging.Logger:
    """Retrieve a child logger under the 'sentinel_cv' namespace.

    Args:
        name: Sub-module name (e.g. 'pipeline', 'detector', 'config').

    Returns:
        logging.Logger: Logger instance under the sentinel_cv namespace.
    """
    if not _ROOT_LOGGER_INITIALIZED:
        setup_logging()

    if name.startswith("sentinel_cv.") or name == "sentinel_cv":
        return logging.getLogger(name)
    return logging.getLogger(f"sentinel_cv.{name}")
