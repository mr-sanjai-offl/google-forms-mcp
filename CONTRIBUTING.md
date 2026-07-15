# Contributing to Google-Forms-MCP

Thank you for your interest in contributing! We welcome bug reports, feature requests, and pull requests.

## Getting Started

1. Fork the repository and clone it locally.
2. Install [`uv`](https://github.com/astral-sh/uv).
3. Run `uv sync --all-extras` to install the package and dev dependencies.

## Development Workflow

1. Create a feature branch: `git checkout -b feature/my-new-feature`
2. Make your changes in `src/`.
3. Add tests in `tests/`.
4. Run formatting and linting:
   - `uv run ruff format src/ tests/`
   - `uv run ruff check src/ tests/`
5. Run type checking: `uv run pyright`
6. Run the test suite: `uv run pytest`

## Pull Requests

Please ensure that your code passes all CI checks and maintains 100% test coverage for new functionality before submitting a pull request.
