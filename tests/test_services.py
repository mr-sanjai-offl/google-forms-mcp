"""Tests for the DriveService and SheetsService (service layer)."""

from datetime import datetime
from unittest.mock import MagicMock

from google_forms_mcp.models import drive as _drive_module
from google_forms_mcp.models.drive import DriveFile
from google_forms_mcp.services.drive_service import DriveService

# Inject datetime into the drive module namespace before rebuilding
_drive_module.datetime = datetime  # type: ignore[attr-defined]
DriveFile.model_rebuild()


def test_search_forms():
    """Test search_forms delegates to search_files with correct mime type."""
    mock_client = MagicMock()
    mock_client.list_files.return_value = {
        "files": [
            {
                "id": "form1",
                "name": "Test Form",
                "mimeType": "application/vnd.google-apps.form",
                "webViewLink": "https://docs.google.com/forms/d/form1",
            }
        ]
    }
    service = DriveService(mock_client)

    files, _next_token = service.search_forms(query="Test")
    assert len(files) == 1
    assert files[0].file_id == "form1"
    assert files[0].name == "Test Form"

    # Verify the query included forms mime type
    call_args = mock_client.list_files.call_args
    assert "application/vnd.google-apps.form" in call_args.kwargs["query"]


def test_create_folder():
    """Test folder creation."""
    mock_client = MagicMock()
    mock_client.create_file.return_value = {
        "id": "folder123",
        "name": "New Folder",
        "webViewLink": "https://drive.google.com/folder123",
    }
    service = DriveService(mock_client)

    folder = service.create_folder("New Folder")
    assert folder.folder_id == "folder123"
    assert folder.name == "New Folder"


def test_trash_file():
    """Test trashing a file."""
    mock_client = MagicMock()
    service = DriveService(mock_client)

    service.trash_file("file123")
    mock_client.update_file.assert_called_once_with(file_id="file123", body={"trashed": True})


def test_share_file():
    """Test sharing a file with a user."""
    mock_client = MagicMock()
    mock_client.create_permission.return_value = {
        "id": "perm1",
        "role": "writer",
        "type": "user",
        "emailAddress": "user@example.com",
    }
    service = DriveService(mock_client)

    perm = service.share("file1", "user@example.com", role="writer")
    assert perm.role == "writer"
    assert perm.email_address == "user@example.com"


def test_get_file_metadata_caching():
    """Test that get_file_metadata caches results."""
    mock_client = MagicMock()
    mock_client.get_file.return_value = {
        "id": "file1",
        "name": "cached.pdf",
        "mimeType": "application/pdf",
    }
    service = DriveService(mock_client)

    # First call: hits the API
    result1 = service.get_file_metadata("file1")
    assert result1.file_id == "file1"

    # Second call: should be cached, no second API call
    result2 = service.get_file_metadata("file1")
    assert result2.file_id == "file1"

    # Client should only have been called once
    assert mock_client.get_file.call_count == 1
