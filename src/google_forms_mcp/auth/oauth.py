"""OAuth 2.0 authentication flows for Google APIs.

Supports two authentication strategies:
1. Environment variable credentials (client_id + client_secret + refresh_token)
2. Interactive desktop OAuth flow (client_secrets.json → browser consent)
"""

from __future__ import annotations

from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from google_forms_mcp.config import GOOGLE_FORMS_SCOPES, Settings
from google_forms_mcp.exceptions import (
    InvalidCredentialsError,
    RefreshFailedError,
)
from google_forms_mcp.infrastructure.logging import get_logger

logger = get_logger("oauth")


def build_credentials_from_env(settings: Settings) -> Credentials:
    """Build Google credentials from environment variables.

    Creates a Credentials object using the pre-configured client ID,
    client secret, and refresh token. The access token will be obtained
    automatically on first use.

    Args:
        settings: Application settings containing OAuth credentials.

    Returns:
        Google OAuth Credentials object.

    Raises:
        InvalidCredentialsError: If required environment variables are missing.
    """
    if not settings.has_env_credentials:
        raise InvalidCredentialsError(
            "Missing required environment variables: "
            "GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REFRESH_TOKEN"
        )

    creds = Credentials(
        token=None,  # Will be fetched on first use
        refresh_token=settings.google_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=GOOGLE_FORMS_SCOPES,
    )

    logger.info("Built credentials from environment variables")
    return creds


def build_credentials_from_secrets_file(settings: Settings) -> Credentials:
    """Build Google credentials via interactive OAuth flow.

    Opens a browser for user consent and obtains tokens via the
    InstalledAppFlow (desktop application) flow.

    Args:
        settings: Application settings containing the client secrets file path.

    Returns:
        Google OAuth Credentials object with access and refresh tokens.

    Raises:
        InvalidCredentialsError: If the client secrets file is invalid.
    """
    if not settings.has_client_secrets_file:
        raise InvalidCredentialsError(
            f"Client secrets file not found: {settings.google_client_secrets_file}"
        )

    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            settings.google_client_secrets_file,
            scopes=GOOGLE_FORMS_SCOPES,
        )
        port = 0
        if settings.oauth_redirect_uri.startswith("http://localhost:"):
            try:
                # Extract port from e.g., http://localhost:8080/
                port = int(settings.oauth_redirect_uri.split(":")[2].strip("/"))
            except (IndexError, ValueError):
                pass

        creds = flow.run_local_server(
            port=port,
            access_type="offline",
            prompt="consent",
        )
        logger.info("Obtained credentials via interactive OAuth flow")
        return creds
    except Exception as e:
        raise InvalidCredentialsError(f"Failed to complete OAuth flow: {e}") from e


def refresh_credentials(creds: Credentials) -> Credentials:
    """Refresh expired credentials.

    Args:
        creds: Google OAuth Credentials object with a refresh token.

    Returns:
        Refreshed credentials with a new access token.

    Raises:
        RefreshFailedError: If the refresh attempt fails.
    """
    if not creds.refresh_token:
        raise RefreshFailedError("No refresh token available. Please re-authenticate.")

    try:
        creds.refresh(Request())
        logger.debug("Successfully refreshed access token")
        return creds
    except Exception as e:
        raise RefreshFailedError(f"Failed to refresh access token: {e}") from e


def credentials_to_dict(creds: Credentials) -> dict[str, Any]:
    """Serialize credentials to a dictionary for storage.

    Args:
        creds: Google OAuth Credentials object.

    Returns:
        Dictionary representation of the credentials.
    """
    return {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes) if creds.scopes else GOOGLE_FORMS_SCOPES,
    }


def credentials_from_dict(data: dict[str, Any]) -> Credentials:
    """Deserialize credentials from a dictionary.

    Args:
        data: Dictionary containing credential fields.

    Returns:
        Google OAuth Credentials object.
    """
    return Credentials(
        token=data.get("token"),
        refresh_token=data.get("refresh_token"),
        token_uri=data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=data.get("client_id"),
        client_secret=data.get("client_secret"),
        scopes=data.get("scopes", GOOGLE_FORMS_SCOPES),
    )
