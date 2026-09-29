"""
pytest 配置文件

提供测试夹具（fixtures）和测试钩子

{!--< tips >!--}
1. 本文件只保留全测试套件共用的设施：语言钉子、事件去重开关、i18n 隔离、
   storage 会话收尾、命令/事件系统共享清理与少量活跃 fixture
2. 命令治理类测试的状态清理统一引用 :func:`_clean_event_command_state`
   （此前 9 个测试文件各自复制约 30 行几乎相同的清理体）
{!--< /tips >!--}
"""

import os
import sys
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import pytest

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# 测试套件语言钉子：文案断言（错误提示 / 帮助文本等）按 zh-CN 书写，
# 与维护者本机的语言环境（ERISPULSE_LANG / cli_state / config.toml）解耦——
# i18n 对该变量的消费是动态读取且优先级高于持久化设置，import 时即可生效。
# setdefault：维护者可用环境变量显式覆盖为其他语言跑套件
os.environ.setdefault("ERISPULSE_LANG", "zh-CN")


# ==================== 测试环境设置 ====================

@pytest.fixture(scope="session", autouse=True)
def _pin_test_language() -> Generator[None, None, None]:
    """
    会话级钉死 i18n 实例语言为 zh-CN（与套件文案断言一致）

    单靠 ERISPULSE_LANG 不够——"手动设置"优先级高于它，先于钉子执行的
    语言类测试（test_unit_i18n）会经 set_language 改写实例状态；虽由
    `_isolate_i18n_state` 按用例还原，但还原基准须是被钉住的状态。

    {!--< internal-use >!--}
    """
    try:
        from ErisPulse.Core.i18n import i18n as _i18n

        _i18n.set_language("zh-CN", persist=False)
    except Exception:
        pass
    yield


@pytest.fixture(scope="function", autouse=True)
def _reset_event_dedupe() -> Generator[None, None, None]:
    """
    测试期间禁用事件幂等去重，用例后恢复

    问题背景：``AdapterManager.emit`` 按 ``event["id"]`` LRU 去重（防平台
    重连重推），而测试普遍使用固定 id 的合成事件且同一用例内连续多次
    emit——第 2 条起会被误判为重复而丢弃。

    此 fixture 在每个用例期间关闭去重（``adapter._event_dedupe_enabled = False``），
    结束后恢复惰性配置态；去重功能本身由专用用例显式开启覆盖。

    {!--< internal-use >!--}
    """
    try:
        from ErisPulse.Core.adapter import adapter as _adapter

        _adapter._event_dedupe_enabled = False
        _adapter._seen_event_ids.clear()
    except Exception:
        pass
    yield
    try:
        from ErisPulse.Core.adapter import adapter as _adapter

        _adapter._event_dedupe_enabled = None
        _adapter._seen_event_ids.clear()
    except Exception:
        pass


@pytest.fixture(scope="session", autouse=True)
def _close_storage_on_teardown() -> Generator[None, None, None]:
    """
    测试会话结束时关闭 storage 单例的后端资源，避免 ResourceWarning

    {!--< internal-use >!--}
    """
    yield
    try:
        from ErisPulse.Core.storage import storage as _storage

        if hasattr(_storage, "close"):
            _storage.close()
    except Exception:
        pass


@pytest.fixture(scope="session", autouse=True)
def _protect_repo_config() -> Generator[None, None, None]:
    """
    会话级备份/还原仓库根 config/config.toml

    问题背景：单测的 ``persist=True`` 写入（scope / overrides ACL 等）落在
    进程 cwd 的真实用户配置上且测试结束不清理——残留的 ACL / 覆写节会让
    后续测试运行（以及本地真实开发）被静默改变行为（如命令被 ACL 拒绝）。

    会话开始备份、结束还原；开始时不存在的文件在结束时移除。

    {!--< internal-use >!--}
    """
    from ErisPulse.Core.constants import DEFAULT_CONFIG_FILE_PATH

    config_path = Path(DEFAULT_CONFIG_FILE_PATH)
    backup: bytes | None = None
    if config_path.exists():
        backup = config_path.read_bytes()
    yield
    try:
        # 先丢弃未刷盘的脏写入（防止还原后被 atexit/延迟刷盘再次覆盖）
        try:
            import importlib

            _config_pkg = importlib.import_module("ErisPulse.Core.config")
            with _config_pkg.config._lock:
                _config_pkg.config._dirty_keys.clear()
        except Exception:
            pass
        if backup is not None:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_bytes(backup)
        elif config_path.exists():
            config_path.unlink()
    except OSError:
        pass


@pytest.fixture(scope="function", autouse=True)
def _isolate_i18n_state() -> Generator[None, None, None]:
    """
    隔离 i18n 模块的单例状态，避免测试间互相污染

    问题背景：``I18nManager.set_language`` 会同时修改实例状态 ``_current_lang``
    并写入全局持久化文件 ``~/.erispulse/cli_state.json``。
    若某个测试设置了语言（如 ``set_language("en")``）未还原，后续依赖
    i18n 默认语言的测试（如 router 报错消息的中文匹配）会间歇性失败。

    此 fixture 在每个测试前后快照/还原 i18n 实例状态与全局状态文件。

    {!--< internal-use >!--}
    """
    import json
    from pathlib import Path

    state_path = Path.home() / ".erispulse" / "cli_state.json"
    snapshot_file = state_path.read_bytes() if state_path.exists() else None

    # 快照 i18n 单例的实例状态
    instance_state: dict[str, object] = {}
    try:
        from ErisPulse.Core.i18n import i18n as _i18n

        instance_state = {
            "_current_lang": getattr(_i18n, "_current_lang", None),
            "_detected_lang": getattr(_i18n, "_detected_lang", None),
        }
    except Exception:
        pass

    yield

    # 还原 i18n 实例状态
    try:
        from ErisPulse.Core.i18n import i18n as _i18n

        for k, v in instance_state.items():
            setattr(_i18n, k, v)
    except Exception:
        pass

    # 还原全局状态文件
    try:
        if snapshot_file is not None:
            state_path.write_bytes(snapshot_file)
        elif state_path.exists():
            # 测试前不存在 → 删除测试中创建的文件
            try:
                with state_path.open(encoding="utf-8") as f:
                    data = json.load(f)
                data.pop("language", None)
                if data:
                    with state_path.open("w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                else:
                    state_path.unlink()
            except (FileNotFoundError, json.JSONDecodeError, OSError):
                pass
    except Exception:
        pass


# ==================== 命令/事件系统共享清理 ====================


@pytest.fixture
def _clean_event_command_state() -> Generator[None, None, None]:
    """
    命令/事件系统单例状态的共享清理（setup + teardown 对称执行）

    覆盖各命令治理类测试文件 clean_state 的公共核心（命令四表 + 事件处理器
    + 适配器事件通道）；文件特有的增量清理（冷却表 / scope / interaction /
    影子账本等）在各自的 autouse fixture 中引用本 fixture 后追加。

    {!--< internal-use >!--}
    """
    from ErisPulse.Core.Event import _clear_all_handlers
    from ErisPulse.Core.Event.command import command as command_handler
    from ErisPulse.Core.adapter import adapter

    def _clean() -> None:
        _clear_all_handlers()
        command_handler.commands.clear()
        command_handler.aliases.clear()
        command_handler.groups.clear()
        command_handler.permissions.clear()
        adapter._onebot_handlers.clear()
        adapter._raw_handlers.clear()
        adapter._onebot_middlewares.clear()
        adapter._bots.clear()

    _clean()
    yield
    _clean()


# ==================== SDK / 日志 / 网络测试夹具 ====================


@pytest.fixture
async def mock_sdk(clean_environment, test_config_file: Path) -> AsyncGenerator:
    """
    创建模拟的 SDK 实例

    为测试提供一个模拟的 SDK 对象
    """
    from ErisPulse import sdk as _sdk

    # 初始化 SDK
    try:
        success = await _sdk.init()
        if success:
            yield _sdk
            # 反初始化
            await _sdk.uninit()
        else:
            pytest.skip("SDK 初始化失败")
    except Exception as e:
        pytest.skip(f"SDK 初始化异常: {e}")


@pytest.fixture(scope="session")
def test_data_dir(tmp_path_factory) -> Path:
    """
    创建测试数据目录（mock_sdk 链路的临时目录）
    """
    return tmp_path_factory.mktemp("test_data")


@pytest.fixture(scope="session")
def test_config_file(test_data_dir: Path) -> Path:
    """
    创建测试配置文件（mock_sdk 链路使用）
    """
    config_file = test_data_dir / "test_config.toml"
    config_file.write_text("""
[ErisPulse]
[ErisPulse.server]
host = "127.0.0.1"
port = 8888

[ErisPulse.logger]
level = "DEBUG"
log_files = []
memory_limit = 100

[ErisPulse.storage]
max_snapshot = 5

[ErisPulse.framework]
enable_lazy_loading = false

[ErisPulse.modules]
TestModule1 = true
TestModule2 = false

[ErisPulse.adapters]
TestAdapter1 = true
TestAdapter2 = false

[ErisPulse.event]
[ErisPulse.event.command]
prefix = "/"
case_sensitive = false
allow_space_prefix = false

[ErisPulse.event.message]
ignore_self = true
""")
    return config_file


@pytest.fixture(scope="function")
def clean_environment(test_data_dir: Path) -> Generator[None, None, None]:
    """
    清理测试环境（chdir 到临时目录并快照/还原环境变量，mock_sdk 链路使用）
    """
    original_cwd = os.getcwd()
    original_env = os.environ.copy()

    os.chdir(str(test_data_dir))

    yield

    os.chdir(original_cwd)
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_logger():
    """
    创建模拟日志记录器
    """
    from ErisPulse.Core.logger import Logger

    logger = Logger()
    logger._logger.handlers = []  # 移除所有处理器
    logger._logs = {}
    logger._module_levels = {}

    # 添加内存处理器
    import logging

    class TestHandler(logging.Handler):
        def __init__(self):
            super().__init__()
            self.records = []

        def emit(self, record):
            self.records.append(record)

    handler = TestHandler()
    logger._logger.addHandler(handler)
    logger._test_handler = handler

    return logger


@pytest.fixture
def free_port():
    """
    获取可用的端口号
    """
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]

    return port


# ==================== pytest 配置和钩子 ====================


def pytest_collection_modifyitems(config, items):
    """
    修改测试收集结果：按文件路径 / 测试名自动补标记
    """
    for item in items:
        # 根据文件路径添加标记
        if "test_unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "test_integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "test_e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        elif "test_perf" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        elif "test_stress" in str(item.fspath):
            item.add_marker(pytest.mark.stress)

        # 根据测试名称添加标记
        if "adapter" in item.name.lower():
            item.add_marker(pytest.mark.adapter)
        elif "module" in item.name.lower():
            item.add_marker(pytest.mark.module)
        elif "event" in item.name.lower():
            item.add_marker(pytest.mark.event)
        elif "lifecycle" in item.name.lower():
            item.add_marker(pytest.mark.lifecycle)
