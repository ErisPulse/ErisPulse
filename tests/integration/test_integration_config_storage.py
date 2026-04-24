"""
配置与存储集成测试

测试 ConfigManager + StorageManager 联合操作、事务回滚、并发读写。
"""

import pytest
import threading
import time
from unittest.mock import patch

from ErisPulse.Core.config import ConfigManager
from ErisPulse.Core.storage import StorageManager


@pytest.fixture
def temp_config(tmp_path):
    config_file = str(tmp_path / "config.toml")
    (tmp_path / "config.toml").write_text(
        """
[test]
key1 = "value1"
key2 = 42

[test.nested]
a = 1
b = 2
""",
        encoding="utf-8",
    )
    return ConfigManager(config_file=config_file)


@pytest.fixture
def temp_storage(tmp_path):
    db_file = str(tmp_path / "test.db")

    class TempStorage(StorageManager):
        _instance = None

        def __new__(cls, *args, **kwargs):
            return super(StorageManager, cls).__new__(cls)

        def __init__(self):
            self._initialized = False
            self.db_path = db_file
            self._local = threading.local()
            self._init_db()
            self._initialized = True

    return TempStorage()


class TestConfigStorageIntegration:
    """配置与存储集成测试"""

    def test_config_read_nested_key(self, temp_config):
        value = temp_config.getConfig("test.key1")
        assert value == "value1"

    def test_config_read_default(self, temp_config):
        value = temp_config.getConfig("nonexistent.key", "default_val")
        assert value == "default_val"

    def test_config_set_and_read(self, temp_config):
        temp_config.setConfig("new_section.new_key", "new_value", immediate=True)
        value = temp_config.getConfig("new_section.new_key")
        assert value == "new_value"

    def test_config_overwrite_value(self, temp_config):
        temp_config.setConfig("test.key1", "updated", immediate=True)
        value = temp_config.getConfig("test.key1")
        assert value == "updated"

    def test_storage_set_and_get(self, temp_storage):
        temp_storage.set("test.key", "test_value")
        assert temp_storage.get("test.key") == "test_value"

    def test_storage_default(self, temp_storage):
        assert temp_storage.get("nonexistent", "default") == "default"

    def test_storage_complex_value(self, temp_storage):
        complex_val = {"nested": {"a": [1, 2, 3], "b": True}}
        temp_storage.set("complex", complex_val)
        result = temp_storage.get("complex")
        assert result == complex_val

    def test_storage_delete(self, temp_storage):
        temp_storage.set("to_delete", "value")
        assert temp_storage.get("to_delete") == "value"

        temp_storage.delete("to_delete")
        assert temp_storage.get("to_delete") is None

    def test_storage_get_all_keys(self, temp_storage):
        temp_storage.set("k1", "v1")
        temp_storage.set("k2", "v2")
        temp_storage.set("k3", "v3")

        keys = temp_storage.get_all_keys()
        assert "k1" in keys
        assert "k2" in keys
        assert "k3" in keys

    def test_storage_batch_operations(self, temp_storage):
        temp_storage.set_multi(
            {
                "batch.k1": "v1",
                "batch.k2": "v2",
                "batch.k3": "v3",
            }
        )
        assert temp_storage.get("batch.k1") == "v1"
        assert temp_storage.get("batch.k2") == "v2"
        assert temp_storage.get("batch.k3") == "v3"

        temp_storage.delete_multi(["batch.k1", "batch.k2"])
        assert temp_storage.get("batch.k1") is None
        assert temp_storage.get("batch.k2") is None
        assert temp_storage.get("batch.k3") == "v3"

    def test_storage_get_multi(self, temp_storage):
        temp_storage.set("gm1", "a")
        temp_storage.set("gm2", "b")
        temp_storage.set("gm3", "c")

        result = temp_storage.get_multi(["gm1", "gm2", "gm_nonexist"])
        assert result["gm1"] == "a"
        assert result["gm2"] == "b"
        assert result.get("gm_nonexist") is None

    def test_storage_transaction_commit(self, temp_storage):
        with temp_storage.transaction():
            temp_storage.set("tx.k1", "v1")
            temp_storage.set("tx.k2", "v2")

        assert temp_storage.get("tx.k1") == "v1"
        assert temp_storage.get("tx.k2") == "v2"

    def test_storage_transaction_rollback(self, temp_storage):
        temp_storage.set("tx.before", "exists")

        try:
            with temp_storage.transaction():
                temp_storage.set("tx.k1", "v1")
                temp_storage.set("tx.k2", "v2")
                raise ValueError("force rollback")
        except ValueError:
            pass

        assert temp_storage.get("tx.before") == "exists"
        assert temp_storage.get("tx.k1") is None
        assert temp_storage.get("tx.k2") is None

    def test_storage_clear(self, temp_storage):
        temp_storage.set("k1", "v1")
        temp_storage.set("k2", "v2")
        temp_storage.clear()
        assert temp_storage.get_all_keys() == []

    def test_concurrent_storage_writes(self, temp_storage):
        """多线程并发写入"""
        errors = []
        num_threads = 10
        writes_per_thread = 50

        def write_thread(thread_id):
            try:
                for i in range(writes_per_thread):
                    key = f"thread.{thread_id}.{i}"
                    temp_storage.set(key, f"value_{thread_id}_{i}")
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=write_thread, args=(tid,))
            for tid in range(num_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        total_keys = temp_storage.get_all_keys()
        assert len(total_keys) == num_threads * writes_per_thread

    def test_concurrent_reads_and_writes(self, temp_storage):
        """并发读写（注意：非原子操作，最终值 <= 理论值）"""
        errors = []

        def writer():
            try:
                for _ in range(100):
                    val = temp_storage.get("counter", 0)
                    temp_storage.set("counter", val + 1)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        final_val = temp_storage.get("counter", 0)
        assert final_val <= 500
        assert final_val > 0

    def test_storage_attribute_access(self, temp_storage):
        """通过属性访问存储项"""
        temp_storage.set("my_key", "my_value")
        assert temp_storage.my_key == "my_value"

    def test_storage_attribute_not_found(self, temp_storage):
        with pytest.raises(AttributeError):
            _ = temp_storage.nonexistent_key
