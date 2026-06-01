# ErisPulse Install Script

$ErrorActionPreference = "Stop"

$script:UseUv = $false
$script:TargetVersion = ""
$script:PythonCmd = ""
$script:VenvDir = ".venv"
$script:DockerAvailable = $false
$script:DockerComposeCmd = ""
$script:DashboardToken = ""
$script:InstallDashboard = $false
$script:Lang = ""

# ==================== i18n ====================

$L = @{}

$langData = @{
    zh = @{
        lang_name = "简体中文"
        info_tag = "信息"
        success_tag = "成功"
        warning_tag = "警告"
        error_tag = "错误"
        select_lang = "选择语言 / Select Language"
        install_title = "ErisPulse 安装程序"
        docker_mode = "Docker 安装模式"
        docker_image_builtin = "官方镜像已内置 ErisPulse 和 Dashboard"
        traditional_mode = "传统安装模式"
        uv_bootstrap_mode = "安装 uv 工具链"
        uv_desc = "uv 可以自动管理 Python 版本和虚拟环境"
        select_install = "选择安装方式:"
        docker_install = "Docker 安装（推荐）"
        traditional_install = "传统安装（pip/uv + 虚拟环境）"
        uv_bootstrap_install = "通过 uv 安装 Python 并配置环境"
        fetching_versions = "正在从 PyPI 获取版本信息..."
        available_versions = "可用版本:"
        latest_stable = "最新稳定版"
        latest_pre = "最新预发布版"
        view_all = "查看所有版本"
        manual_version = "手动指定版本号"
        pre_release = "预发布"
        select_default = "请选择 [1-4] (默认: 1)"
        no_stable = "没有找到稳定版本"
        no_pre = "没有找到预发布版本"
        enter_version = "请输入版本号"
        version_empty = "版本号不能为空"
        invalid_choice = "请输入有效的选项"
        select_mirror = "选择镜像源:"
        mirror_hub = "Docker Hub (erispulse/erispulse)"
        mirror_ghcr = "GitHub Container Registry (ghcr.io/erispulse/erispulse)"
        select_channel = "选择版本通道:"
        channel_stable = "stable（稳定版）"
        channel_dev = "dev（预发布版）"
        enable_dashboard = "是否启用 Dashboard 管理面板？ [Y/n]"
        set_token = "请设置 Dashboard 登录令牌"
        token_empty = "令牌不能为空，Dashboard 将不启用"
        set_port = "设置端口 (默认: 8000)"
        confirm_install = "确认安装？ [Y/n]"
        cancelled = "操作已取消"
        generating_config = "正在生成配置文件..."
        pulling_image = "正在拉取镜像并启动..."
        install_complete = "安装完成"
        install_config = "安装配置确认"
        image_label = "镜像"
        channel_label = "通道"
        port_label = "端口"
        enabled = "已启用"
        not_enabled = "未启用"
        manage_commands = "管理命令:"
        view_logs = "查看日志"
        stop_service = "停止服务"
        restart_service = "重启服务"
        update_image = "更新镜像"
        dashboard_label = "Dashboard"
        access_url = "访问地址"
        login_token = "登录令牌"
        use_uv = "将使用 uv 进行安装"
        use_pip = "将使用 pip 进行安装"
        will_install = "将安装"
        latest_version = "最新版本"
        install_dashboard = "是否安装 Dashboard 管理面板模块？ [Y/n]"
        install_version = "安装版本"
        install_latest = "安装最新版本"
        installing = "正在安装"
        install_success = "安装成功"
        install_fail = "安装失败"
        detected = "检测到"
        will_use_uv = "检测到 uv，将优先使用"
        uv_installed = "uv 已安装"
        uv_install_success = "uv 安装成功"
        uv_install_fail = "uv 安装失败"
        installing_python = "正在安装 Python 3.12..."
        python_install_success = "Python 3.12 安装成功"
        python_install_fail = "Python 安装失败"
        creating_venv = "正在创建虚拟环境..."
        venv_exists = "虚拟环境已存在"
        venv_recreate = "是否删除并重新创建？ [y/N]"
        venv_use_existing = "使用现有虚拟环境"
        venv_created = "虚拟环境创建成功"
        venv_create_fail = "虚拟环境创建失败"
        venv_activated = "虚拟环境已激活"
        venv_activate_fail = "虚拟环境激活脚本不存在"
        activating_venv = "正在激活虚拟环境..."
        python_path = "当前Python路径"
        python_not_found = "未找到 Python，请先安装 Python 3.10 或更高版本"
        python_download = "下载地址: https://www.python.org/downloads/"
        python_version_fail = "无法检测 Python 版本"
        python_detected = "检测到 Python"
        python_version_low = "Python 版本过低，建议使用 3.10 或更高版本"
        continue_ = "是否继续？ [y/N]"
        docker_detected = "检测到 Docker"
        auto_selected = "仅检测到一种安装方式，自动选择"
        no_install_method = "未检测到可用的安装方式"
        install_tools = "请安装以下任一工具:"
        docker_start_fail = "Docker 启动失败"
        docker_manual = "你可以手动运行"
        dashboard_installed = "已安装 ErisPulse-Dashboard 模块"
        dashboard_access = "运行后访问"
        dashboard_config = "在 config.toml 中配置 [Dashboard] token 以设置登录令牌"
        tips = "提示"
        tip_activate = "每次打开新终端需先激活虚拟环境"
        tip_deactivate = "输入 deactivate 可以退出虚拟环境"
        tip_update = "更新框架: epsdk self-update"
        quick_start = "快速开始"
        activate_venv = "激活虚拟环境"
        init_project = "初始化项目: epsdk init"
        install_module = "安装模块: epsdk install <模块名>"
        run_project = "运行项目: epsdk run main.py"
        all_versions_title = "可用版本列表"
        select_version_or_number = "请输入版本序号 [{0}-{1}] 或版本号"
        invalid_index = "请输入有效的序号"
        invalid_version = "请输入有效的序号或版本号"
        fetch_fail = "无法获取版本信息，将安装最新版本"
        docker_compose_generated = "docker-compose.yml 已生成"
        env_generated = ".env 已生成"
        erispulse_started = "ErisPulse 已启动"
        dashboard_install_fail = "Dashboard 安装失败，但 ErisPulse 已安装成功"
        select_1_2 = "请输入 1 或 2"
        select_1_n = "请选择 [1-{0}]"
        admin_warn = "不建议使用管理员身份运行此脚本"
        generating_files = "正在生成配置文件..."
        date_unknown = "未知"
        star_message = "喜欢我们的话欢迎来点个 star: https://github.com/ErisPulse/ErisPulse"
        i18n_note = "如果您启动程序发现都是中文，请不要担心，Dashboard 同样支持多语言！"
    }
    "zh-TW" = @{
        lang_name = "繁體中文"
        info_tag = "資訊"
        success_tag = "成功"
        warning_tag = "警告"
        error_tag = "錯誤"
        select_lang = "選擇語言 / Select Language"
        install_title = "ErisPulse 安裝程式"
        docker_mode = "Docker 安裝模式"
        docker_image_builtin = "官方映像已內建 ErisPulse 和 Dashboard"
        traditional_mode = "傳統安裝模式"
        uv_bootstrap_mode = "安裝 uv 工具鏈"
        uv_desc = "uv 可以自動管理 Python 版本和虛擬環境"
        select_install = "選擇安裝方式:"
        docker_install = "Docker 安裝（推薦）"
        traditional_install = "傳統安裝（pip/uv + 虛擬環境）"
        uv_bootstrap_install = "透過 uv 安裝 Python 並設定環境"
        fetching_versions = "正在從 PyPI 取得版本資訊..."
        available_versions = "可用版本:"
        latest_stable = "最新穩定版"
        latest_pre = "最新預發布版"
        view_all = "檢視所有版本"
        manual_version = "手動指定版本號"
        pre_release = "預發布"
        select_default = "請選擇 [1-4] (預設: 1)"
        no_stable = "沒有找到穩定版本"
        no_pre = "沒有找到預發布版本"
        enter_version = "請輸入版本號"
        version_empty = "版本號不能為空"
        invalid_choice = "請輸入有效的選項"
        select_mirror = "選擇映像來源:"
        mirror_hub = "Docker Hub (erispulse/erispulse)"
        mirror_ghcr = "GitHub Container Registry (ghcr.io/erispulse/erispulse)"
        select_channel = "選擇版本通道:"
        channel_stable = "stable（穩定版）"
        channel_dev = "dev（預發布版）"
        enable_dashboard = "是否啟用 Dashboard 管理面板？ [Y/n]"
        set_token = "請設定 Dashboard 登入令牌"
        token_empty = "令牌不能為空，Dashboard 將不啟用"
        set_port = "設定埠 (預設: 8000)"
        confirm_install = "確認安裝？ [Y/n]"
        cancelled = "操作已取消"
        generating_config = "正在產生設定檔..."
        pulling_image = "正在拉取映像並啟動..."
        install_complete = "安裝完成"
        install_config = "安裝設定確認"
        image_label = "映像"
        channel_label = "通道"
        port_label = "埠"
        enabled = "已啟用"
        not_enabled = "未啟用"
        manage_commands = "管理命令:"
        view_logs = "檢視日誌"
        stop_service = "停止服務"
        restart_service = "重啟服務"
        update_image = "更新映像"
        dashboard_label = "Dashboard"
        access_url = "存取位址"
        login_token = "登入令牌"
        use_uv = "將使用 uv 進行安裝"
        use_pip = "將使用 pip 進行安裝"
        will_install = "將安裝"
        latest_version = "最新版本"
        install_dashboard = "是否安裝 Dashboard 管理面板模組？ [Y/n]"
        install_version = "安裝版本"
        install_latest = "安裝最新版本"
        installing = "正在安裝"
        install_success = "安裝成功"
        install_fail = "安裝失敗"
        detected = "偵測到"
        will_use_uv = "偵測到 uv，將優先使用"
        uv_installed = "uv 已安裝"
        uv_install_success = "uv 安裝成功"
        uv_install_fail = "uv 安裝失敗"
        installing_python = "正在安裝 Python 3.12..."
        python_install_success = "Python 3.12 安裝成功"
        python_install_fail = "Python 安裝失敗"
        creating_venv = "正在建立虛擬環境..."
        venv_exists = "虛擬環境已存在"
        venv_recreate = "是否刪除並重新建立？ [y/N]"
        venv_use_existing = "使用現有虛擬環境"
        venv_created = "虛擬環境建立成功"
        venv_create_fail = "虛擬環境建立失敗"
        venv_activated = "虛擬環境已啟用"
        venv_activate_fail = "虛擬環境啟用指令碼不存在"
        activating_venv = "正在啟用虛擬環境..."
        python_path = "目前 Python 路徑"
        python_not_found = "未找到 Python，請先安裝 Python 3.10 或更高版本"
        python_download = "下載位址: https://www.python.org/downloads/"
        python_version_fail = "無法偵測 Python 版本"
        python_detected = "偵測到 Python"
        python_version_low = "Python 版本過低，建議使用 3.10 或更高版本"
        continue_ = "是否繼續？ [y/N]"
        docker_detected = "偵測到 Docker"
        auto_selected = "僅偵測到一種安裝方式，自動選擇"
        no_install_method = "未偵測到可用的安裝方式"
        install_tools = "請安裝以下任一工具:"
        docker_start_fail = "Docker 啟動失敗"
        docker_manual = "你可以手動執行"
        dashboard_installed = "已安裝 ErisPulse-Dashboard 模組"
        dashboard_access = "執行後存取"
        dashboard_config = "在 config.toml 中設定 [Dashboard] token 以設定登入令牌"
        tips = "提示"
        tip_activate = "每次開啟新終端需先啟用虛擬環境"
        tip_deactivate = "輸入 deactivate 可以退出虛擬環境"
        tip_update = "更新框架: epsdk self-update"
        quick_start = "快速開始"
        activate_venv = "啟用虛擬環境"
        init_project = "初始化專案: epsdk init"
        install_module = "安裝模組: epsdk install <模組名>"
        run_project = "執行專案: epsdk run main.py"
        all_versions_title = "可用版本列表"
        select_version_or_number = "請輸入版本序號 [{0}-{1}] 或版本號"
        invalid_index = "請輸入有效的序號"
        invalid_version = "請輸入有效的序號或版本號"
        fetch_fail = "無法取得版本資訊，將安裝最新版本"
        docker_compose_generated = "docker-compose.yml 已產生"
        env_generated = ".env 已產生"
        erispulse_started = "ErisPulse 已啟動"
        dashboard_install_fail = "Dashboard 安裝失敗，但 ErisPulse 已安裝成功"
        select_1_2 = "請輸入 1 或 2"
        select_1_n = "請選擇 [1-{0}]"
        admin_warn = "不建議使用管理員身份執行此指令碼"
        generating_files = "正在產生設定檔..."
        date_unknown = "未知"
        star_message = "喜歡我們的話歡迎來點個 star: https://github.com/ErisPulse/ErisPulse"
        i18n_note = "如果您啟動程式發現都是簡體中文，請不要擔心，Dashboard 同樣支援多語言！"
    }
    en = @{
        lang_name = "English"
        info_tag = "INFO"
        success_tag = "OK"
        warning_tag = "WARN"
        error_tag = "ERROR"
        select_lang = "Select Language / 选择语言"
        install_title = "ErisPulse Installer"
        docker_mode = "Docker Installation"
        docker_image_builtin = "Official image includes ErisPulse and Dashboard"
        traditional_mode = "Traditional Installation"
        uv_bootstrap_mode = "Install uv Toolchain"
        uv_desc = "uv can automatically manage Python versions and virtual environments"
        select_install = "Select installation method:"
        docker_install = "Docker Install (Recommended)"
        traditional_install = "Traditional Install (pip/uv + venv)"
        uv_bootstrap_install = "Install Python via uv and setup environment"
        fetching_versions = "Fetching version info from PyPI..."
        available_versions = "Available versions:"
        latest_stable = "Latest stable"
        latest_pre = "Latest pre-release"
        view_all = "View all versions"
        manual_version = "Specify version manually"
        pre_release = "pre-release"
        select_default = "Select [1-4] (default: 1)"
        no_stable = "No stable version found"
        no_pre = "No pre-release version found"
        enter_version = "Enter version number"
        version_empty = "Version cannot be empty"
        invalid_choice = "Please enter a valid option"
        select_mirror = "Select image registry:"
        mirror_hub = "Docker Hub (erispulse/erispulse)"
        mirror_ghcr = "GitHub Container Registry (ghcr.io/erispulse/erispulse)"
        select_channel = "Select channel:"
        channel_stable = "stable"
        channel_dev = "dev (pre-release)"
        enable_dashboard = "Enable Dashboard? [Y/n]"
        set_token = "Set Dashboard login token"
        token_empty = "Token cannot be empty, Dashboard will be disabled"
        set_port = "Set port (default: 8000)"
        confirm_install = "Confirm install? [Y/n]"
        cancelled = "Operation cancelled"
        generating_config = "Generating config files..."
        pulling_image = "Pulling image and starting..."
        install_complete = "Installation Complete"
        install_config = "Installation Summary"
        image_label = "Image"
        channel_label = "Channel"
        port_label = "Port"
        enabled = "Enabled"
        not_enabled = "Disabled"
        manage_commands = "Management commands:"
        view_logs = "View logs"
        stop_service = "Stop service"
        restart_service = "Restart service"
        update_image = "Update image"
        dashboard_label = "Dashboard"
        access_url = "Access URL"
        login_token = "Login token"
        use_uv = "Using uv for installation"
        use_pip = "Using pip for installation"
        will_install = "Will install"
        latest_version = "latest version"
        install_dashboard = "Install Dashboard module? [Y/n]"
        install_version = "Install version"
        install_latest = "Install latest version"
        installing = "Installing"
        install_success = "installed successfully"
        install_fail = "Installation failed"
        detected = "Detected"
        will_use_uv = "uv detected, will be used preferentially"
        uv_installed = "uv is already installed"
        uv_install_success = "uv installed successfully"
        uv_install_fail = "uv installation failed"
        installing_python = "Installing Python 3.12..."
        python_install_success = "Python 3.12 installed successfully"
        python_install_fail = "Python installation failed"
        creating_venv = "Creating virtual environment..."
        venv_exists = "Virtual environment already exists"
        venv_recreate = "Delete and recreate? [y/N]"
        venv_use_existing = "Using existing virtual environment"
        venv_created = "Virtual environment created"
        venv_create_fail = "Virtual environment creation failed"
        venv_activated = "Virtual environment activated"
        venv_activate_fail = "Virtual environment activation script not found"
        activating_venv = "Activating virtual environment..."
        python_path = "Current Python path"
        python_not_found = "Python not found. Please install Python 3.10+"
        python_download = "Download: https://www.python.org/downloads/"
        python_version_fail = "Cannot detect Python version"
        python_detected = "Detected Python"
        python_version_low = "Python version too low, 3.10+ recommended"
        continue_ = "Continue? [y/N]"
        docker_detected = "Detected Docker"
        auto_selected = "Only one method available, auto-selected"
        no_install_method = "No installation method available"
        install_tools = "Please install one of the following:"
        docker_start_fail = "Docker start failed"
        docker_manual = "You can manually run"
        dashboard_installed = "ErisPulse-Dashboard module installed"
        dashboard_access = "Access after running"
        dashboard_config = "Configure [Dashboard] token in config.toml"
        tips = "Tips"
        tip_activate = "Activate venv each time you open a new terminal"
        tip_deactivate = "Type deactivate to exit virtual environment"
        tip_update = "Update framework: epsdk self-update"
        quick_start = "Quick Start"
        activate_venv = "Activate venv"
        init_project = "Init project: epsdk init"
        install_module = "Install module: epsdk install <name>"
        run_project = "Run project: epsdk run main.py"
        all_versions_title = "Available Versions"
        select_version_or_number = "Enter version number [1-{0}] or version string"
        invalid_index = "Please enter a valid index"
        invalid_version = "Please enter a valid index or version"
        fetch_fail = "Cannot fetch version info, will install latest"
        docker_compose_generated = "docker-compose.yml generated"
        env_generated = ".env generated"
        erispulse_started = "ErisPulse started"
        dashboard_install_fail = "Dashboard install failed, but ErisPulse was installed"
        select_1_2 = "Please enter 1 or 2"
        select_1_n = "Select [1-{0}]"
        admin_warn = "Running as administrator is not recommended"
        generating_files = "Generating config files..."
        date_unknown = "unknown"
        star_message = "If you like this project, please give us a star: https://github.com/ErisPulse/ErisPulse"
        i18n_note = "If you see Chinese text after launching, don't worry - Dashboard also supports i18n and your language!"
    }
    ja = @{
        lang_name = "日本語"
        info_tag = "情報"
        success_tag = "成功"
        warning_tag = "警告"
        error_tag = "エラー"
        select_lang = "言語を選択 / Select Language"
        install_title = "ErisPulse インストーラー"
        docker_mode = "Docker インストール"
        docker_image_builtin = "公式イメージに ErisPulse と Dashboard が内蔵されています"
        traditional_mode = "従来インストール"
        uv_bootstrap_mode = "uv ツールチェーンのインストール"
        uv_desc = "uv は Python バージョンと仮想環境を自動管理できます"
        select_install = "インストール方法を選択:"
        docker_install = "Docker インストール（推奨）"
        traditional_install = "従来インストール（pip/uv + venv）"
        uv_bootstrap_install = "uv で Python をインストールして環境を構築"
        fetching_versions = "PyPI からバージョン情報を取得中..."
        available_versions = "利用可能なバージョン:"
        latest_stable = "最新安定版"
        latest_pre = "最新プレリリース版"
        view_all = "全バージョンを表示"
        manual_version = "バージョンを手動指定"
        pre_release = "プレリリース"
        select_default = "選択 [1-4] (デフォルト: 1)"
        no_stable = "安定版が見つかりません"
        no_pre = "プレリリース版が見つかりません"
        enter_version = "バージョン番号を入力"
        version_empty = "バージョン番号は空にできません"
        invalid_choice = "有効なオプションを入力してください"
        select_mirror = "ミラーソースを選択:"
        mirror_hub = "Docker Hub (erispulse/erispulse)"
        mirror_ghcr = "GitHub Container Registry (ghcr.io/erispulse/erispulse)"
        select_channel = "チャンネルを選択:"
        channel_stable = "stable（安定版）"
        channel_dev = "dev（プレリリース版）"
        enable_dashboard = "Dashboard 管理パネルを有効にしますか？ [Y/n]"
        set_token = "Dashboard ログイントークンを設定"
        token_empty = "トークンは空にできません。Dashboard は無効になります"
        set_port = "ポートを設定 (デフォルト: 8000)"
        confirm_install = "インストールを確認？ [Y/n]"
        cancelled = "操作がキャンセルされました"
        generating_config = "設定ファイルを生成中..."
        pulling_image = "イメージをプルして起動中..."
        install_complete = "インストール完了"
        install_config = "インストール設定の確認"
        image_label = "イメージ"
        channel_label = "チャンネル"
        port_label = "ポート"
        enabled = "有効"
        not_enabled = "無効"
        manage_commands = "管理コマンド:"
        view_logs = "ログを表示"
        stop_service = "サービスを停止"
        restart_service = "サービスを再起動"
        update_image = "イメージを更新"
        dashboard_label = "Dashboard"
        access_url = "アクセスURL"
        login_token = "ログイントークン"
        use_uv = "uv を使用してインストール"
        use_pip = "pip を使用してインストール"
        will_install = "インストール予定"
        latest_version = "最新バージョン"
        install_dashboard = "Dashboard モジュールをインストールしますか？ [Y/n]"
        install_version = "インストールバージョン"
        install_latest = "最新バージョンをインストール"
        installing = "インストール中"
        install_success = "インストール成功"
        install_fail = "インストール失敗"
        detected = "検出"
        will_use_uv = "uv を検出、優先的に使用します"
        uv_installed = "uv はインストール済み"
        uv_install_success = "uv インストール成功"
        uv_install_fail = "uv インストール失敗"
        installing_python = "Python 3.12 をインストール中..."
        python_install_success = "Python 3.12 インストール成功"
        python_install_fail = "Python インストール失敗"
        creating_venv = "仮想環境を作成中..."
        venv_exists = "仮想環境は既に存在します"
        venv_recreate = "削除して再作成しますか？ [y/N]"
        venv_use_existing = "既存の仮想環境を使用"
        venv_created = "仮想環境が作成されました"
        venv_create_fail = "仮想環境の作成に失敗"
        venv_activated = "仮想環境が有効化されました"
        venv_activate_fail = "仮想環境のアクティベーションスクリプトが見つかりません"
        activating_venv = "仮想環境を有効化中..."
        python_path = "現在の Python パス"
        python_not_found = "Python が見つかりません。Python 3.10+ をインストールしてください"
        python_download = "ダウンロード: https://www.python.org/downloads/"
        python_version_fail = "Python バージョンを検出できません"
        python_detected = "Python を検出"
        python_version_low = "Python バージョンが低すぎます。3.10+ を推奨"
        continue_ = "続行しますか？ [y/N]"
        docker_detected = "Docker を検出"
        auto_selected = "インストール方法が1つのみ、自動選択"
        no_install_method = "利用可能なインストール方法がありません"
        install_tools = "以下のいずれかをインストールしてください:"
        docker_start_fail = "Docker の起動に失敗"
        docker_manual = "手動で実行できます"
        dashboard_installed = "ErisPulse-Dashboard モジュールがインストールされました"
        dashboard_access = "実行後にアクセス"
        dashboard_config = "config.toml で [Dashboard] token を設定"
        tips = "ヒント"
        tip_activate = "新しいターミナルを開くたびに仮想環境を有効化"
        tip_deactivate = "deactivate で仮想環境を終了"
        tip_update = "フレームワーク更新: epsdk self-update"
        quick_start = "クイックスタート"
        activate_venv = "仮想環境を有効化"
        init_project = "プロジェクト初期化: epsdk init"
        install_module = "モジュールインストール: epsdk install <名前>"
        run_project = "プロジェクト実行: epsdk run main.py"
        all_versions_title = "利用可能なバージョン"
        select_version_or_number = "バージョン番号 [1-{0}] またはバージョン文字列を入力"
        invalid_index = "有効な番号を入力してください"
        invalid_version = "有効な番号またはバージョンを入力してください"
        fetch_fail = "バージョン情報を取得できません。最新版をインストールします"
        docker_compose_generated = "docker-compose.yml が生成されました"
        env_generated = ".env が生成されました"
        erispulse_started = "ErisPulse が起動しました"
        dashboard_install_fail = "Dashboard のインストールに失敗、ErisPulse はインストール済み"
        select_1_2 = "1 または 2 を入力してください"
        select_1_n = "選択 [1-{0}]"
        admin_warn = "管理者としての実行は推奨されません"
        generating_files = "設定ファイルを生成中..."
        date_unknown = "不明"
        star_message = "このプロジェクトが気に入ったら、スターをお願いします: https://github.com/ErisPulse/ErisPulse"
        i18n_note = "起動後に中国語が表示されても心配しないでください。Dashboard は多言語（i18n）に対応しています！"
    }
    ru = @{
        lang_name = "Русский"
        info_tag = "ИНФО"
        success_tag = "ОК"
        warning_tag = "ВНИМ"
        error_tag = "ОШИБ"
        select_lang = "Выберите язык / Select Language"
        install_title = "Установщик ErisPulse"
        docker_mode = "Установка через Docker"
        docker_image_builtin = "Официальный образ включает ErisPulse и Dashboard"
        traditional_mode = "Традиционная установка"
        uv_bootstrap_mode = "Установка uv"
        uv_desc = "uv автоматически управляет версиями Python и виртуальными окружениями"
        select_install = "Выберите способ установки:"
        docker_install = "Установка через Docker (рекомендуется)"
        traditional_install = "Традиционная установка (pip/uv + venv)"
        uv_bootstrap_install = "Установить Python через uv и настроить среду"
        fetching_versions = "Получение информации о версиях из PyPI..."
        available_versions = "Доступные версии:"
        latest_stable = "Последняя стабильная"
        latest_pre = "Последняя предварительная"
        view_all = "Все версии"
        manual_version = "Указать версию вручную"
        pre_release = "предварительная"
        select_default = "Выбор [1-4] (по умолчанию: 1)"
        no_stable = "Стабильная версия не найдена"
        no_pre = "Предварительная версия не найдена"
        enter_version = "Введите номер версии"
        version_empty = "Версия не может быть пустой"
        invalid_choice = "Введите корректный вариант"
        select_mirror = "Выберите источник образа:"
        mirror_hub = "Docker Hub (erispulse/erispulse)"
        mirror_ghcr = "GitHub Container Registry (ghcr.io/erispulse/erispulse)"
        select_channel = "Выберите канал:"
        channel_stable = "stable (стабильная)"
        channel_dev = "dev (предварительная)"
        enable_dashboard = "Включить Dashboard? [Y/n]"
        set_token = "Установите токен входа Dashboard"
        token_empty = "Токен не может быть пустым, Dashboard будет отключён"
        set_port = "Установите порт (по умолчанию: 8000)"
        confirm_install = "Подтвердить установку? [Y/n]"
        cancelled = "Операция отменена"
        generating_config = "Генерация конфигурационных файлов..."
        pulling_image = "Загрузка образа и запуск..."
        install_complete = "Установка завершена"
        install_config = "Подтверждение установки"
        image_label = "Образ"
        channel_label = "Канал"
        port_label = "Порт"
        enabled = "Включён"
        not_enabled = "Отключён"
        manage_commands = "Команды управления:"
        view_logs = "Просмотр логов"
        stop_service = "Остановка сервиса"
        restart_service = "Перезапуск сервиса"
        update_image = "Обновление образа"
        dashboard_label = "Dashboard"
        access_url = "URL доступа"
        login_token = "Токен входа"
        use_uv = "Используется uv"
        use_pip = "Используется pip"
        will_install = "Будет установлено"
        latest_version = "последняя версия"
        install_dashboard = "Установить модуль Dashboard? [Y/n]"
        install_version = "Версия установки"
        install_latest = "Установить последнюю версию"
        installing = "Установка"
        install_success = "установлено успешно"
        install_fail = "Ошибка установки"
        detected = "Обнаружен"
        will_use_uv = "uv обнаружен, будет использоваться"
        uv_installed = "uv уже установлен"
        uv_install_success = "uv успешно установлен"
        uv_install_fail = "Ошибка установки uv"
        installing_python = "Установка Python 3.12..."
        python_install_success = "Python 3.12 успешно установлен"
        python_install_fail = "Ошибка установки Python"
        creating_venv = "Создание виртуального окружения..."
        venv_exists = "Виртуальное окружение уже существует"
        venv_recreate = "Удалить и пересоздать? [y/N]"
        venv_use_existing = "Использование существующего окружения"
        venv_created = "Виртуальное окружение создано"
        venv_create_fail = "Ошибка создания виртуального окружения"
        venv_activated = "Виртуальное окружение активировано"
        venv_activate_fail = "Скрипт активации не найден"
        activating_venv = "Активация виртуального окружения..."
        python_path = "Текущий путь Python"
        python_not_found = "Python не найден. Установите Python 3.10+"
        python_download = "Скачать: https://www.python.org/downloads/"
        python_version_fail = "Не удалось определить версию Python"
        python_detected = "Обнаружен Python"
        python_version_low = "Версия Python слишком старая, рекомендуется 3.10+"
        continue_ = "Продолжить? [y/N]"
        docker_detected = "Обнаружен Docker"
        auto_selected = "Только один способ, выбран автоматически"
        no_install_method = "Нет доступных способов установки"
        install_tools = "Установите один из следующих инструментов:"
        docker_start_fail = "Ошибка запуска Docker"
        docker_manual = "Вы можете запустить вручную"
        dashboard_installed = "Модуль ErisPulse-Dashboard установлен"
        dashboard_access = "Доступ после запуска"
        dashboard_config = "Настройте [Dashboard] token в config.toml"
        tips = "Подсказки"
        tip_activate = "Активируйте venv при каждом новом терминале"
        tip_deactivate = "Введите deactivate для выхода из venv"
        tip_update = "Обновление: epsdk self-update"
        quick_start = "Быстрый старт"
        activate_venv = "Активация venv"
        init_project = "Инициализация: epsdk init"
        install_module = "Установка модуля: epsdk install <имя>"
        run_project = "Запуск: epsdk run main.py"
        all_versions_title = "Доступные версии"
        select_version_or_number = "Введите номер [1-{0}] или строку версии"
        invalid_index = "Введите корректный номер"
        invalid_version = "Введите корректный номер или версию"
        fetch_fail = "Не удалось получить версии, будет установлена последняя"
        docker_compose_generated = "docker-compose.yml создан"
        env_generated = ".env создан"
        erispulse_started = "ErisPulse запущен"
        dashboard_install_fail = "Dashboard не установлен, но ErisPulse установлен"
        select_1_2 = "Введите 1 или 2"
        select_1_n = "Выбор [1-{0}]"
        admin_warn = "Запуск от имени администратора не рекомендуется"
        generating_files = "Генерация конфигурационных файлов..."
        date_unknown = "неизвестно"
        star_message = "Если вам понравился проект, поставьте звезду: https://github.com/ErisPulse/ErisPulse"
        i18n_note = "Если после запуска вы видите китайский текст — не волнуйтесь, Dashboard поддерживает i18n и ваш язык!"
    }
}

function t {
    param([string]$Key)
    $val = $L[$Key]
    if ($val) { return $val }
    $fallback = $langData["en"][$Key]
    if ($fallback) { return $fallback }
    return $Key
}

function Select-Language {
    Write-Host ""
    Write-Host "Select Language / 选择语言 / 言語を選択 / Выберите язык" -ForegroundColor Cyan
    Write-Host ""
    $langs = @("zh", "zh-TW", "en", "ja", "ru")
    $i = 1
    foreach ($lang in $langs) {
        Write-Host "  $i. $($langData[$lang].lang_name)" -ForegroundColor Green
        $i++
    }
    Write-Host ""
    
    $sysLang = ""
    try {
        $sysLang = [System.Globalization.CultureInfo]::CurrentUICulture.TwoLetterISOLanguageName
    } catch {}
    
    $defaultLang = "1"
    if ($sysLang -eq "zh") { $defaultLang = "1" }
    elseif ($sysLang -eq "ja") { $defaultLang = "4" }
    elseif ($sysLang -eq "ru") { $defaultLang = "5" }
    else { $defaultLang = "3" }
    
    $choice = Read-Host "[$defaultLang] "
    $choice = if ($choice) { $choice } else { $defaultLang }
    
    $idx = [int]$choice - 1
    if ($idx -ge 0 -and $idx -lt $langs.Count) {
        $script:Lang = $langs[$idx]
    } else {
        $script:Lang = "en"
    }
    
    $L = $langData[$script:Lang]
}

# ==================== Output helpers ====================

function Write-Info {
    param([string]$Message)
    Write-Host "[$(t 'info_tag')] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[$(t 'success_tag')] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[$(t 'warning_tag')] $Message" -ForegroundColor Yellow
}

function Write-Err {
    param([string]$Message)
    Write-Host "[$(t 'error_tag')] $Message" -ForegroundColor Red
}

function Write-Header {
    param([string]$Message)
    Write-Host ""
    Write-Host $Message -ForegroundColor Cyan
    Write-Host ("=" * 50) -ForegroundColor Cyan
    Write-Host ""
}

function Write-CompletionFooter {
    if ($script:Lang -ne "zh" -and $script:Lang -ne "zh-TW") {
        Write-Host ""
        Write-Host "$(t 'i18n_note')" -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "$(t 'star_message')" -ForegroundColor Magenta
    Write-Host ""
}

function Test-Command {
    param([string]$Command)
    try {
        $null = Get-Command $Command -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

# ==================== Core functions ====================

function Get-PyPiVersions {
    $tempFile = Join-Path $env:TEMP "erispulse_versions_$([Guid]::NewGuid())"
    
    try {
        if (Test-Command "curl") {
            $null = curl.exe -s --max-time 10 "https://pypi.org/pypi/ErisPulse/json" -o $tempFile 2>$null
        } elseif (Test-Command "wget") {
            $null = wget.exe -q --timeout=10 "https://pypi.org/pypi/ErisPulse/json" -O $tempFile 2>$null
        } else {
            Invoke-WebRequest -Uri "https://pypi.org/pypi/ErisPulse/json" -OutFile $tempFile -TimeoutSec 10
        }
    } catch {
        Remove-Item $tempFile -Force -ErrorAction SilentlyContinue
        return @()
    }
    
    if (-not (Test-Path $tempFile) -or ((Get-Item $tempFile).Length -eq 0)) {
        Remove-Item $tempFile -Force -ErrorAction SilentlyContinue
        return @()
    }
    
    try {
        $jsonContent = Get-Content $tempFile -Raw -Encoding UTF8
        $data = $jsonContent | ConvertFrom-Json
        
        $versions = @()
        foreach ($version in $data.releases.PSObject.Properties.Name) {
            $files = $data.releases.$version
            if ($files -and $files.Count -gt 0) {
                $uploadTime = $files[0].upload_time_iso_8601
                $dateStr = if ($uploadTime) { $uploadTime.Split('T')[0] } else { t 'date_unknown' }
                $isPre = @('a', 'b', 'rc', 'dev', 'alpha', 'beta') | Where-Object { $version.ToLower().Contains($_) }
                $versions += [PSCustomObject]@{
                    Version = $version
                    IsPre = $isPre.Count -gt 0
                    Date = $dateStr
                }
            }
        }
        
        $sortedVersions = $versions | Sort-Object {
            $parts = $_.Version.Split('.')
            $major = if ($parts[0] -match '^\d+$') { [int]$parts[0] } else { 0 }
            $minor = if ($parts.Count -gt 1 -and $parts[1] -match '^\d+$') { [int]$parts[1] } else { 0 }
            $patchStr = if ($parts.Count -gt 2) { $parts[2].Split('-')[0] } else { "0" }
            $patchNum = if ($patchStr -match '^\d+$') { [int]$patchStr } else { 0 }
            $pre = if ($_.IsPre) { 1 } else { 0 }
            "$major,$minor,$patchNum,$pre,$($_.Version)"
        } -Descending
        
        Remove-Item $tempFile -Force -ErrorAction SilentlyContinue
        return $sortedVersions
    } catch {
        Remove-Item $tempFile -Force -ErrorAction SilentlyContinue
        return @()
    }
}

function Show-VersionMenu {
    Write-Info (t 'fetching_versions')
    $versions = Get-PyPiVersions
    Write-Host ""
    
    if ($versions.Count -gt 0) {
        $latestStable = $null
        $latestPre = $null
        
        foreach ($ver in $versions) {
            if (-not $ver.IsPre -and -not $latestStable) { $latestStable = $ver.Version }
            if ($ver.IsPre -and -not $latestPre) { $latestPre = $ver.Version }
            if ($latestStable -and $latestPre) { break }
        }
        
        Write-Host (t 'available_versions') -ForegroundColor Cyan
        Write-Host ""
        
        if ($latestStable) {
            Write-Host "  1. $(t 'latest_stable') ($latestStable)" -ForegroundColor Green
        }
        if ($latestPre) {
            Write-Host "  2. $(t 'latest_pre') ($latestPre)" -ForegroundColor Yellow
        }
        Write-Host "  3. $(t 'view_all')"
        Write-Host "  4. $(t 'manual_version')"
        Write-Host ""
        
        while ($true) {
            $choice = Read-Host (t 'select_default')
            $choice = if ($choice) { $choice } else { "1" }
            
            switch ($choice) {
                "1" {
                    if ($latestStable) { $script:TargetVersion = $latestStable; return }
                    else { Write-Warning (t 'no_stable') }
                }
                "2" {
                    if ($latestPre) { $script:TargetVersion = $latestPre; return }
                    else { Write-Warning (t 'no_pre') }
                }
                "3" { Show-AllVersions $versions; return }
                "4" {
                    $manualVer = Read-Host (t 'enter_version')
                    if ($manualVer) { $script:TargetVersion = $manualVer; return }
                    else { Write-Warning (t 'version_empty') }
                }
                default { Write-Warning (t 'invalid_choice') }
            }
        }
    } else {
        Write-Warning (t 'fetch_fail')
        $script:TargetVersion = ""
    }
}

function Show-AllVersions {
    param($Versions)
    
    $versionList = @()
    Write-Host ""
    Write-Host "=== $(t 'all_versions_title') ===" -ForegroundColor Cyan
    Write-Host ""
    
    $index = 1
    foreach ($ver in $Versions) {
        $versionList += $ver.Version
        if ($ver.IsPre) {
            Write-Host "  $index. $($ver.Version) [$(t 'pre_release')]  ($($ver.Date))" -ForegroundColor Yellow
        } else {
            Write-Host "  $index. $($ver.Version)  ($($ver.Date))" -ForegroundColor Green
        }
        $index++
        if ($index -gt 15) { break }
    }
    
    Write-Host ""
    while ($true) {
        $input = Read-Host (t 'select_version_or_number' -f "1", "$index")
        if ($input -match '^\d+$') {
            $idx = [int]$input - 1
            if ($idx -ge 0 -and $idx -lt $versionList.Count) {
                $script:TargetVersion = $versionList[$idx]
                return
            } else { Write-Warning (t 'invalid_index') }
        } else {
            if ($input -in $versionList) { $script:TargetVersion = $input; return }
            else { Write-Warning (t 'invalid_version') }
        }
    }
}

function Test-Docker {
    if (-not (Test-Command "docker")) {
        $script:DockerAvailable = $false
        return
    }
    
    try {
        $null = & docker info 2>$null
    } catch {
        $script:DockerAvailable = $false
        return
    }
    
    $composeCmd = ""
    try {
        $null = & docker compose version 2>$null
        $composeCmd = "docker compose"
    } catch {}
    
    if (-not $composeCmd) {
        if (Test-Command "docker-compose") {
            try {
                $null = & docker-compose version 2>$null
                $composeCmd = "docker-compose"
            } catch {}
        }
    }
    
    if ($composeCmd) {
        $script:DockerAvailable = $true
        $script:DockerComposeCmd = $composeCmd
        Write-Success "$(t 'docker_detected') ($composeCmd)"
    } else {
        $script:DockerAvailable = $false
    }
}

function Test-Python {
    $pyCmd = ""
    
    $candidates = @("python", "py", "python3")
    foreach ($cmd in $candidates) {
        if (Test-Command $cmd) {
            $testOutput = & $cmd -c "import sys; print(sys.version_info.major)" 2>$null
            if ($testOutput -and $testOutput -match '^\d+$') {
                $pyCmd = $cmd
                break
            }
        }
    }
    
    if (-not $pyCmd) {
        Write-Err (t 'python_not_found')
        Write-Info (t 'python_download')
        return $false
    }
    
    try {
        $pyMajor = & $pyCmd -c "import sys; print(sys.version_info.major)" 2>$null
        $pyMinor = & $pyCmd -c "import sys; print(sys.version_info.minor)" 2>$null
        if (-not $pyMajor -or -not $pyMinor) {
            Write-Err (t 'python_version_fail')
            return $false
        }
        
        $pyVersion = "$pyMajor.$pyMinor"
        Write-Success "$(t 'python_detected') $pyVersion"
        
        if ([int]$pyMajor -lt 3 -or ([int]$pyMajor -eq 3 -and [int]$pyMinor -lt 10)) {
            Write-Warning (t 'python_version_low')
            $continueChoice = Read-Host (t 'continue_')
            if ($continueChoice -notmatch '^[yY]$') { return $false }
        }
        
        $script:PythonCmd = $pyCmd
        return $true
    } catch {
        Write-Err (t 'python_version_fail')
        return $false
    }
}

function New-VirtualEnvironment {
    Write-Info (t 'creating_venv')
    
    if (Test-Path $script:VenvDir) {
        Write-Warning (t 'venv_exists')
        $recreate = Read-Host (t 'venv_recreate')
        if ($recreate -match '^[yY]$') {
            Remove-Item -Path $script:VenvDir -Recurse -Force
        } else {
            Write-Info (t 'venv_use_existing')
            return $true
        }
    }
    
    $venvCmd = if ($script:UseUv) { "uv venv" } else { "$($script:PythonCmd) -m venv" }
    
    try {
        Invoke-Expression "$venvCmd $script:VenvDir"
        Write-Success (t 'venv_created')
        return $true
    } catch {
        Write-Err "$(t 'venv_create_fail'): $_"
        return $false
    }
}

function Activate-VirtualEnvironment {
    $activateScript = Join-Path $script:VenvDir "Scripts\activate.ps1"
    if (Test-Path $activateScript) {
        & $activateScript
        Write-Success (t 'venv_activated')
        return $true
    } else {
        Write-Err (t 'venv_activate_fail')
        return $false
    }
}

function Install-ErisPulse {
    param([string]$Version)
    
    Write-Info "$(t 'installing') ErisPulse..."
    
    $pkgSpec = "ErisPulse"
    if ($Version) {
        $pkgSpec = "ErisPulse==$Version"
        Write-Info "$(t 'install_version'): $Version"
    } else {
        Write-Info (t 'install_latest')
    }
    
    $installCmd = if ($script:UseUv) { "uv pip install $pkgSpec" } else { "pip install $pkgSpec" }
    
    try {
        Invoke-Expression $installCmd
        Write-Success "ErisPulse $(t 'install_success')"
        return $true
    } catch {
        Write-Err "ErisPulse $(t 'install_fail'): $_"
        return $false
    }
}

function Install-DashboardModule {
    Write-Info "$(t 'installing') ErisPulse-Dashboard..."
    
    $installCmd = if ($script:UseUv) { "uv pip install ErisPulse-Dashboard" } else { "pip install ErisPulse-Dashboard" }
    
    try {
        Invoke-Expression $installCmd
        Write-Success "ErisPulse-Dashboard $(t 'install_success')"
        return $true
    } catch {
        Write-Err "ErisPulse-Dashboard $(t 'install_fail'): $_"
        return $false
    }
}

function Install-DockerMode {
    Write-Header (t 'docker_mode')
    Write-Host (t 'docker_image_builtin') -ForegroundColor Cyan
    Write-Host ""
    
    $image = ""
    $tag = "latest"
    $channel = "stable"
    $port = 8000
    $dashboardToken = ""
    
    Write-Host (t 'select_mirror') -ForegroundColor Cyan
    Write-Host "  1. $(t 'mirror_hub')"
    Write-Host "  2. $(t 'mirror_ghcr')"
    Write-Host ""
    while ($true) {
        $mirrorChoice = Read-Host "[$(t 'select_default')]"
        $mirrorChoice = if ($mirrorChoice) { $mirrorChoice } else { "1" }
        switch ($mirrorChoice) {
            "1" { $image = "erispulse/erispulse"; break }
            "2" { $image = "ghcr.io/erispulse/erispulse"; break }
            default { Write-Warning (t 'select_1_2'); continue }
        }
        break
    }
    
    Write-Host ""
    Write-Host (t 'select_channel') -ForegroundColor Cyan
    Write-Host "  1. $(t 'channel_stable')"
    Write-Host "  2. $(t 'channel_dev')"
    Write-Host ""
    while ($true) {
        $channelChoice = Read-Host "[$(t 'select_default')]"
        $channelChoice = if ($channelChoice) { $channelChoice } else { "1" }
        switch ($channelChoice) {
            "1" { $channel = "stable"; $tag = "latest"; break }
            "2" { $channel = "dev"; $tag = "dev"; break }
            default { Write-Warning (t 'select_1_2'); continue }
        }
        break
    }
    
    Write-Host ""
    $dashboardChoice = Read-Host (t 'enable_dashboard')
    if ($dashboardChoice -notmatch '^[nN]$') {
        $dashboardToken = Read-Host (t 'set_token')
        if (-not $dashboardToken) {
            Write-Warning (t 'token_empty')
            $dashboardToken = ""
        }
    }
    
    Write-Host ""
    $portInput = Read-Host (t 'set_port')
    if ($portInput -match '^\d+$') {
        $port = [int]$portInput
    }
    
    Write-Host ""
    Write-Host "===========================================" -ForegroundColor Cyan
    Write-Host "  $(t 'install_config')" -ForegroundColor Cyan
    Write-Host "===========================================" -ForegroundColor Cyan
    Write-Host "  $(t 'image_label'): $image`:$tag"
    Write-Host "  $(t 'channel_label'): $channel"
    Write-Host "  $(t 'port_label'): $port"
    Write-Host "  Dashboard: $(if ($dashboardToken) { t 'enabled' } else { t 'not_enabled' })"
    Write-Host "===========================================" -ForegroundColor Cyan
    Write-Host ""
    
    $confirm = Read-Host (t 'confirm_install')
    if ($confirm -match '^[nN]$') {
        Write-Info (t 'cancelled')
        return $false
    }
    
    $composeContent = @"
# ErisPulse Docker Compose
services:
  erispulse:
    image: ${image}:${tag}
    container_name: erispulse
    ports:
      - "`${ERISPULSE_PORT:-${port}}:8000"
    volumes:
      - ./config:/app/config
    env_file:
      - .env
    restart: unless-stopped
"@
    
    $envContent = @"
ERISPULSE_CHANNEL=${channel}
ERISPULSE_UPDATE_ON_START=false
TZ=Asia/Shanghai
"@
    
    if ($dashboardToken) {
        $envContent = "ERISPULSE_DASHBOARD_TOKEN=${dashboardToken}`n" + $envContent
    }
    
    Write-Info (t 'generating_config')
    
    Set-Content -Path "docker-compose.yml" -Value $composeContent -Encoding UTF8
    Set-Content -Path ".env" -Value $envContent -Encoding UTF8
    Write-Success (t 'docker_compose_generated')
    Write-Success (t 'env_generated')
    
    Write-Host ""
    Write-Info (t 'pulling_image')
    
    try {
        Invoke-Expression "$($script:DockerComposeCmd) up -d"
        Write-Success (t 'erispulse_started')
        
        Write-Host ""
        Write-Header (t 'install_complete')
        
        Write-Host (t 'manage_commands') -ForegroundColor Cyan
        Write-Host "  $(t 'view_logs'):   $($script:DockerComposeCmd) logs -f" -ForegroundColor Green
        Write-Host "  $(t 'stop_service'):   $($script:DockerComposeCmd) down" -ForegroundColor Green
        Write-Host "  $(t 'restart_service'):   $($script:DockerComposeCmd) restart" -ForegroundColor Green
        Write-Host "  $(t 'update_image'):   $($script:DockerComposeCmd) pull && $($script:DockerComposeCmd) up -d" -ForegroundColor Green
        Write-Host ""
        
        if ($dashboardToken) {
            Write-Host "$(t 'dashboard_label'):" -ForegroundColor Cyan
            Write-Host "  $(t 'access_url'): http://localhost:${port}/Dashboard" -ForegroundColor Green
            Write-Host "  $(t 'login_token'): $dashboardToken" -ForegroundColor Yellow
            Write-Host ""
        }
        
        Write-CompletionFooter
        
        return $true
    } catch {
        Write-Err "$(t 'docker_start_fail'): $_"
        Write-Info "$(t 'docker_manual'): $($script:DockerComposeCmd) up -d"
        return $false
    }
}

function Install-TraditionalMode {
    Write-Header (t 'traditional_mode')
    
    if (-not (Test-Python)) { return $false }
    
    if ($script:UseUv) {
        Write-Success (t 'use_uv')
    } else {
        Write-Info (t 'use_pip')
    }
    
    Show-VersionMenu
    
    Write-Host ""
    $dashboardChoice = Read-Host (t 'install_dashboard')
    $script:InstallDashboard = $dashboardChoice -notmatch '^[nN]$'
    
    Write-Host ""
    if ($script:TargetVersion) {
        Write-Host "$(t 'will_install') ErisPulse $($script:TargetVersion)" -ForegroundColor Cyan
    } else {
        Write-Host "$(t 'will_install') ErisPulse $(t 'latest_version')" -ForegroundColor Cyan
    }
    if ($script:InstallDashboard) {
        Write-Host "$(t 'will_install') ErisPulse-Dashboard" -ForegroundColor Cyan
    }
    
    $confirm = Read-Host (t 'confirm_install')
    if ($confirm -match '^[nN]$') {
        Write-Info (t 'cancelled')
        return $false
    }
    
    if (-not (New-VirtualEnvironment)) { return $false }
    if (-not (Activate-VirtualEnvironment)) { return $false }
    if (-not (Install-ErisPulse $script:TargetVersion)) { return $false }
    
    if ($script:InstallDashboard) {
        if (-not (Install-DashboardModule)) {
            Write-Warning (t 'dashboard_install_fail')
        }
    }
    
    Write-Host ""
    Write-Header (t 'install_complete')
    
    Write-Host "$(t 'activate_venv'): .\.venv\Scripts\activate.ps1" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "$(t 'quick_start'):"
    Write-Host "  1. $(t 'activate_venv'): .\.venv\Scripts\activate.ps1" -ForegroundColor Green
    Write-Host "  2. $(t 'init_project')" -ForegroundColor Green
    Write-Host "  3. $(t 'install_module')" -ForegroundColor Green
    Write-Host "  4. $(t 'run_project')" -ForegroundColor Green
    Write-Host ""
    
    if ($script:InstallDashboard) {
        Write-Host "$(t 'dashboard_label'):" -ForegroundColor Cyan
        Write-Host "  $(t 'dashboard_installed')" -ForegroundColor Green
        Write-Host "  $(t 'dashboard_access'): http://localhost:8000/Dashboard" -ForegroundColor Green
        Write-Host "  $(t 'dashboard_config')" -ForegroundColor Yellow
        Write-Host ""
    }
    
    Write-Host "$(t 'tips'):"
    Write-Host "  - $(t 'tip_activate')"
    Write-Host "  - $(t 'tip_deactivate')" -ForegroundColor Green
    Write-Host "  - $(t 'tip_update')" -ForegroundColor Green
    Write-Host ""
    
    $activateScript = Join-Path $script:VenvDir "Scripts\activate.ps1"
    if (Test-Path $activateScript) {
        Write-Info (t 'activating_venv')
        & $activateScript
        Write-Success (t 'venv_activated')
        Write-Host "$(t 'python_path'): $((Get-Command python).Source)" -ForegroundColor Yellow
    }
    
    Write-CompletionFooter
    
    return $true
}

function Install-UvAndPython {
    Write-Header (t 'uv_bootstrap_mode')
    
    Write-Info (t 'uv_desc')
    Write-Host ""
    
    if ($script:UseUv) {
        Write-Success (t 'uv_installed')
    } else {
        Write-Info "$(t 'installing') uv..."
        try {
            irm https://astral.sh/uv/install.ps1 | iex
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "User") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "Machine")
            if (Test-Command "uv") {
                $script:UseUv = $true
                Write-Success (t 'uv_install_success')
            } else {
                Write-Err (t 'uv_install_fail')
                return $false
            }
        } catch {
            Write-Err "$(t 'uv_install_fail'): $_"
            return $false
        }
    }
    
    Write-Info (t 'installing_python')
    try {
        & uv python install 3.12
        Write-Success (t 'python_install_success')
    } catch {
        Write-Err "$(t 'python_install_fail'): $_"
        return $false
    }
    
    Write-Info (t 'creating_venv')
    try {
        & uv venv $script:VenvDir
        Write-Success (t 'venv_created')
    } catch {
        Write-Err "$(t 'venv_create_fail'): $_"
        return $false
    }
    
    $activateScript = Join-Path $script:VenvDir "Scripts\activate.ps1"
    if (Test-Path $activateScript) {
        & $activateScript
        Write-Success (t 'venv_activated')
    }
    
    return $true
}

function Main {
    Select-Language
    
    Write-Header (t 'install_title')
    
    Test-Docker
    $pythonAvailable = Test-Python
    $script:UseUv = Test-Command "uv"
    if ($script:UseUv) {
        Write-Success (t 'will_use_uv')
    }
    
    Write-Host ""
    Write-Host (t 'select_install') -ForegroundColor Cyan
    Write-Host ""
    
    $options = @()
    $optionNum = 1
    
    if ($script:DockerAvailable) {
        Write-Host "  ${optionNum}. $(t 'docker_install')" -ForegroundColor Green
        $options += "docker"
        $optionNum++
    }
    
    if ($pythonAvailable) {
        Write-Host "  ${optionNum}. $(t 'traditional_install')" -ForegroundColor Green
        $options += "traditional"
        $optionNum++
    }
    
    if (-not $pythonAvailable) {
        Write-Host "  ${optionNum}. $(t 'uv_bootstrap_install')" -ForegroundColor Yellow
        $options += "uv-bootstrap"
        $optionNum++
    }
    
    if ($options.Count -eq 0) {
        Write-Err (t 'no_install_method')
        Write-Info (t 'install_tools')
        Write-Info "  - Docker: https://docs.docker.com/get-docker/"
        Write-Info "  - Python >= 3.10: https://www.python.org/downloads/"
        Write-Info "  - uv: https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    }
    
    if ($options.Count -eq 1) {
        Write-Host ""
        Write-Info (t 'auto_selected')
        $selected = $options[0]
    } else {
        Write-Host ""
        while ($true) {
            $choice = Read-Host "$(t 'select_1_n' -f "$($optionNum - 1)")"
            if ($choice -match '^\d+$') {
                $idx = [int]$choice - 1
                if ($idx -ge 0 -and $idx -lt $options.Count) {
                    $selected = $options[$idx]
                    break
                }
            }
            Write-Warning (t 'invalid_choice')
        }
    }
    
    Write-Host ""
    switch ($selected) {
        "docker" { 
            if (-not (Install-DockerMode)) { exit 1 }
        }
        "traditional" {
            if (-not (Install-TraditionalMode)) { exit 1 }
        }
        "uv-bootstrap" {
            if (-not (Install-UvAndPython)) { exit 1 }
            Show-VersionMenu
            if (-not (Install-ErisPulse $script:TargetVersion)) { exit 1 }
            
            $dashboardChoice = Read-Host (t 'install_dashboard')
            if ($dashboardChoice -notmatch '^[nN]$') {
                if (-not (Install-DashboardModule)) {
                    Write-Warning (t 'dashboard_install_fail')
                }
            }
            
            Write-Host ""
            Write-Header (t 'install_complete')
            Write-Host "$(t 'activate_venv'): .\.venv\Scripts\activate.ps1" -ForegroundColor Green
            Write-Host "$(t 'init_project')" -ForegroundColor Green
            Write-Host "$(t 'run_project')" -ForegroundColor Green
            Write-Host ""
            Write-CompletionFooter
        }
    }
}

$currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Warning (t 'admin_warn')
    $continueAsAdmin = Read-Host "[$(t 'continue_')]"
    if ($continueAsAdmin -notmatch '^[yY]$') { exit 1 }
}

Main
