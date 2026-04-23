# logging.py configures Loguru as HERVEX's logging system.
# Loguru replaces all print() statements with structured,
# leveled, and formatted log output.
#
# Why Loguru over Python's built-in logging?
# - Zero configuration for basic use
# - Automatic log rotation and retention
# - Colored terminal output for readability
# - Structured JSON logging for production
# - Exception tracing built in

import sys
from loguru import logger
from app.core.config import settings

def setup_logging():
    """
    Configures Loguru for HERVEX.
    Development: colored, human-readable terminal output.
    Production: structured JSON output for log aggregation tools.

    Called once in main.py during app initialization.
    """

    # Remove Loguru's default handler
    logger.remove()

    if settings.APP_ENV == "development":
        # Development: colored, readable format with file and line number
        logger.add(
            sys.stdout,
            level="DEBUG",
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{line}</cyan> | "
                "<level>{message}</level>"
            ),
            colorize=True
        )
    else:
        # Production: JSON format for log aggregation (Datadog, CloudWatch, etc.)
        logger.add(
            sys.stdout,
            level="INFO",
            serialize=True  # Outputs structured JSON
        )

    # Always write errors to a rotating log file regardless of environment
    # Rotation: new file every 10MB, kept for 7 days
    logger.add(
        "logs/hervex_errors.log",
        level="ERROR",
        rotation="10 MB",
        retention="7 days",
        serialize=True
    )

    logger.info("HERVEX logging initialized.")
