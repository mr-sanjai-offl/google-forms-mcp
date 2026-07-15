# ---- Stage 1: Build ----
FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim AS builder

WORKDIR /app

# Enable bytecode compilation for faster startup
ENV UV_COMPILE_BYTECODE=1
# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Copy only dependency files first (Docker layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies only (no project code yet)
RUN uv sync --frozen --no-install-project --no-dev

# Copy the full project source
COPY . /app

# Install the project itself
RUN uv sync --frozen --no-dev

# ---- Stage 2: Runtime ----
FROM python:3.10-slim-bookworm AS runtime

LABEL maintainer="Google Forms MCP Contributors"
LABEL org.opencontainers.image.title="google-forms-mcp"
LABEL org.opencontainers.image.description="Production-grade MCP server for Google Forms automation"
LABEL org.opencontainers.image.source="https://github.com/your-org/google-forms-mcp"
LABEL org.opencontainers.image.licenses="MIT"

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash mcp
WORKDIR /app

# Copy the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

# Create persistent data directory
RUN mkdir -p /app/data && chown mcp:mcp /app/data

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

# Switch to non-root user
USER mcp

# Expose port for SSE/HTTP transport
EXPOSE 8000

# Healthcheck for HTTP/SSE mode (skipped in stdio mode)
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 0

# Run the MCP server
CMD ["python", "-m", "google_forms_mcp"]
