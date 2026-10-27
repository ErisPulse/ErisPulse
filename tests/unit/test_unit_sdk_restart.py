"""
SDK 软重启（联动热重载系统）单元测试

2.11 起 ``restart()`` 语义 = 组件层代码级热重载：全部模块走
``reload_all_modules`` 统一管线、全部适配器逐个 ``reload_adapter``，
不再整体 uninit/init。本文件验证编排顺序、失败聚合与异常兜底。
"""

import asyncio

import pytest

from ErisPulse import SDK


@pytest.fixture
def sdk():
    """构造已初始化的 SDK（与 CLI run 等价的最小形态）"""
    sdk = SDK()
    sdk.Initializer(sdk)
    yield sdk


@pytest.mark.unit
class TestSoftRestart:
    """软重启编排（联动热重载系统）"""

    async def test_restart_orchestrates_modules_and_adapters(self, sdk, monkeypatch):
        """全部模块 + 全部适配器逐个走热重载管线"""
        calls: dict = {}

        async def fake_reload_all():
            calls["modules"] = True
            return {"A": True, "B": True}

        async def fake_reload_adapter(name, **kwargs):
            calls.setdefault("adapters", []).append(name)
            return True

        monkeypatch.setattr(sdk, "reload_all_modules", fake_reload_all)
        monkeypatch.setattr(sdk, "reload_adapter", fake_reload_adapter)
        monkeypatch.setattr(
            sdk.adapter, "_adapter_info", {"aiocqhttp": {"meta": {}}, "telegram": {"meta": {}}}
        )

        assert await sdk._do_restart() is True
        assert calls.get("modules") is True
        assert sorted(calls.get("adapters") or []) == ["aiocqhttp", "telegram"]

    async def test_partial_failure_returns_false(self, sdk, monkeypatch):
        """任一模块失败 → 软重启判定为失败（失败清单进日志）"""

        async def fake_reload_all():
            return {"A": True, "B": False}

        async def fake_reload_adapter(name, **kwargs):
            return True

        monkeypatch.setattr(sdk, "reload_all_modules", fake_reload_all)
        monkeypatch.setattr(sdk, "reload_adapter", fake_reload_adapter)
        monkeypatch.setattr(sdk.adapter, "_adapter_info", {})

        assert await sdk._do_restart() is False

    async def test_adapter_error_does_not_break_chain(self, sdk, monkeypatch):
        """单个适配器重载抛异常：记录失败并继续其余适配器"""
        calls: dict = {}

        async def fake_reload_all():
            return {"A": True}

        async def fake_reload_adapter(name, **kwargs):
            calls.setdefault("adapters", []).append(name)
            if name == "bad":
                raise RuntimeError("adapter boom")
            return True

        monkeypatch.setattr(sdk, "reload_all_modules", fake_reload_all)
        monkeypatch.setattr(sdk, "reload_adapter", fake_reload_adapter)
        monkeypatch.setattr(
            sdk.adapter, "_adapter_info", {"bad": {"meta": {}}, "good": {"meta": {}}}
        )

        assert await sdk._do_restart() is False
        assert sorted(calls.get("adapters") or []) == ["bad", "good"]

    async def test_restart_schedules_background_task(self, sdk, monkeypatch):
        """restart() 立即返回 True（后台调度语义），实际执行交给 _do_restart"""
        started = asyncio.Event()

        async def fake_do_restart():
            started.set()
            return True

        monkeypatch.setattr(sdk, "_do_restart", fake_do_restart)
        assert await sdk.restart() is True
        # 后台任务被调度执行（等待其完成标志）
        for _ in range(100):
            if started.is_set():
                break
            await asyncio.sleep(0.01)
        assert started.is_set()


@pytest.mark.unit
class TestDumpStateRouterFields:
    """dump_state 的 router 段字段须与 RouterManager 实际属性对齐（防字段漂移回归）"""

    def test_router_section_reflects_real_attributes(self, sdk):
        state = sdk.dump_state()
        router_state = state["router"]
        # 未启动服务：running 为 False 而非字段不存在导致的恒 False 误报
        assert router_state.get("running") is False
        # 路由计数为非负整数（按路径累计），而非命名空间数或恒 0
        assert isinstance(router_state.get("http_routes"), int)
        assert router_state["http_routes"] >= 0
        assert isinstance(router_state.get("ws_routes"), int)
        assert router_state["ws_routes"] >= 0
        assert "error" not in router_state


@pytest.mark.unit
class TestRestartPrecheckRejection:
    """模块整体预检拒绝：整轮闭环（适配器层跳过 + 判定失败）"""

    async def test_precheck_rejected_skips_adapters_and_fails(self, sdk, monkeypatch):
        """预检拒绝：适配器不重载（避免无谓断连）、restart 返回 False"""
        calls: dict = {}

        async def fake_reload_all():
            calls["modules"] = True
            return {}

        async def fake_reload_adapter(name, **kwargs):
            calls.setdefault("adapters", []).append(name)
            return True

        async def fake_adapter_load(manager, quiet=True):
            calls["adapter_rediscover"] = True
            return {}, {}, []

        monkeypatch.setattr(sdk, "reload_all_modules", fake_reload_all)
        monkeypatch.setattr(sdk, "reload_adapter", fake_reload_adapter)
        monkeypatch.setattr(sdk, "_adapter_loader", types_stub_loader(fake_adapter_load))
        monkeypatch.setattr(
            sdk.adapter, "_adapter_info", {"aiocqhttp": {"meta": {}}}
        )
        # 预检拒绝标记（reload_all 管线置位）
        monkeypatch.setattr(
            sdk._module_loader, "_last_reload_all_rejected", True, raising=False
        )

        assert await sdk._do_restart() is False
        # 模块层执行过、适配器层完全未被触碰
        assert calls.get("modules") is True
        assert "adapters" not in calls
        assert "adapter_rediscover" not in calls


def types_stub_loader(load_fn):
    """最小适配器加载器桩（只需 load 方法）"""
    import types as _types

    stub = _types.SimpleNamespace()
    stub.load = load_fn
    return stub


@pytest.mark.unit
class TestHotLoadMutex:
    """全新插件热装载（on_created）进入热重载互斥"""

    async def test_hot_load_runs_inside_exclusive_lock(self, sdk, monkeypatch):
        """load_new_plugin 执行时互斥锁被持有（与 restart/reload 串行）"""
        from ErisPulse.runtime.reload_ops import reload_ops

        lock_held: list[bool] = []

        async def fake_load_new_plugin(name, manager, sdk_inst):
            lock_held.append(reload_ops.is_locked())
            return True

        assert "brand_new_hotplug" not in (
            getattr(sdk._module_loader, "_last_module_objs", {}) or {}
        )
        monkeypatch.setattr(sdk._module_loader, "load_new_plugin", fake_load_new_plugin)

        ok = await sdk._reload_module("brand_new_hotplug")
        assert ok is True
        assert lock_held == [True], "热装载未在热重载互斥区内执行"
