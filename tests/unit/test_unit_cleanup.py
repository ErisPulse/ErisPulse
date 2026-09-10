"""
归属清理钩子（on_cleanup / off_cleanup）单元测试

覆盖：owner 上下文自动记名与显式指定、幂等注册、注销、
run_owner_cleanups 触发与异常隔离、异步回调超时保护，
以及模块卸载 / 适配器资源清理链的集成触发。
"""

import asyncio

import pytest

from ErisPulse.Core.adapter import AdapterManager
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.module import ModuleManager
from ErisPulse.runtime import get_current_caller, get_current_owner, owner_scope
from ErisPulse.runtime import owner_cleanup as owner_cleanup_module
from ErisPulse.runtime.owner_cleanup import (
    _owner_cleanups,
    off_cleanup,
    on_cleanup,
    run_owner_cleanups,
)


@pytest.fixture(autouse=True)
def _clean_registry():
    """每个用例前后清空钩子注册表，避免跨用例污染"""
    _owner_cleanups.clear()
    yield
    _owner_cleanups.clear()


def _record_into(calls: list):
    def _cb(owner):
        calls.append(owner)

    return _cb


@pytest.mark.unit
class TestOnCleanup:
    """钩子注册测试"""

    def test_records_owner_from_context(self):
        """owner_scope 上下文内注册自动记名到当前 owner"""
        calls = []
        with owner_scope("OrderModule"):
            on_cleanup(_record_into(calls))
        assert _owner_cleanups["OrderModule"] and calls == []

    def test_explicit_owner_overrides_context(self):
        """显式 owner 参数覆盖上下文归属"""
        with owner_scope("CtxOwner"):
            on_cleanup(_record_into([]), owner="TargetOwner")
        assert "TargetOwner" in _owner_cleanups
        assert "CtxOwner" not in _owner_cleanups

    def test_no_owner_raises(self):
        """无 owner 上下文且未显式指定时抛 ValueError"""
        with pytest.raises(ValueError):
            on_cleanup(_record_into([]))

    def test_caller_context_takes_precedence(self):
        """module.call 执行期间（caller 已注入）优先记名到调用方而非本模块"""
        calls = []
        with owner_scope("TargetModule"):
            from ErisPulse.runtime.context import current_caller

            token = current_caller.set("CallerModule")
            try:
                on_cleanup(_record_into(calls))
            finally:
                current_caller.reset(token)
        assert calls == []
        assert _owner_cleanups.get("CallerModule")
        assert "TargetModule" not in _owner_cleanups

    def test_duplicate_registration_deduped(self):
        """同一 (owner, callback) 重复注册去重"""
        cb = _record_into([])
        with owner_scope("Mod"):
            on_cleanup(cb)
            on_cleanup(cb)
        assert len(_owner_cleanups["Mod"]) == 1

    def test_same_callback_multiple_owners(self):
        """同一回调可登记到多个 owner（注册顺序保持）"""
        cb = _record_into([])
        on_cleanup(cb, owner="A")
        on_cleanup(cb, owner="B")
        assert _owner_cleanups["A"] == [cb]
        assert _owner_cleanups["B"] == [cb]


@pytest.mark.unit
class TestOffCleanup:
    """钩子注销测试"""

    def test_off_specific_owner(self):
        """指定 owner 时仅注销该 owner 名下的钩子"""
        cb = _record_into([])
        on_cleanup(cb, owner="A")
        on_cleanup(cb, owner="B")
        assert off_cleanup(cb, owner="A") == 1
        assert "A" not in _owner_cleanups
        assert _owner_cleanups["B"] == [cb]

    def test_off_all_owners_returns_count(self):
        """owner=None 时注销该回调的全部登记并返回数量"""
        cb = _record_into([])
        on_cleanup(cb, owner="A")
        on_cleanup(cb, owner="B")
        on_cleanup(cb, owner="C")
        assert off_cleanup(cb) == 3
        assert _owner_cleanups == {}

    def test_off_removes_empty_key(self):
        """注销最后一个钩子后空键回收"""
        cb = _record_into([])
        on_cleanup(cb, owner="Mod")
        off_cleanup(cb, owner="Mod")
        assert "Mod" not in _owner_cleanups

    def test_off_unknown_returns_zero(self):
        """注销未登记的回调返回 0"""
        assert off_cleanup(_record_into([])) == 0


@pytest.mark.unit
class TestRunOwnerCleanups:
    """钩子触发测试"""

    async def test_runs_sync_and_async_in_order(self):
        """同步与异步回调均被触发，参数为 owner 名，保持注册顺序"""
        calls = []

        def sync_cb(owner):
            calls.append(("sync", owner))

        async def async_cb(owner):
            calls.append(("async", owner))

        on_cleanup(sync_cb, owner="Mod")
        on_cleanup(async_cb, owner="Mod")

        assert await run_owner_cleanups("Mod") == 2
        assert calls == [("sync", "Mod"), ("async", "Mod")]

    async def test_entries_removed_after_run(self):
        """触发后条目被移除，重复触发为空操作"""
        on_cleanup(_record_into([]), owner="Mod")
        assert await run_owner_cleanups("Mod") == 1
        assert "Mod" not in _owner_cleanups
        assert await run_owner_cleanups("Mod") == 0

    async def test_unknown_owner_returns_zero(self):
        """触发不存在的 owner 返回 0"""
        assert await run_owner_cleanups("NoSuchOwner") == 0

    async def test_sync_exception_isolated(self):
        """同步回调异常被隔离，不影响后续钩子"""
        calls = []

        def bad(owner):
            raise RuntimeError("boom")

        on_cleanup(bad, owner="Mod")
        on_cleanup(_record_into(calls), owner="Mod")

        assert await run_owner_cleanups("Mod") == 1
        assert calls == ["Mod"]

    async def test_async_exception_isolated(self):
        """异步回调异常被隔离，不影响后续钩子"""
        calls = []

        async def bad(owner):
            raise RuntimeError("boom")

        on_cleanup(bad, owner="Mod")
        on_cleanup(_record_into(calls), owner="Mod")

        assert await run_owner_cleanups("Mod") == 1
        assert calls == ["Mod"]

    async def test_async_timeout_isolated(self, monkeypatch):
        """异步回调超时被隔离并放弃，不影响后续钩子"""
        monkeypatch.setattr(
            owner_cleanup_module, "CLEANUP_CALLBACK_TIMEOUT_SECS", 0.01
        )
        calls = []

        async def slow(owner):
            await asyncio.sleep(1)

        on_cleanup(slow, owner="Mod")
        on_cleanup(_record_into(calls), owner="Mod")

        assert await run_owner_cleanups("Mod") == 1
        assert calls == ["Mod"]


@pytest.mark.unit
class TestCleanupChainIntegration:
    """框架清理链集成触发测试"""

    async def test_module_unload_triggers_hooks(self):
        """模块卸载时触发其 owner 名下的钩子并移除条目"""
        received = []

        class OrderModule(BaseModule):
            def __init__(self, sdk=None):
                self.sdk = sdk

            async def on_load(self, event):
                # 模拟工具模块在 OrderModule 注册资源时登记清理钩子
                on_cleanup(_record_into(received))

            async def on_unload(self, event):
                pass

        manager = ModuleManager()
        manager._modules.clear()
        manager._module_classes.clear()
        manager._loaded_modules.clear()
        manager._module_info.clear()
        manager.register("OrderModule", OrderModule)

        assert await manager.load("OrderModule") is True
        assert _owner_cleanups.get("OrderModule")

        assert await manager.unload("OrderModule") is True
        assert received == ["OrderModule"]
        assert "OrderModule" not in _owner_cleanups

    async def test_adapter_resource_cleanup_triggers_hooks(self):
        """适配器资源清理链触发以平台名为 owner 的钩子"""
        manager = AdapterManager()
        received = []
        on_cleanup(_record_into(received), owner="MyPlatform")

        await manager._cleanup_adapter_resources("MyPlatform")

        assert received == ["MyPlatform"]
        assert "MyPlatform" not in _owner_cleanups

    def _make_manager(self) -> ModuleManager:
        manager = ModuleManager()
        manager._modules.clear()
        manager._module_classes.clear()
        manager._loaded_modules.clear()
        manager._module_info.clear()
        return manager

    async def test_module_call_attributes_caller_and_hooks_follow(self):
        """module.call 执行期间注入 caller 上下文；RPC 内登记的钩子记名到调用方"""
        seen = {}

        class CronStub(BaseModule):
            def __init__(self, sdk=None):
                self.sdk = sdk

            async def on_load(self, event):
                pass

            async def register_handler(self):
                # owner 归因到本模块，调用方身份经 caller 上下文读取
                seen["owner"] = get_current_owner()
                seen["caller"] = get_current_caller()
                on_cleanup(_record_into(received))

            async def on_unload(self, event):
                pass

        class CallerModule(BaseModule):
            def __init__(self, sdk=None):
                self.sdk = sdk

            async def on_load(self, event):
                pass

            async def on_unload(self, event):
                pass

        manager = self._make_manager()
        manager.register("Cron", CronStub)
        manager.register("Caller", CallerModule)
        assert await manager.load("Cron") is True
        assert await manager.load("Caller") is True

        received = []
        with owner_scope("Caller"):
            await manager.call("Cron", "register_handler")

        assert seen == {"owner": "Cron", "caller": "Caller"}
        assert _owner_cleanups.get("Caller")
        assert "Cron" not in _owner_cleanups

        # 调用结束后上下文复位
        assert get_current_caller() is None

        # 卸载调用方模块时钩子被触发
        assert await manager.unload("Caller") is True
        assert received == ["Caller"]
