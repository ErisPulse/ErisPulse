"""
压力测试专用 fixtures
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from ErisPulse.Core.adapter import AdapterManager
from ErisPulse.Core.storage import StorageManager
from ErisPulse.Core.Bases import BaseAdapter


class _StressAdapter(BaseAdapter):
    async def start(self):
        pass

    async def shutdown(self):
        pass

    async def call_api(self, endpoint: str, **params):
        return {"status": "ok", "retcode": 0, "data": {}, "message_id": "id"}


@pytest.fixture
def stress_adapter():
    mgr = AdapterManager()
    mgr._adapters.clear()
    mgr._started_instances.clear()
    mgr._adapter_info.clear()
    mgr._onebot_handlers.clear()
    mgr._raw_handlers.clear()
    mgr._onebot_middlewares.clear()
    mgr._bots.clear()
    mgr.register("stress", _StressAdapter)
    yield mgr
    mgr._onebot_handlers.clear()
    mgr._onebot_middlewares.clear()


@pytest.fixture
def stress_storage(tmp_path):
    db_file = str(tmp_path / "stress.db")

    class TempStorage(StorageManager):
        def __init__(self):
            self._initialized = False
            self.db_path = db_file
            self._local = self._local.__class__()
            self._init_db()
            self._initialized = True

    return TempStorage()


@pytest.fixture
def stress_router():
    from ErisPulse.Core.router import RouterManager

    mgr = RouterManager()
    mgr._http_routes.clear()
    mgr._websocket_routes.clear()
    return mgr
