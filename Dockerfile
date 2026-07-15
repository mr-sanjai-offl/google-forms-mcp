# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim

# Install the project into `/app`
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Copy the project requirements
COPY pyproject.toml uv.lock ./

# Install the project's dependencies
# We use --no-install-project to only install dependencies, allowing caching
RUN uv sync --frozen --no-install-project --no-dev

# Copy the project source code
COPY . /app

# Install the project itself
RUN uv sync --frozen --no-dev

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Run the MCP server
# We use stdio by default for MCP, but it can be overridden
CMD ["uv", "run", "python", "-m", "google_forms_mcp"]
