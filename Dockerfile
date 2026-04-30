# ===========================================================================
# ErisPulse Docker Image
# https://github.com/ErisPulse/ErisPulse
#
# Usage:
#   docker build -t erispulse/erispulse .
#
# Dashboard:
#   Set ERISPULSE_DASHBOARD_TOKEN env to configure login token.
#   Access via http://localhost:8000
#
# Docker Hub: https://hub.docker.com/r/erispulse/erispulse
# ===========================================================================

FROM python:3.13-slim AS production

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    ERISPULSE_DASHBOARD_TOKEN=""

LABEL org.opencontainers.image.title="ErisPulse" \
      org.opencontainers.image.description="ErisPulse - 事件驱动的多平台机器人开发框架" \
      org.opencontainers.image.url="https://github.com/ErisPulse/ErisPulse" \
      org.opencontainers.image.source="https://github.com/ErisPulse/ErisPulse" \
      org.opencontainers.image.vendor="ErisDev"

WORKDIR /app

RUN uv pip install --system ErisPulse ErisPulse-Dashboard

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

VOLUME ["/app/config"]
EXPOSE 8000

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["epsdk", "run"]
