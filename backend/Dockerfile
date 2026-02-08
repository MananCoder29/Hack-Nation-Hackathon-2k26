FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

# Copy dependency files first
COPY uv.lock pyproject.toml ./

# Install dependencies without cache mounts
RUN uv sync --frozen --no-install-project --no-dev

# Final stage
FROM python:3.11-slim-bookworm

# Copy the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
WORKDIR /app
COPY . .

# Set PATH to use venv
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8080

# Use exec form for better signal handling
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
