# ===========================================================================
# ErisPulse Docker Image
# https://github.com/ErisPulse/ErisPulse
#
# Usage:
#   Production (stable):
#     docker build -t erispulse/erispulse:latest .
#
#   Dev (pre-release):
#     docker build --target dev -t erispulse/erispulse:dev .
#
# Environment variables (runtime):
#   ERISPULSE_CHANNEL           - "stable" or "dev" (default: stable)
#   ERISPULSE_UPDATE_ON_START   - "true" to auto-update on start (default: false)
#   ERISPULSE_DASHBOARD_TOKEN   - Dashboard login token
#
# Docker Hub: https://hub.docker.com/r/erispulse/erispulse
# ===========================================================================

FROM python:3.13-slim AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    ERISPULSE_DASHBOARD_TOKEN="" \
    ERISPULSE_CHANNEL="" \
    ERISPULSE_UPDATE_ON_START=""

LABEL org.opencontainers.image.title="ErisPulse" \
      org.opencontainers.image.description="ErisPulse - 事件驱动的多平台机器人开发框架" \
      org.opencontainers.image.url="https://github.com/ErisPulse/ErisPulse" \
      org.opencontainers.image.source="https://github.com/ErisPulse/ErisPulse" \
      org.opencontainers.image.vendor="ErisDev"

WORKDIR /app

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

VOLUME ["/app/config"]
EXPOSE 8000

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["epsdk", "run"]

# --- Production: stable release from PyPI ---
FROM base AS production

ARG ERISPULSE_VERSION=""
RUN if [ -n "$ERISPULSE_VERSION" ]; then \
      uv pip install --system "ErisPulse==${ERISPULSE_VERSION}" ErisPulse-Dashboard; \
    else \
      uv pip install --system ErisPulse ErisPulse-Dashboard; \
    fi

# --- Dev: latest pre-release from PyPI ---
FROM base AS dev

RUN uv pip install --system --pre ErisPulse ErisPulse-Dashboard
ENV ERISPULSE_CHANNEL="dev"
