"""Structured logging for Google Forms MCP Server.

CRITICAL: In STDIO transport mode, stdout is reserved for the JSON-RPC protocol.
All logging MUST go to stderr. Using print() will corrupt the protocol stream.
"""

from __future__ import annotations

import logging
import sys


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure and return the application logger.

    All output goes to stderr to avoid corrupting the STDIO JSON-RPC stream.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR).

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("google_forms_mcp")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Prevent duplicate handlers on repeated calls
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(getattr(logging, level.upper(), logging.INFO))

        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Prevent propagation to root logger (which might use stdout)
    logger.propagate = False

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Get a child logger for a specific module.

    Args:
        name: Module name for the child logger. If None, returns the root app logger.

    Returns:
        Logger instance.
    """
    base = "google_forms_mcp"
    if name:
        return logging.getLogger(f"{base}.{name}")
    return logging.getLogger(base)
