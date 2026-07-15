"""Data models for Google Sheets entities."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class SheetProperties(BaseModel):
    """Properties of a single sheet within a spreadsheet."""

    sheet_id: int = 0
    title: str = ""
    index: int = 0
    row_count: int = 0
    column_count: int = 0


class Spreadsheet(BaseModel):
    """Representation of a Google Sheets spreadsheet."""

    spreadsheet_id: str = ""
    title: str = ""
    spreadsheet_url: str = ""
    sheets: list[SheetProperties] = Field(default_factory=list)


class SheetData(BaseModel):
    """Data read from a spreadsheet range."""

    range: str = ""
    values: list[list[Any]] = Field(default_factory=list)
    major_dimension: str = "ROWS"


class SheetWriteResult(BaseModel):
    """Result of a write/append operation."""

    spreadsheet_id: str = ""
    updated_range: str = ""
    updated_rows: int = 0
    updated_columns: int = 0
    updated_cells: int = 0
