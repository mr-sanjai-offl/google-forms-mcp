"""Tests for the exception hierarchy and error domain models."""

import pytest

from google_forms_mcp.exceptions import (
    AuthNotConfiguredError,
    FormNotFoundError,
    GoogleFormsMCPError,
    InvalidFormIdError,
    InvalidQuestionTypeError,
    ItemNotFoundError,
    MissingRequiredFieldError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    SpreadsheetNotFoundError,
    TemplateNotFoundError,
)


def test_base_exception_hierarchy():
    """All exceptions should inherit from GoogleFormsMCPError."""
    with pytest.raises(GoogleFormsMCPError):
        raise FormNotFoundError("test-id")


def test_form_not_found_error():
    err = FormNotFoundError("abc123")
    assert err.form_id == "abc123"
    assert "abc123" in str(err)


def test_item_not_found_error():
    err = ItemNotFoundError("item1", "form1")
    assert err.item_id == "item1"
    assert err.form_id == "form1"
    assert "item1" in str(err)
    assert "form1" in str(err)


def test_invalid_form_id_error():
    err = InvalidFormIdError("!!!bad!!!")
    assert "!!!bad!!!" in str(err)


def test_invalid_question_type_error():
    err = InvalidQuestionTypeError("INVALID", ["SHORT_ANSWER", "PARAGRAPH"])
    assert "INVALID" in str(err)
    assert "SHORT_ANSWER" in str(err)


def test_missing_required_field():
    err = MissingRequiredFieldError("title", "When creating a form")
    assert "title" in str(err)
    assert "When creating a form" in str(err)


def test_not_found_error():
    err = NotFoundError("Form", "xyz")
    assert err.resource_type == "Form"
    assert err.resource_id == "xyz"
    assert err.status_code == 404


def test_rate_limit_error_with_retry():
    err = RateLimitError("Forms API", retry_after=30)
    assert err.retry_after == 30
    assert "30" in str(err)


def test_permission_denied_error():
    err = PermissionDeniedError("form", "edit")
    assert "edit" in str(err)
    assert "form" in str(err)
    assert err.status_code == 403


def test_spreadsheet_not_found():
    err = SpreadsheetNotFoundError("sheet123")
    assert err.spreadsheet_id == "sheet123"


def test_template_not_found():
    err = TemplateNotFoundError("unknown_template")
    assert "unknown_template" in str(err)


def test_auth_not_configured_default():
    err = AuthNotConfiguredError()
    assert "GOOGLE_CLIENT_ID" in str(err)


def test_auth_not_configured_custom():
    err = AuthNotConfiguredError("Custom auth error message")
    assert "Custom auth error message" in str(err)
