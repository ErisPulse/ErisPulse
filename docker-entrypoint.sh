#!/usr/bin/env bash
set -e

ERISPULSE_DIR="/app"
CONFIG_DIR="${ERISPULSE_DIR}/config"
CONFIG_FILE="${CONFIG_DIR}/config.toml"

ERISPULSE_CHANNEL="${ERISPULSE_CHANNEL:-}"
ERISPULSE_UPDATE_ON_START="${ERISPULSE_UPDATE_ON_START:-}"

resolve_channel() {
    if [ -z "${ERISPULSE_CHANNEL}" ]; then
        if pip show ErisPulse 2>/dev/null | grep -qE 'Version:.*dev'; then
            ERISPULSE_CHANNEL="dev"
        else
            ERISPULSE_CHANNEL="stable"
        fi
    fi
}

resolve_update_flag() {
    if [ -z "${ERISPULSE_UPDATE_ON_START}" ]; then
        ERISPULSE_UPDATE_ON_START="false"
    fi
}

update_erispulse() {
    local pre_flag=""
    if [ "${ERISPULSE_CHANNEL}" = "dev" ]; then
        pre_flag="--pre"
    fi

    echo "[ErisPulse] 正在检查更新 (channel: ${ERISPULSE_CHANNEL})..."

    local old_version new_version
    old_version=$(python3 -c "import importlib.metadata; print(importlib.metadata.version('ErisPulse'))" 2>/dev/null || echo "unknown")

    uv pip install --system ${pre_flag} --upgrade ErisPulse ErisPulse-Dashboard 2>&1 | tail -1

    new_version=$(python3 -c "import importlib.metadata; print(importlib.metadata.version('ErisPulse'))" 2>/dev/null || echo "unknown")

    if [ "${old_version}" != "${new_version}" ]; then
        echo "[ErisPulse] 已更新: ${old_version} -> ${new_version}"
    else
        echo "[ErisPulse] 已是最新版本: ${new_version}"
    fi
}

ensure_config_dir() {
    mkdir -p "${CONFIG_DIR}"
}

ensure_dashboard_config() {
    if [ -z "${ERISPULSE_DASHBOARD_TOKEN}" ]; then
        return
    fi

    if [ -f "${CONFIG_FILE}" ] && grep -q '^\[Dashboard\]' "${CONFIG_FILE}"; then
        return
    fi

    if [ ! -f "${CONFIG_FILE}" ]; then
        cat > "${CONFIG_FILE}" <<EOF
[Dashboard]
token = "${ERISPULSE_DASHBOARD_TOKEN}"
title = "ErisPulse Dashboard"

[ErisPulse.framework]
enable_lazy_loading = true

[ErisPulse.logger]
level = "INFO"

[ErisPulse.server]
host = "0.0.0.0"
port = 8000

[ErisPulse.modules.status]
Dashboard = true
EOF
        echo "[ErisPulse] 已生成默认配置 (含 Dashboard 令牌)"
    else
        echo "" >> "${CONFIG_FILE}"
        echo "[Dashboard]" >> "${CONFIG_FILE}"
        echo "token = \"${ERISPULSE_DASHBOARD_TOKEN}\"" >> "${CONFIG_FILE}"
        echo "title = \"ErisPulse Dashboard\"" >> "${CONFIG_FILE}"
        echo "[ErisPulse.modules.status]" >> "${CONFIG_FILE}"
        echo "Dashboard = true" >> "${CONFIG_FILE}"
        echo "[ErisPulse] 已追加 Dashboard 配置到现有配置文件"
    fi
}

shutdown() {
    echo ""
    echo "[ErisPulse] 正在停止..."
    exit 0
}

trap shutdown SIGTERM SIGINT

echo "==========================================="
echo "  ErisPulse Docker"
echo "==========================================="

resolve_channel
resolve_update_flag

ensure_config_dir

if [ "${ERISPULSE_UPDATE_ON_START}" = "true" ]; then
    update_erispulse
fi

ensure_dashboard_config

if [ -f "${CONFIG_FILE}" ]; then
    echo "[ErisPulse] 配置文件: ${CONFIG_FILE}"
else
    echo "[ErisPulse] 未检测到配置文件，将使用默认配置"
fi

if [ -n "${ERISPULSE_DASHBOARD_TOKEN}" ]; then
    echo "[ErisPulse] Dashboard 令牌: 已配置"
else
    echo "[ErisPulse] Dashboard 令牌: 未设置 (可通过 ERISPULSE_DASHBOARD_TOKEN 环境变量配置)"
fi

echo "[ErisPulse] Channel: ${ERISPULSE_CHANNEL}"
echo "[ErisPulse] Dashboard: http://0.0.0.0:8000"
echo "[ErisPulse] 正在启动..."
echo "==========================================="

exec "$@"
