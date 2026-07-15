"""Authentication manager — handles credential lifecycle and API client creation.

The AuthManager is the single source of truth for Google API credentials.
All services receive their API clients from here, ensuring consistent auth state.
"""

from __future__ import annotations

from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from google_forms_mcp.auth.oauth import (
    build_credentials_from_env,
    build_credentials_from_secrets_file,
    credentials_from_dict,
    credentials_to_dict,
    refresh_credentials,
)
from google_forms_mcp.auth.token_store import TokenStore
from google_forms_mcp.config import Settings
from google_forms_mcp.exceptions import AuthNotConfiguredError
from google_forms_mcp.infrastructure.logging import get_logger

logger = get_logger("auth")


class AuthManager:
    """Manages Google API authentication and client construction.

    Handles the complete credential lifecycle:
    1. Load from token store (cached credentials)
    2. Build from environment variables or interactive flow
    3. Auto-refresh expired tokens
    4. Persist tokens to disk for reuse

    Usage:
        auth = AuthManager(settings)
        forms_service = auth.get_forms_client()
        drive_service = auth.get_drive_client()
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize the AuthManager.

        Args:
            settings: Application settings with auth configuration.
        """
        self._settings = settings
        self._token_store = TokenStore(settings.token_path)
        self._credentials: Credentials | None = None

    def get_credentials(self) -> Credentials:
        """Get valid Google OAuth credentials.

        Attempts to load cached credentials first, falling back to
        environment variables or interactive flow. Automatically
        refreshes expired tokens.

        Returns:
            Valid Google OAuth Credentials.

        Raises:
            AuthNotConfiguredError: If no authentication method is configured.
        """
        # 1. Try cached credentials
        if self._credentials and self._credentials.valid:
            return self._credentials

        # 2. Try to refresh expired cached credentials
        if self._credentials and self._credentials.expired and self._credentials.refresh_token:
            try:
                self._credentials = refresh_credentials(self._credentials)
                self._save_credentials()
                return self._credentials
            except Exception:
                logger.warning("Failed to refresh cached credentials, re-authenticating")
                self._credentials = None

        # 3. Try to load from token store
        if not self._credentials:
            self._credentials = self._load_from_store()

        # 4. Try to refresh stored credentials
        if self._credentials and self._credentials.expired and self._credentials.refresh_token:
            try:
                self._credentials = refresh_credentials(self._credentials)
                self._save_credentials()
                return self._credentials
            except Exception:
                logger.warning("Failed to refresh stored credentials, re-authenticating")
                self._credentials = None

        # 5. Return valid stored credentials
        if self._credentials and self._credentials.valid:
            return self._credentials

        # 6. Build new credentials
        self._credentials = self._build_new_credentials()
        self._save_credentials()
        return self._credentials

    def get_forms_client(self) -> Any:
        """Get an authenticated Google Forms API client.

        Returns:
            Google Forms API service resource.
        """
        creds = self.get_credentials()
        return build("forms", "v1", credentials=creds)

    def get_drive_client(self) -> Any:
        """Get an authenticated Google Drive API client.

        Returns:
            Google Drive API service resource.
        """
        creds = self.get_credentials()
        return build("drive", "v3", credentials=creds)

    def get_sheets_client(self) -> Any:
        """Get an authenticated Google Sheets API client.

        Returns:
            Google Sheets API service resource.
        """
        creds = self.get_credentials()
        return build("sheets", "v4", credentials=creds)

    def _load_from_store(self) -> Credentials | None:
        """Load credentials from the token store.

        Returns:
            Credentials if found, None otherwise.
        """
        token_data = self._token_store.load()
        if token_data:
            try:
                creds = credentials_from_dict(token_data)
                logger.debug("Loaded credentials from token store")
                return creds
            except Exception as e:
                logger.warning("Failed to load credentials from store: %s", e)
        return None

    def _build_new_credentials(self) -> Credentials:
        """Build new credentials based on the configured auth method.

        Returns:
            Fresh Google OAuth Credentials.

        Raises:
            AuthNotConfiguredError: If no auth method is configured.
        """
        method = self._settings.auth_method

        if method == "env_credentials":
            logger.info("Authenticating with environment variable credentials")
            creds = build_credentials_from_env(self._settings)
            # Force a refresh to get an access token
            creds = refresh_credentials(creds)
            return creds

        elif method == "client_secrets":
            logger.info("Starting interactive OAuth flow")
            return build_credentials_from_secrets_file(self._settings)

        elif method == "service_account":
            # Service account support will be added in Phase 2
            raise AuthNotConfiguredError()

        else:
            raise AuthNotConfiguredError()

    def _save_credentials(self) -> None:
        """Persist current credentials to the token store."""
        if self._credentials:
            try:
                token_data = credentials_to_dict(self._credentials)
                self._token_store.save(token_data)
            except Exception as e:
                logger.warning("Failed to save credentials: %s", e)
