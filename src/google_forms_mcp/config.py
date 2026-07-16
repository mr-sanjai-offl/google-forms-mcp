"""Configuration management for Google Forms MCP Server.

Loads settings from environment variables with optional fallback to a TOML config file.
"""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TransportMode(str, Enum):
    """Supported MCP transport modes."""

    STDIO = "stdio"
    HTTP = "http"


class LogLevel(str, Enum):
    """Supported log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings are optional with sensible defaults. The minimum required
    configuration is either:
    - GOOGLE_CLIENT_ID + GOOGLE_CLIENT_SECRET + GOOGLE_REFRESH_TOKEN (env var auth)
    - GOOGLE_CLIENT_SECRETS_FILE (interactive OAuth flow)
    - GOOGLE_SERVICE_ACCOUNT_FILE (service account auth)
    """

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Google OAuth 2.0 Credentials ---
    google_client_id: str | None = Field(
        default=None,
        description="Google OAuth 2.0 Client ID",
    )
    google_client_secret: str | None = Field(
        default=None,
        description="Google OAuth 2.0 Client Secret",
    )
    google_refresh_token: str | None = Field(
        default=None,
        description="Pre-obtained Google OAuth 2.0 Refresh Token",
    )

    # --- Alternative Auth: File-based credentials ---
    google_client_secrets_file: str | None = Field(
        default=None,
        description="Path to OAuth client secrets JSON file",
    )
    google_service_account_file: str | None = Field(
        default=None,
        description="Path to service account key JSON file",
    )

    # --- Token Storage ---
    google_forms_mcp_token_path: str = Field(
        default="",
        description="Path for token storage. Defaults to ~/.google-forms-mcp/token.json",
    )

    # --- Transport ---
    google_forms_mcp_transport: TransportMode = Field(
        default=TransportMode.STDIO,
        description="MCP transport mode: stdio or http",
    )
    google_forms_mcp_port: int = Field(
        default=8000,
        description="HTTP port (only used when transport is http)",
    )

    # --- Phase 2: Advanced Auth & Client Config ---
    oauth_redirect_uri: str = Field(
        default="http://localhost:8080/",
        description="Redirect URI for localhost OAuth flow",
    )
    api_timeout_seconds: int = Field(
        default=60,
        description="Default timeout for Google API requests",
    )
    max_retries: int = Field(
        default=5,
        description="Maximum number of retries for transient Google API errors",
    )
    retry_backoff_factor: float = Field(
        default=2.0,
        description="Exponential backoff multiplier for retries",
    )

    # --- Logging ---
    google_forms_mcp_log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Log level: DEBUG, INFO, WARNING, ERROR",
    )

    @property
    def token_path(self) -> Path:
        """Resolve the token storage path."""
        if self.google_forms_mcp_token_path:
            return Path(self.google_forms_mcp_token_path).expanduser()
        return Path.home() / ".google-forms-mcp" / "token.json"

    @property
    def has_env_credentials(self) -> bool:
        """Check if environment variable credentials are configured."""
        return bool(
            self.google_client_id and self.google_client_secret and self.google_refresh_token
        )

    @property
    def has_client_secrets_file(self) -> bool:
        """Check if a client secrets file is configured."""
        return bool(
            self.google_client_secrets_file and os.path.isfile(self.google_client_secrets_file)
        )

    @property
    def has_service_account(self) -> bool:
        """Check if a service account file is configured."""
        return bool(
            self.google_service_account_file and os.path.isfile(self.google_service_account_file)
        )

    @property
    def auth_method(self) -> str:
        """Determine which authentication method is available.

        Returns:
            One of: 'env_credentials', 'client_secrets', 'service_account', 'none'
        """
        if self.has_env_credentials:
            return "env_credentials"
        if self.has_client_secrets_file:
            return "client_secrets"
        if self.has_service_account:
            return "service_account"
        return "none"


# OAuth scopes required by the MCP server
GOOGLE_FORMS_SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/forms.responses.readonly",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]


def get_settings() -> Settings:
    """Create and return a Settings instance.

    This function is called once at server startup and the result
    is shared across all components via dependency injection.
    """
    return Settings()
