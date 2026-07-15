"""Master MCP prompts for AI form planning and execution."""

import json
from typing import Any

from fastmcp.prompts.base import Message

from google_forms_mcp.prompts.templates import TEMPLATES


def plan_form(intent: str | None = None) -> list[Message]:
    """Generate the master prompt for the autonomous form planner."""

    # We construct a system prompt that guides the AI on its behavior.
    prompt_text = (
        "You are an autonomous Google Forms Agent. Your goal is to guide the user from a high-level intent "
        "to a fully executed Google Form, orchestrated through the available MCP tools.\n\n"
        "### Workflow Pipeline\n"
        "You MUST strictly follow this pipeline. Do not skip steps.\n"
        "1. **Intent Detection & Template Matching**: Identify the purpose of the form. If a template exists "
        "for this intent, use it as a baseline.\n"
        "2. **Missing Information Engine**: Ask the user interactive follow-up questions to gather necessary details. "
        "Do not ask all questions at once if there are too many; ask logical groupings. Examples of things to ask: "
        "Form title/description, required sections, specific data fields (e.g., email, phone, age), and branching logic.\n"
        "3. **Execution Plan Generation**: Once you have enough information, generate a structured Execution Plan. "
        "Present the structure (Sections, Questions, Settings) to the user for final approval.\n"
        "4. **Validation**: Use the `validate_execution_plan` tool (if available) to verify your structure against API rules.\n"
        "5. **Tool Orchestration**: Once approved, execute the plan by calling the Google Forms MCP tools sequentially. "
        "Start with `create_form`, then add sections, questions, and update settings.\n"
        "6. **Result Summary**: Present the final form link to the user.\n\n"
        "### API Constraints to Remember\n"
        "- Google Forms API does NOT support visual theme customization (colors, fonts, header images).\n"
        "- Forms created via the API are published automatically.\n"
        "- Branching (`set_question_branching`, `set_section_navigation`) relies on exact IDs and specific question types (Multiple Choice/Dropdown).\n\n"
    )

    if intent:
        prompt_text += f"\n**User Intent Hint:** The user has indicated they want to create a form related to: {intent}\n"

    # Provide a list of available templates
    prompt_text += "\n### Available Templates\n"
    for key, template in TEMPLATES.items():
        prompt_text += f"- **{key}**: {template['title']} - {template['description']}\n"

    prompt_text += (
        "\n### Immediate Action\n"
        "Begin by greeting the user, confirming their intent, and asking the first set of follow-up questions "
        "to gather missing information. Do NOT attempt to create the form until you have collected sufficient details."
    )

    return [Message(role="user", content=prompt_text)]


def get_template(template_name: str) -> list[Message]:
    """Get a specific form template structure."""
    if template_name not in TEMPLATES:
        return [
            Message(
                role="user",
                content=f"Template '{template_name}' not found. Available templates: {', '.join(TEMPLATES.keys())}",
            )
        ]

    template_json = json.dumps(TEMPLATES[template_name], indent=2)
    return [
        Message(
            role="user",
            content=f"Here is the structure for the '{template_name}' template:\n```json\n{template_json}\n```\n"
            "Use this as a baseline to create your execution plan.",
        )
    ]


def register_prompts(mcp: Any) -> None:
    """Register all planning and agentic prompts."""
    mcp.prompt()(plan_form)
    mcp.prompt()(get_template)
