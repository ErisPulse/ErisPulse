#!/usr/bin/env bash
set -e

ERISPULSE_DIR="/app"
CONFIG_DIR="${ERISPULSE_DIR}/config"
CONFIG_FILE="${CONFIG_DIR}/config.toml"

LANG_CODE=""

# ==================== i18n ====================

declare -A L

_L_zh="config_generated=已生成默认配置（含 Dashboard 令牌）
config_appended=已追加 Dashboard 配置到现有配置文件
stopping=正在停止...
config_file=配置文件
no_config=未检测到配置文件，将使用默认配置
dashboard_token_set=Dashboard 令牌: 已配置
dashboard_token_unset=Dashboard 令牌: 未设置
dashboard_token_hint=（可通过环境变量 ERISPULSE_DASHBOARD_TOKEN 配置）
starting=正在启动...
pkg_repairing=检测到核心包损坏，正在从镜像备份还原
pkg_repaired=核心包已从镜像备份还原
pkg_repair_failed=核心包还原后仍异常，请检查日志"

_L_zh_TW="config_generated=已產生預設設定（含 Dashboard 權杖）
config_appended=已附加 Dashboard 設定到現有設定檔
stopping=正在停止...
config_file=設定檔
no_config=未偵測到設定檔，將使用預設設定
dashboard_token_set=Dashboard 權杖: 已設定
dashboard_token_unset=Dashboard 權杖: 未設定
dashboard_token_hint=（可透過環境變數 ERISPULSE_DASHBOARD_TOKEN 設定）
starting=正在啟動...
pkg_repairing=偵測到核心套件損壞，正在從映像檔備份還原
pkg_repaired=核心套件已從映像檔備份還原
pkg_repair_failed=核心套件還原後仍異常，請檢查日誌"

_L_en="config_generated=Generated default config (with Dashboard token)
config_appended=Appended Dashboard config to existing file
stopping=Stopping...
config_file=Config file
no_config=No config detected, using defaults
dashboard_token_set=Dashboard token: configured
dashboard_token_unset=Dashboard token: not set
dashboard_token_hint=(set via ERISPULSE_DASHBOARD_TOKEN env var)
starting=Starting...
pkg_repairing=Corrupted core package detected, restoring from image backup
pkg_repaired=Core package restored from image backup
pkg_repair_failed=Core package still broken after restore, check logs"

_L_ja="config_generated=デフォルト設定を生成しました（Dashboard トークン付き）
config_appended=既存の設定ファイルに Dashboard 設定を追加しました
stopping=停止中...
config_file=設定ファイル
no_config=設定ファイルが見つかりません。デフォルト設定を使用します
dashboard_token_set=Dashboard トークン: 設定済み
dashboard_token_unset=Dashboard トークン: 未設定
dashboard_token_hint=（環境変数 ERISPULSE_DASHBOARD_TOKEN で設定可能）
starting=起動中...
pkg_repairing=コアパッケージの破損を検出しました。イメージバックアップから復元しています
pkg_repaired=コアパッケージをイメージバックアップから復元しました
pkg_repair_failed=復元後もコアパッケージに異常があります。ログを確認してください"

_L_ru="config_generated=Создана конфигурация по умолчанию (с токеном Dashboard)
config_appended=Конфигурация Dashboard добавлена в существующий файл
stopping=Остановка...
config_file=Файл конфигурации
no_config=Файл конфигурации не найден, используются настройки по умолчанию
dashboard_token_set=Токен Dashboard: настроен
dashboard_token_unset=Токен Dashboard: не задан
dashboard_token_hint=(задайте через переменную окружения ERISPULSE_DASHBOARD_TOKEN)
starting=Запуск...
pkg_repairing=Обнаружено повреждение базового пакета, восстановление из резервной копии образа
pkg_repaired=Базовый пакет восстановлен из резервной копии образа
pkg_repair_failed=Базовый пакет по-прежнему неисправен после восстановления, проверьте журналы"

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

# ==================== Functions ====================

ensure_config_dir() {
    mkdir -p "${CONFIG_DIR}"
}

ensure_packages() {
    # 如果 site-packages 为空（首次 bind mount），从镜像备份初始化
    local pkg_dir="/usr/local/lib/python3.13/site-packages"
    local init_dir="/opt/site-packages-init"
    if [ -d "$init_dir" ] && [ -z "$(ls -A "$pkg_dir" 2>/dev/null)" ]; then
        echo "[ErisPulse] Initializing packages from image..."
        cp -a "$init_dir"/* "$pkg_dir"/ 2>/dev/null || true
    fi
}

verify_and_repair_packages() {
    # 核心包完整性自愈：热更新/容器重启被中断可能残留半写状态的包
    # （如 click/__init__.py 被截断，import 成功但导出缺失），仅判空无法发现，
    # 必须探测哨兵属性；损坏时从镜像备份还原该包
    local pkg_dir="/usr/local/lib/python3.13/site-packages"
    local init_dir="/opt/site-packages-init"
    [ -d "$init_dir" ] || return 0

    # 格式: 模块名:哨兵属性表达式
    local probes=("click:click.Choice" "uvicorn:uvicorn.Server" "fastapi:fastapi.FastAPI" "ErisPulse:ErisPulse.sdk")

    local entry mod expr
    for entry in "${probes[@]}"; do
        mod="${entry%%:*}"
        expr="${entry#*:}"
        if python -c "import $mod; $expr" >/dev/null 2>&1; then
            continue
        fi

        echo "[ErisPulse] $(t 'pkg_repairing'): ${mod}"
        # 删除损坏的包目录与元数据（连字符匹配，不误伤下划线包如 ErisPulse_Dashboard）
        rm -rf "${pkg_dir:?}/${mod}" "${pkg_dir:?}/${mod}"-*.dist-info
        # 从镜像备份还原（备份中不存在的包不处理，避免误删用户自装模块）
        if [ -d "${init_dir}/${mod}" ]; then
            cp -a "${init_dir}/${mod}" "${pkg_dir}/"
            cp -a "${init_dir}"/"${mod}"-*.dist-info "${pkg_dir}/" 2>/dev/null || true
        fi

        if python -c "import $mod; $expr" >/dev/null 2>&1; then
            echo "[ErisPulse] $(t 'pkg_repaired'): ${mod}"
        else
            echo "[ErisPulse] $(t 'pkg_repair_failed'): ${mod}"
        fi
    done
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

ensure_config_dir
ensure_packages
verify_and_repair_packages
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

echo "[ErisPulse] Dashboard: http://0.0.0.0:8000"
echo "[ErisPulse] $(t 'starting')"

exec "$@"
