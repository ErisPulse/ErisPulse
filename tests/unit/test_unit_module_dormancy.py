"""
懒加载休眠（dormancy）单元测试

2.11 新增行为：sleep 归眠释放运行时资源但保留懒代理与注册存根（模块回到
"已注册未加载"状态），唤醒走既有懒初始化路径；状态经 on_before_unload /
on_load 与 storage 接续；清扫器按 dormant_after 阈值自动归眠；懒初始化
失败按 ACTIVATE_RETRY_COOLDOWN_SECS 冷却后可重试。
"""

import time

import pytest

from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.module import ModuleManager
from ErisPulse.loaders.module import LazyModule


class _Sdk:
    """LazyModule 持 SDK 弱引用，桩需支持 weakref"""


def _dormant_class(name: str, state: list, store: dict) -> type:
    """构造带状态接续的模块类：on_before_unload 存计数、on_load 恢复计数"""

    class _Dorm(BaseModule):
        async def on_load(self, event):
            state.append(("load", name))
            self._count = store.get("count", 0)
            return True

        async def on_before_unload(self, event):
            state.append(("before_unload", name, event.get("reason")))
            store["count"] = getattr(self, "_count", 0)
            return True

        async def on_unload(self, event):
            state.append(("unload", name))
            return True

        def current(self):
            return self._count

    _Dorm.__name__ = name
    return _Dorm


def _mount_proxy(manager: ModuleManager, name: str, cls: type, module_info: dict):
    """挂载懒代理（与 initialize_modules 懒路径一致）"""
    sdk = _Sdk()
    proxy = LazyModule(name, cls, sdk, module_info, manager)
    manager.register_lazy(name, proxy)
    setattr(sdk, name, proxy)
    return sdk, proxy


@pytest.mark.unit
class TestDormancy:
    """归眠 / 唤醒 / 状态接续"""

    async def test_sleep_releases_instance_but_keeps_proxy(self):
        """归眠：实例移除、代理保留并重置、sdk 属性保持透明"""
        manager = ModuleManager()
        state: list = []
        store: dict = {}
        cls = _dormant_class("Dorm", state, store)
        manager.register("Dorm", cls)
        sdk, proxy = _mount_proxy(manager, "Dorm", cls, manager._module_info["Dorm"])

        assert await manager.load("Dorm") is True
        assert manager.is_loaded("Dorm")

        assert await manager.sleep("Dorm") is True
        # 实例已移除，代理保留并回到未初始化态
        assert manager.is_loaded("Dorm") is False
        assert manager.get("Dorm") is proxy
        assert proxy._initialized is False
        # sdk 属性仍是代理（透明懒加载语义不破坏）
        assert sdk.Dorm is proxy
        # 钩子按 dormant 来意触发，on_unload 照常执行
        assert ("before_unload", "Dorm", "dormant") in state
        assert ("unload", "Dorm") in state

    async def test_wake_via_attribute_access_restores_state(self):
        """唤醒：属性访问透明触发重新初始化，on_load 恢复归眠前状态"""
        manager = ModuleManager()
        state: list = []
        store: dict = {}
        cls = _dormant_class("Waker", state, store)
        manager.register("Waker", cls)
        sdk, proxy = _mount_proxy(manager, "Waker", cls, manager._module_info["Waker"])

        assert await manager.load("Waker") is True
        instance = manager.get("Waker")
        instance._count = 7

        assert await manager.sleep("Waker") is True
        # 唤醒：访问代理属性 → 重新 load → on_load 从 store 恢复
        assert proxy.current() == 7
        assert manager.is_loaded("Waker") is True
        assert ("load", "Waker") in state

    async def test_sleep_on_not_loaded_module_is_noop(self):
        """未加载模块归眠：直接返回 True（无事可做）"""
        manager = ModuleManager()
        manager.register("Idle", _dormant_class("Idle", [], {}))
        assert await manager.sleep("Idle") is True
        assert manager.is_loaded("Idle") is False

    async def test_sweep_sleeps_module_beyond_threshold(self):
        """清扫：闲置超过阈值 → 自动归眠；未超阈值保持加载"""
        manager = ModuleManager()
        state: list = []
        manager.register("Sleepy", _dormant_class("Sleepy", state, {}))
        manager.register("Active", _dormant_class("Active", state, {}))
        await manager.load("Sleepy")
        await manager.load("Active")

        manager._dormant_after = {"Sleepy": 5, "Active": 3600}
        manager._module_activity["Sleepy"] = time.monotonic() - 100
        manager._module_activity["Active"] = time.monotonic()

        await manager._dormancy_sweep()
        assert manager.is_loaded("Sleepy") is False
        assert manager.is_loaded("Active") is True

    async def test_sweep_initializes_missing_activity(self):
        """无活跃记录的模块：本轮仅补记时间戳，不误归眠"""
        manager = ModuleManager()
        manager.register("Fresh", _dormant_class("Fresh", [], {}))
        await manager.load("Fresh")
        manager._dormant_after = {"Fresh": 1}
        manager._module_activity.pop("Fresh", None)

        await manager._dormancy_sweep()
        assert manager.is_loaded("Fresh") is True
        assert "Fresh" in manager._module_activity

    async def test_clear_resets_dormancy_state(self):
        """clear：休眠状态（活跃表 / 阈值表 / 清扫器标记）一并重置"""
        manager = ModuleManager()
        manager._module_activity["X"] = time.monotonic()
        manager._dormant_after["X"] = 60
        manager._dormancy_sweeper_started = True
        manager.clear()
        assert manager._module_activity == {}
        assert manager._dormant_after == {}
        assert manager._dormancy_sweeper_started is False


@pytest.mark.unit
class TestLazyFailureCooldown:
    """懒初始化失败冷却重试（替代旧的"失败即永久死亡"语义）"""

    def _make_flaky_class(self, calls: list):
        class _Flaky:
            token = "ok"

            def __init__(self, sdk=None):
                calls.append("init")
                if len(calls) == 1:
                    raise ValueError("first init fails")

        return _Flaky

    def test_failure_retries_after_cooldown(self):
        manager = ModuleManager()
        calls: list = []
        cls = self._make_flaky_class(calls)
        manager.register("Flaky", cls)
        _sdk, proxy = _mount_proxy(
            manager, "Flaky", cls, {"meta": {"name": "Flaky", "is_base_module": False}}
        )

        # 首次访问失败 → 类型化异常
        with pytest.raises(Exception):
            proxy.anything
        assert calls == ["init"]

        # 冷却窗口内：短路不重试
        with pytest.raises(Exception):
            proxy.anything
        assert calls == ["init"]

        # 冷却结束：允许重试并成功
        proxy._init_failed_at = time.monotonic() - 9999
        assert proxy.token == "ok"
        assert calls == ["init", "init"]
