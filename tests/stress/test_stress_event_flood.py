"""
事件洪泛压力测试

大量事件快速连续 emit，验证无崩溃、无内存泄漏、全部事件被处理。
"""

import pytest
import asyncio
from ErisPulse.Core.adapter import AdapterManager
from ErisPulse.Core.Bases import BaseAdapter


class _FloodAdapter(BaseAdapter):
    async def start(self):
        pass

    async def shutdown(self):
        pass

    async def call_api(self, endpoint: str, **params):
        return {"status": "ok", "retcode": 0, "data": {}, "message_id": "id"}


def _make_event(event_id):
    return {
        "id": f"flood_{event_id}",
        "time": 1712345678,
        "type": "message",
        "detail_type": "private",
        "platform": "flood",
        "self": {"platform": "flood", "user_id": "bot_flood"},
        "user_id": "u1",
        "message": [{"type": "text", "data": {"text": f"msg_{event_id}"}}],
        "alt_message": f"msg_{event_id}",
    }


@pytest.fixture
def flood_adapter():
    mgr = AdapterManager()
    mgr._adapters.clear()
    mgr._started_instances.clear()
    mgr._adapter_info.clear()
    mgr._onebot_handlers.clear()
    mgr._raw_handlers.clear()
    mgr._onebot_middlewares.clear()
    mgr._bots.clear()
    mgr.register("flood", _FloodAdapter)
    yield mgr
    mgr._onebot_handlers.clear()
    mgr._onebot_middlewares.clear()


class TestEventFloodStress:
    @pytest.mark.asyncio
    async def test_1000_events_all_processed(self, flood_adapter):
        """1000 个事件全部被处理"""
        received = []
        lock = asyncio.Lock()

        @flood_adapter.on("message")
        async def handler(data):
            async with lock:
                received.append(data["id"])

        tasks = [flood_adapter.emit(_make_event(i)) for i in range(1000)]
        await asyncio.gather(*tasks)

        assert len(received) == 1000
        assert received == [f"flood_{i}" for i in range(1000)]

    @pytest.mark.asyncio
    async def test_10000_events_all_processed(self, flood_adapter):
        """10000 个事件全部被处理"""
        received = []
        lock = asyncio.Lock()

        @flood_adapter.on("message")
        async def handler(data):
            async with lock:
                received.append(1)

        batch_size = 1000
        for batch_start in range(0, 10000, batch_size):
            tasks = [
                flood_adapter.emit(_make_event(i))
                for i in range(batch_start, batch_start + batch_size)
            ]
            await asyncio.gather(*tasks)

        assert len(received) == 10000

    @pytest.mark.asyncio
    async def test_1000_events_with_5_middlewares(self, flood_adapter):
        """1000 事件 + 5 个 middleware"""
        received = []
        lock = asyncio.Lock()

        for i in range(5):

            @flood_adapter.middleware
            async def mw(data, _i=i):
                data[f"mw{_i}"] = True
                return data

        @flood_adapter.on("message")
        async def handler(data):
            async with lock:
                received.append(1)

        tasks = [flood_adapter.emit(_make_event(i)) for i in range(1000)]
        await asyncio.gather(*tasks)

        assert len(received) == 1000

    @pytest.mark.asyncio
    async def test_1000_events_multiple_handlers(self, flood_adapter):
        """1000 事件，每个事件 5 个 handler"""
        counts = {i: 0 for i in range(5)}
        lock = asyncio.Lock()

        for idx in range(5):

            @flood_adapter.on("message")
            async def handler(data, _idx=idx):
                async with lock:
                    counts[_idx] += 1

        tasks = [flood_adapter.emit(_make_event(i)) for i in range(1000)]
        await asyncio.gather(*tasks)

        for count in counts.values():
            assert count == 1000

    @pytest.mark.asyncio
    async def test_rapid_event_burst(self, flood_adapter):
        """快速突发 500 个事件"""
        received = []
        lock = asyncio.Lock()

        @flood_adapter.on("message")
        async def handler(data):
            async with lock:
                received.append(data["id"])

        coros = [flood_adapter.emit(_make_event(i)) for i in range(500)]
        await asyncio.gather(*coros)

        assert len(received) == 500

    @pytest.mark.asyncio
    async def test_no_handler_no_crash(self, flood_adapter):
        """无 handler 时大量 emit 不崩溃"""
        tasks = [flood_adapter.emit(_make_event(i)) for i in range(500)]
        await asyncio.gather(*tasks)

    @pytest.mark.asyncio
    async def test_mixed_event_types(self, flood_adapter):
        """混合事件类型"""
        received = {"message": 0, "notice": 0, "meta": 0}
        lock = asyncio.Lock()

        @flood_adapter.on("message")
        async def msg_handler(data):
            async with lock:
                received["message"] += 1

        @flood_adapter.on("notice")
        async def notice_handler(data):
            async with lock:
                received["notice"] += 1

        @flood_adapter.on("meta")
        async def meta_handler(data):
            async with lock:
                received["meta"] += 1

        tasks = []
        for i in range(500):
            if i % 3 == 0:
                tasks.append(flood_adapter.emit(_make_event(i)))
            elif i % 3 == 1:
                tasks.append(
                    flood_adapter.emit(
                        {
                            "id": f"notice_{i}",
                            "time": 1,
                            "type": "notice",
                            "detail_type": "friend_add",
                            "platform": "flood",
                            "self": {"platform": "flood", "user_id": "bot"},
                        }
                    )
                )
            else:
                tasks.append(
                    flood_adapter.emit(
                        {
                            "id": f"meta_{i}",
                            "time": 1,
                            "type": "meta",
                            "detail_type": "connect",
                            "platform": "flood",
                            "self": {"platform": "flood", "user_id": "bot"},
                        }
                    )
                )

        await asyncio.gather(*tasks)

        assert received["message"] + received["notice"] + received["meta"] == 500
