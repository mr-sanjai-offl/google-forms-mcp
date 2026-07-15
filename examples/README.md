# Examples

This directory contains example MCP workflow configurations and form templates.

## Usage

These examples show how you can prompt the AI to create forms through the MCP server.

### With Claude Desktop

1. Configure the MCP server in `claude_desktop_config.json` (see README).
2. Open Claude Desktop and type a natural-language request:

```
Create a hackathon registration form for "AI Builders 2025" with fields for
team name, team size, project idea, and dietary preferences.
```

The AI will use the `plan_form` prompt to guide itself through:
- Detecting your intent
- Matching the "hackathon" template
- Asking follow-up questions
- Building and validating the execution plan
- Executing tools to create the form on Google Forms

## Template Examples

| File | Description |
|------|-------------|
| `student_registration.json` | Student registration with personal info and academic details |
| `hackathon_registration.json` | Hackathon team registration with project details |
| `employee_feedback.json` | Employee satisfaction and feedback survey |
| `event_rsvp.json` | Event RSVP with attendance and dietary preferences |
| `quiz.json` | General knowledge quiz with grading |
| `placement_form.json` | Job placement application form |
| `research_survey.json` | Academic research survey |
| `attendance.json` | Daily attendance tracking form |
| `feedback_form.json` | Generic feedback collection form |
| `custom_workflow.json` | Custom prompt-driven workflow example |
