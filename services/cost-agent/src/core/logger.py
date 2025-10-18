"""
Structured logging setup for Cost Agent.
"""

import logging
import sys

from pythonjsonlogger import jsonlogger

from src.config import settings


def setup_logging() -> logging.Logger:
    """
    Setup structured JSON logging.

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger("cost_agent")

    # Set log level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    # Create JSON formatter
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    return logger
