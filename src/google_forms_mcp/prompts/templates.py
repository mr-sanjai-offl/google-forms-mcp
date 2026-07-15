"""Reusable form templates for the AI planner."""

from typing import Any

TEMPLATES: dict[str, dict[str, Any]] = {
    "hackathon": {
        "title": "Hackathon Registration",
        "description": "Register for our upcoming hackathon.",
        "sections": [
            {
                "title": "Personal Details",
                "questions": [
                    {"type": "SHORT_ANSWER", "title": "Full Name", "required": True},
                    {
                        "type": "SHORT_ANSWER",
                        "title": "Email Address",
                        "required": True,
                        "validation": {"type": "EMAIL"},
                    },
                    {"type": "SHORT_ANSWER", "title": "Phone Number", "required": True},
                ],
            },
            {
                "title": "Team Details",
                "questions": [
                    {
                        "type": "MULTIPLE_CHOICE",
                        "title": "Are you registering as an individual or a team?",
                        "options": ["Individual", "Team"],
                        "required": True,
                    },
                    {
                        "type": "SHORT_ANSWER",
                        "title": "Team Name (if applicable)",
                        "required": False,
                    },
                ],
            },
            {
                "title": "Additional Information",
                "questions": [
                    {
                        "type": "MULTIPLE_CHOICE",
                        "title": "Food Preferences",
                        "options": ["Vegetarian", "Vegan", "Halal", "Gluten-Free", "None"],
                        "required": True,
                    },
                    {"type": "SHORT_ANSWER", "title": "Any allergies?", "required": False},
                    {
                        "type": "MULTIPLE_CHOICE",
                        "title": "Require Accommodation?",
                        "options": ["Yes", "No"],
                        "required": True,
                    },
                    {"type": "FILE_UPLOAD", "title": "Upload College ID", "required": True},
                ],
            },
        ],
    },
    "student_registration": {
        "title": "Student Registration",
        "description": "Enrollment form for the new academic year.",
        "sections": [
            {
                "title": "Student Details",
                "questions": [
                    {"type": "SHORT_ANSWER", "title": "First Name", "required": True},
                    {"type": "SHORT_ANSWER", "title": "Last Name", "required": True},
                    {"type": "DATE", "title": "Date of Birth", "required": True},
                    {"type": "SHORT_ANSWER", "title": "Student ID", "required": True},
                ],
            },
            {
                "title": "Contact Information",
                "questions": [
                    {
                        "type": "SHORT_ANSWER",
                        "title": "Email Address",
                        "required": True,
                        "validation": {"type": "EMAIL"},
                    },
                    {"type": "SHORT_ANSWER", "title": "Phone Number", "required": True},
                    {"type": "PARAGRAPH", "title": "Residential Address", "required": True},
                ],
            },
            {
                "title": "Emergency Contact",
                "questions": [
                    {"type": "SHORT_ANSWER", "title": "Emergency Contact Name", "required": True},
                    {"type": "SHORT_ANSWER", "title": "Emergency Contact Number", "required": True},
                    {"type": "SHORT_ANSWER", "title": "Relationship to Student", "required": True},
                ],
            },
        ],
    },
    "employee_feedback": {
        "title": "Employee Feedback Survey",
        "description": "Please provide your honest feedback. Your responses will be kept confidential.",
        "sections": [
            {
                "title": "Work Environment",
                "questions": [
                    {
                        "type": "LINEAR_SCALE",
                        "title": "How satisfied are you with the work environment?",
                        "low_value": 1,
                        "high_value": 5,
                        "low_label": "Very Dissatisfied",
                        "high_label": "Very Satisfied",
                        "required": True,
                    },
                    {
                        "type": "LINEAR_SCALE",
                        "title": "How would you rate your work-life balance?",
                        "low_value": 1,
                        "high_value": 5,
                        "low_label": "Poor",
                        "high_label": "Excellent",
                        "required": True,
                    },
                ],
            },
            {
                "title": "Open Feedback",
                "questions": [
                    {
                        "type": "PARAGRAPH",
                        "title": "What do you like most about working here?",
                        "required": False,
                    },
                    {
                        "type": "PARAGRAPH",
                        "title": "What improvements would you suggest?",
                        "required": False,
                    },
                ],
            },
        ],
    },
    "event_rsvp": {
        "title": "Event RSVP",
        "description": "Please let us know if you can make it!",
        "sections": [
            {
                "title": "Attendance",
                "questions": [
                    {"type": "SHORT_ANSWER", "title": "Full Name", "required": True},
                    {
                        "type": "SHORT_ANSWER",
                        "title": "Email Address",
                        "required": True,
                        "validation": {"type": "EMAIL"},
                    },
                    {
                        "type": "MULTIPLE_CHOICE",
                        "title": "Will you be attending?",
                        "options": ["Yes, I'll be there", "No, I can't make it"],
                        "required": True,
                    },
                    {
                        "type": "SHORT_ANSWER",
                        "title": "Number of guests (including yourself)",
                        "required": True,
                        "validation": {
                            "type": "NUMBER",
                            "number_op": "GREATER_THAN",
                            "number_value": 0,
                        },
                    },
                ],
            }
        ],
    },
    "quiz": {
        "title": "General Knowledge Quiz",
        "description": "Test your knowledge!",
        "settings": {"is_quiz": True, "shuffle_questions": True, "progress_bar": True},
        "sections": [
            {
                "title": "Questions",
                "questions": [
                    {
                        "type": "MULTIPLE_CHOICE",
                        "title": "What is the capital of France?",
                        "options": ["London", "Berlin", "Paris", "Madrid"],
                        "required": True,
                        "grading": {"point_value": 1, "correct_answers": ["Paris"]},
                    },
                    {
                        "type": "MULTIPLE_CHOICE",
                        "title": "Which planet is known as the Red Planet?",
                        "options": ["Venus", "Mars", "Jupiter", "Saturn"],
                        "required": True,
                        "grading": {"point_value": 1, "correct_answers": ["Mars"]},
                    },
                ],
            }
        ],
    },
}
