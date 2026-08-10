"""
runtime.tasks 后台任务调度单元测试

验证 spawn_background 的三级回退链（当前循环 → 主循环 → 临时循环）、
引用生命周期管理（_background_tasks 自动清理）以及主循环注册的读写。
"""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from ErisPulse.runtime import tasks
from ErisPulse.runtime.tasks import register_main_loop, spawn_background


@pytest.fixture(autouse=True)
def _reset_main_loop():
    """每个用例前后重置主循环注册状态，避免模块级全局态跨用例泄漏"""
    register_main_loop(None)
    yield
    register_main_loop(None)


class TestRegisterMainLoop:
    """register_main_loop / _get_main_loop"""

    def test_register_and_get_roundtrip(self):
        """注册后可读取到同一循环"""
        loop = asyncio.new_event_loop()
        try:
            register_main_loop(loop)
            assert tasks._get_main_loop() is loop
        finally:
            loop.close()

    def test_register_overrides_previous(self):
        """重复注册覆盖为最新值"""
        loop1 = asyncio.new_event_loop()
        loop2 = asyncio.new_event_loop()
        try:
            register_main_loop(loop1)
            assert tasks._get_main_loop() is loop1
            register_main_loop(loop2)
            assert tasks._get_main_loop() is loop2
        finally:
            loop1.close()
            loop2.close()


class TestSpawnBackgroundWithRunningLoop:
    """有运行中事件循环：返回 Task 并追踪引用"""

    @pytest.mark.asyncio
    async def test_returns_task_and_tracks_reference(self):
        """返回 asyncio.Task，加入 _background_tasks 集合"""
        async def work():
            return 1

        task = spawn_background(work())
        assert isinstance(task, asyncio.Task)
        assert task in tasks._background_tasks
        await task
        assert task not in tasks._background_tasks

    @pytest.mark.asyncio
    async def test_done_callback_auto_cleans_reference(self):
        """任务完成后 done_callback 自动从 _background_tasks 移除"""
        async def work():
            return "ok"

        task = spawn_background(work())
        await task
        # 允许 done_callback 执行（回调在同一次循环迭代内调度）
        await asyncio.sleep(0)
        assert task not in tasks._background_tasks

    @pytest.mark.asyncio
    async def test_exception_propagated_via_task(self):
        """协程抛出的异常进入 Task，可被 await 捕获"""
        async def boom():
            raise ValueError("kaboom")

        task = spawn_background(boom())
        assert isinstance(task, asyncio.Task)
        with pytest.raises(ValueError, match="kaboom"):
            await task
        assert task not in tasks._background_tasks


class TestSpawnBackgroundWithoutLoop:
    """无运行中事件循环（同步上下文）的回退链"""

    def test_temporary_loop_when_no_main_loop(self):
        """无主循环时用临时循环同步执行，返回 None"""
        async def work():
            return 42

        with patch.object(tasks, "_get_main_loop", return_value=None):
            result = spawn_background(work())
        assert result is None

    def test_main_loop_route_when_registered_and_running(self):
        """主循环已注册且运行中时走 run_coroutine_threadsafe，返回其 Future"""
        fake_loop = MagicMock()
        fake_loop.is_running.return_value = True

        async def work():
            return 42

        with (
            patch.object(tasks, "_get_main_loop", return_value=fake_loop),
            patch(
                "ErisPulse.runtime.tasks.asyncio.run_coroutine_threadsafe",
                return_value="sched-future",
            ) as rcs,
        ):
            result = spawn_background(work())
        assert result == "sched-future"
        rcs.assert_called_once()

    def test_main_loop_not_running_falls_back_to_temporary(self):
        """主循环已注册但未运行时回退到临时循环，返回 None"""
        fake_loop = MagicMock()
        fake_loop.is_running.return_value = False

        async def work():
            return 7

        with patch.object(tasks, "_get_main_loop", return_value=fake_loop):
            result = spawn_background(work())
        assert result is None

    def test_temporary_loop_actually_executes_coroutine(self):
        """临时循环路径应真正执行协程副作用"""
        flag = {"ran": False}

        async def work():
            flag["ran"] = True

        with patch.object(tasks, "_get_main_loop", return_value=None):
            spawn_background(work())
        assert flag["ran"] is True
