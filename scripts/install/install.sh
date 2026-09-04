#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

USE_UV=false
TARGET_VERSION=""
PYTHON_CMD=""
VENV_DIR=".venv"
DOCKER_AVAILABLE=false
DOCKER_COMPOSE_CMD=""
INSTALL_DASHBOARD=false
LANG_CODE=""

# ==================== i18n ====================

declare -A L

_L_zh="lang_name=简体中文
info_tag=信息
success_tag=成功
warning_tag=警告
error_tag=错误
install_title=ErisPulse 安装程序
docker_mode=Docker 安装模式
docker_image_builtin=官方镜像已内置 ErisPulse 和 Dashboard
traditional_mode=传统安装模式
uv_bootstrap_mode=安装 uv 工具链
uv_desc=uv 可以自动管理 Python 版本和虚拟环境
select_install=选择安装方式:
docker_install=Docker 安装（推荐）
traditional_install=传统安装（pip/uv + 虚拟环境）
uv_bootstrap_install=通过 uv 安装 Python 并配置环境
fetching_versions=正在从 PyPI 获取版本信息...
available_versions=可用版本:
latest_stable=最新稳定版
latest_pre=最新预发布版
view_all=查看所有版本
manual_version=手动指定版本号
pre_release=预发布
select_default=请选择 [1-4] (默认: 1)
no_stable=没有找到稳定版本
no_pre=没有找到预发布版本
enter_version=请输入版本号
version_empty=版本号不能为空
invalid_choice=请输入有效的选项
select_mirror=选择镜像源:
mirror_hub=Docker Hub (erispulse/erispulse)
mirror_ghcr=GitHub Container Registry (ghcr.io/erispulse/erispulse)
select_channel=选择版本通道:
channel_stable=stable（稳定版）
channel_dev=dev（预发布版）
enable_dashboard=是否启用 Dashboard 管理面板？ [Y/n]
set_token=请设置 Dashboard 登录令牌
token_empty=令牌不能为空，Dashboard 将不启用
set_port=设置端口 (默认: 8000)
confirm_install=确认安装？ [Y/n]
cancelled=操作已取消
generating_config=正在生成配置文件...
pulling_image=正在拉取镜像并启动...
install_complete=安装完成
install_config=安装配置确认
image_label=镜像
channel_label=通道
port_label=端口
enabled=已启用
not_enabled=未启用
manage_commands=管理命令:
view_logs=查看日志
stop_service=停止服务
restart_service=重启服务
update_image=更新镜像
dashboard_label=Dashboard
access_url=访问地址
login_token=登录令牌
use_uv=将使用 uv 进行安装
use_pip=将使用 pip 进行安装
will_install=将安装
latest_version=最新版本
install_dashboard=是否安装 Dashboard 管理面板模块？ [Y/n]
install_version=安装版本
install_latest=安装最新版本
installing=正在安装
install_success=安装成功
install_fail=安装失败
detected=检测到
will_use_uv=检测到 uv，将优先使用
uv_installed=uv 已安装
uv_install_success=uv 安装成功
uv_install_fail=uv 安装失败
installing_python=正在安装 Python 3.12...
python_install_success=Python 3.12 安装成功
python_install_fail=Python 安装失败
creating_venv=正在创建虚拟环境...
venv_exists=虚拟环境已存在
venv_recreate=是否删除并重新创建？ [y/N]
venv_use_existing=使用现有虚拟环境
venv_created=虚拟环境创建成功
venv_create_fail=虚拟环境创建失败
venv_activated=虚拟环境已激活
venv_activate_fail=虚拟环境激活脚本不存在
activating_venv=正在激活虚拟环境...
python_path=当前Python路径
python_not_found=未找到 Python，请先安装 Python 3.10 或更高版本
python_download=下载地址: https://www.python.org/downloads/
install_uv_for_python=是否安装 uv 以安装 Python 继续？ [Y/n]
python_version_fail=无法检测 Python 版本
python_detected=检测到 Python
python_version_low=Python 版本过低，建议使用 3.10 或更高版本
continue_=是否继续？ [y/N]
docker_detected=检测到 Docker
auto_selected=仅检测到一种安装方式，自动选择
no_install_method=未检测到可用的安装方式
install_tools=请安装以下任一工具:
docker_start_fail=Docker 启动失败
docker_manual=你可以手动运行
dashboard_installed=已安装 ErisPulse-Dashboard 模块
dashboard_access=运行后访问
dashboard_config=在 config.toml 中配置 [Dashboard] token 以设置登录令牌
tips=提示
tip_activate=每次打开新终端需先激活虚拟环境
tip_deactivate=输入 deactivate 可以退出虚拟环境
tip_update=更新框架: epsdk self-update
quick_start=快速开始
activate_venv=激活虚拟环境
init_project=初始化项目: epsdk init
install_module=安装模块: epsdk install <模块名>
run_project=运行项目: epsdk run
all_versions_title=可用版本列表
invalid_index=请输入有效的序号
invalid_version=请输入有效的序号或版本号
fetch_fail=无法获取版本信息，将安装最新版本
docker_compose_generated=docker-compose.yml 已生成
env_generated=.env 已生成
erispulse_started=ErisPulse 已启动
dashboard_install_fail=Dashboard 安装失败，但 ErisPulse 已安装成功
select_1_2=请输入 1 或 2
venv_ensurepip_missing=系统 Python 缺少 ensurepip，无法创建带 pip 的虚拟环境
venv_auto_install_pkg=是否自动安装所需系统包？ [Y/n]
venv_pkg_installed=依赖包安装成功
venv_pkg_install_fail=系统包安装失败
venv_manual_hint=请先手动安装 venv 支持（Debian/Ubuntu: sudo apt install python3-venv），然后重新运行本脚本
date_unknown=未知
star_message=喜欢我们的话欢迎来点个 star: https://github.com/ErisPulse/ErisPulse
i18n_note=如果您启动程序发现都是中文，请不要担心，Dashboard 同样支持多语言！"

_L_zh_TW="lang_name=繁體中文
info_tag=資訊
success_tag=成功
warning_tag=警告
error_tag=錯誤
install_title=ErisPulse 安裝程式
docker_mode=Docker 安裝模式
docker_image_builtin=官方映像已內建 ErisPulse 和 Dashboard
traditional_mode=傳統安裝模式
uv_bootstrap_mode=安裝 uv 工具鏈
uv_desc=uv 可以自動管理 Python 版本和虛擬環境
select_install=選擇安裝方式:
docker_install=Docker 安裝（推薦）
traditional_install=傳統安裝（pip/uv + 虛擬環境）
uv_bootstrap_install=透過 uv 安裝 Python 並設定環境
fetching_versions=正在從 PyPI 取得版本資訊...
available_versions=可用版本:
latest_stable=最新穩定版
latest_pre=最新預發布版
view_all=檢視所有版本
manual_version=手動指定版本號
pre_release=預發布
select_default=請選擇 [1-4] (預設: 1)
no_stable=沒有找到穩定版本
no_pre=沒有找到預發布版本
enter_version=請輸入版本號
version_empty=版本號不能為空
invalid_choice=請輸入有效的選項
select_mirror=選擇映像來源:
mirror_hub=Docker Hub (erispulse/erispulse)
mirror_ghcr=GitHub Container Registry (ghcr.io/erispulse/erispulse)
select_channel=選擇版本通道:
channel_stable=stable（穩定版）
channel_dev=dev（預發布版）
enable_dashboard=是否啟用 Dashboard 管理面板？ [Y/n]
set_token=請設定 Dashboard 登入令牌
token_empty=令牌不能為空，Dashboard 將不啟用
set_port=設定埠 (預設: 8000)
confirm_install=確認安裝？ [Y/n]
cancelled=操作已取消
generating_config=正在產生設定檔...
pulling_image=正在拉取映像並啟動...
install_complete=安裝完成
install_config=安裝設定確認
image_label=映像
channel_label=通道
port_label=埠
enabled=已啟用
not_enabled=未啟用
manage_commands=管理命令:
view_logs=檢視日誌
stop_service=停止服務
restart_service=重啟服務
update_image=更新映像
dashboard_label=Dashboard
access_url=存取位址
login_token=登入令牌
use_uv=將使用 uv 進行安裝
use_pip=將使用 pip 進行安裝
will_install=將安裝
latest_version=最新版本
install_dashboard=是否安裝 Dashboard 管理面板模組？ [Y/n]
installing=正在安裝
install_success=安裝成功
install_fail=安裝失敗
detected=偵測到
will_use_uv=偵測到 uv，將優先使用
uv_installed=uv 已安裝
uv_install_success=uv 安裝成功
uv_install_fail=uv 安裝失敗
installing_python=正在安裝 Python 3.12...
python_install_success=Python 3.12 安裝成功
python_install_fail=Python 安裝失敗
creating_venv=正在建立虛擬環境...
venv_exists=虛擬環境已存在
venv_recreate=是否刪除並重新建立？ [y/N]
venv_use_existing=使用現有虛擬環境
venv_created=虛擬環境建立成功
venv_create_fail=虛擬環境建立失敗
venv_activated=虛擬環境已啟用
venv_activate_fail=虛擬環境啟用指令碼不存在
activating_venv=正在啟用虛擬環境...
python_path=目前 Python 路徑
python_not_found=未找到 Python，請先安裝 Python 3.10 或更高版本
python_download=下載位址: https://www.python.org/downloads/
install_uv_for_python=是否安裝 uv 以安裝 Python 繼續？ [Y/n]
python_version_fail=無法偵測 Python 版本
python_detected=偵測到 Python
python_version_low=Python 版本過低，建議使用 3.10 或更高版本
continue_=是否繼續？ [y/N]
docker_detected=偵測到 Docker
auto_selected=僅偵測到一種安裝方式，自動選擇
no_install_method=未偵測到可用的安裝方式
install_tools=請安裝以下任一工具:
docker_start_fail=Docker 啟動失敗
docker_manual=你可以手動執行
dashboard_installed=已安裝 ErisPulse-Dashboard 模組
dashboard_access=執行後存取
dashboard_config=在 config.toml 中設定 [Dashboard] token 以設定登入令牌
tips=提示
tip_activate=每次開啟新終端需先啟用虛擬環境
tip_deactivate=輸入 deactivate 可以退出虛擬環境
tip_update=更新框架: epsdk self-update
quick_start=快速開始
activate_venv=啟用虛擬環境
init_project=初始化專案: epsdk init
install_module=安裝模組: epsdk install <模組名>
run_project=執行專案: epsdk run
all_versions_title=可用版本列表
invalid_index=請輸入有效的序號
invalid_version=請輸入有效的序號或版本號
fetch_fail=無法取得版本資訊，將安裝最新版本
docker_compose_generated=docker-compose.yml 已產生
env_generated=.env 已產生
erispulse_started=ErisPulse 已啟動
dashboard_install_fail=Dashboard 安裝失敗，但 ErisPulse 已安裝成功
select_1_2=請輸入 1 或 2
venv_ensurepip_missing=系統 Python 缺少 ensurepip，無法建立帶 pip 的虛擬環境
venv_auto_install_pkg=是否自動安裝所需系統套件？ [Y/n]
venv_pkg_installed=相依套件安裝成功
venv_pkg_install_fail=系統套件安裝失敗
venv_manual_hint=請先手動安裝 venv 支援（Debian/Ubuntu: sudo apt install python3-venv），然後重新執行本指令碼
date_unknown=未知
star_message=喜歡我們的話歡迎來點個 star: https://github.com/ErisPulse/ErisPulse
i18n_note=如果您啟動程式發現都是簡體中文，請不要擔心，Dashboard 同樣支援多語言！"

_L_en="lang_name=English
info_tag=INFO
success_tag=OK
warning_tag=WARN
error_tag=ERROR
install_title=ErisPulse Installer
docker_mode=Docker Installation
docker_image_builtin=Official image includes ErisPulse and Dashboard
traditional_mode=Traditional Installation
uv_bootstrap_mode=Install uv Toolchain
uv_desc=uv can automatically manage Python versions and virtual environments
select_install=Select installation method:
docker_install=Docker Install (Recommended)
traditional_install=Traditional Install (pip/uv + venv)
uv_bootstrap_install=Install Python via uv and setup environment
fetching_versions=Fetching version info from PyPI...
available_versions=Available versions:
latest_stable=Latest stable
latest_pre=Latest pre-release
view_all=View all versions
manual_version=Specify version manually
pre_release=pre-release
select_default=Select [1-4] (default: 1)
no_stable=No stable version found
no_pre=No pre-release version found
enter_version=Enter version number
version_empty=Version cannot be empty
invalid_choice=Please enter a valid option
select_mirror=Select image registry:
mirror_hub=Docker Hub (erispulse/erispulse)
mirror_ghcr=GitHub Container Registry (ghcr.io/erispulse/erispulse)
select_channel=Select channel:
channel_stable=stable
channel_dev=dev (pre-release)
enable_dashboard=Enable Dashboard? [Y/n]
set_token=Set Dashboard login token
token_empty=Token cannot be empty, Dashboard will be disabled
set_port=Set port (default: 8000)
confirm_install=Confirm install? [Y/n]
cancelled=Operation cancelled
generating_config=Generating config files...
pulling_image=Pulling image and starting...
install_complete=Installation Complete
install_config=Installation Summary
image_label=Image
channel_label=Channel
port_label=Port
enabled=Enabled
not_enabled=Disabled
manage_commands=Management commands:
view_logs=View logs
stop_service=Stop service
restart_service=Restart service
update_image=Update image
dashboard_label=Dashboard
access_url=Access URL
login_token=Login token
use_uv=Using uv for installation
use_pip=Using pip for installation
will_install=Will install
latest_version=latest version
install_dashboard=Install Dashboard module? [Y/n]
install_version=Install version
install_latest=Install latest version
installing=Installing
install_success=installed successfully
install_fail=Installation failed
detected=Detected
will_use_uv=uv detected, will be used preferentially
uv_installed=uv is already installed
uv_install_success=uv installed successfully
uv_install_fail=uv installation failed
installing_python=Installing Python 3.12...
python_install_success=Python 3.12 installed successfully
python_install_fail=Python installation failed
creating_venv=Creating virtual environment...
venv_exists=Virtual environment already exists
venv_recreate=Delete and recreate? [y/N]
venv_use_existing=Using existing virtual environment
venv_created=Virtual environment created
venv_create_fail=Virtual environment creation failed
venv_activated=Virtual environment activated
venv_activate_fail=Virtual environment activation script not found
activating_venv=Activating virtual environment...
python_path=Current Python path
python_not_found=Python not found. Please install Python 3.10+
python_download=Download: https://www.python.org/downloads/
install_uv_for_python=Install uv to install Python and continue? [Y/n]
python_version_fail=Cannot detect Python version
python_detected=Detected Python
python_version_low=Python version too low, 3.10+ recommended
continue_=Continue? [y/N]
docker_detected=Detected Docker
auto_selected=Only one method available, auto-selected
no_install_method=No installation method available
install_tools=Please install one of the following:
docker_start_fail=Docker start failed
docker_manual=You can manually run
dashboard_installed=ErisPulse-Dashboard module installed
dashboard_access=Access after running
dashboard_config=Configure [Dashboard] token in config.toml
tips=Tips
tip_activate=Activate venv each time you open a new terminal
tip_deactivate=Type deactivate to exit virtual environment
tip_update=Update framework: epsdk self-update
quick_start=Quick Start
activate_venv=Activate venv
init_project=Init project: epsdk init
install_module=Install module: epsdk install <name>
run_project=Run project: epsdk run
all_versions_title=Available Versions
invalid_index=Please enter a valid index
invalid_version=Please enter a valid index or version
fetch_fail=Cannot fetch version info, will install latest
docker_compose_generated=docker-compose.yml generated
env_generated=.env generated
erispulse_started=ErisPulse started
dashboard_install_fail=Dashboard install failed, but ErisPulse was installed
select_1_2=Please enter 1 or 2
venv_ensurepip_missing=System Python is missing ensurepip, cannot create a venv with pip
venv_auto_install_pkg=Install the required system package automatically? [Y/n]
venv_pkg_installed=System package installed successfully
venv_pkg_install_fail=Failed to install system package
venv_manual_hint=Please install venv support manually first (Debian/Ubuntu: sudo apt install python3-venv), then re-run this script
date_unknown=unknown
star_message=If you like this project, please give us a star: https://github.com/ErisPulse/ErisPulse
i18n_note=If you see Chinese text after launching, don't worry - Dashboard also supports i18n and your language!"

_L_ja="lang_name=日本語
info_tag=情報
success_tag=成功
warning_tag=警告
error_tag=エラー
install_title=ErisPulse インストーラー
docker_mode=Docker インストール
docker_image_builtin=公式イメージに ErisPulse と Dashboard が内蔵されています
traditional_mode=従来インストール
uv_bootstrap_mode=uv ツールチェーンのインストール
uv_desc=uv は Python バージョンと仮想環境を自動管理できます
select_install=インストール方法を選択:
docker_install=Docker インストール（推奨）
traditional_install=従来インストール（pip/uv + venv）
uv_bootstrap_install=uv で Python をインストールして環境を構築
fetching_versions=PyPI からバージョン情報を取得中...
available_versions=利用可能なバージョン:
latest_stable=最新安定版
latest_pre=最新プレリリース版
view_all=全バージョンを表示
manual_version=バージョンを手動指定
pre_release=プレリリース
select_default=選択 [1-4] (デフォルト: 1)
no_stable=安定版が見つかりません
no_pre=プレリリース版が見つかりません
enter_version=バージョン番号を入力
version_empty=バージョン番号は空にできません
invalid_choice=有効なオプションを入力してください
select_mirror=ミラーソースを選択:
mirror_hub=Docker Hub (erispulse/erispulse)
mirror_ghcr=GitHub Container Registry (ghcr.io/erispulse/erispulse)
select_channel=チャンネルを選択:
channel_stable=stable（安定版）
channel_dev=dev（プレリリース版）
enable_dashboard=Dashboard 管理パネルを有効にしますか？ [Y/n]
set_token=Dashboard ログイントークンを設定
token_empty=トークンは空にできません。Dashboard は無効になります
set_port=ポートを設定 (デフォルト: 8000)
confirm_install=インストールを確認？ [Y/n]
cancelled=操作がキャンセルされました
generating_config=設定ファイルを生成中...
pulling_image=イメージをプルして起動中...
install_complete=インストール完了
install_config=インストール設定の確認
image_label=イメージ
channel_label=チャンネル
port_label=ポート
enabled=有効
not_enabled=無効
manage_commands=管理コマンド:
view_logs=ログを表示
stop_service=サービスを停止
restart_service=サービスを再起動
update_image=イメージを更新
dashboard_label=Dashboard
access_url=アクセスURL
login_token=ログイントークン
use_uv=uv を使用してインストール
use_pip=pip を使用してインストール
will_install=インストール予定
latest_version=最新バージョン
install_dashboard=Dashboard モジュールをインストールしますか？ [Y/n]
installing=インストール中
install_success=インストール成功
install_fail=インストール失敗
detected=検出
will_use_uv=uv を検出、優先的に使用します
uv_installed=uv はインストール済み
uv_install_success=uv インストール成功
uv_install_fail=uv インストール失敗
installing_python=Python 3.12 をインストール中...
python_install_success=Python 3.12 インストール成功
python_install_fail=Python インストール失敗
creating_venv=仮想環境を作成中...
venv_exists=仮想環境は既に存在します
venv_recreate=削除して再作成しますか？ [y/N]
venv_use_existing=既存の仮想環境を使用
venv_created=仮想環境が作成されました
venv_create_fail=仮想環境の作成に失敗
venv_activated=仮想環境が有効化されました
venv_activate_fail=仮想環境のアクティベーションスクリプトが見つかりません
activating_venv=仮想環境を有効化中...
python_path=現在の Python パス
python_not_found=Python が見つかりません。Python 3.10+ をインストールしてください
python_download=ダウンロード: https://www.python.org/downloads/
install_uv_for_python=uv をインストールして Python を導入し続行しますか？ [Y/n]
python_version_fail=Python バージョンを検出できません
python_detected=Python を検出
python_version_low=Python バージョンが低すぎます。3.10+ を推奨
continue_=続行しますか？ [y/N]
docker_detected=Docker を検出
auto_selected=インストール方法が1つのみ、自動選択
no_install_method=利用可能なインストール方法がありません
install_tools=以下のいずれかをインストールしてください:
docker_start_fail=Docker の起動に失敗
docker_manual=手動で実行できます
dashboard_installed=ErisPulse-Dashboard モジュールがインストールされました
dashboard_access=実行後にアクセス
dashboard_config=config.toml で [Dashboard] token を設定
tips=ヒント
tip_activate=新しいターミナルを開くたびに仮想環境を有効化
tip_deactivate=deactivate で仮想環境を終了
tip_update=フレームワーク更新: epsdk self-update
quick_start=クイックスタート
activate_venv=仮想環境を有効化
init_project=プロジェクト初期化: epsdk init
install_module=モジュールインストール: epsdk install <名前>
run_project=プロジェクト実行: epsdk run
all_versions_title=利用可能なバージョン
invalid_index=有効な番号を入力してください
invalid_version=有効な番号またはバージョンを入力してください
fetch_fail=バージョン情報を取得できません。最新版をインストールします
docker_compose_generated=docker-compose.yml が生成されました
env_generated=.env が生成されました
erispulse_started=ErisPulse が起動しました
dashboard_install_fail=Dashboard のインストールに失敗、ErisPulse はインストール済み
select_1_2=1 または 2 を入力してください
venv_ensurepip_missing=システム Python に ensurepip がなく、pip 付きの仮想環境を作成できません
venv_auto_install_pkg=必要なシステムパッケージを自動インストールしますか？ [Y/n]
venv_pkg_installed=システムパッケージのインストールに成功しました
venv_pkg_install_fail=システムパッケージのインストールに失敗しました
venv_manual_hint=先に venv サポートを手動でインストールし（Debian/Ubuntu: sudo apt install python3-venv）、その後このスクリプトを再実行してください
date_unknown=不明
star_message=このプロジェクトが気に入ったら、スターをお願いします: https://github.com/ErisPulse/ErisPulse
i18n_note=起動後に中国語が表示されても心配しないでください。Dashboard は多言語（i18n）に対応しています！"

_L_ru="lang_name=Русский
info_tag=ИНФО
success_tag=ОК
warning_tag=ВНИМ
error_tag=ОШИБ
install_title=Установщик ErisPulse
docker_mode=Установка через Docker
docker_image_builtin=Официальный образ включает ErisPulse и Dashboard
traditional_mode=Традиционная установка
uv_bootstrap_mode=Установка uv
uv_desc=uv автоматически управляет версиями Python и виртуальными окружениями
select_install=Выберите способ установки:
docker_install=Установка через Docker (рекомендуется)
traditional_install=Традиционная установка (pip/uv + venv)
uv_bootstrap_install=Установить Python через uv и настроить среду
fetching_versions=Получение информации о версиях из PyPI...
available_versions=Доступные версии:
latest_stable=Последняя стабильная
latest_pre=Последняя предварительная
view_all=Все версии
manual_version=Указать версию вручную
pre_release=предварительная
select_default=Выбор [1-4] (по умолчанию: 1)
no_stable=Стабильная версия не найдена
no_pre=Предварительная версия не найдена
enter_version=Введите номер версии
version_empty=Версия не может быть пустой
invalid_choice=Введите корректный вариант
select_mirror=Выберите источник образа:
mirror_hub=Docker Hub (erispulse/erispulse)
mirror_ghcr=GitHub Container Registry (ghcr.io/erispulse/erispulse)
select_channel=Выберите канал:
channel_stable=stable (стабильная)
channel_dev=dev (предварительная)
enable_dashboard=Включить Dashboard? [Y/n]
set_token=Установите токен входа Dashboard
token_empty=Токен не может быть пустым, Dashboard будет отключён
set_port=Установите порт (по умолчанию: 8000)
confirm_install=Подтвердить установку? [Y/n]
cancelled=Операция отменена
generating_config=Генерация конфигурационных файлов...
pulling_image=Загрузка образа и запуск...
install_complete=Установка завершена
install_config=Подтверждение установки
image_label=Образ
channel_label=Канал
port_label=Порт
enabled=Включён
not_enabled=Отключён
manage_commands=Команды управления:
view_logs=Просмотр логов
stop_service=Остановка сервиса
restart_service=Перезапуск сервиса
update_image=Обновление образа
dashboard_label=Dashboard
access_url=URL доступа
login_token=Токен входа
use_uv=Используется uv
use_pip=Используется pip
will_install=Будет установлено
latest_version=последняя версия
install_dashboard=Установить модуль Dashboard? [Y/n]
install_version=Версия установки
install_latest=Установить последнюю версию
installing=Установка
install_success=установлено успешно
install_fail=Ошибка установки
detected=Обнаружен
will_use_uv=uv обнаружен, будет использоваться
uv_installed=uv уже установлен
uv_install_success=uv успешно установлен
uv_install_fail=Ошибка установки uv
installing_python=Установка Python 3.12...
python_install_success=Python 3.12 успешно установлен
python_install_fail=Ошибка установки Python
creating_venv=Создание виртуального окружения...
venv_exists=Виртуальное окружение уже существует
venv_recreate=Удалить и пересоздать? [y/N]
venv_use_existing=Использование существующего окружения
venv_created=Виртуальное окружение создано
venv_create_fail=Ошибка создания виртуального окружения
venv_activated=Виртуальное окружение активировано
venv_activate_fail=Скрипт активации не найден
activating_venv=Активация виртуального окружения...
python_path=Текущий путь Python
python_not_found=Python не найден. Установите Python 3.10+
python_download=Скачать: https://www.python.org/downloads/
install_uv_for_python=Установить uv для установки Python и продолжения? [Y/n]
python_version_fail=Не удалось определить версию Python
python_detected=Обнаружен Python
python_version_low=Версия Python слишком старая, рекомендуется 3.10+
continue_=Продолжить? [y/N]
docker_detected=Обнаружен Docker
auto_selected=Только один способ, выбран автоматически
no_install_method=Нет доступных способов установки
install_tools=Установите один из следующих инструментов:
docker_start_fail=Ошибка запуска Docker
docker_manual=Вы можете запустить вручную
dashboard_installed=Модуль ErisPulse-Dashboard установлен
dashboard_access=Доступ после запуска
dashboard_config=Настройте [Dashboard] token в config.toml
tips=Подсказки
tip_activate=Активируйте venv при каждом новом терминале
tip_deactivate=Введите deactivate для выхода из venv
tip_update=Обновление: epsdk self-update
quick_start=Быстрый старт
activate_venv=Активация venv
init_project=Инициализация: epsdk init
install_module=Установка модуля: epsdk install <имя>
run_project=Запуск: epsdk run
all_versions_title=Доступные версии
invalid_index=Введите корректный номер
invalid_version=Введите корректный номер или версию
fetch_fail=Не удалось получить версии, будет установлена последняя
docker_compose_generated=docker-compose.yml создан
env_generated=.env создан
erispulse_started=ErisPulse запущен
dashboard_install_fail=Dashboard не установлен, но ErisPulse установлен
select_1_2=Введите 1 или 2
venv_ensurepip_missing=В системном Python отсутствует ensurepip, невозможно создать venv с pip
venv_auto_install_pkg=Установить необходимый системный пакет автоматически? [Y/n]
venv_pkg_installed=Системный пакет успешно установлен
venv_pkg_install_fail=Не удалось установить системный пакет
venv_manual_hint=Сначала установите поддержку venv вручную (Debian/Ubuntu: sudo apt install python3-venv), затем перезапустите этот скрипт
date_unknown=неизвестно
star_message=Если вам понравился проект, поставьте звезду: https://github.com/ErisPulse/ErisPulse
i18n_note=Если после запуска вы видите китайский текст — не волнуйтесь, Dashboard поддерживает i18n и ваш язык！"

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

print_completion_footer() {
    if [ "$LANG_CODE" != "zh" ] && [ "$LANG_CODE" != "zh_TW" ]; then
        echo ""
        echo -e "${YELLOW}$(t 'i18n_note')${NC}"
    fi
    echo ""
    echo -e "${MAGENTA}$(t 'star_message')${NC}"
    echo ""
}

select_language() {
    echo ""
    echo -e "${CYAN}Select Language / 选择语言 / 言語を選択 / Выберите язык${NC}"
    echo ""
    echo -e "  ${BOLD}1${NC}. 简体中文"
    echo -e "  ${BOLD}2${NC}. 繁體中文"
    echo -e "  ${BOLD}3${NC}. English"
    echo -e "  ${BOLD}4${NC}. 日本語"
    echo -e "  ${BOLD}5${NC}. Русский"
    echo ""

    local sys_lang="${LANG:0:2}"
    local default=3
    [ "$sys_lang" = "zh" ] && default=1
    [ "$sys_lang" = "ja" ] && default=4
    [ "$sys_lang" = "ru" ] && default=5

    if [ -t 0 ]; then
        read -p "[$default] " lang_choice
        lang_choice=${lang_choice:-$default}
    else
        lang_choice=$default
    fi

    case "$lang_choice" in
        1) LANG_CODE="zh" ;;
        2) LANG_CODE="zh_TW" ;;
        3) LANG_CODE="en" ;;
        4) LANG_CODE="ja" ;;
        5) LANG_CODE="ru" ;;
        *) LANG_CODE="en" ;;
    esac
    _load_lang "$LANG_CODE"
}

# ==================== Output helpers ====================

print_info() { echo -e "${BLUE}${BOLD}[$(t 'info_tag')]${NC} $1"; }
print_success() { echo -e "${GREEN}${BOLD}[$(t 'success_tag')]${NC} $1"; }
print_warning() { echo -e "${YELLOW}${BOLD}[$(t 'warning_tag')]${NC} $1"; }
print_error() { echo -e "${RED}${BOLD}[$(t 'error_tag')]${NC} $1"; }
print_header() { echo ""; echo -e "${CYAN}${BOLD}$1${NC}"; echo -e "${CYAN}${BOLD}$(printf '=%.0s' {1..50})${NC}"; echo ""; }

command_exists() { command -v "$1" >/dev/null 2>&1; }

# ==================== Core functions ====================

get_pypi_versions() {
    local temp_file="/tmp/erispulse_versions_$$"
    if command_exists curl; then
        curl -s --max-time 10 "https://pypi.org/pypi/ErisPulse/json" -o "$temp_file" 2>/dev/null || true
    elif command_exists wget; then
        wget -q --timeout=10 "https://pypi.org/pypi/ErisPulse/json" -O "$temp_file" 2>/dev/null || true
    fi
    if [ ! -s "$temp_file" ]; then
        rm -f "$temp_file"
        return 1
    fi
    if command_exists python3; then
        python3 -c "
import json, sys
try:
    with open('$temp_file', 'r') as f:
        data = json.load(f)
    releases = data.get('releases', {})
    versions = []
    for version, files in releases.items():
        if not files: continue
        upload_time = files[0].get('upload_time_iso_8601', '')
        date_str = upload_time.split('T')[0] if upload_time else '$(t 'date_unknown')'
        is_pre = any(x in version.lower() for x in ['a', 'b', 'rc', 'dev', 'alpha', 'beta'])
        versions.append((version, is_pre, date_str))
    def sort_key(v):
        parts = v[0].split('.')
        major = int(parts[0]) if parts[0].isdigit() else 0
        minor = int(parts[1]) if len(parts) > 1 and parts[1].replace('.', '').isdigit() else 0
        patch_str = parts[2].split('-')[0] if len(parts) > 2 else '0'
        patch_num = int(patch_str) if patch_str.isdigit() else 0
        pre = 0 if not v[1] else 1
        return (major, minor, patch_num, pre, v[0])
    versions.sort(key=sort_key, reverse=True)
    for v, is_pre, date in versions:
        print(f'{v}|{is_pre}|{date}')
except Exception as e:
    sys.stderr.write(str(e) + '\n')
    sys.exit(1)
"
        local ret=$?
        rm -f "$temp_file"
        [ $ret -eq 0 ] && return 0 || return 1
    else
        rm -f "$temp_file"
        return 1
    fi
}

show_version_menu() {
    print_info "$(t 'fetching_versions')"
    local versions_output
    versions_output=$(get_pypi_versions)
    local has_versions=$?
    echo ""

    if [ $has_versions -eq 0 ] && [ -n "$versions_output" ]; then
        local latest_stable="" latest_pre=""
        while IFS='|' read -r ver is_pre date; do
            [ "$is_pre" = "False" ] && [ -z "$latest_stable" ] && latest_stable="$ver"
            [ "$is_pre" = "True" ] && [ -z "$latest_pre" ] && latest_pre="$ver"
            [ -n "$latest_stable" ] && [ -n "$latest_pre" ] && break
        done <<< "$versions_output"

        echo -e "${CYAN}$(t 'available_versions')${NC}"
        echo ""
        [ -n "$latest_stable" ] && echo -e "  ${BOLD}1${NC}. ${GREEN}$(t 'latest_stable') ($latest_stable)${NC}"
        [ -n "$latest_pre" ] && echo -e "  ${BOLD}2${NC}. ${YELLOW}$(t 'latest_pre') ($latest_pre)${NC}"
        echo -e "  ${BOLD}3${NC}. $(t 'view_all')"
        echo -e "  ${BOLD}4${NC}. $(t 'manual_version')"
        echo ""

        while true; do
            read -p "$(t 'select_default'): " choice
            choice=${choice:-1}
            case "$choice" in
                1) [ -n "$latest_stable" ] && TARGET_VERSION="$latest_stable" && return 0 || print_warning "$(t 'no_stable')" ;;
                2) [ -n "$latest_pre" ] && TARGET_VERSION="$latest_pre" && return 0 || print_warning "$(t 'no_pre')" ;;
                3) show_all_versions "$versions_output"; return 0 ;;
                4) read -p "$(t 'enter_version'): " manual_ver; [ -n "$manual_ver" ] && TARGET_VERSION="$manual_ver" && return 0 || print_warning "$(t 'version_empty')" ;;
                *) print_warning "$(t 'invalid_choice')" ;;
            esac
        done
    else
        print_warning "$(t 'fetch_fail')"
        TARGET_VERSION=""
    fi
}

show_all_versions() {
    local versions_output="$1"
    local index=1 version_list=()
    echo ""
    echo -e "${CYAN}${BOLD}=== $(t 'all_versions_title') ===${NC}"
    echo ""
    while IFS='|' read -r ver is_pre date; do
        version_list+=("$ver")
        if [ "$is_pre" = "True" ]; then
            echo -e "  ${BOLD}$index${NC}. ${YELLOW}${ver}${NC} ${YELLOW}[$(t 'pre_release')]${NC}  ${CYAN}(${date})${NC}"
        else
            echo -e "  ${BOLD}$index${NC}. ${GREEN}${ver}${NC}  ${CYAN}(${date})${NC}"
        fi
        index=$((index + 1))
        [ $index -gt 15 ] && break
    done <<< "$versions_output"
    echo ""
    while true; do
        read -p "$(t 'enter_version') [1-$index]: " input
        if [[ "$input" =~ ^[0-9]+$ ]]; then
            local idx=$((input - 1))
            [ $idx -ge 0 ] && [ $idx -lt ${#version_list[@]} ] && TARGET_VERSION="${version_list[$idx]}" && return 0
            print_warning "$(t 'invalid_index')"
        else
            for ver in "${version_list[@]}"; do
                [ "$ver" = "$input" ] && TARGET_VERSION="$input" && return 0
            done
            print_warning "$(t 'invalid_version')"
        fi
    done
}

check_docker() {
    command_exists docker || { DOCKER_AVAILABLE=false; return; }
    docker info >/dev/null 2>&1 || { DOCKER_AVAILABLE=false; return; }
    local compose_cmd=""
    docker compose version >/dev/null 2>&1 && compose_cmd="docker compose"
    [ -z "$compose_cmd" ] && command_exists docker-compose && docker-compose version >/dev/null 2>&1 && compose_cmd="docker-compose"
    if [ -n "$compose_cmd" ]; then
        DOCKER_AVAILABLE=true
        DOCKER_COMPOSE_CMD="$compose_cmd"
        print_success "$(t 'docker_detected') ($compose_cmd)"
    else
        DOCKER_AVAILABLE=false
    fi
}

check_python() {
    local py_cmd=""
    for cmd in python3 python; do
        if command_exists "$cmd"; then
            local test_output=$($cmd -c "import sys; print(sys.version_info.major)" 2>/dev/null || true)
            if [ -n "$test_output" ] && [[ "$test_output" =~ ^[0-9]+$ ]]; then
                py_cmd="$cmd"
                break
            fi
        fi
    done
    if [ -z "$py_cmd" ]; then
        print_error "$(t 'python_not_found')"
        print_info "$(t 'python_download')"
        return 1
    fi
    local py_version=$($py_cmd -c "import sys; print(str(sys.version_info.major) + '.' + str(sys.version_info.minor))" 2>/dev/null || echo "0.0")
    [ "$py_version" = "0.0" ] && { print_error "$(t 'python_version_fail')"; return 1; }
    print_success "$(t 'python_detected') $py_version"
    local major=$(echo $py_version | cut -d'.' -f1)
    local minor=$(echo $py_version | cut -d'.' -f2)
    if [ "$major" -lt 3 ] || ([ "$major" -eq 3 ] && [ "$minor" -lt 10 ]); then
        print_warning "$(t 'python_version_low')"
        read -p "$(t 'continue_'): " continue_choice
        [[ ! "$continue_choice" =~ ^[yY]$ ]] && return 1
    fi
    PYTHON_CMD="$py_cmd"
    return 0
}

ensure_venv_capability() {
    # uv 创建的虚拟环境不依赖 ensurepip
    [ "$USE_UV" = true ] && return 0
    $PYTHON_CMD -m ensurepip --version >/dev/null 2>&1 && return 0

    print_warning "$(t 'venv_ensurepip_missing')"

    if command_exists apt-get; then
        local py_version=$($PYTHON_CMD -c "import sys; print(str(sys.version_info.major) + '.' + str(sys.version_info.minor))" 2>/dev/null || echo "")
        local pkg="python3-venv"
        [ -n "$py_version" ] && pkg="python${py_version}-venv"
        local sudo_cmd=""
        if [ "$(id -u)" -ne 0 ]; then
            if command_exists sudo; then
                sudo_cmd="sudo"
            else
                print_error "$(t 'venv_pkg_install_fail')"
                print_info "$(t 'venv_manual_hint')"
                return 1
            fi
        fi
        if [ -t 0 ]; then
            read -p "$(t 'venv_auto_install_pkg'): " install_choice
            [[ ! "$install_choice" =~ ^[yY]$ ]] && { print_info "$(t 'venv_manual_hint')"; return 1; }
        fi
        print_info "apt-get install $pkg"
        if ! $sudo_cmd apt-get install -y "$pkg"; then
            print_warning "$pkg: $(t 'venv_pkg_install_fail')"
            pkg="python3-venv"
            print_info "apt-get install $pkg"
            if ! $sudo_cmd apt-get install -y "$pkg"; then
                print_error "$(t 'venv_pkg_install_fail')"
                print_info "$(t 'venv_manual_hint')"
                return 1
            fi
        fi
        print_success "$(t 'venv_pkg_installed')"
        return 0
    fi

    print_info "$(t 'venv_manual_hint')"
    return 1
}

create_venv() {
    print_info "$(t 'creating_venv')"
    if [ -d "$VENV_DIR" ]; then
        print_warning "$(t 'venv_exists')"
        read -p "$(t 'venv_recreate'): " recreate
        if [[ "$recreate" =~ ^[yY]$ ]]; then
            rm -rf "$VENV_DIR"
        else
            print_info "$(t 'venv_use_existing')"
            return 0
        fi
    fi
    ensure_venv_capability || return 1
    local venv_cmd
    [ "$USE_UV" = true ] && venv_cmd="uv venv" || venv_cmd="$PYTHON_CMD -m venv"
    if $venv_cmd "$VENV_DIR"; then
        print_success "$(t 'venv_created')"
        return 0
    else
        print_error "$(t 'venv_create_fail')"
        return 1
    fi
}

activate_venv() {
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
        print_success "$(t 'venv_activated')"
        return 0
    else
        print_error "$(t 'venv_activate_fail')"
        return 1
    fi
}

install_erispulse() {
    local version="$1"
    print_info "$(t 'installing') ErisPulse..."
    local pkg_spec="ErisPulse"
    [ -n "$version" ] && pkg_spec="ErisPulse==$version" && print_info "$(t 'install_version'): $version" || print_info "$(t 'install_latest')"
    local install_cmd
    [ "$USE_UV" = true ] && install_cmd="uv pip install $pkg_spec" || install_cmd="pip install $pkg_spec"
    if eval "$install_cmd"; then
        print_success "ErisPulse $(t 'install_success')"
        return 0
    else
        print_error "ErisPulse $(t 'install_fail')"
        return 1
    fi
}

install_dashboard() {
    print_info "$(t 'installing') ErisPulse-Dashboard..."
    local install_cmd
    [ "$USE_UV" = true ] && install_cmd="uv pip install ErisPulse-Dashboard" || install_cmd="pip install ErisPulse-Dashboard"
    if eval "$install_cmd"; then
        print_success "ErisPulse-Dashboard $(t 'install_success')"
        return 0
    else
        print_error "ErisPulse-Dashboard $(t 'install_fail')"
        return 1
    fi
}

install_docker_mode() {
    print_header "$(t 'docker_mode')"
    echo -e "${CYAN}$(t 'docker_image_builtin')${NC}"
    echo ""

    local image="" tag="latest" channel="stable" port=8000 dashboard_token=""

    echo -e "${CYAN}$(t 'select_mirror')${NC}"
    echo "  1. $(t 'mirror_hub')"
    echo "  2. $(t 'mirror_ghcr')"
    echo ""
    while true; do
        read -p "[$(t 'select_default')]: " mirror_choice
        mirror_choice=${mirror_choice:-1}
        case "$mirror_choice" in
            1) image="erispulse/erispulse"; break ;;
            2) image="ghcr.io/erispulse/erispulse"; break ;;
            *) print_warning "$(t 'select_1_2')" ;;
        esac
    done

    echo ""
    echo -e "${CYAN}$(t 'select_channel')${NC}"
    echo "  1. $(t 'channel_stable')"
    echo "  2. $(t 'channel_dev')"
    echo ""
    while true; do
        read -p "[$(t 'select_default')]: " channel_choice
        channel_choice=${channel_choice:-1}
        case "$channel_choice" in
            1) channel="stable"; tag="latest"; break ;;
            2) channel="dev"; break ;;
            *) print_warning "$(t 'select_1_2')" ;;
        esac
    done

    echo ""
    read -p "$(t 'enable_dashboard'): " dashboard_choice
    if [[ ! "$dashboard_choice" =~ ^[nN]$ ]]; then
        read -p "$(t 'set_token'): " dashboard_token
        [ -z "$dashboard_token" ] && print_warning "$(t 'token_empty')" && dashboard_token=""
    fi

    echo ""
    read -p "$(t 'set_port'): " port_input
    [[ "$port_input" =~ ^[0-9]+$ ]] && port="$port_input"

    echo ""
    echo -e "${CYAN}===========================================${NC}"
    echo -e "${CYAN}  $(t 'install_config')${NC}"
    echo -e "${CYAN}===========================================${NC}"
    echo "  $(t 'image_label'): ${image}:latest"
    echo "  $(t 'channel_label'): ${channel}"
    echo "  $(t 'port_label'): ${port}"
    echo "  Dashboard: $([ -n "$dashboard_token" ] && t 'enabled' || t 'not_enabled')"
    echo -e "${CYAN}===========================================${NC}"
    echo ""

    read -p "$(t 'confirm_install'): " confirm
    if [[ "$confirm" =~ ^[nN]$ ]]; then
        print_info "$(t 'cancelled')"
        return 1
    fi

    print_info "$(t 'generating_config')"

    cat > docker-compose.yml <<EOF
# ErisPulse Docker Compose
services:
  erispulse:
    image: ${image}:latest
    container_name: erispulse
    ports:
      - "\${ERISPULSE_PORT:-${port}}:8000"
    volumes:
      - ./config:/app/config
    env_file:
      - .env
    restart: unless-stopped
EOF

    {
        [ -n "$dashboard_token" ] && echo "ERISPULSE_DASHBOARD_TOKEN=${dashboard_token}"
        echo "ERISPULSE_CHANNEL=${channel}"
        echo "ERISPULSE_UPDATE_ON_START=false"
        echo "TZ=Asia/Shanghai"
    } > .env

    print_success "$(t 'docker_compose_generated')"
    print_success "$(t 'env_generated')"

    echo ""
    print_info "$(t 'pulling_image')"

    if $DOCKER_COMPOSE_CMD up -d; then
        print_success "$(t 'erispulse_started')"
        echo ""
        print_header "$(t 'install_complete')"
        echo -e "${BOLD}$(t 'manage_commands')${NC}"
        echo ""
        echo -e "  $(t 'view_logs'):   ${GREEN}${DOCKER_COMPOSE_CMD} logs -f${NC}"
        echo -e "  $(t 'stop_service'):   ${GREEN}${DOCKER_COMPOSE_CMD} down${NC}"
        echo -e "  $(t 'restart_service'):   ${GREEN}${DOCKER_COMPOSE_CMD} restart${NC}"
        echo -e "  $(t 'update_image'):   ${GREEN}${DOCKER_COMPOSE_CMD} pull && ${DOCKER_COMPOSE_CMD} up -d${NC}"
        echo ""
        if [ -n "$dashboard_token" ]; then
            echo -e "${BOLD}$(t 'dashboard_label'):${NC}"
            echo -e "  $(t 'access_url'): ${GREEN}http://localhost:${port}/Dashboard${NC}"
            echo -e "  $(t 'login_token'): ${YELLOW}${dashboard_token}${NC}"
            echo ""
        fi
        print_completion_footer
        return 0
    else
        print_error "$(t 'docker_start_fail')"
        print_info "$(t 'docker_manual'): ${DOCKER_COMPOSE_CMD} up -d"
        return 1
    fi
}

install_traditional_mode() {
    print_header "$(t 'traditional_mode')"
    check_python || return 1
    [ "$USE_UV" = true ] && print_success "$(t 'use_uv')" || print_info "$(t 'use_pip')"
    show_version_menu
    echo ""
    read -p "$(t 'install_dashboard'): " dashboard_choice
    [[ ! "$dashboard_choice" =~ ^[nN]$ ]] && INSTALL_DASHBOARD=true
    echo ""
    [ -n "$TARGET_VERSION" ] && echo -e "${CYAN}$(t 'will_install') ErisPulse ${BOLD}${TARGET_VERSION}${NC}" || echo -e "${CYAN}$(t 'will_install') ErisPulse ${BOLD}$(t 'latest_version')${NC}"
    [ "$INSTALL_DASHBOARD" = true ] && echo -e "${CYAN}$(t 'will_install') ErisPulse-Dashboard${NC}"
    read -p "$(t 'confirm_install'): " confirm
    [[ "$confirm" =~ ^[nN]$ ]] && print_info "$(t 'cancelled')" && return 1
    create_venv || return 1
    activate_venv || return 1
    install_erispulse "$TARGET_VERSION" || return 1
    [ "$INSTALL_DASHBOARD" = true ] && { install_dashboard || print_warning "$(t 'dashboard_install_fail')"; }
    echo ""
    print_header "$(t 'install_complete')"
    echo -e "${BOLD}$(t 'activate_venv'):${NC}"
    echo -e "  ${GREEN}source .venv/bin/activate${NC}"
    echo ""
    echo -e "${BOLD}$(t 'quick_start'):${NC}"
    echo -e "  1. $(t 'activate_venv'): ${GREEN}source .venv/bin/activate${NC}"
    echo -e "  2. $(t 'init_project')"
    echo -e "  3. $(t 'install_module')"
    echo -e "  4. $(t 'run_project')"
    echo ""
    [ "$INSTALL_DASHBOARD" = true ] && {
        echo -e "${BOLD}$(t 'dashboard_label'):${NC}"
        echo -e "  $(t 'dashboard_installed')"
        echo -e "  $(t 'dashboard_access'): ${GREEN}http://localhost:8000/Dashboard${NC}"
        echo -e "  $(t 'dashboard_config')"
        echo ""
    }
    echo -e "${BOLD}$(t 'tips'):${NC}"
    echo "  - $(t 'tip_activate')"
    echo -e "  - $(t 'tip_deactivate')"
    echo -e "  - $(t 'tip_update')"
    echo ""
    [ -f "$VENV_DIR/bin/activate" ] && {
        print_info "$(t 'activating_venv')"
        source "$VENV_DIR/bin/activate"
        print_success "$(t 'venv_activated')"
        echo -e "${YELLOW}$(t 'python_path'): ${BLUE}$(which python)${NC}"
    }
    print_completion_footer
    return 0
}

install_uv_bootstrap() {
    print_header "$(t 'uv_bootstrap_mode')"
    print_info "$(t 'uv_desc')"
    echo ""
    if [ "$USE_UV" = true ]; then
        print_success "$(t 'uv_installed')"
    else
        print_info "$(t 'installing') uv..."
        local uv_install_script="/tmp/uv_install_$$"
        if command_exists curl; then
            curl -LsSf https://astral.sh/uv/install.sh -o "$uv_install_script"
        elif command_exists wget; then
            wget -qO- https://astral.sh/uv/install.sh -O "$uv_install_script"
        else
            print_error "curl or wget required"
            return 1
        fi
        if [ -f "$uv_install_script" ]; then
            sh "$uv_install_script"
            rm -f "$uv_install_script"
            export PATH="$HOME/.cargo/bin:$PATH"
            if command_exists uv; then
                USE_UV=true
                print_success "$(t 'uv_install_success')"
            else
                print_error "$(t 'uv_install_fail')"
                return 1
            fi
        else
            print_error "$(t 'uv_install_fail')"
            return 1
        fi
    fi
    print_info "$(t 'installing_python')"
    if ! uv python install 3.12; then
        print_error "$(t 'python_install_fail')"
        return 1
    fi
    print_success "$(t 'python_install_success')"
    print_info "$(t 'creating_venv')"
    if ! uv venv "$VENV_DIR"; then
        print_error "$(t 'venv_create_fail')"
        return 1
    fi
    print_success "$(t 'venv_created')"
    [ -f "$VENV_DIR/bin/activate" ] && source "$VENV_DIR/bin/activate" && print_success "$(t 'venv_activated')"
    return 0
}

main() {
    select_language
    print_header "$(t 'install_title')"

    check_docker
    local python_ok=true
    check_python || python_ok=false
    USE_UV=$(command_exists uv && echo true || echo false)
    [ "$USE_UV" = true ] && print_success "$(t 'will_use_uv')"
    
    # If Python not found, offer to install uv to get Python
    if [ "$python_ok" = false ]; then
        echo ""
        read -p "$(t 'install_uv_for_python'): " uv_install_choice
        if [[ ! "$uv_install_choice" =~ ^[nN]$ ]]; then
            # Install uv if needed
            if [ "$USE_UV" != true ]; then
                print_info "$(t 'installing') uv..."
                local uv_install_script="/tmp/uv_install_$$"
                if command_exists curl; then
                    curl -LsSf https://astral.sh/uv/install.sh -o "$uv_install_script"
                elif command_exists wget; then
                    wget -qO- https://astral.sh/uv/install.sh -O "$uv_install_script"
                else
                    print_error "curl or wget required"
                    exit 1
                fi
                if [ -f "$uv_install_script" ]; then
                    sh "$uv_install_script"
                    rm -f "$uv_install_script"
                    export PATH="$HOME/.cargo/bin:$PATH"
                    if command_exists uv; then
                        USE_UV=true
                        print_success "$(t 'uv_install_success')"
                    else
                        print_error "$(t 'uv_install_fail')"
                        exit 1
                    fi
                else
                    print_error "$(t 'uv_install_fail')"
                    exit 1
                fi
            fi
            
            # Install Python via uv
            print_info "$(t 'installing_python')"
            if ! uv python install 3.12; then
                print_error "$(t 'python_install_fail')"
                exit 1
            fi
            print_success "$(t 'python_install_success')"
            
            # Create venv with uv
            print_info "$(t 'creating_venv')"
            if ! uv venv "$VENV_DIR"; then
                print_error "$(t 'venv_create_fail')"
                exit 1
            fi
            print_success "$(t 'venv_created')"
            
            [ -f "$VENV_DIR/bin/activate" ] && source "$VENV_DIR/bin/activate" && print_success "$(t 'venv_activated')"
            
            # Python is now available in the venv
            python_ok=true
            PYTHON_CMD="python"
        fi
    fi

    echo ""
    echo -e "${CYAN}$(t 'select_install')${NC}"
    echo ""
    local options=() option_num=1
    if [ "$DOCKER_AVAILABLE" = true ]; then
        echo -e "  ${BOLD}${option_num}${NC}. ${GREEN}$(t 'docker_install')${NC}"
        options+=("docker")
        option_num=$((option_num + 1))
    fi
    if [ "$python_ok" = true ]; then
        echo -e "  ${BOLD}${option_num}${NC}. ${GREEN}$(t 'traditional_install')${NC}"
        options+=("traditional")
        option_num=$((option_num + 1))
    fi
    if [ "$python_ok" = false ]; then
        echo -e "  ${BOLD}${option_num}${NC}. ${YELLOW}$(t 'uv_bootstrap_install')${NC}"
        options+=("uv-bootstrap")
        option_num=$((option_num + 1))
    fi
    if [ ${#options[@]} -eq 0 ]; then
        print_error "$(t 'no_install_method')"
        print_info "$(t 'install_tools')"
        print_info "  - Docker: https://docs.docker.com/get-docker/"
        print_info "  - Python >= 3.10: https://www.python.org/downloads/"
        print_info "  - uv: https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    fi
    if [ ${#options[@]} -eq 1 ]; then
        echo ""
        print_info "$(t 'auto_selected')"
        selected="${options[0]}"
    else
        echo ""
        while true; do
            read -p "$(t 'select_default') [1-$((option_num - 1))]: " choice
            if [[ "$choice" =~ ^[0-9]+$ ]]; then
                local idx=$((choice - 1))
                [ $idx -ge 0 ] && [ $idx -lt ${#options[@]} ] && selected="${options[$idx]}" && break
            fi
            print_warning "$(t 'invalid_choice')"
        done
    fi
    echo ""
    case "$selected" in
        docker) install_docker_mode || exit 1 ;;
        traditional) install_traditional_mode || exit 1 ;;
        uv-bootstrap)
            install_uv_bootstrap || exit 1
            show_version_menu
            install_erispulse "$TARGET_VERSION" || exit 1
            read -p "$(t 'install_dashboard'): " dashboard_choice
            if [[ ! "$dashboard_choice" =~ ^[nN]$ ]]; then
                install_dashboard || print_warning "$(t 'dashboard_install_fail')"
            fi
            echo ""
            print_header "$(t 'install_complete')"
            echo -e "  $(t 'activate_venv'): ${GREEN}source .venv/bin/activate${NC}"
            echo -e "  $(t 'init_project')"
            echo -e "  $(t 'run_project')"
            echo ""
            print_completion_footer
            ;;
    esac
}

main
