"""
后台任务待发队列单元测试

覆盖主循环缺失时入队、register_main_loop 冲队列、队列上限、
按 owner 清理与退出滞留告警。
"""

import asyncio

import pytest

from ErisPulse.runtime import tasks as tasks_module


@pytest.fixture(autouse=True)
def _reset_task_state():
    tasks_module._MAIN_LOOP = None
    tasks_module._PENDING_TASKS.clear()
    tasks_module._owner_tasks.clear()
    tasks_module._background_tasks.clear()
    yield
    for awaitable, _ in list(tasks_module._PENDING_TASKS):
        tasks_module._close_awaitable(awaitable)
    tasks_module._PENDING_TASKS.clear()
    tasks_module._MAIN_LOOP = None
    tasks_module._owner_tasks.clear()
    tasks_module._background_tasks.clear()


def test_spawn_background_queues_without_loop():
    coro = asyncio.sleep(0)
    assert tasks_module.spawn_background(coro) is None
    assert len(tasks_module._PENDING_TASKS) == 1


def test_run_main_loop_queues_without_loop():
    coro = asyncio.sleep(0, result=1)
    assert tasks_module.run_main_loop(coro) is None
    assert len(tasks_module._PENDING_TASKS) == 1


def test_register_main_loop_drains_queue():
    box = {"done": False}

    async def work():
        box["done"] = True

    tasks_module.spawn_background(work())
    loop = asyncio.new_event_loop()
    try:
        tasks_module.register_main_loop(loop)
        loop.run_until_complete(asyncio.sleep(0.05))
    finally:
        loop.close()
    assert box["done"] is True
    assert len(tasks_module._PENDING_TASKS) == 0


def test_queue_full_drops_new_task(monkeypatch, caplog):
    monkeypatch.setattr(tasks_module, "PENDING_TASK_QUEUE_MAX", 1)
    assert tasks_module.spawn_background(asyncio.sleep(0)) is None
    assert tasks_module.spawn_background(asyncio.sleep(0)) is None
    assert len(tasks_module._PENDING_TASKS) == 1
    assert "队列已满" in caplog.text


async def test_cancel_owner_tasks_drops_pending():
    assert tasks_module._enqueue_pending(asyncio.sleep(0), "ModA") is True
    assert len(tasks_module._PENDING_TASKS) == 1
    cancelled = await tasks_module.cancel_owner_tasks("ModA")
    assert cancelled == 1
    assert len(tasks_module._PENDING_TASKS) == 0


async def test_cancel_all_background_tasks_drops_pending(caplog):
    assert tasks_module._enqueue_pending(asyncio.sleep(0), "ModA") is True
    assert tasks_module._enqueue_pending(asyncio.sleep(0), "ModB") is True
    total = await tasks_module.cancel_all_background_tasks()
    assert total == 2
    assert len(tasks_module._PENDING_TASKS) == 0
    assert "待发后台任务" in caplog.text
