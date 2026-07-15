"""MCP tool definitions for Google Drive operations."""

from __future__ import annotations

import json
from typing import Any

from google_forms_mcp.exceptions import GoogleFormsMCPError


def register_drive_tools(mcp: Any, drive_service: Any) -> None:
    """Register all Drive-related MCP tools."""

    @mcp.tool()
    def create_folder(name: str, parent_id: str | None = None) -> str:
        """Create a folder in Google Drive.

        Args:
            name: Name of the folder.
            parent_id: Parent folder ID (optional, creates in root if not specified).

        Returns:
            JSON string with folder details (folder_id, name, web_view_link).
        """
        try:
            folder = drive_service.create_folder(name, parent_id=parent_id)
            return json.dumps(folder.model_dump(exclude_none=True), indent=2)
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def search_forms(
        query: str | None = None,
        folder_id: str | None = None,
        page_size: int = 20,
    ) -> str:
        """Search for Google Forms in your Drive.

        Args:
            query: Search text to match against form names (optional).
            folder_id: Limit search to a specific folder (optional).
            page_size: Number of results to return (default 20, max 100).

        Returns:
            JSON string with list of matching forms.
        """
        try:
            files, next_token = drive_service.search_forms(
                query=query, folder_id=folder_id, page_size=page_size
            )
            result = {
                "forms": [f.model_dump(mode="json", exclude_none=True) for f in files],
                "total_in_page": len(files),
                "next_page_token": next_token,
            }
            return json.dumps(result, indent=2, default=str)
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def search_files(
        query: str | None = None,
        mime_type: str | None = None,
        folder_id: str | None = None,
        page_size: int = 20,
    ) -> str:
        """Search for files in Google Drive.

        Args:
            query: Search text to match against file names (optional).
            mime_type: Filter by MIME type (optional). Examples:
                - "application/vnd.google-apps.form" for Google Forms
                - "application/vnd.google-apps.spreadsheet" for Google Sheets
                - "application/vnd.google-apps.folder" for folders
            folder_id: Limit search to a specific folder (optional).
            page_size: Number of results to return (default 20, max 100).

        Returns:
            JSON string with list of matching files.
        """
        try:
            files, next_token = drive_service.search_files(
                query=query, mime_type=mime_type, folder_id=folder_id, page_size=page_size
            )
            result = {
                "files": [f.model_dump(mode="json", exclude_none=True) for f in files],
                "total_in_page": len(files),
                "next_page_token": next_token,
            }
            return json.dumps(result, indent=2, default=str)
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def move_file(
        file_id: str,
        new_parent_id: str,
        remove_from_current: bool = True,
    ) -> str:
        """Move a file to a different folder in Google Drive.

        Args:
            file_id: ID of the file to move.
            new_parent_id: ID of the destination folder.
            remove_from_current: Remove from current parent folder (default True).

        Returns:
            JSON string with updated file details.
        """
        try:
            file = drive_service.move_file(file_id, new_parent_id, remove_from_current)
            return json.dumps(
                file.model_dump(mode="json", exclude_none=True), indent=2, default=str
            )
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def copy_file(
        file_id: str,
        new_name: str | None = None,
        folder_id: str | None = None,
    ) -> str:
        """Copy a file in Google Drive.

        Args:
            file_id: ID of the file to copy.
            new_name: Name for the copy (optional).
            folder_id: Destination folder ID (optional).

        Returns:
            JSON string with the copied file details.
        """
        try:
            file = drive_service.copy_file(file_id, new_name=new_name, folder_id=folder_id)
            return json.dumps(
                file.model_dump(mode="json", exclude_none=True), indent=2, default=str
            )
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def trash_file(file_id: str) -> str:
        """Move a file to the trash in Google Drive.

        The file can be recovered from trash within 30 days.

        Args:
            file_id: ID of the file to trash.

        Returns:
            Confirmation message.
        """
        try:
            drive_service.trash_file(file_id)
            return json.dumps({"status": "success", "message": f"File {file_id} moved to trash."})
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def restore_file(file_id: str) -> str:
        """Restore a file from the trash in Google Drive.

        Args:
            file_id: ID of the file to restore.

        Returns:
            Confirmation message.
        """
        try:
            drive_service.restore_file(file_id)
            return json.dumps(
                {"status": "success", "message": f"File {file_id} restored from trash."}
            )
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def get_file_metadata(file_id: str) -> str:
        """Get full metadata for a file in Google Drive.

        Args:
            file_id: ID of the file.

        Returns:
            JSON string with complete file details.
        """
        try:
            file = drive_service.get_file_metadata(file_id)
            return json.dumps(
                file.model_dump(mode="json", exclude_none=True), indent=2, default=str
            )
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def share_file(
        file_id: str,
        email_or_domain: str,
        role: str = "reader",
        share_type: str = "user",
    ) -> str:
        """Share a file with a user, group, or domain.

        Args:
            file_id: ID of the file to share.
            email_or_domain: Email address (for user/group) or domain name.
            role: Permission level — "reader", "commenter", "writer", or "organizer".
            share_type: Who to share with — "user", "group", "domain", or "anyone".

        Returns:
            JSON string with the created permission details.
        """
        try:
            perm = drive_service.share(file_id, email_or_domain, role=role, share_type=share_type)
            return json.dumps(perm.model_dump(exclude_none=True), indent=2)
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def get_permissions(file_id: str) -> str:
        """List all sharing permissions for a file.

        Args:
            file_id: ID of the file.

        Returns:
            JSON string with list of permissions.
        """
        try:
            perms = drive_service.list_permissions(file_id)
            result = [p.model_dump(exclude_none=True) for p in perms]
            return json.dumps(result, indent=2)
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def remove_permission(file_id: str, permission_id: str) -> str:
        """Remove a sharing permission from a file.

        Args:
            file_id: ID of the file.
            permission_id: ID of the permission to remove.

        Returns:
            Confirmation message.
        """
        try:
            drive_service.remove_permission(file_id, permission_id)
            return json.dumps(
                {"status": "success", "message": f"Permission {permission_id} removed."}
            )
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def transfer_ownership(file_id: str, email: str) -> str:
        """Transfer file ownership to another user.

        Args:
            file_id: ID of the file.
            email: Email address of the new owner.

        Returns:
            JSON string with the created permission details.
        """
        try:
            perm = drive_service.transfer_ownership(file_id, email)
            return json.dumps(perm.model_dump(exclude_none=True), indent=2)
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"
