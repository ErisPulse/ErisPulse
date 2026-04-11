# ===========================================================================
# ErisPulse Docker Image
# https://github.com/ErisPulse/ErisPulse
#
# Multi-stage build:
#   - base:        Python 3.13-slim + system deps + uv
#   - production:  ErisPulse from PyPI + Dashboard (default)
#   - development: ErisPulse from source + dev deps + Dashboard
#
# Usage:
#   Production:  docker build -t wsu2059/erispulse .
#   Development: docker build --target development -t wsu2059/erispulse:dev .
#
# Dashboard:
#   Set ERISPULSE_DASHBOARD_TOKEN env to configure login token.
#   Access via http://localhost:8000
#
# Docker Hub: https://hub.docker.com/r/wsu2059/erispulse
# ===========================================================================

# ---------------------------------------------------------------------------
# Stage: base
# ---------------------------------------------------------------------------
FROM python:3.13-slim AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# ---------------------------------------------------------------------------
# Stage: production
# ---------------------------------------------------------------------------
FROM base AS production

LABEL org.opencontainers.image.title="ErisPulse" \
      org.opencontainers.image.description="ErisPulse - 事件驱动的多平台机器人开发框架" \
      org.opencontainers.image.url="https://github.com/ErisPulse/ErisPulse" \
      org.opencontainers.image.source="https://github.com/ErisPulse/ErisPulse" \
      org.opencontainers.image.vendor="ErisDev"

ENV ERISPULSE_DASHBOARD_TOKEN=""

RUN uv pip install --system ErisPulse ErisPulse-Dashboard

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

VOLUME ["/app/config"]
EXPOSE 8000

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "main.py"]

# ---------------------------------------------------------------------------
# Stage: development
# ---------------------------------------------------------------------------
FROM base AS development

LABEL org.opencontainers.image.title="ErisPulse (Dev)" \
      org.opencontainers.image.description="ErisPulse Development Image"

ENV ERISPULSE_DASHBOARD_TOKEN=""

COPY src/ /app/src/
COPY pyproject.toml /app/

RUN uv pip install --system -e ".[dev]" ErisPulse-Dashboard

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

VOLUME ["/app/config"]
EXPOSE 8000

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "main.py"]
