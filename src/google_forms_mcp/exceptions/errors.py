"""Custom exception hierarchy for Google Forms MCP Server.

All exceptions inherit from GoogleFormsMCPError. The hierarchy is designed so that:
- The service layer raises domain-specific exceptions
- The tool layer catches them and translates to user-friendly ToolError messages
- No raw Google API errors leak to MCP clients
"""

from __future__ import annotations


class GoogleFormsMCPError(Exception):
    """Base exception for all Google Forms MCP errors."""

    def __init__(self, message: str, *, details: str | None = None) -> None:
        self.message = message
        self.details = details
        super().__init__(message)


# --- Authentication Errors ---


class AuthenticationError(GoogleFormsMCPError):
    """Base class for authentication-related errors."""


class TokenExpiredError(AuthenticationError):
    """The access token has expired and could not be refreshed."""


class InvalidCredentialsError(AuthenticationError):
    """The provided credentials are invalid or malformed."""


class MissingScopesError(AuthenticationError):
    """The credentials lack required OAuth scopes."""


class RefreshFailedError(AuthenticationError):
    """Failed to refresh the access token using the refresh token."""


class AuthNotConfiguredError(AuthenticationError):
    """No authentication method is configured."""

    def __init__(self, message: str | None = None) -> None:
        super().__init__(
            message
            or (
                "No authentication configured. Please set GOOGLE_CLIENT_ID, "
                "GOOGLE_CLIENT_SECRET, and GOOGLE_REFRESH_TOKEN environment variables, "
                "or provide a GOOGLE_CLIENT_SECRETS_FILE for interactive OAuth."
            )
        )


# --- API Errors ---


class APIError(GoogleFormsMCPError):
    """Base class for Google API errors."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        api: str | None = None,
        details: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.api = api
        super().__init__(message, details=details)


class RateLimitError(APIError):
    """API rate limit (429) exceeded."""

    def __init__(self, api: str = "Google API", retry_after: int | None = None) -> None:
        self.retry_after = retry_after
        msg = f"{api} rate limit exceeded."
        if retry_after:
            msg += f" Retry after {retry_after} seconds."
        super().__init__(msg, status_code=429, api=api)


class QuotaExceededError(APIError):
    """API quota has been exhausted."""


class NotFoundError(APIError):
    """The requested resource was not found (404)."""

    def __init__(self, resource_type: str, resource_id: str) -> None:
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(
            f"{resource_type} not found: '{resource_id}'. "
            "Please verify the ID and ensure you have access.",
            status_code=404,
        )


class PermissionDeniedError(APIError):
    """Insufficient permissions to access the resource (403)."""

    def __init__(self, resource_type: str = "resource", action: str = "access") -> None:
        super().__init__(
            f"Permission denied: you do not have permission to {action} this {resource_type}. "
            "Check your sharing settings or OAuth scopes.",
            status_code=403,
        )


class InvalidRequestError(APIError):
    """The API request was malformed (400)."""


class ServerError(APIError):
    """The Google API returned a server error (5xx)."""


# --- Validation Errors ---


class ValidationError(GoogleFormsMCPError):
    """Base class for input validation errors."""


class InvalidFormIdError(ValidationError):
    """The provided form ID is invalid."""

    def __init__(self, form_id: str) -> None:
        super().__init__(
            f"Invalid form ID format: '{form_id}'. "
            "Form IDs should contain only alphanumeric characters, hyphens, and underscores."
        )


class InvalidQuestionTypeError(ValidationError):
    """The specified question type is not valid."""

    def __init__(self, question_type: str, valid_types: list[str]) -> None:
        super().__init__(
            f"Invalid question type: '{question_type}'. Valid types are: {', '.join(valid_types)}"
        )


class MissingRequiredFieldError(ValidationError):
    """A required field was not provided."""

    def __init__(self, field_name: str, context: str = "") -> None:
        msg = f"Missing required field: '{field_name}'."
        if context:
            msg += f" {context}"
        super().__init__(msg)


class InvalidParameterError(ValidationError):
    """A parameter value is invalid."""

    def __init__(self, param_name: str, value: object, reason: str = "") -> None:
        msg = f"Invalid value for '{param_name}': {value!r}."
        if reason:
            msg += f" {reason}"
        super().__init__(msg)


# --- Operation Errors ---


class OperationError(GoogleFormsMCPError):
    """Base class for operation-level errors."""


class FormNotFoundError(OperationError):
    """The specified form does not exist or is inaccessible."""

    def __init__(self, form_id: str) -> None:
        self.form_id = form_id
        super().__init__(
            f"Form not found: '{form_id}'. Verify the form ID and ensure you have access."
        )


class ItemNotFoundError(OperationError):
    """A form item (question, section) was not found."""

    def __init__(self, item_id: str, form_id: str) -> None:
        self.item_id = item_id
        self.form_id = form_id
        super().__init__(f"Item '{item_id}' not found in form '{form_id}'.")


class SpreadsheetNotFoundError(OperationError):
    """The specified spreadsheet does not exist or is inaccessible."""

    def __init__(self, spreadsheet_id: str) -> None:
        self.spreadsheet_id = spreadsheet_id
        super().__init__(
            f"Spreadsheet not found: '{spreadsheet_id}'. "
            "Verify the spreadsheet ID and ensure you have access."
        )


class UnsupportedOperationError(OperationError):
    """The requested operation is not supported by the Google API."""

    def __init__(self, operation: str, reason: str = "") -> None:
        msg = f"Unsupported operation: '{operation}'."
        if reason:
            msg += f" {reason}"
        super().__init__(msg)


# --- Template Errors ---


class TemplateError(GoogleFormsMCPError):
    """Base class for template-related errors."""


class TemplateNotFoundError(TemplateError):
    """The requested form template does not exist."""

    def __init__(self, template_name: str) -> None:
        super().__init__(f"Form template not found: '{template_name}'.")


class TemplateValidationError(TemplateError):
    """The template data is invalid."""
