"""MCP tool definitions for Google Forms operations.

These are the Layer 2 atomic tools for form CRUD, question management,
sections, settings, publishing, and responses. Each tool is a thin
adapter that validates inputs, calls the appropriate service method,
and formats the output for the MCP protocol.
"""

from __future__ import annotations

import json
from typing import Any

from fastmcp import Context

from google_forms_mcp.exceptions import GoogleFormsMCPError
from google_forms_mcp.models.form import (
    FormCreateRequest,
    MediaCreateRequest,
    MediaType,
    QuestionCreateRequest,
    QuestionType,
    SectionCreateRequest,
    SettingsUpdateRequest,
    TextItemCreateRequest,
    ValidationRule,
    GradingConfig,
    CorrectAnswer,
    Feedback,
)


def _serialize(obj: Any) -> str:
    """Serialize a Pydantic model or dict to a JSON string."""
    if hasattr(obj, "model_dump"):
        return json.dumps(obj.model_dump(mode="json", exclude_none=True), indent=2, default=str)
    return json.dumps(obj, indent=2, default=str)


def register_form_tools(mcp: Any, forms_service: Any, drive_service: Any) -> None:
    """Register all form-related MCP tools.

    Args:
        mcp: FastMCP server instance.
        forms_service: FormsService instance.
        drive_service: DriveService instance.
    """

    @mcp.tool()
    def create_form(
        title: str,
        description: str = "",
        is_quiz: bool = False,
        publish: bool = True,
    ) -> str:
        """Create a new Google Form.

        Creates an empty form with the specified title and optional settings.
        Since June 2026, forms are created unpublished by default. This tool
        automatically publishes the form unless publish=False.

        Args:
            title: The title of the form (required).
            description: Optional description shown at the top of the form.
            is_quiz: If True, enables quiz mode with grading features.
            publish: If True (default), publishes the form to accept responses.

        Returns:
            JSON string with form details including form_id, edit URL, and responder URL.
        """
        try:
            request = FormCreateRequest(
                title=title,
                description=description,
                is_quiz=is_quiz,
                publish=publish,
            )
            form = forms_service.create(request)
            return _serialize(form)
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def get_form(form_id: str) -> str:
        """Retrieve a Google Form's complete structure and metadata.

        Returns the form's title, description, all questions with their types
        and options, sections, settings, and URLs.

        Args:
            form_id: The ID of the form to retrieve.

        Returns:
            JSON string with complete form structure.
        """
        try:
            form = forms_service.get(form_id)
            return _serialize(form)
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def update_form_info(
        form_id: str,
        title: str | None = None,
        description: str | None = None,
    ) -> str:
        """Update a form's title and/or description.

        Args:
            form_id: The ID of the form to update.
            title: New title for the form (optional).
            description: New description for the form (optional).

        Returns:
            JSON string with updated form details.
        """
        try:
            form = forms_service.update_info(form_id, title=title, description=description)
            return _serialize(form)
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def delete_form(form_id: str, permanent: bool = False) -> str:
        """Delete a Google Form.

        By default, moves the form to trash (recoverable). Set permanent=True
        to permanently delete (not recoverable).

        Note: This uses the Google Drive API since the Forms API does not
        support form deletion directly.

        Args:
            form_id: The ID of the form to delete.
            permanent: If True, permanently deletes the form. Default is False (trash).

        Returns:
            Confirmation message.
        """
        try:
            if permanent:
                drive_service.delete_file(form_id)
                return json.dumps({"status": "success", "message": f"Form {form_id} permanently deleted."})
            else:
                drive_service.trash_file(form_id)
                return json.dumps({"status": "success", "message": f"Form {form_id} moved to trash."})
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def duplicate_form(
        form_id: str,
        new_title: str | None = None,
        folder_id: str | None = None,
    ) -> str:
        """Duplicate (copy) an existing Google Form.

        Creates a copy of the form with all questions, settings, and structure.
        Uses the Google Drive API copy operation.

        Args:
            form_id: The ID of the form to duplicate.
            new_title: Title for the copy (optional, defaults to "Copy of [original]").
            folder_id: Destination folder ID (optional).

        Returns:
            JSON string with the duplicated form details.
        """
        try:
            file = drive_service.copy_file(form_id, new_name=new_title, folder_id=folder_id)
            # Get the full form details
            form = forms_service.get(file.file_id)
            return _serialize(form)
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def publish_form(
        form_id: str,
        is_accepting_responses: bool = True,
    ) -> str:
        """Publish or unpublish a Google Form.

        Controls whether a form is published and accepting responses.
        Since June 2026, forms created via the API are unpublished by default.

        Args:
            form_id: The ID of the form.
            is_accepting_responses: If True, form accepts responses. If False, form stops accepting responses.

        Returns:
            Confirmation message.
        """
        try:
            forms_service.publish(form_id, is_published=is_accepting_responses, is_accepting=is_accepting_responses)
            status = "published and accepting responses" if is_accepting_responses else "unpublished"
            return json.dumps({"status": "success", "message": f"Form {form_id} is now {status}."})
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def add_question(
        form_id: str,
        question_type: str,
        title: str,
        description: str = "",
        required: bool = False,
        position: int | None = None,
        options: list[str] | None = None,
        has_other_option: bool = False,
        shuffle_options: bool = False,
        low_value: int = 1,
        high_value: int = 5,
        low_label: str = "",
        high_label: str = "",
        include_year: bool = False,
        include_time: bool = False,
        row_labels: list[str] | None = None,
        column_labels: list[str] | None = None,
        max_files: int = 1,
        point_value: int | None = None,
        correct_answers: list[str] | None = None,
        when_right_feedback: str | None = None,
        when_wrong_feedback: str | None = None,
    ) -> str:
        """Add a question to a Google Form.

        Supports all 11 Google Forms question types. Provide type-specific
        parameters as needed.

        Args:
            form_id: The ID of the form.
            question_type: Type of question. One of: SHORT_ANSWER, PARAGRAPH,
                MULTIPLE_CHOICE, CHECKBOXES, DROPDOWN, FILE_UPLOAD, LINEAR_SCALE,
                DATE, TIME, MULTIPLE_CHOICE_GRID, CHECKBOX_GRID.
            title: The question text.
            description: Optional helper text below the question.
            required: Whether the question is required.
            position: Position index (0-based). Appends to end if not specified.
            options: List of option strings (for MULTIPLE_CHOICE, CHECKBOXES, DROPDOWN).
            has_other_option: Add an "Other" free-text option (for choice questions).
            shuffle_options: Randomize option order (for choice questions).
            low_value: Minimum value for LINEAR_SCALE (default 1).
            high_value: Maximum value for LINEAR_SCALE (default 5).
            low_label: Label for the low end of LINEAR_SCALE.
            high_label: Label for the high end of LINEAR_SCALE.
            include_year: Include year field for DATE questions.
            include_time: Include time field for DATE questions.
            row_labels: Row labels for grid questions (MULTIPLE_CHOICE_GRID, CHECKBOX_GRID).
            column_labels: Column labels for grid questions.
            max_files: Maximum file uploads allowed for FILE_UPLOAD (default 1).
            point_value: Points for quiz grading (optional).
            correct_answers: List of correct answer values for quiz grading (optional).
            when_right_feedback: Feedback shown when answer is correct (optional).
            when_wrong_feedback: Feedback shown when answer is wrong (optional).

        Returns:
            JSON string with updated form structure.
        """
        try:
            # Parse question type
            try:
                qt = QuestionType(question_type.upper())
            except ValueError:
                valid = [t.value for t in QuestionType]
                return f"Error: Invalid question type '{question_type}'. Valid types: {', '.join(valid)}"

            # Build grading config if quiz parameters provided
            grading = None
            if point_value is not None or correct_answers:
                grading = GradingConfig(
                    point_value=point_value or 0,
                    correct_answers=CorrectAnswer(values=correct_answers or []) if correct_answers else None,
                    when_right=Feedback(text=when_right_feedback) if when_right_feedback else None,
                    when_wrong=Feedback(text=when_wrong_feedback) if when_wrong_feedback else None,
                )

            request = QuestionCreateRequest(
                question_type=qt,
                title=title,
                description=description,
                required=required,
                position=position,
                options=options or [],
                has_other_option=has_other_option,
                shuffle_options=shuffle_options,
                low_value=low_value,
                high_value=high_value,
                low_label=low_label,
                high_label=high_label,
                include_year=include_year,
                include_time=include_time,
                row_labels=row_labels or [],
                column_labels=column_labels or [],
                max_files=max_files,
                grading=grading,
            )

            form = forms_service.add_question(form_id, request)
            return _serialize(form)
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def update_question(
        form_id: str,
        item_id: str,
        title: str | None = None,
        description: str | None = None,
        required: bool | None = None,
    ) -> str:
        """Update an existing question in a form.

        Args:
            form_id: The ID of the form.
            item_id: The ID of the question item to update.
            title: New question text (optional).
            description: New description text (optional).
            required: Whether the question should be required (optional).

        Returns:
            JSON string with updated form structure.
        """
        try:
            updates = {}
            if title is not None:
                updates["title"] = title
            if description is not None:
                updates["description"] = description
            if required is not None:
                updates["questionItem.question.required"] = required

            form = forms_service.update_question(form_id, item_id, updates)
            return _serialize(form)
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def delete_question(form_id: str, item_id: str) -> str:
        """Delete a question from a form.

        Args:
            form_id: The ID of the form.
            item_id: The ID of the question to delete.

        Returns:
            JSON string with updated form structure.
        """
        try:
            form = forms_service.delete_question(form_id, item_id=item_id)
            return _serialize(form)
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def move_question(form_id: str, item_id: str, new_index: int) -> str:
        """Move a question to a new position in the form.

        Args:
            form_id: The ID of the form.
            item_id: The ID of the question to move.
            new_index: The target position (0-based index).

        Returns:
            JSON string with updated form structure.
        """
        try:
            form = forms_service.move_question(form_id, item_id, new_index)
            return _serialize(form)
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def add_section(
        form_id: str,
        title: str,
        description: str = "",
        position: int | None = None,
    ) -> str:
        """Add a section (page break) to a form.

        Sections divide a form into multiple pages. Each section has a
        title and optional description.

        Args:
            form_id: The ID of the form.
            title: Section title.
            description: Section description (optional).
            position: Position index (optional, appends to end if not specified).

        Returns:
            JSON string with updated form structure.
        """
        try:
            request = SectionCreateRequest(title=title, description=description, position=position)
            form = forms_service.add_section(form_id, request)
            return _serialize(form)
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def update_section(
        form_id: str,
        item_id: str,
        title: str | None = None,
        description: str | None = None,
    ) -> str:
        """Update a section's title or description.

        Args:
            form_id: The ID of the form.
            item_id: The ID of the section to update.
            title: New section title (optional).
            description: New section description (optional).

        Returns:
            JSON string with updated form structure.
        """
        try:
            form = forms_service.update_section(form_id, item_id, title=title, description=description)
            return _serialize(form)
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def delete_section(form_id: str, item_id: str) -> str:
        """Delete a section (page break) from a form.

        Note: This only removes the page break. Questions within the section
        are not deleted — they become part of the previous section.

        Args:
            form_id: The ID of the form.
            item_id: The ID of the section to delete.

        Returns:
            JSON string with updated form structure.
        """
        try:
            form = forms_service.delete_section(form_id, item_id)
            return _serialize(form)
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def update_settings(
        form_id: str,
        is_quiz: bool | None = None,
        confirmation_message: str | None = None,
        shuffle_questions: bool | None = None,
    ) -> str:
        """Update form-level settings.

        Args:
            form_id: The ID of the form.
            is_quiz: Enable or disable quiz mode (optional).
            confirmation_message: Message shown after form submission (optional).
            shuffle_questions: Randomize question order (optional).

        Returns:
            JSON string with updated form details.
        """
        try:
            request = SettingsUpdateRequest(
                is_quiz=is_quiz,
                confirmation_message=confirmation_message,
                shuffle_questions=shuffle_questions,
            )
            form = forms_service.update_settings(form_id, request)
            return _serialize(form)
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def add_media(
        form_id: str,
        media_type: str,
        uri: str,
        title: str = "",
        position: int | None = None,
    ) -> str:
        """Add an image or video to a form.

        Args:
            form_id: The ID of the form.
            media_type: Type of media: "IMAGE" or "VIDEO".
            uri: URL of the image or YouTube video.
            title: Optional title/caption for the media.
            position: Position index (optional).

        Returns:
            JSON string with updated form structure.
        """
        try:
            mt = MediaType(media_type.upper())
            request = MediaCreateRequest(media_type=mt, uri=uri, title=title, position=position)
            form = forms_service.add_media(form_id, request)
            return _serialize(form)
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def add_text_item(
        form_id: str,
        title: str,
        description: str = "",
        position: int | None = None,
    ) -> str:
        """Add a text/description block to a form.

        Text items display informational text without collecting input.
        Useful for instructions, disclaimers, or section introductions.

        Args:
            form_id: The ID of the form.
            title: Title of the text block.
            description: Body text / description.
            position: Position index (optional).

        Returns:
            JSON string with updated form structure.
        """
        try:
            request = TextItemCreateRequest(title=title, description=description, position=position)
            form = forms_service.add_text_item(form_id, request)
            return _serialize(form)
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def get_responses(
        form_id: str,
        page_size: int = 100,
        page_token: str | None = None,
    ) -> str:
        """Get all responses for a form.

        Returns a paginated list of form submissions with all answers.

        Args:
            form_id: The ID of the form.
            page_size: Number of responses per page (default 100, max 5000).
            page_token: Token for the next page of results (from previous call).

        Returns:
            JSON string with list of responses and optional nextPageToken.
        """
        try:
            responses, next_token = forms_service.list_responses(
                form_id, page_size=page_size, page_token=page_token
            )
            result = {
                "responses": [r.model_dump(mode="json", exclude_none=True) for r in responses],
                "total_in_page": len(responses),
                "next_page_token": next_token,
            }
            return json.dumps(result, indent=2, default=str)
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def get_response(form_id: str, response_id: str) -> str:
        """Get a single response by its ID.

        Args:
            form_id: The ID of the form.
            response_id: The ID of the specific response.

        Returns:
            JSON string with the response details.
        """
        try:
            response = forms_service.get_response(form_id, response_id)
            return _serialize(response)
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def get_response_summary(form_id: str) -> str:
        """Get aggregated summary statistics for all form responses.

        Computes per-question statistics including option counts for choice
        questions, average/median for scale questions, and text response lists
        for text questions.

        Args:
            form_id: The ID of the form.

        Returns:
            JSON string with response summary statistics.
        """
        try:
            from google_forms_mcp.services.analytics_service import AnalyticsService

            form = forms_service.get(form_id)
            all_responses = []
            next_token = None

            # Fetch all responses (paginated)
            while True:
                responses, next_token = forms_service.list_responses(
                    form_id, page_size=5000, page_token=next_token
                )
                all_responses.extend(responses)
                if not next_token:
                    break

            analytics = AnalyticsService()
            summary = analytics.compute_summary(form, all_responses)
            return _serialize(summary)
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"

    @mcp.tool()
    def export_responses(
        form_id: str,
        format: str = "csv",
    ) -> str:
        """Export all form responses as CSV or JSON.

        Args:
            form_id: The ID of the form.
            format: Export format — "csv" or "json" (default: "csv").

        Returns:
            CSV string or JSON array of responses.
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

            if format.lower() == "json":
                data = analytics.export_responses_json(form, all_responses)
                return json.dumps(data, indent=2, default=str)
            else:
                return analytics.export_responses_csv(form, all_responses)
        except GoogleFormsMCPError as e:
            return f"Error: {e.message}"
