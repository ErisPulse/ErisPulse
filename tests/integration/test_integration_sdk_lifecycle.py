"""
SDK 完整生命周期集成测试

测试 init → load modules → adapter startup → uninit 的完整流程，
验证生命周期事件正确触发、资源正确清理、可重复 init/uninit。
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from ErisPulse.Core.adapter import AdapterManager
from ErisPulse.Core.module import ModuleManager
from ErisPulse.Core.lifecycle import lifecycle
from ErisPulse.Core.Event import command, message
from ErisPulse.Core.Bases import BaseAdapter, BaseModule


class _TestAdapter(BaseAdapter):
    def __init__(self):
        super().__init__()
        self.started = False

    async def start(self):
        self.started = True

    async def shutdown(self):
        self.started = False

    async def call_api(self, endpoint: str, **params):
        return {"status": "ok", "retcode": 0, "data": {}, "message_id": "id"}


class _TestModule(BaseModule):
    def __init__(self, sdk=None):
        self.sdk = sdk
        self.loaded = False

    async def on_load(self, event):
        self.loaded = True
        return True

    async def on_unload(self, event):
        self.loaded = False
        return True


@pytest.fixture
def clean_lifecycle():
    lifecycle._handlers.clear()
    lifecycle._timers.clear()
    yield
    lifecycle._handlers.clear()
    lifecycle._timers.clear()


class TestSDKLifecycleIntegration:
    """SDK 生命周期集成测试"""

    @pytest.fixture(autouse=True)
    def setup(self, clean_lifecycle):
        self.adapter_mgr = AdapterManager()
        self.adapter_mgr._adapters.clear()
        self.adapter_mgr._started_instances.clear()
        self.adapter_mgr._adapter_info.clear()
        self.adapter_mgr._onebot_handlers.clear()
        self.adapter_mgr._raw_handlers.clear()
        self.adapter_mgr._onebot_middlewares.clear()
        self.adapter_mgr._bots.clear()

        self.module_mgr = ModuleManager()
        self.module_mgr._modules.clear()
        self.module_mgr._module_classes.clear()
        self.module_mgr._loaded_modules.clear()
        self.module_mgr._module_info.clear()

    def test_register_and_list_adapter(self):
        self.adapter_mgr.register("test_platform", _TestAdapter)
        assert "test_platform" in self.adapter_mgr._adapters
        assert isinstance(self.adapter_mgr._adapters["test_platform"], _TestAdapter)

    @pytest.mark.asyncio
    async def test_register_and_load_module(self):
        self.module_mgr.register("test_module", _TestModule)
        result = await self.module_mgr.load("test_module")
        assert result is True
        assert self.module_mgr._modules["test_module"].loaded is True

    @pytest.mark.asyncio
    async def test_register_load_unload_module_sequence(self):
        self.module_mgr.register("m1", _TestModule)
        await self.module_mgr.load("m1")
        assert "m1" in self.module_mgr._loaded_modules

        await self.module_mgr.unload("m1")
        assert "m1" not in self.module_mgr._loaded_modules

    @pytest.mark.asyncio
    async def test_multiple_modules_lifecycle(self):
        self.module_mgr.register("m1", _TestModule)
        self.module_mgr.register("m2", _TestModule)
        await self.module_mgr.load("m1")
        await self.module_mgr.load("m2")

        assert len(self.module_mgr._loaded_modules) == 2

        await self.module_mgr.unload()
        assert len(self.module_mgr._loaded_modules) == 0

    @pytest.mark.asyncio
    async def test_module_load_emits_lifecycle_event(self):
        events_received = []

        async def on_module_load(data):
            events_received.append(data)

        lifecycle.on("module.load")(on_module_load)

        self.module_mgr.register("m1", _TestModule)
        await self.module_mgr.load("m1")

        assert len(events_received) == 1
        assert events_received[0]["data"]["module_name"] == "m1"
        assert events_received[0]["data"]["success"] is True

    @pytest.mark.asyncio
    async def test_module_unload_emits_lifecycle_event(self):
        events_received = []

        async def on_module_unload(data):
            events_received.append(data)

        lifecycle.on("module.unload")(on_module_unload)

        self.module_mgr.register("m1", _TestModule)
        await self.module_mgr.load("m1")
        await self.module_mgr.unload("m1")

        assert any(e["event"] == "module.unload" for e in events_received)

    @pytest.mark.asyncio
    async def test_adapter_register_and_clear(self):
        self.adapter_mgr.register("p1", _TestAdapter)
        assert "p1" in self.adapter_mgr._adapters

        self.adapter_mgr.clear()
        assert len(self.adapter_mgr._adapters) == 0

    @pytest.mark.asyncio
    async def test_multiple_init_uninit_cycles(self):
        for i in range(3):
            self.module_mgr.register(f"m{i}", _TestModule)
            await self.module_mgr.load(f"m{i}")
            assert f"m{i}" in self.module_mgr._loaded_modules

            await self.module_mgr.unload()
            assert len(self.module_mgr._loaded_modules) == 0

            self.module_mgr._module_classes.clear()

    @pytest.mark.asyncio
    async def test_concurrent_module_load(self):
        self.module_mgr.register("m1", _TestModule)
        self.module_mgr.register("m2", _TestModule)
        self.module_mgr.register("m3", _TestModule)

        await asyncio.gather(
            self.module_mgr.load("m1"),
            self.module_mgr.load("m2"),
            self.module_mgr.load("m3"),
        )

        assert len(self.module_mgr._loaded_modules) == 3

    @pytest.mark.asyncio
    async def test_lifecycle_wildcard_handler(self):
        events = []

        def wildcard(data):
            events.append(data["event"])

        lifecycle.on("*")(wildcard)

        lifecycle.on("custom.test")(lambda d: None)
        await lifecycle.submit_event("custom.test")

        assert "custom.test" in events
