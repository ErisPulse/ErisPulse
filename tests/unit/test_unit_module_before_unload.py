"""
卸载前钩子（on_before_unload）单元测试

2.11 新增行为：卸载流水线第一步触发可选钩子与 module.before_unload 事件，
reason 标注来意（unload / cascade / reload / disable / dormant），钩子失败
仅告警不阻塞卸载。
"""

import asyncio

import pytest

from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.lifecycle import lifecycle
from ErisPulse.Core.module import ModuleManager


def _make_module_class(name: str, calls: list, *, fail_before_unload: bool = False) -> type:
    """构造带 on_before_unload 记录的模块类"""

    class _M(BaseModule):
        async def on_load(self, event):
            calls.append(("load", name))
            return True

        async def on_before_unload(self, event):
            if fail_before_unload:
                raise ValueError("hook boom")
            calls.append(("before_unload", name, event.get("reason")))
            return True

        async def on_unload(self, event):
            calls.append(("unload", name))
            return True

    _M.__name__ = name
    return _M


@pytest.mark.unit
class TestBeforeUnloadHook:
    """on_before_unload 钩子时序与 reason 透传"""

    async def test_hook_runs_before_on_unload(self):
        """普通卸载：钩子在流水线第一步（先于 on_unload），reason=unload"""
        manager = ModuleManager()
        calls: list = []
        manager.register("A", _make_module_class("A", calls))
        assert await manager.load("A") is True
        assert await manager.unload("A") is True
        assert calls == [
            ("load", "A"),
            ("before_unload", "A", "unload"),
            ("unload", "A"),
        ]

    async def test_reason_cascade_for_dependents(self):
        """级联卸载：依赖者 reason=cascade 且先卸载，目标 reason=unload"""
        manager = ModuleManager()
        calls: list = []
        manager.register("Base", _make_module_class("Base", calls))
        manager.register(
            "Dep",
            _make_module_class("Dep", calls),
            {"meta": {"name": "Dep", "depends": ["Base"]}},
        )
        await manager.load("Base")
        await manager.load("Dep")
        await manager.unload("Base")
        assert calls == [
            ("load", "Base"),
            ("load", "Dep"),
            ("before_unload", "Dep", "cascade"),
            ("unload", "Dep"),
            ("before_unload", "Base", "unload"),
            ("unload", "Base"),
        ]

    async def test_reason_reload_via_reload_unload(self):
        """重载路径卸载：reason=reload（经 unload(reason=...) 透传）"""
        manager = ModuleManager()
        calls: list = []
        manager.register("R", _make_module_class("R", calls))
        await manager.load("R")
        await manager.unload("R", reason="reload")
        assert ("before_unload", "R", "reload") in calls

    async def test_reason_disable_fires_in_background(self):
        """禁用路径：钩子以 disable 来意在后台触发（disable 为同步入口）"""
        manager = ModuleManager()
        calls: list = []
        manager.register("D", _make_module_class("D", calls))
        await manager.load("D")
        manager.disable("D")
        await asyncio.sleep(0.15)
        assert ("before_unload", "D", "disable") in calls

    async def test_hook_failure_does_not_block_unload(self):
        """钩子抛异常：仅告警，卸载流程继续完成"""
        manager = ModuleManager()
        calls: list = []
        manager.register("X", _make_module_class("X", calls, fail_before_unload=True))
        await manager.load("X")
        assert await manager.unload("X") is True
        assert manager.is_loaded("X") is False
        # on_unload 仍然执行（卸载未被阻塞）
        assert ("unload", "X") in calls

    async def test_module_without_hook_unloads_normally(self):
        """未声明钩子的模块：卸载行为与旧版一致"""
        manager = ModuleManager()

        class _Plain(BaseModule):
            async def on_load(self, event):
                return True

            async def on_unload(self, event):
                return True

        manager.register("P", _Plain)
        await manager.load("P")
        assert await manager.unload("P") is True
        assert manager.is_loaded("P") is False

    async def test_before_unload_event_payload(self):
        """module.before_unload 事件载荷：module_name + reason"""
        manager = ModuleManager()
        events: list = []

        def _capture(data):
            events.append(dict(data))

        lifecycle.register("module.before_unload", _capture)
        calls: list = []
        manager.register("E", _make_module_class("E", calls))
        try:
            await manager.load("E")
            await manager.unload("E", reason="reload")
        finally:
            lifecycle.unregister("module.before_unload", _capture)
        assert events
        assert events[-1] == {"module_name": "E", "reason": "reload"}
