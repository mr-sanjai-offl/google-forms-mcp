"""Google Drive API Client."""

from __future__ import annotations

from typing import Any

from google_forms_mcp.clients.base_client import BaseGoogleClient


class DriveClient(BaseGoogleClient):
    """Client for Google Drive API v3."""

    def create_file(self, body: dict[str, Any], fields: str = "id, name, mimeType") -> dict[str, Any]:
        """Create a file or folder.

        Args:
            body: File metadata.
            fields: Fields to include in the response.

        Returns:
            Created file metadata.
        """
        request = self._resource.files().create(body=body, fields=fields)
        return self.execute(request)

    def list_files(self, query: str, fields: str = "nextPageToken, files(id, name, mimeType, parents, trashed)", page_size: int = 10, page_token: str | None = None) -> dict[str, Any]:
        """Search for files.

        Args:
            query: The search query.
            fields: Fields to include in the response.
            page_size: Number of results per page.
            page_token: Page token for pagination.

        Returns:
            List of files and next page token.
        """
        kwargs: dict[str, Any] = {"q": query, "fields": fields, "pageSize": page_size}
        if page_token:
            kwargs["pageToken"] = page_token

        request = self._resource.files().list(**kwargs)
        return self.execute(request)

    def update_file(self, file_id: str, body: dict[str, Any] | None = None, add_parents: str | None = None, remove_parents: str | None = None, fields: str = "id, name, parents, trashed") -> dict[str, Any]:
        """Update a file's metadata or parent folders (move).

        Args:
            file_id: The ID of the file.
            body: File metadata updates.
            add_parents: Comma-separated list of parent IDs to add.
            remove_parents: Comma-separated list of parent IDs to remove.
            fields: Fields to include in the response.

        Returns:
            Updated file metadata.
        """
        kwargs: dict[str, Any] = {"fileId": file_id, "fields": fields}
        if body:
            kwargs["body"] = body
        if add_parents:
            kwargs["addParents"] = add_parents
        if remove_parents:
            kwargs["removeParents"] = remove_parents

        request = self._resource.files().update(**kwargs)
        return self.execute(request)

    def delete_file(self, file_id: str) -> None:
        """Permanently delete a file.

        Args:
            file_id: The ID of the file.
        """
        request = self._resource.files().delete(fileId=file_id)
        self.execute(request)

    def copy_file(self, file_id: str, body: dict[str, Any], fields: str = "id, name, parents") -> dict[str, Any]:
        """Copy a file.

        Args:
            file_id: The ID of the file to copy.
            body: Metadata for the new copy.
            fields: Fields to include in the response.

        Returns:
            Copied file metadata.
        """
        request = self._resource.files().copy(fileId=file_id, body=body, fields=fields)
        return self.execute(request)

    def create_permission(self, file_id: str, body: dict[str, Any], send_notification_email: bool = False, fields: str = "id, type, role, emailAddress") -> dict[str, Any]:
        """Create a sharing permission on a file.

        Args:
            file_id: The ID of the file.
            body: Permission specification.
            send_notification_email: Whether to notify users.
            fields: Fields to include in the response.

        Returns:
            Created permission details.
        """
        request = self._resource.permissions().create(
            fileId=file_id,
            body=body,
            sendNotificationEmail=send_notification_email,
            fields=fields
        )
        return self.execute(request)

    def list_permissions(self, file_id: str, fields: str = "permissions(id, type, role, emailAddress)") -> dict[str, Any]:
        """List permissions for a file.

        Args:
            file_id: The ID of the file.
            fields: Fields to include in the response.

        Returns:
            List of permissions.
        """
        request = self._resource.permissions().list(fileId=file_id, fields=fields)
        return self.execute(request)

    def delete_permission(self, file_id: str, permission_id: str) -> None:
        """Remove a permission from a file.

        Args:
            file_id: The ID of the file.
            permission_id: The ID of the permission.
        """
        request = self._resource.permissions().delete(fileId=file_id, permissionId=permission_id)
        self.execute(request)
