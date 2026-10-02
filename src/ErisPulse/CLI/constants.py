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

__all__ = [
    "ADAPTER_ENTRY_POINT_GROUP",
    "RUN_CRASH_BACKOFF_MAX_SECS",
    "RUN_CRASH_BACKOFF_PER_CRASH_SECS",
    "RUN_RESTART_PAUSE_SECS",
    "RUN_PERSISTENT_CRASH_HINT_THRESHOLD",
    "ENV_SUPERVISED",
    "HARD_RESTART_EXIT_CODE",
    "MODULE_ENTRY_POINT_GROUP",
    "PYPI_PACKAGE_JSON_URL_TEMPLATE",
]
