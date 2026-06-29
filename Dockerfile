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
#   ERISPULSE_DASHBOARD_TOKEN   - Dashboard login token
#   LANG                        - System locale, auto-detects entrypoint language (default: en_US.UTF-8)
#   ERISPULSE_LANG              - Force entrypoint language: zh, zh_TW, en, ja, ru (overrides LANG)
#
# Note:
#   框架更新由 Dashboard 热更新完成，Docker 不参与包管理。
#
# Docker Hub: https://hub.docker.com/r/erispulse/erispulse
# ===========================================================================

FROM python:3.13-slim AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN apt-get update && apt-get install -y --no-install-recommends locales \
    && sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen \
    && sed -i '/zh_CN.UTF-8/s/^# //g' /etc/locale.gen \
    && sed -i '/zh_TW.UTF-8/s/^# //g' /etc/locale.gen \
    && sed -i '/ja_JP.UTF-8/s/^# //g' /etc/locale.gen \
    && sed -i '/ru_RU.UTF-8/s/^# //g' /etc/locale.gen \
    && locale-gen \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    ERISPULSE_DASHBOARD_TOKEN="" \
    ERISPULSE_LANG=""

LABEL org.opencontainers.image.title="ErisPulse" \
    org.opencontainers.image.description="ErisPulse - 事件驱动的多平台机器人开发框架" \
    org.opencontainers.image.url="https://github.com/ErisPulse/ErisPulse" \
    org.opencontainers.image.source="https://github.com/ErisPulse/ErisPulse" \
    org.opencontainers.image.vendor="ErisDev"

WORKDIR /app

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/ping')" || exit 1

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
# 备份 site-packages，用于持久化卷首次挂载时初始化
RUN cp -a /usr/local/lib/python3.13/site-packages /opt/site-packages-init

# --- Dev: latest pre-release from PyPI ---
FROM base AS dev

RUN uv pip install --system --pre ErisPulse ErisPulse-Dashboard
# 备份 site-packages，用于持久化卷首次挂载时初始化
RUN cp -a /usr/local/lib/python3.13/site-packages /opt/site-packages-init
