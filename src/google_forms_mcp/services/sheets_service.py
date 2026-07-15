"""Google Sheets API service layer.

Handles spreadsheet creation, data reading/writing, and export operations.
"""

from __future__ import annotations

import csv
import io
from typing import Any

from google_forms_mcp.exceptions import SpreadsheetNotFoundError
from google_forms_mcp.infrastructure.logging import get_logger
from google_forms_mcp.infrastructure.rate_limiter import RateLimiter
from google_forms_mcp.infrastructure.retry import with_retry
from google_forms_mcp.models.sheets import (
    SheetData,
    SheetProperties,
    SheetWriteResult,
    Spreadsheet,
)

logger = get_logger("sheets_service")


class SheetsService:
    """Service for Google Sheets API operations."""

    def __init__(self, sheets_client: Any, rate_limiter: RateLimiter) -> None:
        self._client = sheets_client
        self._limiter = rate_limiter

    @with_retry()
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
        self._limiter.acquire("sheets_write")

        body: dict[str, Any] = {"properties": {"title": title}}

        if sheet_names:
            body["sheets"] = [
                {"properties": {"title": name, "index": idx}}
                for idx, name in enumerate(sheet_names)
            ]

        result = self._client.spreadsheets().create(
            body=body, fields="spreadsheetId,properties,spreadsheetUrl,sheets"
        ).execute()

        return self._parse_spreadsheet(result)

    @with_retry()
    def get_info(self, spreadsheet_id: str) -> Spreadsheet:
        """Get spreadsheet metadata.

        Args:
            spreadsheet_id: ID of the spreadsheet.

        Returns:
            Spreadsheet metadata.
        """
        self._limiter.acquire("sheets_read")

        try:
            result = self._client.spreadsheets().get(
                spreadsheetId=spreadsheet_id,
                fields="spreadsheetId,properties,spreadsheetUrl,sheets",
            ).execute()
        except Exception as e:
            if "404" in str(e):
                raise SpreadsheetNotFoundError(spreadsheet_id) from e
            raise

        return self._parse_spreadsheet(result)

    @with_retry()
    def read(self, spreadsheet_id: str, range_str: str) -> SheetData:
        """Read values from a spreadsheet range.

        Args:
            spreadsheet_id: ID of the spreadsheet.
            range_str: A1 notation range (e.g., "Sheet1!A1:B10").

        Returns:
            SheetData with the values.
        """
        self._limiter.acquire("sheets_read")

        result = self._client.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_str,
        ).execute()

        return SheetData(
            range=result.get("range", ""),
            values=result.get("values", []),
            major_dimension=result.get("majorDimension", "ROWS"),
        )

    @with_retry()
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
        self._limiter.acquire("sheets_write")

        result = self._client.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_str,
            valueInputOption="USER_ENTERED",
            body={"values": values},
        ).execute()

        return SheetWriteResult(
            spreadsheet_id=result.get("spreadsheetId", ""),
            updated_range=result.get("updatedRange", ""),
            updated_rows=result.get("updatedRows", 0),
            updated_columns=result.get("updatedColumns", 0),
            updated_cells=result.get("updatedCells", 0),
        )

    @with_retry()
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
        self._limiter.acquire("sheets_write")

        result = self._client.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_str,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": values},
        ).execute()

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
