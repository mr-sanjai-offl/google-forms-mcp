"""Google Sheets API Client."""

from __future__ import annotations

from typing import Any

from google_forms_mcp.clients.base_client import BaseGoogleClient


class SheetsClient(BaseGoogleClient):
    """Client for Google Sheets API v4."""

    def create(self, body: dict[str, Any]) -> dict[str, Any]:
        """Create a new spreadsheet.

        Args:
            body: Spreadsheet properties.

        Returns:
            Created spreadsheet metadata.
        """
        request = self._resource.spreadsheets().create(body=body)
        return self.execute(request)

    def get(self, spreadsheet_id: str, include_grid_data: bool = False) -> dict[str, Any]:
        """Get spreadsheet metadata.

        Args:
            spreadsheet_id: The ID of the spreadsheet.
            include_grid_data: Whether to include cell data.

        Returns:
            Spreadsheet metadata.
        """
        request = self._resource.spreadsheets().get(
            spreadsheetId=spreadsheet_id,
            includeGridData=include_grid_data
        )
        return self.execute(request)

    def get_values(self, spreadsheet_id: str, range_name: str, value_render_option: str = "FORMATTED_VALUE", date_time_render_option: str = "SERIAL_NUMBER") -> dict[str, Any]:
        """Read values from a range.

        Args:
            spreadsheet_id: The ID of the spreadsheet.
            range_name: The A1 notation of the range.
            value_render_option: How values should be represented.
            date_time_render_option: How dates should be represented.

        Returns:
            Value range data.
        """
        request = self._resource.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueRenderOption=value_render_option,
            dateTimeRenderOption=date_time_render_option
        )
        return self.execute(request)

    def update_values(self, spreadsheet_id: str, range_name: str, body: dict[str, Any], value_input_option: str = "USER_ENTERED") -> dict[str, Any]:
        """Update values in a range.

        Args:
            spreadsheet_id: The ID of the spreadsheet.
            range_name: The A1 notation of the range.
            body: Value range to write.
            value_input_option: How input data should be interpreted.

        Returns:
            Update response.
        """
        request = self._resource.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            body=body,
            valueInputOption=value_input_option
        )
        return self.execute(request, token_cost=2)

    def append_values(self, spreadsheet_id: str, range_name: str, body: dict[str, Any], value_input_option: str = "USER_ENTERED", insert_data_option: str = "INSERT_ROWS") -> dict[str, Any]:
        """Append values to a range.

        Args:
            spreadsheet_id: The ID of the spreadsheet.
            range_name: The A1 notation of the range to search for a table.
            body: Value range to append.
            value_input_option: How input data should be interpreted.
            insert_data_option: How existing data should be shifted.

        Returns:
            Append response.
        """
        request = self._resource.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            body=body,
            valueInputOption=value_input_option,
            insertDataOption=insert_data_option
        )
        return self.execute(request, token_cost=2)
