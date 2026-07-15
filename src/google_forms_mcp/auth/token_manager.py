"""JSON-based token persistence with multi-profile support.

Stores OAuth tokens as human-readable JSON files with restrictive permissions.
"""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Any

from google_forms_mcp.infrastructure.logging import get_logger

logger = get_logger("token_manager")


class TokenManager:
    """Manages reading and writing OAuth tokens to disk.

    Supports multiple accounts (profiles) stored in a single JSON file
    or individual files, depending on the implementation.
    Here we store a dictionary of profiles in a single JSON file with 
    owner-only permissions (0600 on Unix).
    """

    def __init__(self, token_path: Path) -> None:
        """Initialize the token manager.

        Args:
            token_path: Path where the token file will be stored.
        """
        self._token_path = token_path

    @property
    def token_path(self) -> Path:
        """Return the configured token path."""
        return self._token_path

    def _read_all(self) -> dict[str, dict[str, Any]]:
        """Read the entire token file.

        Returns:
            Dictionary mapping profile names to token data.
        """
        if not self._token_path.exists():
            return {}

        try:
            with open(self._token_path, encoding="utf-8") as f:
                data = json.load(f)
            # Support migrating from old format (single token at root)
            if data and "token" in data and "profiles" not in data:
                return {"default": data}

            return data.get("profiles", {})
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load token file: %s", e)
            return {}

    def _write_all(self, profiles_data: dict[str, dict[str, Any]]) -> None:
        """Write all profiles to the token file."""
        self._token_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self._token_path, "w", encoding="utf-8") as f:
            json.dump({"profiles": profiles_data}, f, indent=2, default=str)

        try:
            if os.name != "nt":  # Not Windows
                os.chmod(self._token_path, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            logger.debug("Could not set file permissions on token file")

    def load_token(self, profile: str = "default") -> dict[str, Any] | None:
        """Load token data for a specific profile.

        Args:
            profile: Name of the profile to load.

        Returns:
            Token data dictionary, or None if not found.
        """
        profiles = self._read_all()
        token = profiles.get(profile)
        if token:
            logger.debug("Loaded token for profile '%s'", profile)
        return token

    def save_token(self, token_data: dict[str, Any], profile: str = "default") -> None:
        """Save token data for a specific profile.

        Args:
            token_data: Token data dictionary to persist.
            profile: Name of the profile.
        """
        profiles = self._read_all()
        profiles[profile] = token_data
        self._write_all(profiles)
        logger.debug("Saved token for profile '%s'", profile)

    def delete_token(self, profile: str = "default") -> None:
        """Delete a profile's token from disk.
        
        Args:
            profile: Name of the profile.
        """
        profiles = self._read_all()
        if profile in profiles:
            del profiles[profile]
            self._write_all(profiles)
            logger.info("Deleted token for profile '%s'", profile)

    def list_profiles(self) -> list[str]:
        """List all available profiles.
        
        Returns:
            List of profile names.
        """
        return list(self._read_all().keys())
