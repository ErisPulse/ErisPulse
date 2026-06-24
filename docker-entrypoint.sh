#!/usr/bin/env bash
set -e

ERISPULSE_DIR="/app"
CONFIG_DIR="${ERISPULSE_DIR}/config"
CONFIG_FILE="${CONFIG_DIR}/config.toml"

ERISPULSE_CHANNEL="${ERISPULSE_CHANNEL:-}"
ERISPULSE_UPDATE_ON_START="${ERISPULSE_UPDATE_ON_START:-}"
LANG_CODE=""

# ==================== i18n ====================

declare -A L

_L_zh="checking_update=正在检查更新
updated=已更新
already_latest=已是最新版本
update_failed=更新失败
config_generated=已生成默认配置（含 Dashboard 令牌）
config_appended=已追加 Dashboard 配置到现有配置文件
stopping=正在停止...
config_file=配置文件
no_config=未检测到配置文件，将使用默认配置
dashboard_token_set=Dashboard 令牌: 已配置
dashboard_token_unset=Dashboard 令牌: 未设置
dashboard_token_hint=（可通过环境变量 ERISPULSE_DASHBOARD_TOKEN 配置）
starting=正在启动...
channel_label=渠道"

_L_zh_TW="checking_update=正在檢查更新
updated=已更新
already_latest=已是最新版本
update_failed=更新失敗
config_generated=已產生預設設定（含 Dashboard 權杖）
config_appended=已附加 Dashboard 設定到現有設定檔
stopping=正在停止...
config_file=設定檔
no_config=未偵測到設定檔，將使用預設設定
dashboard_token_set=Dashboard 權杖: 已設定
dashboard_token_unset=Dashboard 權杖: 未設定
dashboard_token_hint=（可透過環境變數 ERISPULSE_DASHBOARD_TOKEN 設定）
starting=正在啟動...
channel_label=管道"

_L_en="checking_update=Checking for updates
updated=Updated
already_latest=Already latest version
update_failed=Update failed
config_generated=Generated default config (with Dashboard token)
config_appended=Appended Dashboard config to existing file
stopping=Stopping...
config_file=Config file
no_config=No config detected, using defaults
dashboard_token_set=Dashboard token: configured
dashboard_token_unset=Dashboard token: not set
dashboard_token_hint=(set via ERISPULSE_DASHBOARD_TOKEN env var)
starting=Starting...
channel_label=Channel"

_L_ja="checking_update=更新を確認中
updated=更新完了
already_latest=最新バージョンです
update_failed=更新に失敗しました
config_generated=デフォルト設定を生成しました（Dashboard トークン付き）
config_appended=既存の設定ファイルに Dashboard 設定を追加しました
stopping=停止中...
config_file=設定ファイル
no_config=設定ファイルが見つかりません。デフォルト設定を使用します
dashboard_token_set=Dashboard トークン: 設定済み
dashboard_token_unset=Dashboard トークン: 未設定
dashboard_token_hint=（環境変数 ERISPULSE_DASHBOARD_TOKEN で設定可能）
starting=起動中...
channel_label=チャネル"

_L_ru="checking_update=Проверка обновлений
updated=Обновлено
already_latest=Актуальная версия
update_failed=Ошибка обновления
config_generated=Создана конфигурация по умолчанию (с токеном Dashboard)
config_appended=Конфигурация Dashboard добавлена в существующий файл
stopping=Остановка...
config_file=Файл конфигурации
no_config=Файл конфигурации не найден, используются настройки по умолчанию
dashboard_token_set=Токен Dashboard: настроен
dashboard_token_unset=Токен Dashboard: не задан
dashboard_token_hint=(задайте через переменную окружения ERISPULSE_DASHBOARD_TOKEN)
starting=Запуск...
channel_label=Канал"

_load_lang() {
    local lang_data_var="_L_$1"
    local lang_data="${!lang_data_var}"
    while IFS='=' read -r key value; do
        [ -n "$key" ] && L["$key"]="$value"
    done <<< "$lang_data"
}

t() {
    local key="$1"
    if [ -n "${L[$key]}" ]; then
        echo "${L[$key]}"
    else
        echo "$key"
    fi
}

detect_lang() {
    if [ -n "${ERISPULSE_LANG}" ]; then
        case "${ERISPULSE_LANG}" in
            zh_TW|zh-Hant|zh_Hant) LANG_CODE="zh_TW" ;;
            zh*) LANG_CODE="zh" ;;
            ja*) LANG_CODE="ja" ;;
            ru*) LANG_CODE="ru" ;;
            en*) LANG_CODE="en" ;;
            *) LANG_CODE="en" ;;
        esac
        return
    fi
    local loc="${LC_ALL:-${LANG:-}}"
    case "${loc:0:5}" in
        zh_TW*|zh_Hant*|zh-Hant*) LANG_CODE="zh_TW" ;;
        zh*) LANG_CODE="zh" ;;
        ja*) LANG_CODE="ja" ;;
        ru*) LANG_CODE="ru" ;;
        *) LANG_CODE="en" ;;
    esac
}

# ==================== Banner ====================

ASCII_BANNER="███████╗██████╗ ███████╗██████╗ ██╗  ██╗
██╔════╝██╔══██╗██╔════╝██╔══██╗██║ ██╔╝
█████╗  ██████╔╝███████╗██║  ██║█████╔╝
██╔══╝  ██╔═══╝ ╚════██║██║  ██║██╔═██╗
███████╗██║     ███████║██████╔╝██║  ██╗
╚══════╝╚═╝     ╚══════╝╚═════╝ ╚═╝  ╚═╝"

# ==================== Helpers ====================

get_version() {
    python3 -c "import importlib.metadata; print(importlib.metadata.version('ErisPulse'))" 2>/dev/null || echo "unknown"
}

# ==================== Functions ====================

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

    echo "[ErisPulse] $(t 'checking_update') (channel: ${ERISPULSE_CHANNEL})..."

    local old_version new_version update_log
    old_version=$(get_version)

    if update_log=$(uv pip install --system ${pre_flag} --upgrade ErisPulse ErisPulse-Dashboard 2>&1); then
        new_version=$(get_version)
        if [ "${old_version}" != "${new_version}" ]; then
            echo "[ErisPulse] $(t 'updated'): ${old_version} -> ${new_version}"
        else
            echo "[ErisPulse] $(t 'already_latest'): ${new_version}"
        fi
    else
        echo "[ErisPulse] $(t 'update_failed')"
        echo "${update_log}" | tail -5
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
        echo "[ErisPulse] $(t 'config_generated')"
    else
        echo "" >> "${CONFIG_FILE}"
        echo "[Dashboard]" >> "${CONFIG_FILE}"
        echo "token = \"${ERISPULSE_DASHBOARD_TOKEN}\"" >> "${CONFIG_FILE}"
        echo "title = \"ErisPulse Dashboard\"" >> "${CONFIG_FILE}"
        echo "[ErisPulse.modules.status]" >> "${CONFIG_FILE}"
        echo "Dashboard = true" >> "${CONFIG_FILE}"
        echo "[ErisPulse] $(t 'config_appended')"
    fi
}

shutdown() {
    echo ""
    echo "[ErisPulse] $(t 'stopping')"
    exit 0
}

trap shutdown SIGTERM SIGINT

# ==================== Main ====================

detect_lang
_load_lang "${LANG_CODE}"

echo ""
echo "${ASCII_BANNER}"
echo "  ErisPulse Docker"
echo ""

resolve_channel
resolve_update_flag

ensure_config_dir

if [ "${ERISPULSE_UPDATE_ON_START}" = "true" ]; then
    update_erispulse
fi

ensure_dashboard_config

if [ -f "${CONFIG_FILE}" ]; then
    echo "[ErisPulse] $(t 'config_file'): ${CONFIG_FILE}"
else
    echo "[ErisPulse] $(t 'no_config')"
fi

if [ -n "${ERISPULSE_DASHBOARD_TOKEN}" ]; then
    echo "[ErisPulse] $(t 'dashboard_token_set')"
else
    echo "[ErisPulse] $(t 'dashboard_token_unset') $(t 'dashboard_token_hint')"
fi

echo "[ErisPulse] $(t 'channel_label'): ${ERISPULSE_CHANNEL}"
echo "[ErisPulse] Dashboard: http://0.0.0.0:8000"
echo "[ErisPulse] $(t 'starting')"

exec "$@"
