"""
CLI 本地常量

ErisPulse 的 CLI 与主库刻意保持隔离：CLI 运行时不应触发主库初始化
（``ErisPulse/__init__.py`` 会全量加载 Core 并实例化 ConfigManager /
StorageManager 等单例）。因此 CLI 需要的常量在此独立维护，**不**从
``ErisPulse.Core.constants`` 导入。

与主库共享的"跨进程 / 跨子系统契约"（如硬重启退出码、入口点组名）在此
镜像一份，由 ``tests/unit/test_unit_cli.py::TestCrossProcessContracts``
钉死——任一侧漂移即测试失败。

{!--< internal-use >!--}
{!--< /internal-use >!--}
"""

# ==============================================================================
# 跨进程 / 跨子系统契约（与 Core/constants.py 镜像，修改须同步两侧）
# ==============================================================================

# 硬重启退出码。
# 主库 sdk.hard_restart() 以此码 os._exit；CLI run 命令据此区分"重启"与"崩溃"。
# 镜像于: ErisPulse.Core.constants.HARD_RESTART_EXIT_CODE
HARD_RESTART_EXIT_CODE: int = 42

# 监督者标记环境变量名。
# CLI run 命令启动子进程时注入；SDK 据此判断是否被监督（决定硬重启是否会被拉起）。
# 镜像于: ErisPulse.Core.constants.ENV_SUPERVISED
ENV_SUPERVISED: str = "ERISPULSE_SUPERVISED"

# reload worker 标记环境变量名（CLI 专有，无 Core 镜像）。
# `epsdk run --reload` 的监督进程拉起 worker 子进程时注入；SDK 不读取。
# 用途：worker 侧知道自己由 reload 监督者启动（将来扩展用），且不与
# `uv run epsdk` 等场景混淆。使用位置: CLI/commands/run.py。
ENV_RELOAD_WORKER: str = "ERISPULSE_RELOAD_WORKER"

# 模块入口点组名（loader / finder / create / types 共用）。
# 镜像于: ErisPulse.Core.constants.MODULE_ENTRY_POINT_GROUP
MODULE_ENTRY_POINT_GROUP: str = "erispulse.module"

# 适配器入口点组名（loader / finder / create / types 共用）。
# 镜像于: ErisPulse.Core.constants.ADAPTER_ENTRY_POINT_GROUP
ADAPTER_ENTRY_POINT_GROUP: str = "erispulse.adapter"

# ==============================================================================
# CLI 专有常量（主库不需要）
# ==============================================================================

# PyPI JSON API URL 模板（仅 CLI 做包查询 / 自更新检查时使用）。
PYPI_PACKAGE_JSON_URL_TEMPLATE: str = "https://pypi.org/pypi/{package}/json"

# run 命令子进程监督的退避参数。
# 使用位置: CLI/commands/run.py -> 监督循环。
# 修改影响: 每次崩溃的重试间隔 = min(MAX, PER_CRASH x 崩溃次数)；
#           RESTART_PAUSE 为硬重启请求后的短暂停顿（让端口等资源释放）。
RUN_CRASH_BACKOFF_MAX_SECS: float = 60.0
RUN_CRASH_BACKOFF_PER_CRASH_SECS: float = 3.0
RUN_RESTART_PAUSE_SECS: float = 0.5
# 连续同退出码崩溃达到该次数后，输出一次排查指引（疑似确定性故障，
# 退避重试无意义）。使用位置: CLI/commands/run.py -> 监督循环；
# 修改影响: 数值越小越早提示，越大越保守（0/负数禁用提示）。
RUN_PERSISTENT_CRASH_HINT_THRESHOLD: int = 3

# init 生成项目对框架本体的依赖下限（pip 依赖声明，非 SDK 加载期检查）。
# 使用位置: CLI/commands/init.py -> pyproject.toml 生成 / uv_add / pm.install_package /
#           append_pyproject_dependencies 四处。
# 修改影响: 真实 pip 依赖——pip 默认不解析预发布版本，该下限不得高于已发布的
#           正式版本（与 create.py 的 _TEMPLATE_MIN_SDK_VERSION 同步升版）。
INIT_ERISPULSE_DEPENDENCY: str = "erispulse>=2.10.0"

# 子进程终止后的等待上限（秒）：terminate() 发出后等待退出，超时即 kill()。
# 使用位置: CLI/commands/run.py（框架子进程三处停止路径）、
#           CLI/utils/package_manager.py（pip/uv 子进程中断收尾）。
# 修改影响: 调小会更容易走强杀分支（可能留下半完成的安装状态），调大拖慢停止体感。
CLI_CHILD_TERMINATE_WAIT_SECS: float = 5.0

# uv 可用性探测（python -m uv --version）的超时（秒）。
# 使用位置: CLI/utils/package_manager.py 的 _resolve_uv_command。
# 修改影响: 调大会在无 uv 环境下拖慢首次安装探测，调小可能误判 uv 不可用。
CLI_UV_PROBE_TIMEOUT_SECS: float = 5.0

# pip 可用性探测（python -m pip --version）超时（秒）。
# 使用位置: CLI/utils/package_manager.py -> _ensure_pip_available。
# 修改影响: 网络半死/代理黑洞时探测不再无限挂起。
CLI_PIP_PROBE_TIMEOUT_SECS: float = 10.0

# ensurepip 自举超时（秒）。
# 使用位置: CLI/utils/package_manager.py -> _ensure_pip_available。
# 修改影响: 自举安装的耐心上限；超时按 pip 不可用处理并走失败路径。
CLI_ENSURE_PIP_TIMEOUT_SECS: float = 120.0

# venv 创建（python -m venv / uv venv）超时（秒）。
# 使用位置: CLI/utils/package_manager.py -> create_project_venv。
# 修改影响: 慢盘/杀软扫描下创建不再无限挂起。
CLI_VENV_CREATE_TIMEOUT_SECS: float = 300.0

# uv 项目联动超时（秒）：uv add / uv remove 在项目环境解析+写入 lock 的耐心上限。
# 使用位置: CLI/utils/package_manager.py -> _run_uv_project_command。
# 修改影响: 大型 lock 解析慢时调大；超时按失败处理并回退 uv pip/pip 通道。
CLI_UV_PROJECT_TIMEOUT_SECS: float = 180.0

# uv 不支持的 pip 风格参数清单：命中即跳过 uv 后端直接走 pip
# （uv pip 会直接报错，随后现有链路整链重跑 pip——预检消灭这次双跑刷屏）。
# 维护依据: uv 0.11 实测 --user / --upgrade-strategy 不支持；需随 uv 版本复核。
# 使用位置: CLI/utils/package_manager.py -> _run_pip_command_with_output。
CLI_UV_UNSUPPORTED_FLAGS: tuple = ("--user", "--upgrade-strategy")

# uv 项目判定文件名（is_uv_project 的三重依据之一/之二）。
# 使用位置: CLI/utils/package_manager.py -> is_uv_project。
UV_PROJECT_LOCK_FILE: str = "uv.lock"
UV_PROJECT_MARKER: str = "uv ="

# 安装/卸载进度轮询间隔（秒）。
# 使用位置: CLI/utils/package_manager.py 的子进程输出轮询循环。
# 修改影响: 调小 CPU 占用略增、输出更即时；调大进度条变钝。
CLI_PACKAGE_POLL_INTERVAL_SECS: float = 0.5

# 拉取远端包元数据（适配器/模块索引）的超时（秒）。
# 使用位置: CLI/commands/init.py 的两处 future.result 等待。
# 修改影响: 调大弱网更宽容，调小弱网下更易失败进降级路径。
CLI_FETCH_METADATA_TIMEOUT_SECS: float = 10.0

# 组件内省子进程（python -c 脚本）的超时（秒）。
# 使用位置: CLI/commands/types.py 的 import-or-load 内省。
# 修改影响: 调大可容纳冷启动慢的目标环境，调大会拉长 doctor/create 体感。
CLI_INTROSPECT_TIMEOUT_SECS: float = 60.0

# 自更新子脚本启动后的静置延时（秒）：等旧进程释放文件锁/环境稳定。
# 使用位置: CLI/utils/package_manager.py 的自更新 f-string 脚本（值内插为字面量）。
CLI_SELFUPDATE_BOOT_DELAY_SECS: float = 2.0

# 自更新子脚本内单次 pip/uv 命令的超时（秒）。
# 使用位置: 同上（值内插为字面量）。
CLI_SELFUPDATE_RUN_TIMEOUT_SECS: float = 300.0

__all__ = [
    "ADAPTER_ENTRY_POINT_GROUP",
    "INIT_ERISPULSE_DEPENDENCY",
    "RUN_CRASH_BACKOFF_MAX_SECS",
    "RUN_CRASH_BACKOFF_PER_CRASH_SECS",
    "RUN_RESTART_PAUSE_SECS",
    "RUN_PERSISTENT_CRASH_HINT_THRESHOLD",
    "ENV_SUPERVISED",
    "ENV_RELOAD_WORKER",
    "HARD_RESTART_EXIT_CODE",
    "MODULE_ENTRY_POINT_GROUP",
    "PYPI_PACKAGE_JSON_URL_TEMPLATE",
    "CLI_CHILD_TERMINATE_WAIT_SECS",
    "CLI_UV_PROBE_TIMEOUT_SECS",
    "CLI_UV_PROJECT_TIMEOUT_SECS",
    "CLI_UV_UNSUPPORTED_FLAGS",
    "UV_PROJECT_LOCK_FILE",
    "UV_PROJECT_MARKER",
    "CLI_PACKAGE_POLL_INTERVAL_SECS",
    "CLI_FETCH_METADATA_TIMEOUT_SECS",
    "CLI_INTROSPECT_TIMEOUT_SECS",
    "CLI_SELFUPDATE_BOOT_DELAY_SECS",
    "CLI_SELFUPDATE_RUN_TIMEOUT_SECS",
]
