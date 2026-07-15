"""Tests for the server module (MCP server bootstrap)."""

from unittest.mock import MagicMock, patch

from fastmcp import FastMCP


def test_server_creation():
    """Test that the FastMCP server can be created without errors when auth is mocked."""
    # We must mock the credential manager since we have no real Google credentials
    with patch("google_forms_mcp.server.CredentialManager") as mock_cred_mgr:
        mock_instance = MagicMock()
        mock_creds = MagicMock()
        mock_creds.token = "fake-token"
        mock_creds.valid = True
        mock_instance.get_valid_credentials.return_value = mock_creds
        mock_cred_mgr.return_value = mock_instance

        # Also mock the Google API discovery builders
        with patch("google_forms_mcp.server.build") as mock_build:
            mock_build.return_value = MagicMock()

            from google_forms_mcp.server import create_server

            mcp = create_server()
            assert mcp is not None
            assert isinstance(mcp, FastMCP)
