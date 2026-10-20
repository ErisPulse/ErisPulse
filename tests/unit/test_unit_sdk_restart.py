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
