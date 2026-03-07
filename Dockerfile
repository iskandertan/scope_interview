# Production Dockerfile: Multi-stage build with UV best practices
# Based on: https://docs.astral.sh/uv/guides/integration/docker/

FROM python:3.10-slim AS builder

# Copy UV from official image
COPY --from=ghcr.io/astral-sh/uv:0.10.9 /uv /uvx /bin/

WORKDIR /app

# Silence link-mode warnings when using cache mounts
ENV UV_LINK_MODE=copy

# Install dependencies with cache mount (only when pyproject.toml/uv.lock change)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable

# Copy project and install (non-editable for production, with bytecode compilation)
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable --compile-bytecode

# Runtime stage: minimal image with only virtual environment
FROM python:3.10-slim

WORKDIR /app

# Copy .venv from builder (source code not included in production image)
COPY --from=builder /app/.venv /app/.venv

# Set up environment
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
