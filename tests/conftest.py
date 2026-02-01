"""
pytest 配置文件

提供测试夹具（fixtures）和测试钩子
"""

import asyncio
import os
import sys
import pytest
import shutil
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, AsyncMock, MagicMock, patch

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ==================== 测试环境设置 ====================

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    创建事件循环
    
    为整个测试会话提供一个单一的事件循环
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_data_dir(tmp_path_factory) -> Path:
    """
    创建测试数据目录
    
    为测试提供临时数据目录
    """
    test_dir = tmp_path_factory.mktemp("test_data")
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir


@pytest.fixture(scope="session")
def test_config_file(test_data_dir: Path) -> Path:
    """
    创建测试配置文件
    
    为测试提供临时配置文件
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
    清理测试环境
    
    在测试前后清理环境
    """
    # 备份原始环境
    original_cwd = os.getcwd()
    original_env = os.environ.copy()
    
    # 设置测试环境
    os.chdir(str(test_data_dir))
    
    yield
    
    # 恢复原始环境
    os.chdir(original_cwd)
    os.environ.clear()
    os.environ.update(original_env)
    
    # 清理临时文件
    import glob
    for db_file in glob.glob(str(test_data_dir / "*.db")):
        try:
            os.remove(db_file)
        except:
            pass


# ==================== SDK 测试夹具 ====================

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


@pytest.fixture
def real_sdk(clean_environment, test_config_file: Path):
    """
    创建真实的 SDK 实例
    
    为集成测试提供真实的 SDK 对象
    """
    from ErisPulse import sdk as _sdk
    return _sdk


# ==================== 模块管理器测试夹具 ====================

@pytest.fixture
def mock_module_manager():
    """
    创建模拟的模块管理器
    """
    from ErisPulse.Core.module import ModuleManager
    
    manager = ModuleManager()
    manager._module_classes = {}
    manager._modules = {}
    manager._loaded_modules = set()
    manager._module_info = {}
    
    return manager


@pytest.fixture
def mock_base_module():
    """
    创建模拟的 BaseModule 子类
    """
    from ErisPulse.Core.Bases import BaseModule
    
    class MockModule(BaseModule):
        def __init__(self, sdk):
            self.sdk = sdk
            self.load_called = False
            self.unload_called = False
            self.test_data = {}
        
        async def on_load(self, event):
            self.load_called = True
            self.test_data["load_event"] = event
            return True
        
        async def on_unload(self, event):
            self.unload_called = True
            self.test_data["unload_event"] = event
            return True
    
    return MockModule


# ==================== 适配器管理器测试夹具 ====================

@pytest.fixture
def mock_adapter_manager():
    """
    创建模拟的适配器管理器
    """
    from ErisPulse.Core.adapter import AdapterManager
    
    manager = AdapterManager()
    manager._adapters = {}
    manager._started_instances = set()
    manager._adapter_info = {}
    manager._onebot_handlers = {}
    manager._raw_handlers = {}
    manager._onebot_middlewares = []
    
    return manager


@pytest.fixture
def mock_base_adapter():
    """
    创建模拟的 BaseAdapter 子类
    """
    from ErisPulse.Core.Bases import BaseAdapter
    
    class MockAdapter(BaseAdapter):
        def __init__(self, sdk):
            super().__init__()
            self.sdk = sdk
            self.start_called = False
            self.shutdown_called = False
            self.call_api_log = []
            self.test_data = {}
        
        async def start(self):
            self.start_called = True
            self.test_data["start_time"] = "mocked"
        
        async def shutdown(self):
            self.shutdown_called = True
            self.test_data["shutdown_time"] = "mocked"
        
        async def call_api(self, endpoint: str, **params):
            self.call_api_log.append({"endpoint": endpoint, "params": params})
            return {
                "status": "ok",
                "retcode": 0,
                "data": {"mocked": True},
                "message_id": "test_msg_id",
                "message": "",
                f"mock_raw": params
            }
    
    return MockAdapter


# ==================== 事件系统测试夹具 ====================

@pytest.fixture
def mock_event_data():
    """
    创建标准的事件数据
    """
    return {
        "id": "test_event_123",
        "time": 1234567890,
        "type": "message",
        "detail_type": "private",
        "platform": "test_platform",
        "self": {
            "platform": "test_platform",
            "user_id": "test_bot_id"
        },
        "user_id": "test_user_id",
        "user_nickname": "TestUser",
        "message": [
            {
                "type": "text",
                "data": {"text": "test message"}
            }
        ],
        "alt_message": "test message",
        "test_raw": {},
        "test_raw_type": "test_event"
    }


@pytest.fixture
def mock_command_event_data():
    """
    创建命令事件数据
    """
    event_data = {
        "id": "test_cmd_event_123",
        "time": 1234567890,
        "type": "message",
        "detail_type": "private",
        "platform": "test_platform",
        "self": {
            "platform": "test_platform",
            "user_id": "test_bot_id"
        },
        "user_id": "test_user_id",
        "user_nickname": "TestUser",
        "message": [
            {
                "type": "text",
                "data": {"text": "/test arg1 arg2"}
            }
        ],
        "alt_message": "/test arg1 arg2"
    }
    return event_data


@pytest.fixture
def mock_notice_event_data():
    """
    创建通知事件数据
    """
    return {
        "id": "test_notice_123",
        "time": 1234567890,
        "type": "notice",
        "detail_type": "friend_increase",
        "platform": "test_platform",
        "self": {
            "platform": "test_platform",
            "user_id": "test_bot_id"
        },
        "user_id": "test_user_id",
        "user_nickname": "TestUser",
        "test_raw": {},
        "test_raw_type": "friend_add"
    }


@pytest.fixture
def mock_request_event_data():
    """
    创建请求事件数据
    """
    return {
        "id": "test_request_123",
        "time": 1234567890,
        "type": "request",
        "detail_type": "friend",
        "platform": "test_platform",
        "self": {
            "platform": "test_platform",
            "user_id": "test_bot_id"
        },
        "user_id": "test_user_id",
        "user_nickname": "TestUser",
        "comment": "请添加好友",
        "test_raw": {},
        "test_raw_type": "friend_request"
    }


# ==================== 配置和存储测试夹具 ====================

@pytest.fixture
def mock_config_file(tmp_path: Path):
    """
    创建临时配置文件
    """
    config_file = tmp_path / "test_config.toml"
    config_file.write_text("""
[test_section]
test_key = "test_value"
number_key = 123
bool_key = true

[nested]
[sub_section]
nested_key = "nested_value"
""")
    return config_file


@pytest.fixture
def mock_storage_db(tmp_path: Path):
    """
    创建临时存储数据库
    """
    db_file = tmp_path / "test_storage.db"
    
    # 初始化数据库
    import sqlite3
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS config (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """)
    
    # 插入测试数据
    import json
    test_data = {
        "test.key1": "value1",
        "test.key2": {"nested": "data"},
        "test.key3": 123
    }
    
    for key, value in test_data.items():
        cursor.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
            (key, json.dumps(value) if isinstance(value, (dict, list)) else str(value))
        )
    
    conn.commit()
    conn.close()
    
    return db_file


# ==================== 日志测试夹具 ====================

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


# ==================== WebSocket 测试夹具 ====================

@pytest.fixture
def mock_websocket():
    """
    创建模拟的 WebSocket 连接
    """
    from unittest.mock import AsyncMock
    
    websocket = AsyncMock()
    websocket.accept = AsyncMock()
    websocket.close = AsyncMock()
    websocket.send_text = AsyncMock()
    websocket.receive_text = AsyncMock()
    websocket.receive_json = AsyncMock()
    websocket.client = type('Client', (), {'host': '127.0.0.1', 'port': 12345})()
    
    return websocket


# ==================== FastAPI 测试客户端 ====================

@pytest.fixture
async def test_client():
    """
    创建 FastAPI 测试客户端
    """
    from fastapi.testclient import TestClient
    from ErisPulse.Core.router import router
    
    client = TestClient(router.app)
    return client


# ==================== 网络测试夹具 ====================

@pytest.fixture
def free_port():
    """
    获取可用的端口号
    """
    import socket
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    
    return port


# ==================== pytest 配置和钩子 ====================

def pytest_configure(config):
    """
    pytest 配置钩子
    
    在测试会话开始前执行
    """
    # 注册自定义标记
    config.addinivalue_line(
        "markers", "unit: 单元测试标记"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试标记"
    )
    config.addinivalue_line(
        "markers", "e2e: 端到端测试标记"
    )


def pytest_collection_modifyitems(config, items):
    """
    修改测试收集结果
    
    为测试添加默认标记
    """
    for item in items:
        # 根据文件路径添加标记
        if "test_unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "test_integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "test_e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        
        # 根据测试名称添加标记
        if "adapter" in item.name.lower():
            item.add_marker(pytest.mark.adapter)
        elif "module" in item.name.lower():
            item.add_marker(pytest.mark.module)
        elif "event" in item.name.lower():
            item.add_marker(pytest.mark.event)
        elif "lifecycle" in item.name.lower():
            item.add_marker(pytest.mark.lifecycle)


def pytest_runtest_setup(item):
    """
    测试执行前的钩子
    """
    # 可以在这里添加测试前的准备逻辑
    pass


def pytest_runtest_teardown(item, nextitem):
    """
    测试执行后的钩子
    """
    # 可以在这里添加测试后的清理逻辑
    pass
