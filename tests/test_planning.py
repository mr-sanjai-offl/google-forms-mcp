import json

from google_forms_mcp.prompts.planning import get_template, plan_form
from google_forms_mcp.tools.planning.tools import validate_execution_plan


def test_plan_form_prompt():
    messages = plan_form("Hackathon")
    assert len(messages) == 1
    assert "Hackathon" in str(messages[0].content)


def test_get_template():
    messages = get_template("hackathon")
    assert len(messages) == 1
    assert "Team Details" in str(messages[0].content)

    # Test invalid template
    messages = get_template("invalid_template")
    assert "not found" in str(messages[0].content)


def test_validate_execution_plan():
    valid_plan = {
        "sections": [
            {"title": "Section 1", "questions": [{"title": "Question 1", "type": "SHORT_ANSWER"}]}
        ]
    }

    result_json = validate_execution_plan(json.dumps(valid_plan))
    result = json.loads(result_json)

    assert result["status"] == "valid"
    assert result["question_count"] == 1

    invalid_plan = {
        "sections": [
            {"title": "Section 1", "questions": [{"title": "Question 1", "type": "INVALID_TYPE"}]}
        ]
    }

    result_json = validate_execution_plan(json.dumps(invalid_plan))
    result = json.loads(result_json)

    assert result["status"] == "invalid"
    assert len(result["errors"]) > 0
    assert "Invalid question type" in result["errors"][0]
