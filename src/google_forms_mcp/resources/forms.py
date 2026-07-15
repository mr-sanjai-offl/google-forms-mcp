"""MCP resource definitions for Google Forms.

Resources provide stateful, read-only data to the MCP client.
"""

from __future__ import annotations

import json
from typing import Any

from google_forms_mcp.exceptions import GoogleFormsMCPError


def register_resources(mcp: Any, forms_service: Any, drive_service: Any) -> None:
    """Register all forms-related MCP resources.

    Args:
        mcp: FastMCP server instance.
        forms_service: FormsService instance.
        drive_service: DriveService instance.
    """

    @mcp.resource("forms://list")
    def list_forms() -> str:
        """List all Google Forms accessible to the authenticated user.
        
        Searches Google Drive for files with the form mime type.
        """
        try:
            files, _ = drive_service.search_forms(page_size=100)
            return json.dumps([f.model_dump(exclude_none=True) for f in files], indent=2)
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.resource("forms://{form_id}")
    def get_form_resource(form_id: str) -> str:
        """Get the complete structure and metadata for a specific form.
        
        Args:
            form_id: The ID of the form.
        """
        try:
            form = forms_service.get(form_id)
            if hasattr(form, "model_dump"):
                return json.dumps(form.model_dump(mode="json", exclude_none=True), indent=2, default=str)
            return json.dumps(form, indent=2, default=str)
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.resource("forms://{form_id}/responses")
    def get_form_responses(form_id: str) -> str:
        """Get all responses for a specific form.
        
        Args:
            form_id: The ID of the form.
        """
        try:
            # Fetch all responses (pagination abstracted for resource)
            all_responses = []
            next_token = None

            while True:
                responses, next_token = forms_service.list_responses(
                    form_id, page_size=5000, page_token=next_token
                )
                all_responses.extend(responses)
                if not next_token:
                    break

            return json.dumps([r.model_dump(mode="json", exclude_none=True) for r in all_responses], indent=2, default=str)
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.resource("forms://{form_id}/summary")
    def get_form_summary(form_id: str) -> str:
        """Get aggregated summary statistics for a specific form's responses.
        
        Args:
            form_id: The ID of the form.
        """
        try:
            from google_forms_mcp.services.analytics_service import AnalyticsService

            form = forms_service.get(form_id)
            all_responses = []
            next_token = None

            while True:
                responses, next_token = forms_service.list_responses(
                    form_id, page_size=5000, page_token=next_token
                )
                all_responses.extend(responses)
                if not next_token:
                    break

            analytics = AnalyticsService()
            summary = analytics.compute_summary(form, all_responses)
            if hasattr(summary, "model_dump"):
                return json.dumps(summary.model_dump(mode="json", exclude_none=True), indent=2, default=str)
            return json.dumps(summary, indent=2, default=str)
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"
