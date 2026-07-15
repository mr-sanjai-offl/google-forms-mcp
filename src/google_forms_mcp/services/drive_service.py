"""Google Drive API service layer.

Handles file management, folder creation, permission management,
and search operations via the Google Drive API v3.
"""

from __future__ import annotations

from typing import Any

from google_forms_mcp.exceptions import NotFoundError, PermissionDeniedError
from google_forms_mcp.infrastructure.logging import get_logger
from google_forms_mcp.infrastructure.rate_limiter import RateLimiter
from google_forms_mcp.infrastructure.retry import with_retry
from google_forms_mcp.models.drive import (
    DriveFile,
    DriveFolder,
    DrivePermission,
    ShareRole,
    ShareType,
)

logger = get_logger("drive_service")

GOOGLE_FORMS_MIME_TYPE = "application/vnd.google-apps.form"
GOOGLE_FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"


class DriveService:
    """Service for Google Drive API operations."""

    def __init__(self, drive_client: Any, rate_limiter: RateLimiter) -> None:
        self._client = drive_client
        self._limiter = rate_limiter

    # --- Folder Operations ---

    @with_retry()
    def create_folder(self, name: str, parent_id: str | None = None) -> DriveFolder:
        """Create a new folder in Google Drive.

        Args:
            name: Folder name.
            parent_id: Parent folder ID (optional, defaults to root).

        Returns:
            Created DriveFolder.
        """
        self._limiter.acquire("drive_write")

        metadata: dict[str, Any] = {
            "name": name,
            "mimeType": GOOGLE_FOLDER_MIME_TYPE,
        }
        if parent_id:
            metadata["parents"] = [parent_id]

        result = self._client.files().create(
            body=metadata, fields="id,name,parents,webViewLink"
        ).execute()

        return DriveFolder(
            folder_id=result.get("id", ""),
            name=result.get("name", ""),
            parent_id=parent_id or "",
            web_view_link=result.get("webViewLink", ""),
        )

    # --- File Operations ---

    @with_retry()
    def search_files(
        self,
        query: str | None = None,
        mime_type: str | None = None,
        folder_id: str | None = None,
        page_size: int = 20,
        page_token: str | None = None,
    ) -> tuple[list[DriveFile], str | None]:
        """Search for files in Google Drive.

        Args:
            query: Search query string (file name search).
            mime_type: Filter by MIME type.
            folder_id: Search within a specific folder.
            page_size: Number of results per page.
            page_token: Token for pagination.

        Returns:
            Tuple of (list of files, next page token).
        """
        self._limiter.acquire("drive_read")

        q_parts = ["trashed = false"]
        if query:
            q_parts.append(f"name contains '{query}'")
        if mime_type:
            q_parts.append(f"mimeType = '{mime_type}'")
        if folder_id:
            q_parts.append(f"'{folder_id}' in parents")

        q_string = " and ".join(q_parts)

        kwargs: dict[str, Any] = {
            "q": q_string,
            "pageSize": min(page_size, 100),
            "fields": "nextPageToken,files(id,name,mimeType,createdTime,modifiedTime,size,parents,webViewLink,trashed,owners)",
            "orderBy": "modifiedTime desc",
        }
        if page_token:
            kwargs["pageToken"] = page_token

        result = self._client.files().list(**kwargs).execute()

        files = [self._parse_file(f) for f in result.get("files", [])]
        next_token = result.get("nextPageToken")

        return files, next_token

    def search_forms(
        self,
        query: str | None = None,
        folder_id: str | None = None,
        page_size: int = 20,
    ) -> tuple[list[DriveFile], str | None]:
        """Search specifically for Google Forms.

        Args:
            query: Search query string.
            folder_id: Search within a specific folder.
            page_size: Number of results per page.

        Returns:
            Tuple of (list of form files, next page token).
        """
        return self.search_files(
            query=query,
            mime_type=GOOGLE_FORMS_MIME_TYPE,
            folder_id=folder_id,
            page_size=page_size,
        )

    @with_retry()
    def copy_file(
        self,
        file_id: str,
        new_name: str | None = None,
        folder_id: str | None = None,
    ) -> DriveFile:
        """Copy a file in Google Drive.

        Args:
            file_id: ID of the file to copy.
            new_name: Name for the copy (optional).
            folder_id: Destination folder ID (optional).

        Returns:
            The copied DriveFile.
        """
        self._limiter.acquire("drive_write")

        body: dict[str, Any] = {}
        if new_name:
            body["name"] = new_name
        if folder_id:
            body["parents"] = [folder_id]

        result = self._client.files().copy(
            fileId=file_id,
            body=body,
            fields="id,name,mimeType,createdTime,webViewLink,parents",
        ).execute()

        return self._parse_file(result)

    @with_retry()
    def move_file(
        self,
        file_id: str,
        new_parent_id: str,
        remove_from_current: bool = True,
    ) -> DriveFile:
        """Move a file to a different folder.

        Args:
            file_id: ID of the file to move.
            new_parent_id: Destination folder ID.
            remove_from_current: Whether to remove from current parent.

        Returns:
            Updated DriveFile.
        """
        self._limiter.acquire("drive_write")

        kwargs: dict[str, Any] = {
            "fileId": file_id,
            "addParents": new_parent_id,
            "fields": "id,name,mimeType,parents,webViewLink",
        }

        if remove_from_current:
            # Get current parents
            current = self._client.files().get(
                fileId=file_id, fields="parents"
            ).execute()
            current_parents = ",".join(current.get("parents", []))
            if current_parents:
                kwargs["removeParents"] = current_parents

        result = self._client.files().update(**kwargs).execute()
        return self._parse_file(result)

    @with_retry()
    def trash_file(self, file_id: str) -> None:
        """Move a file to trash.

        Args:
            file_id: ID of the file to trash.
        """
        self._limiter.acquire("drive_write")

        self._client.files().update(
            fileId=file_id,
            body={"trashed": True},
        ).execute()
        logger.info("Trashed file: %s", file_id)

    @with_retry()
    def delete_file(self, file_id: str) -> None:
        """Permanently delete a file.

        Args:
            file_id: ID of the file to delete permanently.
        """
        self._limiter.acquire("drive_write")

        self._client.files().delete(fileId=file_id).execute()
        logger.info("Permanently deleted file: %s", file_id)

    # --- Permissions ---

    @with_retry()
    def share(
        self,
        file_id: str,
        email_or_domain: str,
        role: str = "reader",
        share_type: str = "user",
        send_notification: bool = True,
    ) -> DrivePermission:
        """Share a file with a user, group, or domain.

        Args:
            file_id: ID of the file to share.
            email_or_domain: Email address or domain.
            role: Permission role (reader, commenter, writer, organizer).
            share_type: Permission type (user, group, domain, anyone).
            send_notification: Whether to send an email notification.

        Returns:
            Created DrivePermission.
        """
        self._limiter.acquire("drive_write")

        body: dict[str, Any] = {
            "role": role,
            "type": share_type,
        }

        if share_type in ("user", "group"):
            body["emailAddress"] = email_or_domain
        elif share_type == "domain":
            body["domain"] = email_or_domain

        result = self._client.permissions().create(
            fileId=file_id,
            body=body,
            sendNotificationEmail=send_notification,
            fields="id,role,type,emailAddress,displayName,domain",
        ).execute()

        return self._parse_permission(result)

    @with_retry()
    def list_permissions(self, file_id: str) -> list[DrivePermission]:
        """List all permissions for a file.

        Args:
            file_id: ID of the file.

        Returns:
            List of DrivePermission objects.
        """
        self._limiter.acquire("drive_read")

        result = self._client.permissions().list(
            fileId=file_id,
            fields="permissions(id,role,type,emailAddress,displayName,domain)",
        ).execute()

        return [
            self._parse_permission(p) for p in result.get("permissions", [])
        ]

    @with_retry()
    def remove_permission(self, file_id: str, permission_id: str) -> None:
        """Remove a permission from a file.

        Args:
            file_id: ID of the file.
            permission_id: ID of the permission to remove.
        """
        self._limiter.acquire("drive_write")

        self._client.permissions().delete(
            fileId=file_id, permissionId=permission_id
        ).execute()
        logger.info("Removed permission %s from file %s", permission_id, file_id)

    # --- Parsing Helpers ---

    @staticmethod
    def _parse_file(data: dict[str, Any]) -> DriveFile:
        """Parse a raw Drive file response into a DriveFile model."""
        owners = []
        for owner in data.get("owners", []):
            owners.append(owner.get("emailAddress", owner.get("displayName", "")))

        return DriveFile(
            file_id=data.get("id", ""),
            name=data.get("name", ""),
            mime_type=data.get("mimeType", ""),
            created_time=data.get("createdTime"),
            modified_time=data.get("modifiedTime"),
            size=data.get("size"),
            parents=data.get("parents", []),
            web_view_link=data.get("webViewLink", ""),
            trashed=data.get("trashed", False),
            owners=owners,
        )

    @staticmethod
    def _parse_permission(data: dict[str, Any]) -> DrivePermission:
        """Parse a raw Drive permission into a DrivePermission model."""
        return DrivePermission(
            permission_id=data.get("id", ""),
            role=data.get("role", "reader"),
            type=data.get("type", "user"),
            email_address=data.get("emailAddress", ""),
            display_name=data.get("displayName", ""),
            domain=data.get("domain", ""),
        )
