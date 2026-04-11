"""
存储负载压力测试

多线程并发写入 SQLite，验证无数据损坏、无死锁。
"""

import pytest
import threading
import time
from ErisPulse.Core.storage import StorageManager


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


class TestStorageUnderLoadStress:
    def test_20_threads_concurrent_writes(self, stress_storage):
        """20 线程并发写入"""
        errors = []

        def writer(tid):
            try:
                for i in range(200):
                    stress_storage.set(f"t{tid}.k{i}", f"v{tid}_{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        total = len(stress_storage.get_all_keys())
        assert total == 20 * 200

    def test_20_threads_mixed_read_write(self, stress_storage):
        """20 线程混合读写"""
        errors = []

        stress_storage.set("shared", 0)

        def reader(tid):
            try:
                for _ in range(100):
                    val = stress_storage.get("shared", 0)
                    assert isinstance(val, int)
            except Exception as e:
                errors.append(e)

        def writer(tid):
            try:
                for _ in range(100):
                    val = stress_storage.get("shared", 0)
                    stress_storage.set("shared", val + 1)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=reader, args=(i,)) for i in range(10)] + [
            threading.Thread(target=writer, args=(i,)) for i in range(10)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

    def test_10_threads_transaction_writes(self, stress_storage):
        """10 线程事务写入"""
        errors = []

        def transaction_writer(tid):
            try:
                for i in range(50):
                    with stress_storage.transaction():
                        for j in range(10):
                            stress_storage.set(f"tx.{tid}.{i}.{j}", f"v{j}")
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=transaction_writer, args=(i,)) for i in range(10)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        total = len(stress_storage.get_all_keys())
        assert total == 10 * 50 * 10

    def test_rapid_set_delete_1000_cycles(self, stress_storage):
        """1000 次 set-delete 循环"""
        errors = []

        def cycle_worker(tid):
            try:
                for i in range(100):
                    key = f"cycle.{tid}.{i}"
                    stress_storage.set(key, f"val_{i}")
                    stress_storage.delete(key)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=cycle_worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

    def test_large_value_writes(self, stress_storage):
        """大值写入"""
        large_value = "x" * 100000

        for i in range(50):
            stress_storage.set(f"large.{i}", large_value)

        for i in range(50):
            val = stress_storage.get(f"large.{i}")
            assert val == large_value

    def test_concurrent_batch_operations(self, stress_storage):
        """并发批量操作"""
        errors = []

        def batch_worker(tid):
            try:
                items = {f"batch.{tid}.{i}": f"v{i}" for i in range(100)}
                stress_storage.set_multi(items)

                keys = [f"batch.{tid}.{i}" for i in range(100)]
                result = stress_storage.get_multi(keys)
                assert len(result) == 100

                stress_storage.delete_multi(keys)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=batch_worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

    def test_clear_under_load(self, stress_storage):
        """负载下 clear 操作"""
        errors = []

        def writer(tid):
            try:
                for i in range(100):
                    stress_storage.set(f"load.{tid}.{i}", f"v{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        before_clear = len(stress_storage.get_all_keys())
        assert before_clear > 0

        stress_storage.clear()
        assert len(stress_storage.get_all_keys()) == 0

    def test_no_deadlock_concurrent_transactions(self, stress_storage):
        """并发事务无死锁（设定超时）"""
        errors = []
        completed = []

        def transaction_worker(tid):
            try:
                for i in range(50):
                    with stress_storage.transaction():
                        stress_storage.set(f"no_deadlock.{tid}.{i}", i)
                completed.append(tid)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=transaction_worker, args=(i,)) for i in range(10)
        ]
        for t in threads:
            t.start()

        for t in threads:
            t.join(timeout=30)

        assert len(errors) == 0
        assert len(completed) == 10
