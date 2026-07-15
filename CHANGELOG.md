# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-07-15

### Added
- **Complete Google Forms & Drive & Sheets Integration**: Full CRUD capabilities for Google Forms, exact schema support for all 11 question types, batch updates, response retrieval, Drive file/folder management (`lru_cache` optimized), and Sheets response export/reading.
- **Autonomous AI Intelligence Layer (Phase 4)**: Prompt-driven `plan_form` and `get_template` prompts with interactive missing information collection, schema validation (`validate_execution_plan`), and sequential MCP tool orchestration without bypassing API layers.
- **Extensive Template Repository (`examples/`)**: 10 production-ready form workflow templates (`student_registration.json`, `hackathon_registration.json`, `employee_feedback.json`, `event_rsvp.json`, `quiz.json`, `placement_form.json`, `research_survey.json`, `attendance.json`, `feedback_form.json`, `custom_workflow.json`) with grading, custom validation, and conditional navigation.
- **Enterprise Security & OAuth 2.0**: Isolated multi-profile `TokenManager`, `CredentialManager`, strict permission validation (`3-tier` read/write/full scoping), and token redaction logging.
- **Production Infrastructure & Observability**: Token bucket rate limiter (`forms_read/write`, `drive_read/write`, `sheets_read/write`), exponential backoff retry system, multi-stage non-root hardened `Dockerfile`, and `docker-compose.yml`.
- **Comprehensive Testing & CI/CD**: 48 fully-mocked unit tests (`test_auth`, `test_clients`, `test_exceptions`, `test_models`, `test_planning`, `test_rate_limiter`, `test_server`, `test_services`, `test_token_manager`) running on multi-Python (3.10-3.13) GitHub Actions CI/CD (`ci.yml` and `release.yml`).
- **Open-Source Governance & Readiness**: Full community documentation (`SECURITY.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `SUPPORT.md`, `ROADMAP.md`, issue/pr templates, and `.github/FUNDING.yml`).
