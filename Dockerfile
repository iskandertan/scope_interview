# Production Dockerfile: Multi-stage build with UV best practices
# Based on: https://docs.astral.sh/uv/guides/integration/docker/
# Python version is read from .python-version (managed by uv)

FROM debian:bookworm-slim AS builder

# Copy UV from official image
COPY --from=ghcr.io/astral-sh/uv:0.10.9 /uv /uvx /bin/

WORKDIR /app

# Silence link-mode warnings when using cache mounts
ENV UV_LINK_MODE=copy

# Install the pinned Python version (reads .python-version)
COPY .python-version .
RUN uv python install

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
FROM debian:bookworm-slim

WORKDIR /app

# Copy uv-managed Python and .venv from builder
COPY --from=builder /root/.local/share/uv /root/.local/share/uv
COPY --from=builder /app/.venv /app/.venv

# Set up environment
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
