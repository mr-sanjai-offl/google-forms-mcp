"""Data models for Google Forms entities.

These Pydantic models serve as the internal representation for forms, questions,
sections, and related entities. They decouple tool interfaces from raw Google API
response structures.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# --- Enums ---


class QuestionType(str, Enum):
    """Supported Google Forms question types."""

    SHORT_ANSWER = "SHORT_ANSWER"
    PARAGRAPH = "PARAGRAPH"
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    CHECKBOXES = "CHECKBOXES"
    DROPDOWN = "DROPDOWN"
    FILE_UPLOAD = "FILE_UPLOAD"
    LINEAR_SCALE = "LINEAR_SCALE"
    DATE = "DATE"
    TIME = "TIME"
    MULTIPLE_CHOICE_GRID = "MULTIPLE_CHOICE_GRID"
    CHECKBOX_GRID = "CHECKBOX_GRID"


class ItemType(str, Enum):
    """Types of items that can exist in a form."""

    QUESTION = "QUESTION"
    QUESTION_GROUP = "QUESTION_GROUP"
    PAGE_BREAK = "PAGE_BREAK"
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"


class MediaType(str, Enum):
    """Types of media that can be embedded in a form."""

    IMAGE = "IMAGE"
    VIDEO = "VIDEO"


class ValidationType(str, Enum):
    """Types of validation that can be applied to questions."""

    NUMBER = "NUMBER"
    TEXT = "TEXT"
    LENGTH = "LENGTH"
    REGEX = "REGEX"
    EMAIL = "EMAIL"
    URL = "URL"


class NumberValidationOp(str, Enum):
    """Number validation comparison operators."""

    GREATER_THAN = "GREATER_THAN"
    GREATER_THAN_OR_EQUAL = "GREATER_THAN_OR_EQUAL"
    LESS_THAN = "LESS_THAN"
    LESS_THAN_OR_EQUAL = "LESS_THAN_OR_EQUAL"
    EQUAL_TO = "EQUAL_TO"
    NOT_EQUAL_TO = "NOT_EQUAL_TO"
    BETWEEN = "BETWEEN"
    NOT_BETWEEN = "NOT_BETWEEN"
    IS_NUMBER = "IS_NUMBER"
    IS_WHOLE_NUMBER = "IS_WHOLE_NUMBER"


# --- Validation & Grading ---


class ValidationRule(BaseModel):
    """Validation rule for a form question."""

    type: ValidationType
    error_message: str = ""

    # Number validation
    number_op: Optional[NumberValidationOp] = None
    number_value: Optional[float] = None
    number_value_high: Optional[float] = None  # For BETWEEN/NOT_BETWEEN

    # Text/regex validation
    pattern: Optional[str] = None

    # Length validation
    min_length: Optional[int] = None
    max_length: Optional[int] = None


class CorrectAnswer(BaseModel):
    """Correct answer for grading."""

    values: list[str] = Field(default_factory=list)


class Feedback(BaseModel):
    """Feedback text for quiz grading."""

    text: str = ""
    links: list[str] = Field(default_factory=list)


class GradingConfig(BaseModel):
    """Grading configuration for a quiz question."""

    point_value: int = 0
    correct_answers: Optional[CorrectAnswer] = None
    when_right: Optional[Feedback] = None
    when_wrong: Optional[Feedback] = None
    general_feedback: Optional[Feedback] = None


# --- Form Items ---


class FormOption(BaseModel):
    """A single option in a choice question."""

    value: str
    is_other: bool = False
    go_to_section_id: Optional[str] = None  # For section navigation


class FormQuestion(BaseModel):
    """Representation of a form question."""

    question_id: str = ""
    title: str = ""
    description: str = ""
    question_type: QuestionType = QuestionType.SHORT_ANSWER
    required: bool = False

    # Choice question fields
    options: list[FormOption] = Field(default_factory=list)
    has_other_option: bool = False
    shuffle_options: bool = False

    # Scale question fields
    low_value: int = 1
    high_value: int = 5
    low_label: str = ""
    high_label: str = ""

    # Date/time question fields
    include_year: bool = False
    include_time: bool = False

    # Grid question fields
    row_labels: list[str] = Field(default_factory=list)
    column_labels: list[str] = Field(default_factory=list)

    # File upload fields
    max_file_size: Optional[int] = None
    allowed_file_types: list[str] = Field(default_factory=list)
    max_files: int = 1

    # Validation & grading
    validation: Optional[ValidationRule] = None
    grading: Optional[GradingConfig] = None


class FormItem(BaseModel):
    """A single item in a form (question, section break, text, image, video)."""

    item_id: str = ""
    title: str = ""
    description: str = ""
    item_type: ItemType = ItemType.QUESTION
    index: int = 0

    # Populated for QUESTION items
    question: Optional[FormQuestion] = None

    # Populated for QUESTION_GROUP items (grids)
    questions: list[FormQuestion] = Field(default_factory=list)

    # Populated for IMAGE items
    image_uri: Optional[str] = None

    # Populated for VIDEO items
    video_uri: Optional[str] = None


class FormInfo(BaseModel):
    """Form metadata."""

    form_id: str = ""
    title: str = ""
    description: str = ""
    document_title: str = ""
    responder_uri: str = ""
    edit_uri: str = ""
    revision_id: str = ""
    linked_sheet_id: Optional[str] = None


class FormSettings(BaseModel):
    """Form-level settings."""

    is_quiz: bool = False
    email_collection: str = "NONE"  # NONE, VERIFIED, RESPONDER_INPUT
    allow_response_edits: bool = False
    limit_one_response: bool = False
    confirmation_message: str = ""
    shuffle_questions: bool = False


class Form(BaseModel):
    """Complete representation of a Google Form."""

    info: FormInfo = Field(default_factory=FormInfo)
    settings: FormSettings = Field(default_factory=FormSettings)
    items: list[FormItem] = Field(default_factory=list)
    revision_id: str = ""


# --- Request Models ---


class FormCreateRequest(BaseModel):
    """Request to create a new form."""

    title: str
    description: str = ""
    is_quiz: bool = False
    publish: bool = True
    folder_id: Optional[str] = None


class QuestionCreateRequest(BaseModel):
    """Request to add a question to a form."""

    question_type: QuestionType
    title: str
    description: str = ""
    required: bool = False
    position: Optional[int] = None

    # Choice question options
    options: list[str] = Field(default_factory=list)
    has_other_option: bool = False
    shuffle_options: bool = False

    # Scale options
    low_value: int = 1
    high_value: int = 5
    low_label: str = ""
    high_label: str = ""

    # Date/time options
    include_year: bool = False
    include_time: bool = False

    # Grid options
    row_labels: list[str] = Field(default_factory=list)
    column_labels: list[str] = Field(default_factory=list)

    # File upload options
    max_file_size: Optional[int] = None
    allowed_file_types: list[str] = Field(default_factory=list)
    max_files: int = 1

    # Validation
    validation: Optional[ValidationRule] = None

    # Grading (quiz mode)
    grading: Optional[GradingConfig] = None


class SectionCreateRequest(BaseModel):
    """Request to add a section (page break) to a form."""

    title: str
    description: str = ""
    position: Optional[int] = None


class MediaCreateRequest(BaseModel):
    """Request to add an image or video to a form."""

    media_type: MediaType
    uri: str
    title: str = ""
    position: Optional[int] = None


class TextItemCreateRequest(BaseModel):
    """Request to add a text/description block to a form."""

    title: str
    description: str = ""
    position: Optional[int] = None


class SettingsUpdateRequest(BaseModel):
    """Request to update form settings."""

    is_quiz: Optional[bool] = None
    email_collection: Optional[str] = None
    confirmation_message: Optional[str] = None
    shuffle_questions: Optional[bool] = None
