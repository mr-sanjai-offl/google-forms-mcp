"""MCP Tools for AI Planning and Plan Validation."""

import json
from typing import Any


def register_planning_tools(mcp: Any) -> None:
    """Register all planning and validation tools.

    Args:
        mcp: FastMCP server instance.
    """

    @mcp.tool()
    def validate_execution_plan(plan_json: str) -> str:
        """Validate an execution plan for a Google Form before making API calls.

        The plan should be a JSON string representing the intended form structure.
        Checks for duplicate questions, invalid question types, and structural issues.

        Args:
            plan_json: A JSON string containing the plan (must have "sections" or "questions").

        Returns:
            JSON string with validation results, warnings, and errors.
        """
        try:
            plan = json.loads(plan_json)
        except json.JSONDecodeError as e:
            return json.dumps({"status": "invalid", "errors": [f"Invalid JSON: {e!s}"]})

        errors = []
        warnings = []
        seen_titles = set()
        question_count = 0

        # Recursively search for questions
        def check_questions(item_list: list[dict[str, Any]], section_title: str) -> None:
            nonlocal question_count
            for item in item_list:
                title = item.get("title", "")
                q_type = item.get("type", "").upper()

                if not title:
                    warnings.append(f"Found a question without a title in section '{section_title}'.")

                if title in seen_titles and title:
                    warnings.append(f"Duplicate question title found: '{title}'.")
                seen_titles.add(title)

                valid_types = {
                    "SHORT_ANSWER", "PARAGRAPH", "MULTIPLE_CHOICE", "CHECKBOXES",
                    "DROPDOWN", "LINEAR_SCALE", "DATE", "TIME", "FILE_UPLOAD",
                    "MULTIPLE_CHOICE_GRID", "CHECKBOX_GRID"
                }

                if q_type and q_type not in valid_types:
                    errors.append(f"Invalid question type '{q_type}' for question '{title}'.")

                # Validation rules check
                if "validation" in item:
                    val = item["validation"]
                    if not isinstance(val, dict) or "type" not in val:
                        errors.append(f"Invalid validation format for question '{title}'. Must have a 'type'.")

                question_count += 1

        if "sections" in plan:
            for i, section in enumerate(plan["sections"]):
                sec_title = section.get("title", f"Section {i+1}")
                if "questions" in section:
                    check_questions(section["questions"], sec_title)
        elif "questions" in plan:
            check_questions(plan["questions"], "Main")
        else:
            errors.append("Plan must contain a 'sections' or 'questions' list.")

        if question_count == 0:
            warnings.append("Plan contains no questions.")

        return json.dumps({
            "status": "valid" if not errors else "invalid",
            "errors": errors,
            "warnings": warnings,
            "question_count": question_count
        }, indent=2)

    @mcp.tool()
    def estimate_completion(question_count: int, has_branching: bool, has_validation: bool) -> str:
        """Estimate the number of API calls and approximate time required to build the form.
        
        Args:
            question_count: Total number of questions.
            has_branching: True if the form uses branching logic.
            has_validation: True if the form uses complex validation.
            
        Returns:
            JSON string with estimates.
        """
        # Base: Create form + Update settings
        api_calls = 2

        # Each question is an API call
        api_calls += question_count

        if has_branching:
            api_calls += (question_count // 2)  # Rough estimate: half the questions have branching updates

        if has_validation:
            # Validation is usually bundled with question creation, but just to be safe
            api_calls += 0

        # At approx 2 API calls per second (due to rate limits)
        estimated_seconds = api_calls * 0.5

        return json.dumps({
            "estimated_api_calls": api_calls,
            "estimated_time_seconds": round(estimated_seconds, 1)
        }, indent=2)
