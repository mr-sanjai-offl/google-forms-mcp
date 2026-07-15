from unittest.mock import MagicMock

import pytest

from google_forms_mcp.config import LogLevel, Settings, TransportMode


@pytest.fixture
def mock_settings() -> Settings:
    return Settings(
        google_client_id="test_client_id",
        google_client_secret="test_client_secret",
        google_refresh_token="test_refresh_token",
        google_forms_mcp_transport=TransportMode.STDIO,
        google_forms_mcp_port=8000,
        google_forms_mcp_log_level=LogLevel.DEBUG,
    )


@pytest.fixture
def mock_rate_limiter() -> MagicMock:
    limiter = MagicMock()
    # Mock acquire to do nothing instead of sleeping
    limiter.acquire.return_value = None
    return limiter
