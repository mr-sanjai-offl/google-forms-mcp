"""JSON-based token persistence.

Stores OAuth tokens as human-readable JSON files with restrictive permissions.
"""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Any

from google_forms_mcp.infrastructure.logging import get_logger

logger = get_logger("token_store")


class TokenStore:
    """Manages reading and writing OAuth tokens to disk.

    Tokens are stored as JSON files with owner-only permissions (0600 on Unix).
    """

    def __init__(self, token_path: Path) -> None:
        """Initialize the token store.

        Args:
            token_path: Path where the token file will be stored.
        """
        self._token_path = token_path

    @property
    def token_path(self) -> Path:
        """Return the configured token path."""
        return self._token_path

    def load(self) -> dict[str, Any] | None:
        """Load token data from disk.

        Returns:
            Token data dictionary, or None if no token file exists.
        """
        if not self._token_path.exists():
            logger.debug("No token file found at %s", self._token_path)
            return None

        try:
            with open(self._token_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.debug("Loaded token from %s", self._token_path)
            return data
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load token file: %s", e)
            return None

    def save(self, token_data: dict[str, Any]) -> None:
        """Save token data to disk.

        Creates parent directories if they don't exist.
        Sets restrictive file permissions on Unix systems.

        Args:
            token_data: Token data dictionary to persist.
        """
        # Ensure parent directory exists
        self._token_path.parent.mkdir(parents=True, exist_ok=True)

        # Write token file
        with open(self._token_path, "w", encoding="utf-8") as f:
            json.dump(token_data, f, indent=2, default=str)

        # Set restrictive permissions (owner-only read/write) on Unix
        try:
            if os.name != "nt":  # Not Windows
                os.chmod(self._token_path, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            logger.debug("Could not set file permissions on token file")

        logger.debug("Saved token to %s", self._token_path)

    def delete(self) -> None:
        """Delete the token file from disk."""
        if self._token_path.exists():
            self._token_path.unlink()
            logger.debug("Deleted token file %s", self._token_path)

    def exists(self) -> bool:
        """Check if a token file exists."""
        return self._token_path.exists()
