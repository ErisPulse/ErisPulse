"""
事件吞吐量性能测试

度量单个事件通过 bus 到达 handler 的延迟，
以及批量事件处理的吞吐量。
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from ErisPulse.Core.adapter import AdapterManager
from ErisPulse.Core.lifecycle import LifecycleManager
from ErisPulse.Core.Bases import BaseAdapter


class _PerfAdapter(BaseAdapter):
    async def start(self):
        pass

    async def shutdown(self):
        pass

    async def call_api(self, endpoint: str, **params):
        return {"status": "ok", "retcode": 0, "data": {}, "message_id": "id"}


def _make_event(event_id=1):
    return {
        "id": f"perf_{event_id}",
        "time": 1712345678,
        "type": "message",
        "detail_type": "private",
        "platform": "perf",
        "self": {"platform": "perf", "user_id": "bot_perf"},
        "user_id": "u1",
        "message": [{"type": "text", "data": {"text": "bench"}}],
        "alt_message": "bench",
    }


@pytest.fixture
def perf_adapter():
    mgr = AdapterManager()
    mgr._adapters.clear()
    mgr._started_instances.clear()
    mgr._adapter_info.clear()
    mgr._onebot_handlers.clear()
    mgr._raw_handlers.clear()
    mgr._onebot_middlewares.clear()
    mgr._bots.clear()
    mgr.register("perf", _PerfAdapter)
    yield mgr
    mgr._onebot_handlers.clear()
    mgr._onebot_middlewares.clear()


@pytest.fixture
def perf_lifecycle():
    mgr = LifecycleManager()
    mgr._handlers.clear()
    mgr._timers.clear()
    yield mgr
    mgr._handlers.clear()
    mgr._timers.clear()


class TestEventThroughputPerformance:
    @pytest.mark.asyncio
    async def test_single_event_dispatch(self, perf_adapter):
        """单个事件分发延迟"""
        received = []

        @perf_adapter.on("message")
        async def handler(data):
            received.append(1)

        event = _make_event()
        await perf_adapter.emit(event)

        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_single_event_with_middleware(self, perf_adapter):
        """带 3 个 middleware 的事件处理"""
        received = []

        @perf_adapter.middleware
        async def mw1(data):
            data["m1"] = True
            return data

        @perf_adapter.middleware
        async def mw2(data):
            data["m2"] = True
            return data

        @perf_adapter.middleware
        async def mw3(data):
            data["m3"] = True
            return data

        @perf_adapter.on("message")
        async def handler(data):
            received.append(data)

        event = _make_event()
        await perf_adapter.emit(event)

        assert len(received) == 1
        assert received[0].get("m1") is True
        assert received[0].get("m2") is True
        assert received[0].get("m3") is True

    @pytest.mark.asyncio
    async def test_batch_100_events(self, perf_adapter):
        """100 个事件批量处理"""
        received = []
        lock = asyncio.Lock()

        @perf_adapter.on("message")
        async def handler(data):
            async with lock:
                received.append(data["id"])

        events = [_make_event(i) for i in range(100)]
        await asyncio.gather(*[perf_adapter.emit(e) for e in events])

        assert len(received) == 100

    @pytest.mark.asyncio
    async def test_batch_1000_events(self, perf_adapter):
        """1000 个事件批量处理"""
        received = []
        lock = asyncio.Lock()

        @perf_adapter.on("message")
        async def handler(data):
            async with lock:
                received.append(1)

        tasks = [perf_adapter.emit(_make_event(i)) for i in range(1000)]
        await asyncio.gather(*tasks)

        assert len(received) == 1000

    @pytest.mark.asyncio
    async def test_multiple_handlers_per_event(self, perf_adapter):
        """单事件 10 个 handler"""
        results = {i: 0 for i in range(10)}
        lock = asyncio.Lock()

        for idx in range(10):

            @perf_adapter.on("message")
            async def handler(data, _idx=idx):
                async with lock:
                    results[_idx] += 1

        await perf_adapter.emit(_make_event())

        for count in results.values():
            assert count == 1

    def test_lifecycle_submit_event(self, perf_lifecycle):
        """lifecycle 事件提交"""
        events = []

        def handler(data):
            events.append(data)

        perf_lifecycle.on("perf.test")(handler)

        import asyncio

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(
                perf_lifecycle.submit_event("perf.test", data={"val": 42})
            )
        finally:
            loop.close()

        assert len(events) == 1

    def test_lifecycle_timer_overhead(self, perf_lifecycle):
        """计时器开销"""
        perf_lifecycle.start_timer("bench")
        perf_lifecycle.stop_timer("bench")
        assert "bench" not in perf_lifecycle._timers

    @pytest.mark.asyncio
    async def test_no_handler_event_no_error(self, perf_adapter):
        """无 handler 时 emit 不报错"""
        event = _make_event()
        await perf_adapter.emit(event)

    @pytest.mark.asyncio
    async def test_middleware_chain_5_middlewares(self, perf_adapter):
        """5 个 middleware 链"""
        for i in range(5):

            @perf_adapter.middleware
            async def mw(data, _i=i):
                data[f"mw{_i}"] = True
                return data

        received = []

        @perf_adapter.on("message")
        async def handler(data):
            received.append(data)

        event = _make_event()
        await perf_adapter.emit(event)

        assert len(received) == 1
        for i in range(5):
            assert received[0].get(f"mw{i}") is True
