from unittest.mock import MagicMock, patch

from google_forms_mcp.auth.credential_manager import CredentialManager


def test_credential_manager_loads_from_settings(mock_settings):
    """Test that credential manager properly loads from settings env vars."""
    manager = CredentialManager(mock_settings)

    # Need to mock the token.json loading or verify the structure
    # Since we don't have a token.json, we expect it to attempt to parse the string

    with patch("google_forms_mcp.auth.token_manager.TokenManager.load_token") as mock_load:
        mock_load.return_value = {"token": "fake", "refresh_token": "fake"}

        with patch("google.oauth2.credentials.Credentials.from_authorized_user_info") as mock_from:
            mock_creds = MagicMock()
            mock_creds.valid = True
            mock_from.return_value = mock_creds

            creds = manager.get_valid_credentials()
            assert creds is not None
            assert creds.valid
