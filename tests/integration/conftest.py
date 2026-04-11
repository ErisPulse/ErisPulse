"""
集成测试专用 fixtures

提供真实组件实例，不使用 mock（除了不可避免的网络/外部依赖）
"""

import asyncio
import os
import sys
import pytest
import shutil
import sqlite3
from pathlib import Path
from unittest.mock import AsyncMock, patch
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from ErisPulse.Core.adapter import AdapterManager
from ErisPulse.Core.module import ModuleManager
from ErisPulse.Core.router import RouterManager
from ErisPulse.Core.lifecycle import LifecycleManager
from ErisPulse.Core.config import ConfigManager
from ErisPulse.Core.storage import StorageManager
from ErisPulse.Core.Bases import BaseAdapter, BaseModule
from ErisPulse.Core.Event import command, message, notice, request, meta


class IntegrationAdapter(BaseAdapter):
    """集成测试用适配器"""

    def __init__(self, sdk=None):
        super().__init__()
        self.sdk = sdk
        self.started = False
        self.shutdown_called = False
        self.start_count = 0
        self.shutdown_count = 0

    async def start(self):
        self.started = True
        self.start_count += 1

    async def shutdown(self):
        self.shutdown_called = True
        self.shutdown_count += 1

    async def call_api(self, endpoint: str, **params):
        return {
            "status": "ok",
            "retcode": 0,
            "data": {"endpoint": endpoint, "params": params},
            "message_id": "integ_test_msg_id",
            "message": "",
            "test_raw": params,
        }


class IntegrationModule(BaseModule):
    """集成测试用模块"""

    def __init__(self, sdk=None):
        self.sdk = sdk
        self.load_called = False
        self.unload_called = False
        self.load_event = None
        self.unload_event = None

    async def on_load(self, event):
        self.load_called = True
        self.load_event = event
        return True

    async def on_unload(self, event):
        self.unload_called = True
        self.unload_event = event
        return True


@pytest.fixture
def tmp_config_dir(tmp_path):
    """创建临时配置目录"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def temp_config(tmp_config_dir):
    """创建临时 ConfigManager"""
    config_file = str(tmp_config_dir / "config.toml")
    config_file_content = """
[ErisPulse]
[ErisPulse.server]
host = "127.0.0.1"
port = 18765

[ErisPulse.logger]
level = "WARNING"
log_files = []
memory_limit = 10

[ErisPulse.storage]
max_snapshot = 3

[ErisPulse.framework]
enable_lazy_loading = false

[ErisPulse.modules]
IntegrationModule = true

[ErisPulse.adapters]
IntegrationAdapter = true

[ErisPulse.event]
[ErisPulse.event.command]
prefix = "/"
case_sensitive = false
allow_space_prefix = false

[ErisPulse.event.message]
ignore_self = true
"""
    (tmp_config_dir / "config.toml").write_text(config_file_content, encoding="utf-8")

    mgr = ConfigManager(config_file=config_file)
    yield mgr


@pytest.fixture
def temp_storage(tmp_path):
    """创建临时 StorageManager"""
    db_file = tmp_path / "test_config.db"

    class TempStorage(StorageManager):
        def __init__(self):
            self._initialized = False
            self.db_path = str(db_file)
            self._local = self._local.__class__()
            self._init_db()
            self._initialized = True

    mgr = TempStorage()
    yield mgr

    if db_file.exists():
        try:
            db_file.unlink()
        except Exception:
            pass


@pytest.fixture
def temp_lifecycle():
    """创建临时 LifecycleManager"""
    mgr = LifecycleManager()
    mgr._handlers.clear()
    mgr._timers.clear()
    yield mgr


@pytest.fixture
def fresh_adapter_manager():
    """创建干净的 AdapterManager"""
    mgr = AdapterManager()
    mgr._adapters.clear()
    mgr._started_instances.clear()
    mgr._adapter_info.clear()
    mgr._onebot_handlers.clear()
    mgr._raw_handlers.clear()
    mgr._onebot_middlewares.clear()
    mgr._bots.clear()
    return mgr


@pytest.fixture
def fresh_module_manager():
    """创建干净的 ModuleManager"""
    mgr = ModuleManager()
    mgr._modules.clear()
    mgr._module_classes.clear()
    mgr._loaded_modules.clear()
    mgr._module_info.clear()
    return mgr


@pytest.fixture
def fresh_router():
    """创建干净的 RouterManager"""
    mgr = RouterManager()
    mgr._http_routes.clear()
    mgr._websocket_routes.clear()
    mgr._server_task = None
    return mgr


@pytest.fixture
def clean_event_system():
    """清理事件系统全局状态"""
    command.commands.clear()
    command.aliases.clear()
    command.groups.clear()
    command.permissions.clear()
    command._waiting_replies.clear()
    message.handler.handlers.clear()
    message.handler._handler_map.clear()
    notice.handler.handlers.clear()
    notice.handler._handler_map.clear()
    request.handler.handlers.clear()
    request.handler._handler_map.clear()
    meta.handler.handlers.clear()
    meta.handler._handler_map.clear()
    yield
    command._clear_commands()
    command.commands.clear()
    command.aliases.clear()
    command.groups.clear()
    command.permissions.clear()
    command._waiting_replies.clear()
    message.handler.handlers.clear()
    message.handler._handler_map.clear()
    notice.handler.handlers.clear()
    notice.handler._handler_map.clear()
    request.handler.handlers.clear()
    request.handler._handler_map.clear()
    meta.handler.handlers.clear()
    meta.handler._handler_map.clear()


@pytest.fixture
def http_test_client():
    """创建 FastAPI 测试客户端"""
    from fastapi.testclient import TestClient

    mgr = RouterManager()
    client = TestClient(mgr.app)
    yield client, mgr


def make_message_event(
    text="/test arg1",
    user_id="user123",
    platform="integration",
    detail_type="private",
    **kwargs,
):
    """构造标准消息事件数据"""
    data = {
        "id": "integ_msg_001",
        "time": 1712345678,
        "type": "message",
        "detail_type": detail_type,
        "platform": platform,
        "self": {
            "platform": platform,
            "user_id": "bot_001",
        },
        "user_id": user_id,
        "user_nickname": "TestUser",
        "message": [{"type": "text", "data": {"text": text}}],
        "alt_message": text,
    }
    data.update(kwargs)
    return data


def make_meta_event(event_type="connect", platform="integration", **kwargs):
    """构造元事件数据"""
    data = {
        "id": "integ_meta_001",
        "time": 1712345678,
        "type": "meta",
        "detail_type": event_type,
        "platform": platform,
        "self": {
            "platform": platform,
            "user_id": "bot_001",
        },
    }
    data.update(kwargs)
    return data
