"""Response analytics service.

Computes summary statistics and generates analysis data from form responses.
This is a pure computation layer — no API calls are made here.
"""

from __future__ import annotations

import csv
import io
import statistics
from collections import Counter

from google_forms_mcp.models.form import Form, FormQuestion, QuestionType
from google_forms_mcp.models.response import (
    FormResponse,
    QuestionSummary,
    ResponseSummary,
)


class AnalyticsService:
    """Service for computing response analytics and summaries."""

    def compute_summary(
        self,
        form: Form,
        responses: list[FormResponse],
    ) -> ResponseSummary:
        """Compute aggregated summary statistics for form responses.

        Args:
            form: The form structure (for question metadata).
            responses: List of all form responses.

        Returns:
            ResponseSummary with per-question statistics.
        """
        # Build a question map from the form
        question_map: dict[str, FormQuestion] = {}
        for item in form.items:
            if item.question:
                question_map[item.question.question_id] = item.question
            for q in item.questions:
                question_map[q.question_id] = q

        # Aggregate answers per question
        question_answers: dict[str, list[list[str]]] = {}
        for response in responses:
            for q_id, answer in response.answers.items():
                if q_id not in question_answers:
                    question_answers[q_id] = []
                question_answers[q_id].append(answer.text_answers)

        # Build per-question summaries
        summaries: list[QuestionSummary] = []
        for q_id, answers_list in question_answers.items():
            question = question_map.get(q_id)
            summary = QuestionSummary(
                question_id=q_id,
                question_title=question.title if question else "",
                response_count=len(answers_list),
            )

            if question:
                qt = question.question_type
                flat_answers = [a for answers in answers_list for a in answers]

                if qt in (
                    QuestionType.MULTIPLE_CHOICE,
                    QuestionType.CHECKBOXES,
                    QuestionType.DROPDOWN,
                ):
                    summary.option_counts = dict(Counter(flat_answers))

                elif qt in (QuestionType.SHORT_ANSWER, QuestionType.PARAGRAPH):
                    # Deduplicate and limit text responses
                    unique = list(dict.fromkeys(flat_answers))
                    summary.text_responses = unique[:100]

                elif qt == QuestionType.LINEAR_SCALE:
                    numeric = []
                    for a in flat_answers:
                        try:
                            numeric.append(float(a))
                        except (ValueError, TypeError):
                            continue
                    if numeric:
                        summary.average = round(statistics.mean(numeric), 2)
                        summary.median = round(statistics.median(numeric), 2)
                        summary.min_value = min(numeric)
                        summary.max_value = max(numeric)

            summaries.append(summary)

        return ResponseSummary(
            form_id=form.info.form_id,
            total_responses=len(responses),
            question_summaries=summaries,
        )

    def export_responses_csv(
        self,
        form: Form,
        responses: list[FormResponse],
    ) -> str:
        """Export responses as a CSV string.

        Args:
            form: The form structure.
            responses: List of responses to export.

        Returns:
            CSV string with headers and data rows.
        """
        # Build ordered list of question IDs and titles
        questions: list[tuple[str, str]] = []
        for item in form.items:
            if item.question:
                questions.append((item.question.question_id, item.question.title or item.title))
            for q in item.questions:
                questions.append((q.question_id, q.title))

        # Build CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Header row
        headers = ["Timestamp", "Email"] + [title for _, title in questions]
        writer.writerow(headers)

        # Data rows
        for response in responses:
            row = [
                str(response.last_submitted_time or response.create_time or ""),
                response.respondent_email,
            ]
            for q_id, _ in questions:
                answer = response.answers.get(q_id)
                if answer:
                    row.append("; ".join(answer.text_answers))
                else:
                    row.append("")
            writer.writerow(row)

        return output.getvalue()

    def export_responses_json(
        self,
        form: Form,
        responses: list[FormResponse],
    ) -> list[dict]:
        """Export responses as a list of dictionaries.

        Args:
            form: The form structure.
            responses: List of responses to export.

        Returns:
            List of response dictionaries with question titles as keys.
        """
        # Build question title map
        q_titles: dict[str, str] = {}
        for item in form.items:
            if item.question:
                q_titles[item.question.question_id] = item.question.title or item.title
            for q in item.questions:
                q_titles[q.question_id] = q.title

        result = []
        for response in responses:
            row: dict = {
                "response_id": response.response_id,
                "timestamp": str(response.last_submitted_time or response.create_time or ""),
                "email": response.respondent_email,
            }
            for q_id, answer in response.answers.items():
                title = q_titles.get(q_id, q_id)
                row[title] = (
                    answer.text_answers
                    if len(answer.text_answers) > 1
                    else (answer.text_answers[0] if answer.text_answers else "")
                )
            result.append(row)

        return result
