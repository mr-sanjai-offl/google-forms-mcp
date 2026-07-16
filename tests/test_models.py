"""Tests for the Pydantic domain models."""

from datetime import datetime

from google_forms_mcp.models import drive as _drive_module
from google_forms_mcp.models.drive import (
    DriveFile,
    DriveFolder,
    DrivePermission,
    ShareRole,
    ShareType,
)
from google_forms_mcp.models.form import (
    FormCreateRequest,
    QuestionCreateRequest,
    QuestionType,
    SectionCreateRequest,
    SettingsUpdateRequest,
)
from google_forms_mcp.models.sheets import SheetData, SheetWriteResult, Spreadsheet

# Inject datetime into the drive module namespace before rebuilding
# (needed because drive.py uses `from __future__ import annotations` with TYPE_CHECKING)
_drive_module.datetime = datetime  # type: ignore[attr-defined]
DriveFile.model_rebuild()


# ---- Form Models ----


def test_form_create_request_minimal():
    req = FormCreateRequest(title="My Form")
    assert req.title == "My Form"
    assert req.is_quiz is False


def test_form_create_request_quiz():
    req = FormCreateRequest(title="Quiz", is_quiz=True)
    assert req.is_quiz is True


def test_question_create_request_short_answer():
    req = QuestionCreateRequest(
        title="Your name",
        question_type=QuestionType.SHORT_ANSWER,
        required=True,
    )
    assert req.question_type == QuestionType.SHORT_ANSWER
    assert req.required is True


def test_question_create_request_multiple_choice():
    req = QuestionCreateRequest(
        title="Pick one",
        question_type=QuestionType.MULTIPLE_CHOICE,
        options=["A", "B", "C"],
    )
    assert len(req.options) == 3


def test_section_create_request():
    req = SectionCreateRequest(
        title="Section 1",
        description="First section",
    )
    assert req.title == "Section 1"


def test_settings_update_request():
    req = SettingsUpdateRequest(
        is_quiz=True,
        email_collection="VERIFIED",
        allow_response_edits=False,
    )
    assert req.is_quiz is True
    assert req.email_collection == "VERIFIED"


# ---- Drive Models ----


def test_drive_file():
    f = DriveFile(
        file_id="abc",
        name="test.pdf",
        mime_type="application/pdf",
    )
    assert f.file_id == "abc"
    assert f.trashed is False


def test_drive_folder():
    f = DriveFolder(
        folder_id="fld1",
        name="My Folder",
    )
    assert f.folder_id == "fld1"


def test_drive_permission():
    p = DrivePermission(
        permission_id="perm1",
        role=ShareRole.WRITER,
        type=ShareType.USER,
        email_address="user@example.com",
    )
    assert p.role == ShareRole.WRITER


# ---- Sheets Models ----


def test_spreadsheet():
    s = Spreadsheet(
        spreadsheet_id="s1",
        title="My Sheet",
        spreadsheet_url="https://docs.google.com/spreadsheets/d/s1",
    )
    assert s.spreadsheet_id == "s1"


def test_sheet_data():
    d = SheetData(
        range="Sheet1!A1:B2",
        values=[["a", "b"], ["c", "d"]],
    )
    assert len(d.values) == 2


def test_sheet_write_result():
    r = SheetWriteResult(
        updated_range="Sheet1!A1:B2",
        updated_rows=2,
        updated_columns=2,
        updated_cells=4,
    )
    assert r.updated_cells == 4
