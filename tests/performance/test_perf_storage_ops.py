"""
存储操作性能测试

度量 storage set/get/delete/batch/transaction 的操作性能。
"""

import pytest
import threading
from ErisPulse.Core.storage import StorageManager


@pytest.fixture
def perf_storage(tmp_path):
    db_file = str(tmp_path / "perf_storage.db")

    class TempStorage(StorageManager):
        def __init__(self):
            self._initialized = False
            self.db_path = db_file
            self._local = self._local.__class__()
            self._init_db()
            self._initialized = True

    return TempStorage()


class TestStorageOpsPerformance:
    def test_single_set_get(self, perf_storage):
        perf_storage.set("key", "value")
        assert perf_storage.get("key") == "value"

    def test_single_delete(self, perf_storage):
        perf_storage.set("key", "value")
        assert perf_storage.delete("key") is True
        assert perf_storage.get("key") is None

    def test_batch_set_100(self, perf_storage):
        for i in range(100):
            perf_storage.set(f"batch.key_{i}", f"value_{i}")

        for i in range(100):
            assert perf_storage.get(f"batch.key_{i}") == f"value_{i}"

    def test_batch_set_1000(self, perf_storage):
        for i in range(1000):
            perf_storage.set(f"large.key_{i}", i)

        assert len(perf_storage.get_all_keys()) == 1000

    def test_set_multi_100(self, perf_storage):
        items = {f"multi.key_{i}": f"value_{i}" for i in range(100)}
        perf_storage.set_multi(items)

        assert len(perf_storage.get_all_keys()) == 100

    def test_get_multi_100(self, perf_storage):
        for i in range(100):
            perf_storage.set(f"gm.key_{i}", f"val_{i}")

        keys = [f"gm.key_{i}" for i in range(100)]
        result = perf_storage.get_multi(keys)
        assert len(result) == 100

    def test_delete_multi_100(self, perf_storage):
        for i in range(100):
            perf_storage.set(f"dm.key_{i}", f"val_{i}")

        keys = [f"dm.key_{i}" for i in range(100)]
        perf_storage.delete_multi(keys)

        assert len(perf_storage.get_all_keys()) == 0

    def test_transaction_commit_100_keys(self, perf_storage):
        with perf_storage.transaction():
            for i in range(100):
                perf_storage.set(f"tx.key_{i}", f"value_{i}")

        assert len(perf_storage.get_all_keys()) == 100

    def test_transaction_rollback(self, perf_storage):
        perf_storage.set("before", "exists")

        try:
            with perf_storage.transaction():
                for i in range(50):
                    perf_storage.set(f"tx.key_{i}", f"value_{i}")
                raise ValueError("rollback")
        except ValueError:
            pass

        assert perf_storage.get("before") == "exists"
        for i in range(50):
            assert perf_storage.get(f"tx.key_{i}") is None

    def test_nested_transaction(self, perf_storage):
        """嵌套事务复用连接"""
        with perf_storage.transaction():
            perf_storage.set("outer", "1")
            with perf_storage.transaction():
                perf_storage.set("inner", "2")

        assert perf_storage.get("outer") == "1"
        assert perf_storage.get("inner") == "2"

    def test_complex_value_serialization(self, perf_storage):
        complex_data = {
            "list": [1, 2, 3, 4, 5],
            "dict": {"nested": {"deep": True}},
            "mixed": [{"a": 1}, {"b": 2}],
        }
        perf_storage.set("complex", complex_data)
        result = perf_storage.get("complex")
        assert result == complex_data

    def test_clear_performance(self, perf_storage):
        for i in range(500):
            perf_storage.set(f"clear.key_{i}", f"val_{i}")

        assert len(perf_storage.get_all_keys()) == 500
        perf_storage.clear()
        assert len(perf_storage.get_all_keys()) == 0

    def test_concurrent_writes_10_threads(self, perf_storage):
        """10 线程并发写入"""
        errors = []

        def writer(tid):
            try:
                for i in range(100):
                    perf_storage.set(f"cw.{tid}.{i}", f"v_{tid}_{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(perf_storage.get_all_keys()) == 1000

    def test_rapid_set_delete_cycle(self, perf_storage):
        """快速 set-delete 循环"""
        for i in range(500):
            perf_storage.set(f"cycle.key", f"value_{i}")
            assert perf_storage.get("cycle.key") == f"value_{i}"
            perf_storage.delete("cycle.key")
            assert perf_storage.get("cycle.key") is None

    def test_attribute_access_performance(self, perf_storage):
        perf_storage.set("attr_test", "value")
        val = perf_storage.attr_test
        assert val == "value"
