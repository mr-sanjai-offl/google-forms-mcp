"""MCP tool definitions for Google Sheets operations."""

from __future__ import annotations

import json
from typing import Any

from google_forms_mcp.exceptions import GoogleFormsMCPError


def register_sheets_tools(mcp: Any, sheets_service: Any) -> None:
    """Register all Sheets-related MCP tools."""

    @mcp.tool()
    def create_spreadsheet(
        title: str,
        sheet_names: list[str] | None = None,
    ) -> str:
        """Create a new Google Sheets spreadsheet.

        Args:
            title: Title of the spreadsheet.
            sheet_names: Optional list of sheet/tab names (default: one sheet named "Sheet1").

        Returns:
            JSON string with spreadsheet details (spreadsheet_id, url, sheets).
        """
        try:
            spreadsheet = sheets_service.create(title, sheet_names=sheet_names)
            return json.dumps(spreadsheet.model_dump(exclude_none=True), indent=2)
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def get_spreadsheet_info(spreadsheet_id: str) -> str:
        """Get metadata for a Google Sheets spreadsheet.

        Args:
            spreadsheet_id: ID of the spreadsheet.

        Returns:
            JSON string with spreadsheet metadata (title, sheets, url).
        """
        try:
            info = sheets_service.get_info(spreadsheet_id)
            return json.dumps(info.model_dump(exclude_none=True), indent=2)
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def read_sheet_data(spreadsheet_id: str, range: str) -> str:
        """Read data from a spreadsheet range.

        Args:
            spreadsheet_id: ID of the spreadsheet.
            range: A1 notation range (e.g., "Sheet1!A1:D10" or "A1:B5").

        Returns:
            JSON string with the cell values as a 2D array.
        """
        try:
            data = sheets_service.read(spreadsheet_id, range)
            return json.dumps(data.model_dump(exclude_none=True), indent=2, default=str)
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def write_sheet_data(
        spreadsheet_id: str,
        range: str,
        values: list[list[Any]],
    ) -> str:
        """Write data to a spreadsheet range.

        Overwrites existing data in the specified range.

        Args:
            spreadsheet_id: ID of the spreadsheet.
            range: A1 notation range (e.g., "Sheet1!A1:D10").
            values: 2D array of values to write. Each inner list is a row.

        Returns:
            JSON string with write result (updated range, rows, cells).
        """
        try:
            result = sheets_service.write(spreadsheet_id, range, values)
            return json.dumps(result.model_dump(exclude_none=True), indent=2)
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def append_sheet_data(
        spreadsheet_id: str,
        range: str,
        values: list[list[Any]],
    ) -> str:
        """Append rows to the end of a spreadsheet.

        Adds new rows after the last row containing data.

        Args:
            spreadsheet_id: ID of the spreadsheet.
            range: A1 notation range indicating the sheet (e.g., "Sheet1!A1").
            values: 2D array of values to append. Each inner list is a row.

        Returns:
            JSON string with append result (updated range, rows, cells).
        """
        try:
            result = sheets_service.append(spreadsheet_id, range, values)
            return json.dumps(result.model_dump(exclude_none=True), indent=2)
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def export_sheet_csv(
        spreadsheet_id: str,
        sheet_name: str | None = None,
    ) -> str:
        """Export a spreadsheet sheet as CSV.

        Args:
            spreadsheet_id: ID of the spreadsheet.
            sheet_name: Name of the specific sheet (optional, defaults to first sheet).

        Returns:
            CSV string of the sheet data.
        """
        try:
            csv_data = sheets_service.export_csv(spreadsheet_id, sheet_name=sheet_name)
            return csv_data
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def clear_sheet_data(
        spreadsheet_id: str,
        range: str,
    ) -> str:
        """Clear data from a spreadsheet range.

        Args:
            spreadsheet_id: ID of the spreadsheet.
            range: A1 notation range to clear (e.g., "Sheet1!A1:D10").

        Returns:
            JSON string with clear result details.
        """
        try:
            result = sheets_service.clear_range(spreadsheet_id, range)
            return json.dumps(result.model_dump(exclude_none=True), indent=2)
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"
