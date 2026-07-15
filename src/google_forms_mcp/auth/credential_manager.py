"""Authentication lifecycle manager.

Handles OAuth consent flow, credential loading, scope validation, and token refresh.
"""

from __future__ import annotations

from google.oauth2.credentials import Credentials

from google_forms_mcp.auth.oauth import (
    build_credentials_from_env,
    build_credentials_from_secrets_file,
    credentials_from_dict,
    credentials_to_dict,
    refresh_credentials,
)
from google_forms_mcp.auth.token_manager import TokenManager
from google_forms_mcp.config import GOOGLE_FORMS_SCOPES, Settings
from google_forms_mcp.exceptions import (
    AuthNotConfiguredError,
    MissingScopesError,
)
from google_forms_mcp.infrastructure.logging import get_logger

logger = get_logger("credential_manager")


class CredentialManager:
    """Manages Google API credential lifecycle.

    Handles login, logout, automatic token refresh, and scope validation.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize the CredentialManager.

        Args:
            settings: Application settings.
        """
        self._settings = settings
        self._token_manager = TokenManager(settings.token_path)
        # Cache active credentials per profile in memory
        self._active_credentials: dict[str, Credentials] = {}

    def get_valid_credentials(self, profile: str = "default") -> Credentials:
        """Get valid Google OAuth credentials for a profile.

        Attempts to load cached credentials first, falling back to
        interactive flow or environment variables. Automatically
        refreshes expired tokens and validates scopes.

        Args:
            profile: Account profile name.

        Returns:
            Valid Google OAuth Credentials.

        Raises:
            AuthNotConfiguredError: If no authentication method is configured.
            MissingScopesError: If existing token lacks required scopes.
        """
        creds = self._active_credentials.get(profile)

        # 1. Check in-memory valid credentials
        if creds and creds.valid:
            self._validate_scopes(creds)
            return creds

        # 2. Try to refresh in-memory credentials
        if creds and creds.expired and creds.refresh_token:
            creds = self._try_refresh(creds, profile)
            if creds:
                return creds

        # 3. Load from disk
        creds = self._load_from_manager(profile)

        # 4. Try to refresh disk credentials
        if creds and creds.expired and creds.refresh_token:
            creds = self._try_refresh(creds, profile)
            if creds:
                return creds

        # 5. Return valid disk credentials
        if creds and creds.valid:
            self._validate_scopes(creds)
            self._active_credentials[profile] = creds
            return creds

        # 6. Build new credentials (Login)
        creds = self.login(profile)
        return creds

    def login(self, profile: str = "default") -> Credentials:
        """Explicitly trigger an authentication flow.

        Args:
            profile: Account profile name.

        Returns:
            Fresh Google OAuth Credentials.
        """
        logger.info("Initiating login for profile '%s'", profile)
        method = self._settings.auth_method

        if method == "env_credentials":
            logger.info("Authenticating with environment variable credentials")
            creds = build_credentials_from_env(self._settings)
            creds = refresh_credentials(creds)

        elif method == "client_secrets":
            logger.info("Starting interactive OAuth flow")
            creds = build_credentials_from_secrets_file(self._settings)

        elif method == "service_account":
            raise AuthNotConfiguredError("Service account auth not yet implemented")

        else:
            raise AuthNotConfiguredError(
                "No authentication method configured. Provide env vars or client_secrets.json"
            )

        self._validate_scopes(creds)
        self._active_credentials[profile] = creds
        self._save_credentials(creds, profile)
        return creds

    def logout(self, profile: str = "default") -> None:
        """Clear credentials for a profile.

        Args:
            profile: Account profile name.
        """
        if profile in self._active_credentials:
            del self._active_credentials[profile]
        self._token_manager.delete_token(profile)
        logger.info("Logged out profile '%s'", profile)

    def list_profiles(self) -> list[str]:
        """List all authenticated profiles."""
        return self._token_manager.list_profiles()

    def _try_refresh(self, creds: Credentials, profile: str) -> Credentials | None:
        """Attempt to refresh a token, handling errors gracefully."""
        try:
            refreshed = refresh_credentials(creds)
            self._validate_scopes(refreshed)
            self._active_credentials[profile] = refreshed
            self._save_credentials(refreshed, profile)
            return refreshed
        except Exception as e:
            logger.warning("Session recovery failed for profile '%s': %s", profile, e)
            # Remove invalid token
            self._active_credentials.pop(profile, None)
            return None

    def _load_from_manager(self, profile: str) -> Credentials | None:
        """Load credentials from the token manager."""
        token_data = self._token_manager.load_token(profile)
        if token_data:
            try:
                creds = credentials_from_dict(token_data)
                logger.debug("Loaded credentials for profile '%s'", profile)
                return creds
            except Exception as e:
                logger.warning("Failed to load credentials for profile '%s': %s", profile, e)
        return None

    def _save_credentials(self, creds: Credentials, profile: str) -> None:
        """Persist current credentials to the token manager."""
        try:
            token_data = credentials_to_dict(creds)
            self._token_manager.save_token(token_data, profile)
        except Exception as e:
            logger.error("Failed to save credentials for profile '%s': %s", profile, e)

    def _validate_scopes(self, creds: Credentials) -> None:
        """Validate that the token has all required scopes.

        Args:
            creds: The credentials to check.

        Raises:
            MissingScopesError: If any required scopes are missing.
        """
        if not creds.scopes:
            return  # Default env creds might not report scopes until first request

        granted_scopes = set(creds.scopes)
        required_scopes = set(GOOGLE_FORMS_SCOPES)

        missing = required_scopes - granted_scopes
        if missing:
            msg = f"Credentials missing required scopes: {', '.join(missing)}"
            logger.error(msg)
            raise MissingScopesError(msg)
