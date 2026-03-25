"""Logging configuration for the application."""

import sys
import os
from loguru import logger
from config import settings


def setup_logger():
    """Configure the application logger (single-client / default mode)."""

    # Remove default handler
    logger.remove()

    # Add console handler with custom format
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True
    )

    # Add file handler for errors
    logger.add(
        "logs/error.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        compression="zip"
    )

    # Add file handler for all logs
    logger.add(
        "logs/app.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
        level="DEBUG",
        rotation="50 MB",
        retention="7 days",
        compression="zip"
    )

    return logger


def get_client_logger(client_name: str, log_level: str = "INFO"):
    """Create a logger instance that writes to a per-client log directory.

    Each client gets:
      logs/<client_name>/app.log   — all messages
      logs/<client_name>/error.log — errors only

    Console output is prefixed with [<client_name>] for easy tailing.

    Args:
        client_name: Unique client identifier (used as directory name).
        log_level: Minimum log level for console output.

    Returns:
        A bound loguru logger with an extra 'client' field pre-set.
    """
    log_dir = os.path.join("logs", client_name)
    os.makedirs(log_dir, exist_ok=True)

    client_logger = logger.bind(client=client_name)

    _fmt_console = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<magenta>[{extra[client]}]</magenta> "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
        "<level>{message}</level>"
    )
    _fmt_file = (
        "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
        "[{extra[client]}] {name}:{function} - {message}"
    )

    # Console sink — filter so only this client's records appear here
    logger.add(
        sys.stdout,
        format=_fmt_console,
        level=log_level,
        colorize=True,
        filter=lambda record: record["extra"].get("client") == client_name,
    )

    # Per-client app log
    logger.add(
        os.path.join(log_dir, "app.log"),
        format=_fmt_file,
        level="DEBUG",
        rotation="50 MB",
        retention="7 days",
        compression="zip",
        filter=lambda record, _cn=client_name: record["extra"].get("client") == _cn,
    )

    # Per-client error log
    logger.add(
        os.path.join(log_dir, "error.log"),
        format=_fmt_file,
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        filter=lambda record, _cn=client_name: record["extra"].get("client") == _cn,
    )

    return client_logger


# Initialize logger (single-client / backward-compatible default)
log = setup_logger()
