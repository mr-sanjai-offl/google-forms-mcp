"""Data models for Google Forms response entities."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Grade(BaseModel):
    """Grade for a single question response."""

    score: float = 0
    correct: bool = False
    feedback: str = ""


class FileUpload(BaseModel):
    """File upload answer details."""

    file_id: str = ""
    file_name: str = ""
    mime_type: str = ""


class Answer(BaseModel):
    """A single answer to a form question."""

    question_id: str = ""
    text_answers: list[str] = Field(default_factory=list)
    file_upload_answers: list[FileUpload] = Field(default_factory=list)
    grade: Optional[Grade] = None


class FormResponse(BaseModel):
    """A single response submission to a form."""

    response_id: str = ""
    form_id: str = ""
    create_time: Optional[datetime] = None
    last_submitted_time: Optional[datetime] = None
    respondent_email: str = ""
    total_score: Optional[float] = None
    answers: dict[str, Answer] = Field(default_factory=dict)


class ResponseSummary(BaseModel):
    """Aggregated summary of form responses."""

    form_id: str = ""
    total_responses: int = 0
    question_summaries: list[QuestionSummary] = Field(default_factory=list)


class QuestionSummary(BaseModel):
    """Summary statistics for a single question's responses."""

    question_id: str = ""
    question_title: str = ""
    response_count: int = 0
    # For choice questions: option → count
    option_counts: dict[str, int] = Field(default_factory=dict)
    # For text questions: list of unique text responses
    text_responses: list[str] = Field(default_factory=list)
    # For numeric/scale: basic statistics
    average: Optional[float] = None
    median: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
