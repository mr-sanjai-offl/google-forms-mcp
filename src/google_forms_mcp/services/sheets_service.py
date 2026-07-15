"""Google Sheets API service layer.

Handles spreadsheet creation, data reading/writing, and export operations.
"""

from __future__ import annotations

import csv
import io
from typing import Any

from google_forms_mcp.clients.sheets_client import SheetsClient
from google_forms_mcp.exceptions import SpreadsheetNotFoundError
from google_forms_mcp.infrastructure.logging import get_logger
from google_forms_mcp.models.sheets import (
    SheetData,
    SheetProperties,
    SheetWriteResult,
    Spreadsheet,
)

logger = get_logger("sheets_service")


class SheetsService:
    """Service for Google Sheets API operations."""

    def __init__(self, sheets_client: SheetsClient) -> None:
        self._client = sheets_client

    def create(
        self,
        title: str,
        sheet_names: list[str] | None = None,
    ) -> Spreadsheet:
        """Create a new spreadsheet.

        Args:
            title: Spreadsheet title.
            sheet_names: Optional list of sheet names (default: one sheet named "Sheet1").

        Returns:
            Created Spreadsheet.
        """
        body: dict[str, Any] = {"properties": {"title": title}}

        if sheet_names:
            body["sheets"] = [
                {"properties": {"title": name, "index": idx}}
                for idx, name in enumerate(sheet_names)
            ]

        result = self._client.create(body=body)

        return self._parse_spreadsheet(result)

    def get_info(self, spreadsheet_id: str) -> Spreadsheet:
        """Get spreadsheet metadata.

        Args:
            spreadsheet_id: ID of the spreadsheet.

        Returns:
            Spreadsheet metadata.
        """
        try:
            result = self._client.get(spreadsheet_id=spreadsheet_id)
        except Exception as e:
            if "404" in str(e):
                raise SpreadsheetNotFoundError(spreadsheet_id) from e
            raise

        return self._parse_spreadsheet(result)

    def read(self, spreadsheet_id: str, range_str: str) -> SheetData:
        """Read values from a spreadsheet range.

        Args:
            spreadsheet_id: ID of the spreadsheet.
            range_str: A1 notation range (e.g., "Sheet1!A1:B10").

        Returns:
            SheetData with the values.
        """
        result = self._client.get_values(
            spreadsheet_id=spreadsheet_id,
            range_name=range_str,
        )

        return SheetData(
            range=result.get("range", ""),
            values=result.get("values", []),
            major_dimension=result.get("majorDimension", "ROWS"),
        )

    def write(
        self,
        spreadsheet_id: str,
        range_str: str,
        values: list[list[Any]],
    ) -> SheetWriteResult:
        """Write values to a spreadsheet range.

        Args:
            spreadsheet_id: ID of the spreadsheet.
            range_str: A1 notation range.
            values: 2D list of values to write.

        Returns:
            SheetWriteResult with update details.
        """
        result = self._client.update_values(
            spreadsheet_id=spreadsheet_id,
            range_name=range_str,
            body={"values": values},
            value_input_option="USER_ENTERED",
        )

        return SheetWriteResult(
            spreadsheet_id=result.get("spreadsheetId", ""),
            updated_range=result.get("updatedRange", ""),
            updated_rows=result.get("updatedRows", 0),
            updated_columns=result.get("updatedColumns", 0),
            updated_cells=result.get("updatedCells", 0),
        )

    def append(
        self,
        spreadsheet_id: str,
        range_str: str,
        values: list[list[Any]],
    ) -> SheetWriteResult:
        """Append rows to the end of a spreadsheet.

        Args:
            spreadsheet_id: ID of the spreadsheet.
            range_str: A1 notation range (data is appended after the last row).
            values: 2D list of values to append.

        Returns:
            SheetWriteResult with update details.
        """
        result = self._client.append_values(
            spreadsheet_id=spreadsheet_id,
            range_name=range_str,
            body={"values": values},
            value_input_option="USER_ENTERED",
            insert_data_option="INSERT_ROWS",
        )

        updates = result.get("updates", {})
        return SheetWriteResult(
            spreadsheet_id=updates.get("spreadsheetId", spreadsheet_id),
            updated_range=updates.get("updatedRange", ""),
            updated_rows=updates.get("updatedRows", 0),
            updated_columns=updates.get("updatedColumns", 0),
            updated_cells=updates.get("updatedCells", 0),
        )

    def export_csv(
        self,
        spreadsheet_id: str,
        sheet_name: str | None = None,
    ) -> str:
        """Export a sheet's data as a CSV string.

        Args:
            spreadsheet_id: ID of the spreadsheet.
            sheet_name: Sheet name (defaults to first sheet).

        Returns:
            CSV string of the sheet data.
        """
        range_str = f"{sheet_name}!A:ZZ" if sheet_name else "A:ZZ"

        data = self.read(spreadsheet_id, range_str)

        output = io.StringIO()
        writer = csv.writer(output)
        for row in data.values:
            writer.writerow(row)

        return output.getvalue()

    def clear_range(
        self,
        spreadsheet_id: str,
        range_str: str,
    ) -> SheetWriteResult:
        """Clear values from a range.

        Args:
            spreadsheet_id: ID of the spreadsheet.
            range_str: A1 notation range to clear.

        Returns:
            SheetWriteResult with cleared range details.
        """
        result = self._client.clear_values(spreadsheet_id=spreadsheet_id, range_name=range_str)

        return SheetWriteResult(
            spreadsheet_id=result.get("spreadsheetId", spreadsheet_id),
            updated_range=result.get("clearedRange", range_str),
            updated_rows=0,
            updated_columns=0,
            updated_cells=0,
        )

    # --- Parsing ---

    @staticmethod
    def _parse_spreadsheet(data: dict[str, Any]) -> Spreadsheet:
        """Parse a raw Sheets API response into a Spreadsheet model."""
        sheets = []
        for sheet in data.get("sheets", []):
            props = sheet.get("properties", {})
            grid_props = props.get("gridProperties", {})
            sheets.append(
                SheetProperties(
                    sheet_id=props.get("sheetId", 0),
                    title=props.get("title", ""),
                    index=props.get("index", 0),
                    row_count=grid_props.get("rowCount", 0),
                    column_count=grid_props.get("columnCount", 0),
                )
            )

        return Spreadsheet(
            spreadsheet_id=data.get("spreadsheetId", ""),
            title=data.get("properties", {}).get("title", ""),
            spreadsheet_url=data.get("spreadsheetUrl", ""),
            sheets=sheets,
        )
