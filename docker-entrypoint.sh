#!/usr/bin/env bash
set -e

ERISPULSE_DIR="/app"
CONFIG_DIR="${ERISPULSE_DIR}/config"
CONFIG_FILE="${CONFIG_DIR}/config.toml"


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

ensure_config_dir
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

echo "[ErisPulse] Dashboard: http://0.0.0.0:8000"
echo "[ErisPulse] 正在启动..."
echo "==========================================="

exec "$@"
