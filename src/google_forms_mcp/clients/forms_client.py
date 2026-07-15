"""Google Forms API Client."""

from __future__ import annotations

from typing import Any

from google_forms_mcp.clients.base_client import BaseGoogleClient


class FormsClient(BaseGoogleClient):
    """Client for Google Forms API v1."""

    def create(self, body: dict[str, Any]) -> dict[str, Any]:
        """Create a new form.

        Args:
            body: Form definition.

        Returns:
            Created form metadata.
        """
        request = self._resource.forms().create(body=body)
        return self.execute(request)

    def get(self, form_id: str) -> dict[str, Any]:
        """Get a form by ID.

        Args:
            form_id: The ID of the form.

        Returns:
            Complete form metadata and structure.
        """
        request = self._resource.forms().get(formId=form_id)
        return self.execute(request)

    def batch_update(self, form_id: str, requests: list[dict[str, Any]]) -> dict[str, Any]:
        """Apply a batch update to a form.

        Args:
            form_id: The ID of the form.
            requests: List of mutation requests.

        Returns:
            Batch update response.
        """
        body = {"requests": requests}
        # Write operations often consume more quota, passing token_cost=2 as a heuristic
        request = self._resource.forms().batchUpdate(formId=form_id, body=body)
        return self.execute(request, token_cost=2)

    def list_responses(self, form_id: str, page_size: int = 50, page_token: str | None = None, filter_str: str | None = None) -> dict[str, Any]:
        """List responses for a form.
        
        Args:
            form_id: The ID of the form.
            page_size: Maximum number of responses to return.
            page_token: Page token for pagination.
            filter_str: Filter expression.
            
        Returns:
            List of responses and next page token.
        """
        kwargs: dict[str, Any] = {"formId": form_id, "pageSize": page_size}
        if page_token:
            kwargs["pageToken"] = page_token
        if filter_str:
            kwargs["filter"] = filter_str

        request = self._resource.forms().responses().list(**kwargs)
        return self.execute(request)

    def get_response(self, form_id: str, response_id: str) -> dict[str, Any]:
        """Get a specific response for a form.
        
        Args:
            form_id: The ID of the form.
            response_id: The ID of the response.
            
        Returns:
            The response details.
        """
        request = self._resource.forms().responses().get(formId=form_id, responseId=response_id)
        return self.execute(request)

    def set_publish_settings(self, form_id: str, body: dict[str, Any]) -> dict[str, Any]:
        """Set publish settings for a form.
        
        Args:
            form_id: The ID of the form.
            body: Publish settings specification.
            
        Returns:
            Publish settings response.
        """
        request = self._resource.forms().setPublishSettings(formId=form_id, body=body)
        return self.execute(request, token_cost=2)
