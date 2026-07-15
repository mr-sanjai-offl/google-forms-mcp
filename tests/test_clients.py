import json
from unittest.mock import MagicMock

import pytest
from googleapiclient.errors import HttpError
from httplib2 import Response

from google_forms_mcp.clients.forms_client import FormsClient
from google_forms_mcp.exceptions import GoogleFormsMCPError


def test_forms_client_get_form(mock_rate_limiter, mock_settings):
    raw_forms = MagicMock()
    # Mock the execute chain: raw_forms.forms().get().execute()
    mock_get = MagicMock()
    mock_get.execute.return_value = {"formId": "123", "info": {"title": "Test Form"}}
    raw_forms.forms.return_value.get.return_value = mock_get

    client = FormsClient(raw_forms, mock_rate_limiter, mock_settings)
    result = client.get("123")

    assert result["formId"] == "123"
    assert result["info"]["title"] == "Test Form"


def test_forms_client_get_form_http_error(mock_rate_limiter, mock_settings):
    raw_forms = MagicMock()
    mock_get = MagicMock()

    # Create an HttpError 404
    resp = Response({"status": "404", "reason": "Not Found"})
    error_content = json.dumps({"error": {"message": "Requested entity was not found."}}).encode(
        "utf-8"
    )
    mock_get.execute.side_effect = HttpError(resp, error_content)
    raw_forms.forms.return_value.get.return_value = mock_get

    client = FormsClient(raw_forms, mock_rate_limiter, mock_settings)

    with pytest.raises(GoogleFormsMCPError) as exc_info:
        client.get("123")

    assert "not found" in str(exc_info.value).lower()
