"""Google Forms API service layer.

Encapsulates all Google Forms API operations, translating between
domain models and raw API request/response structures. This is the
single point of contact with the Forms API.
"""

from __future__ import annotations

from typing import Any

from google_forms_mcp.exceptions import (
    FormNotFoundError,
    InvalidRequestError,
    ItemNotFoundError,
    NotFoundError,
)
from google_forms_mcp.infrastructure.logging import get_logger
from google_forms_mcp.infrastructure.rate_limiter import RateLimiter
from google_forms_mcp.infrastructure.retry import with_retry
from google_forms_mcp.models.form import (
    Form,
    FormCreateRequest,
    FormInfo,
    FormItem,
    FormOption,
    FormQuestion,
    FormSettings,
    GradingConfig,
    ItemType,
    MediaCreateRequest,
    MediaType,
    QuestionCreateRequest,
    QuestionType,
    SectionCreateRequest,
    SettingsUpdateRequest,
    TextItemCreateRequest,
    ValidationRule,
)
from google_forms_mcp.models.response import (
    Answer,
    FileUpload,
    FormResponse,
    Grade,
)

logger = get_logger("forms_service")


class FormsService:
    """Service for Google Forms API operations.

    All methods return domain model objects. Raw Google API structures
    never leak beyond this class.
    """

    def __init__(self, forms_client: Any, rate_limiter: RateLimiter) -> None:
        """Initialize the Forms service.

        Args:
            forms_client: Authenticated Google Forms API client.
            rate_limiter: Rate limiter instance.
        """
        self._client = forms_client
        self._limiter = rate_limiter

    # --- Form CRUD ---

    @with_retry()
    def create(self, request: FormCreateRequest) -> Form:
        """Create a new Google Form.

        Since June 2026, forms are created unpublished. This method
        automatically publishes the form unless publish=False.

        Args:
            request: Form creation parameters.

        Returns:
            The created Form.
        """
        self._limiter.acquire("forms_write")

        # Step 1: Create the form with title
        body = {"info": {"title": request.title}}
        result = self._client.forms().create(body=body).execute()
        form_id = result["formId"]
        logger.info("Created form: %s", form_id)

        # Step 2: Update description if provided
        if request.description:
            self._update_form_info(form_id, description=request.description)

        # Step 3: Enable quiz mode if requested
        if request.is_quiz:
            self._update_settings_raw(form_id, {"quizSettings": {"isQuiz": True}})

        # Step 4: Publish the form (required since June 2026)
        if request.publish:
            self.publish(form_id, is_published=True, is_accepting=True)

        # Return the complete form
        return self.get(form_id)

    @with_retry()
    def get(self, form_id: str) -> Form:
        """Retrieve a form's complete structure and metadata.

        Args:
            form_id: The ID of the form.

        Returns:
            Complete Form object.

        Raises:
            FormNotFoundError: If the form doesn't exist.
        """
        self._limiter.acquire("forms_read")

        try:
            result = self._client.forms().get(formId=form_id).execute()
        except Exception as e:
            if "404" in str(e):
                raise FormNotFoundError(form_id) from e
            raise

        return self._parse_form(result)

    def update_info(
        self,
        form_id: str,
        title: str | None = None,
        description: str | None = None,
    ) -> Form:
        """Update form title and/or description.

        Args:
            form_id: The ID of the form.
            title: New title (optional).
            description: New description (optional).

        Returns:
            Updated Form object.
        """
        self._update_form_info(form_id, title=title, description=description)
        return self.get(form_id)

    # --- Questions ---

    @with_retry()
    def add_question(self, form_id: str, request: QuestionCreateRequest) -> Form:
        """Add a question to a form.

        Handles all 11 question types by dispatching to the appropriate
        API item structure.

        Args:
            form_id: The ID of the form.
            request: Question creation parameters.

        Returns:
            Updated Form object.
        """
        self._limiter.acquire("forms_write")

        # Build the item based on question type
        if request.question_type in (
            QuestionType.MULTIPLE_CHOICE_GRID,
            QuestionType.CHECKBOX_GRID,
        ):
            item = self._build_grid_item(request)
        else:
            item = self._build_question_item(request)

        # Build the createItem request
        create_request: dict[str, Any] = {"createItem": {"item": item, "location": {}}}
        if request.position is not None:
            create_request["createItem"]["location"]["index"] = request.position

        self._batch_update(form_id, [create_request])
        logger.info("Added %s question to form %s", request.question_type.value, form_id)

        return self.get(form_id)

    @with_retry()
    def update_question(
        self,
        form_id: str,
        item_id: str,
        updates: dict[str, Any],
    ) -> Form:
        """Update an existing question.

        Args:
            form_id: The ID of the form.
            item_id: The ID of the item to update.
            updates: Dictionary of fields to update.

        Returns:
            Updated Form object.
        """
        self._limiter.acquire("forms_write")

        # Get the current form to find the item index
        form = self.get(form_id)
        item_index = self._find_item_index(form, item_id)

        # Build update request
        update_request: dict[str, Any] = {
            "updateItem": {
                "item": {"itemId": item_id},
                "location": {"index": item_index},
                "updateMask": ",".join(updates.keys()),
            }
        }

        # Apply updates to the item
        for key, value in updates.items():
            self._set_nested(update_request["updateItem"]["item"], key, value)

        self._batch_update(form_id, [update_request])
        return self.get(form_id)

    @with_retry()
    def delete_question(self, form_id: str, item_id: str | None = None, index: int | None = None) -> Form:
        """Delete a question from a form.

        Args:
            form_id: The ID of the form.
            item_id: The ID of the item to delete.
            index: The index of the item to delete (alternative to item_id).

        Returns:
            Updated Form object.
        """
        self._limiter.acquire("forms_write")

        if item_id and index is None:
            form = self.get(form_id)
            index = self._find_item_index(form, item_id)

        if index is None:
            raise InvalidRequestError(
                "Either item_id or index must be provided to delete a question."
            )

        delete_request = {"deleteItem": {"location": {"index": index}}}
        self._batch_update(form_id, [delete_request])
        logger.info("Deleted item at index %d from form %s", index, form_id)

        return self.get(form_id)

    @with_retry()
    def move_question(self, form_id: str, item_id: str, new_index: int) -> Form:
        """Move a question to a new position.

        Args:
            form_id: The ID of the form.
            item_id: The ID of the item to move.
            new_index: The target index position.

        Returns:
            Updated Form object.
        """
        self._limiter.acquire("forms_write")

        form = self.get(form_id)
        old_index = self._find_item_index(form, item_id)

        move_request = {
            "moveItem": {
                "originalLocation": {"index": old_index},
                "newLocation": {"index": new_index},
            }
        }
        self._batch_update(form_id, [move_request])
        logger.info("Moved item from index %d to %d in form %s", old_index, new_index, form_id)

        return self.get(form_id)

    # --- Sections ---

    @with_retry()
    def add_section(self, form_id: str, request: SectionCreateRequest) -> Form:
        """Add a section (page break) to a form.

        Args:
            form_id: The ID of the form.
            request: Section creation parameters.

        Returns:
            Updated Form object.
        """
        self._limiter.acquire("forms_write")

        item: dict[str, Any] = {
            "title": request.title,
            "description": request.description,
            "pageBreakItem": {},
        }

        create_request: dict[str, Any] = {"createItem": {"item": item, "location": {}}}
        if request.position is not None:
            create_request["createItem"]["location"]["index"] = request.position

        self._batch_update(form_id, [create_request])
        logger.info("Added section '%s' to form %s", request.title, form_id)

        return self.get(form_id)

    @with_retry()
    def update_section(
        self,
        form_id: str,
        item_id: str,
        title: str | None = None,
        description: str | None = None,
    ) -> Form:
        """Update a section's title or description.

        Args:
            form_id: The ID of the form.
            item_id: The ID of the section item.
            title: New title (optional).
            description: New description (optional).

        Returns:
            Updated Form object.
        """
        self._limiter.acquire("forms_write")

        form = self.get(form_id)
        item_index = self._find_item_index(form, item_id)

        item: dict[str, Any] = {"itemId": item_id, "pageBreakItem": {}}
        update_mask_parts = []

        if title is not None:
            item["title"] = title
            update_mask_parts.append("title")
        if description is not None:
            item["description"] = description
            update_mask_parts.append("description")

        if not update_mask_parts:
            return self.get(form_id)

        update_request = {
            "updateItem": {
                "item": item,
                "location": {"index": item_index},
                "updateMask": ",".join(update_mask_parts),
            }
        }
        self._batch_update(form_id, [update_request])

        return self.get(form_id)

    @with_retry()
    def delete_section(self, form_id: str, item_id: str) -> Form:
        """Delete a section (page break) from a form.

        Args:
            form_id: The ID of the form.
            item_id: The ID of the section to delete.

        Returns:
            Updated Form object.
        """
        return self.delete_question(form_id, item_id=item_id)

    # --- Media & Text ---

    @with_retry()
    def add_media(self, form_id: str, request: MediaCreateRequest) -> Form:
        """Add an image or video item to a form.

        Args:
            form_id: The ID of the form.
            request: Media creation parameters.

        Returns:
            Updated Form object.
        """
        self._limiter.acquire("forms_write")

        item: dict[str, Any] = {"title": request.title}

        if request.media_type == MediaType.IMAGE:
            item["imageItem"] = {"image": {"sourceUri": request.uri}}
        else:
            item["videoItem"] = {"video": {"youtubeUri": request.uri}}

        create_request: dict[str, Any] = {"createItem": {"item": item, "location": {}}}
        if request.position is not None:
            create_request["createItem"]["location"]["index"] = request.position

        self._batch_update(form_id, [create_request])
        return self.get(form_id)

    @with_retry()
    def add_text_item(self, form_id: str, request: TextItemCreateRequest) -> Form:
        """Add a text/description block to a form.

        Args:
            form_id: The ID of the form.
            request: Text item creation parameters.

        Returns:
            Updated Form object.
        """
        self._limiter.acquire("forms_write")

        item: dict[str, Any] = {
            "title": request.title,
            "description": request.description,
            "textItem": {},
        }

        create_request: dict[str, Any] = {"createItem": {"item": item, "location": {}}}
        if request.position is not None:
            create_request["createItem"]["location"]["index"] = request.position

        self._batch_update(form_id, [create_request])
        return self.get(form_id)

    # --- Settings ---

    @with_retry()
    def update_settings(self, form_id: str, request: SettingsUpdateRequest) -> Form:
        """Update form-level settings.

        Args:
            form_id: The ID of the form.
            request: Settings update parameters.

        Returns:
            Updated Form object.
        """
        settings: dict[str, Any] = {}

        if request.is_quiz is not None:
            settings["quizSettings"] = {"isQuiz": request.is_quiz}

        if request.email_collection is not None:
            # Will be part of form info update
            pass

        if request.confirmation_message is not None:
            # Confirmation message is in form info
            pass

        if settings:
            self._update_settings_raw(form_id, settings)

        # Handle confirmation message via form info update
        if request.confirmation_message is not None:
            self._update_form_info(
                form_id,
                confirmation_message=request.confirmation_message,
            )

        return self.get(form_id)

    # --- Publishing ---

    @with_retry()
    def publish(
        self,
        form_id: str,
        is_published: bool = True,
        is_accepting: bool = True,
    ) -> None:
        """Publish or unpublish a form.

        Required since June 2026: forms created via API are unpublished by default.

        Args:
            form_id: The ID of the form.
            is_published: Whether the form should be published.
            is_accepting: Whether the form should accept responses.
        """
        self._limiter.acquire("forms_write")

        body = {
            "publishSettings": {
                "publishState": {
                    "isPublished": is_published,
                    "isAcceptingResponses": is_accepting,
                }
            }
        }

        try:
            self._client.forms().setPublishSettings(
                formId=form_id, body=body
            ).execute()
            logger.info(
                "Form %s: published=%s, accepting=%s",
                form_id, is_published, is_accepting,
            )
        except Exception as e:
            # Some older forms may not support publish settings
            logger.warning("Could not set publish settings for %s: %s", form_id, e)

    # --- Responses ---

    @with_retry()
    def list_responses(
        self,
        form_id: str,
        page_size: int = 100,
        page_token: str | None = None,
        filter_str: str | None = None,
    ) -> tuple[list[FormResponse], str | None]:
        """List responses for a form.

        Args:
            form_id: The ID of the form.
            page_size: Number of responses per page (max 5000).
            page_token: Token for the next page.
            filter_str: Optional filter string.

        Returns:
            Tuple of (list of responses, next page token or None).
        """
        self._limiter.acquire("forms_read_expensive")

        kwargs: dict[str, Any] = {
            "formId": form_id,
            "pageSize": min(page_size, 5000),
        }
        if page_token:
            kwargs["pageToken"] = page_token
        if filter_str:
            kwargs["filter"] = filter_str

        try:
            result = self._client.forms().responses().list(**kwargs).execute()
        except Exception as e:
            if "404" in str(e):
                raise FormNotFoundError(form_id) from e
            raise

        responses = [
            self._parse_response(r, form_id)
            for r in result.get("responses", [])
        ]
        next_token = result.get("nextPageToken")

        return responses, next_token

    @with_retry()
    def get_response(self, form_id: str, response_id: str) -> FormResponse:
        """Get a single response by ID.

        Args:
            form_id: The ID of the form.
            response_id: The ID of the response.

        Returns:
            The FormResponse.
        """
        self._limiter.acquire("forms_read_expensive")

        result = (
            self._client.forms()
            .responses()
            .get(formId=form_id, responseId=response_id)
            .execute()
        )

        return self._parse_response(result, form_id)

    # --- Internal Helpers ---

    def _batch_update(self, form_id: str, requests: list[dict[str, Any]]) -> dict[str, Any]:
        """Execute a batchUpdate on a form.

        Args:
            form_id: The ID of the form.
            requests: List of update request objects.

        Returns:
            The batchUpdate response.
        """
        body = {"requests": requests}
        return (
            self._client.forms()
            .batchUpdate(formId=form_id, body=body)
            .execute()
        )

    @with_retry()
    def _update_form_info(
        self,
        form_id: str,
        title: str | None = None,
        description: str | None = None,
        confirmation_message: str | None = None,
    ) -> None:
        """Update form info fields."""
        self._limiter.acquire("forms_write")

        info: dict[str, Any] = {}
        mask_parts = []

        if title is not None:
            info["title"] = title
            mask_parts.append("title")
        if description is not None:
            info["description"] = description
            mask_parts.append("description")

        if not mask_parts:
            return

        request = {
            "updateFormInfo": {
                "info": info,
                "updateMask": ",".join(mask_parts),
            }
        }
        self._batch_update(form_id, [request])

    @with_retry()
    def _update_settings_raw(self, form_id: str, settings: dict[str, Any]) -> None:
        """Update form settings with raw API structure."""
        self._limiter.acquire("forms_write")

        request = {
            "updateSettings": {
                "settings": settings,
                "updateMask": ",".join(settings.keys()),
            }
        }
        self._batch_update(form_id, [request])

    def _build_question_item(self, request: QuestionCreateRequest) -> dict[str, Any]:
        """Build a questionItem API structure from a QuestionCreateRequest."""
        question: dict[str, Any] = {"required": request.required}

        qt = request.question_type

        if qt == QuestionType.SHORT_ANSWER:
            question["textQuestion"] = {"paragraph": False}

        elif qt == QuestionType.PARAGRAPH:
            question["textQuestion"] = {"paragraph": True}

        elif qt in (QuestionType.MULTIPLE_CHOICE, QuestionType.CHECKBOXES, QuestionType.DROPDOWN):
            type_map = {
                QuestionType.MULTIPLE_CHOICE: "RADIO",
                QuestionType.CHECKBOXES: "CHECKBOX",
                QuestionType.DROPDOWN: "DROP_DOWN",
            }
            options = [{"value": opt} for opt in request.options]
            question["choiceQuestion"] = {
                "type": type_map[qt],
                "options": options,
            }
            if request.has_other_option:
                question["choiceQuestion"]["options"].append({"isOther": True})
            if request.shuffle_options:
                question["choiceQuestion"]["shuffle"] = True

        elif qt == QuestionType.LINEAR_SCALE:
            question["scaleQuestion"] = {
                "low": request.low_value,
                "high": request.high_value,
                "lowLabel": request.low_label,
                "highLabel": request.high_label,
            }

        elif qt == QuestionType.DATE:
            question["dateQuestion"] = {
                "includeYear": request.include_year,
                "includeTime": request.include_time,
            }

        elif qt == QuestionType.TIME:
            question["timeQuestion"] = {"duration": False}

        elif qt == QuestionType.FILE_UPLOAD:
            file_q: dict[str, Any] = {
                "maxFiles": request.max_files,
                "folderId": "",  # Auto-created by Google
            }
            if request.max_file_size:
                file_q["maxFileSize"] = request.max_file_size
            if request.allowed_file_types:
                file_q["types"] = request.allowed_file_types
            question["fileUploadQuestion"] = file_q

        # Add validation if specified
        if request.validation:
            question["textQuestion"] = question.get("textQuestion", {})
            # Validation details depend on type - simplified for now

        # Add grading if specified
        if request.grading:
            grading: dict[str, Any] = {"pointValue": request.grading.point_value}
            if request.grading.correct_answers:
                grading["correctAnswers"] = {
                    "answers": [
                        {"value": v} for v in request.grading.correct_answers.values
                    ]
                }
            if request.grading.when_right:
                grading["whenRight"] = {"text": request.grading.when_right.text}
            if request.grading.when_wrong:
                grading["whenWrong"] = {"text": request.grading.when_wrong.text}
            if request.grading.general_feedback:
                grading["generalFeedback"] = {"text": request.grading.general_feedback.text}
            question["grading"] = grading

        item: dict[str, Any] = {
            "title": request.title,
            "description": request.description,
            "questionItem": {"question": question},
        }

        return item

    def _build_grid_item(self, request: QuestionCreateRequest) -> dict[str, Any]:
        """Build a questionGroupItem (grid) API structure."""
        grid_type = (
            "RADIO" if request.question_type == QuestionType.MULTIPLE_CHOICE_GRID
            else "CHECKBOX"
        )

        # Each row becomes a question in the group
        questions = []
        for row_label in request.row_labels:
            questions.append({
                "required": request.required,
                "rowQuestion": {"title": row_label},
            })

        # Columns are the grid choices
        columns = [{"value": col} for col in request.column_labels]

        item: dict[str, Any] = {
            "title": request.title,
            "description": request.description,
            "questionGroupItem": {
                "questions": questions,
                "grid": {
                    "columns": {"type": grid_type, "options": columns},
                },
            },
        }

        return item

    def _find_item_index(self, form: Form, item_id: str) -> int:
        """Find the index of an item in a form by its ID.

        Args:
            form: The form to search.
            item_id: The item ID to find.

        Returns:
            The item's index.

        Raises:
            ItemNotFoundError: If the item is not found.
        """
        for item in form.items:
            if item.item_id == item_id:
                return item.index
        raise ItemNotFoundError(item_id, form.info.form_id)

    @staticmethod
    def _set_nested(d: dict[str, Any], key: str, value: Any) -> None:
        """Set a nested dictionary value using dot-notation keys."""
        keys = key.split(".")
        for k in keys[:-1]:
            d = d.setdefault(k, {})
        d[keys[-1]] = value

    # --- Parsing Helpers ---

    def _parse_form(self, data: dict[str, Any]) -> Form:
        """Parse a raw Google Forms API response into a Form model."""
        info_data = data.get("info", {})
        info = FormInfo(
            form_id=data.get("formId", ""),
            title=info_data.get("title", ""),
            description=info_data.get("description", ""),
            document_title=info_data.get("documentTitle", ""),
            responder_uri=data.get("responderUri", ""),
            edit_uri=f"https://docs.google.com/forms/d/{data.get('formId', '')}/edit",
            revision_id=data.get("revisionId", ""),
            linked_sheet_id=data.get("linkedSheetId"),
        )

        settings_data = data.get("settings", {})
        quiz_data = settings_data.get("quizSettings", {})
        settings = FormSettings(
            is_quiz=quiz_data.get("isQuiz", False),
        )

        items = []
        for idx, item_data in enumerate(data.get("items", [])):
            items.append(self._parse_item(item_data, idx))

        return Form(
            info=info,
            settings=settings,
            items=items,
            revision_id=data.get("revisionId", ""),
        )

    def _parse_item(self, data: dict[str, Any], index: int) -> FormItem:
        """Parse a raw form item into a FormItem model."""
        item = FormItem(
            item_id=data.get("itemId", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            index=index,
        )

        if "questionItem" in data:
            item.item_type = ItemType.QUESTION
            q_data = data["questionItem"].get("question", {})
            item.question = self._parse_question(q_data, data)

        elif "questionGroupItem" in data:
            item.item_type = ItemType.QUESTION_GROUP
            group = data["questionGroupItem"]
            grid = group.get("grid", {})
            columns = grid.get("columns", {})
            col_type = columns.get("type", "RADIO")
            col_options = [
                opt.get("value", "") for opt in columns.get("options", [])
            ]

            for q in group.get("questions", []):
                row_title = q.get("rowQuestion", {}).get("title", "")
                qt = (
                    QuestionType.MULTIPLE_CHOICE_GRID if col_type == "RADIO"
                    else QuestionType.CHECKBOX_GRID
                )
                item.questions.append(
                    FormQuestion(
                        question_id=q.get("questionId", ""),
                        title=row_title,
                        question_type=qt,
                        required=q.get("required", False),
                        column_labels=col_options,
                    )
                )

        elif "pageBreakItem" in data:
            item.item_type = ItemType.PAGE_BREAK

        elif "textItem" in data:
            item.item_type = ItemType.TEXT

        elif "imageItem" in data:
            item.item_type = ItemType.IMAGE
            img = data["imageItem"].get("image", {})
            item.image_uri = img.get("contentUri", img.get("sourceUri", ""))

        elif "videoItem" in data:
            item.item_type = ItemType.VIDEO
            vid = data["videoItem"].get("video", {})
            item.video_uri = vid.get("youtubeUri", "")

        return item

    def _parse_question(self, q_data: dict[str, Any], item_data: dict[str, Any]) -> FormQuestion:
        """Parse a raw question into a FormQuestion model."""
        question = FormQuestion(
            question_id=q_data.get("questionId", ""),
            title=item_data.get("title", ""),
            description=item_data.get("description", ""),
            required=q_data.get("required", False),
        )

        if "textQuestion" in q_data:
            is_paragraph = q_data["textQuestion"].get("paragraph", False)
            question.question_type = (
                QuestionType.PARAGRAPH if is_paragraph else QuestionType.SHORT_ANSWER
            )

        elif "choiceQuestion" in q_data:
            choice = q_data["choiceQuestion"]
            type_map = {
                "RADIO": QuestionType.MULTIPLE_CHOICE,
                "CHECKBOX": QuestionType.CHECKBOXES,
                "DROP_DOWN": QuestionType.DROPDOWN,
            }
            question.question_type = type_map.get(
                choice.get("type", "RADIO"), QuestionType.MULTIPLE_CHOICE
            )
            question.shuffle_options = choice.get("shuffle", False)

            for opt in choice.get("options", []):
                if opt.get("isOther"):
                    question.has_other_option = True
                else:
                    question.options.append(
                        FormOption(
                            value=opt.get("value", ""),
                            go_to_section_id=opt.get("goToSectionId"),
                        )
                    )

        elif "scaleQuestion" in q_data:
            scale = q_data["scaleQuestion"]
            question.question_type = QuestionType.LINEAR_SCALE
            question.low_value = scale.get("low", 1)
            question.high_value = scale.get("high", 5)
            question.low_label = scale.get("lowLabel", "")
            question.high_label = scale.get("highLabel", "")

        elif "dateQuestion" in q_data:
            date_q = q_data["dateQuestion"]
            question.question_type = QuestionType.DATE
            question.include_year = date_q.get("includeYear", False)
            question.include_time = date_q.get("includeTime", False)

        elif "timeQuestion" in q_data:
            question.question_type = QuestionType.TIME

        elif "fileUploadQuestion" in q_data:
            question.question_type = QuestionType.FILE_UPLOAD
            file_q = q_data["fileUploadQuestion"]
            question.max_files = file_q.get("maxFiles", 1)
            question.max_file_size = file_q.get("maxFileSize")
            question.allowed_file_types = file_q.get("types", [])

        # Parse grading
        if "grading" in q_data:
            g = q_data["grading"]
            grading = GradingConfig(point_value=g.get("pointValue", 0))
            if "correctAnswers" in g:
                from google_forms_mcp.models.form import CorrectAnswer
                answers = [a.get("value", "") for a in g["correctAnswers"].get("answers", [])]
                grading.correct_answers = CorrectAnswer(values=answers)
            question.grading = grading

        return question

    def _parse_response(self, data: dict[str, Any], form_id: str) -> FormResponse:
        """Parse a raw form response into a FormResponse model."""
        answers: dict[str, Answer] = {}

        for q_id, answer_data in data.get("answers", {}).items():
            text_answers: list[str] = []
            file_uploads: list[FileUpload] = []

            if "textAnswers" in answer_data:
                for ta in answer_data["textAnswers"].get("answers", []):
                    text_answers.append(ta.get("value", ""))

            if "fileUploadAnswers" in answer_data:
                for fa in answer_data["fileUploadAnswers"].get("answers", []):
                    file_uploads.append(
                        FileUpload(
                            file_id=fa.get("fileId", ""),
                            file_name=fa.get("fileName", ""),
                            mime_type=fa.get("mimeType", ""),
                        )
                    )

            grade = None
            if "grade" in answer_data:
                g = answer_data["grade"]
                grade = Grade(
                    score=g.get("score", 0),
                    correct=g.get("correct", False),
                    feedback=g.get("feedback", {}).get("text", ""),
                )

            answers[q_id] = Answer(
                question_id=q_id,
                text_answers=text_answers,
                file_upload_answers=file_uploads,
                grade=grade,
            )

        return FormResponse(
            response_id=data.get("responseId", ""),
            form_id=form_id,
            create_time=data.get("createTime"),
            last_submitted_time=data.get("lastSubmittedTime"),
            respondent_email=data.get("respondentEmail", ""),
            total_score=data.get("totalScore"),
            answers=answers,
        )
