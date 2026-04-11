"""
性能测试专用 fixtures
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from ErisPulse.Core.adapter import AdapterManager
from ErisPulse.Core.lifecycle import LifecycleManager
from ErisPulse.Core.storage import StorageManager
from ErisPulse.Core.Bases import BaseAdapter


class _BenchAdapter(BaseAdapter):
    async def start(self):
        pass

    async def shutdown(self):
        pass

    async def call_api(self, endpoint: str, **params):
        return {"status": "ok", "retcode": 0, "data": {}, "message_id": "id"}


@pytest.fixture
def bench_adapter():
    mgr = AdapterManager()
    mgr._adapters.clear()
    mgr._started_instances.clear()
    mgr._adapter_info.clear()
    mgr._onebot_handlers.clear()
    mgr._raw_handlers.clear()
    mgr._onebot_middlewares.clear()
    mgr._bots.clear()
    mgr.register("bench", _BenchAdapter)
    return mgr


@pytest.fixture
def bench_lifecycle():
    mgr = LifecycleManager()
    mgr._handlers.clear()
    mgr._timers.clear()
    return mgr


@pytest.fixture
def bench_storage(tmp_path):
    db_file = str(tmp_path / "bench.db")

    class TempStorage(StorageManager):
        def __init__(self):
            self._initialized = False
            self.db_path = db_file
            self._local = self._local.__class__()
            self._init_db()
            self._initialized = True

    return TempStorage()


@pytest.fixture
def bench_router_client():
    from fastapi.testclient import TestClient
    from ErisPulse.Core.router import RouterManager

    mgr = RouterManager()
    client = TestClient(mgr.app)
    return client, mgr
