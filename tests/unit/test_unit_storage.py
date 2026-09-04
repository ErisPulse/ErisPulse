"""
存储管理单元测试

测试StorageManager的键值存储和事务功能
"""

import os
import sqlite3
import tempfile
from unittest.mock import patch

import pytest

from ErisPulse.Core.storage import StorageManager, storage

# ==================== StorageManager 基础测试 ====================


class TestStorageManager:
    """存储管理器测试类"""

    @pytest.fixture
    def temp_db_file(self):
        """创建临时数据库文件"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".db", delete=False) as f:
            temp_path = f.name

        yield temp_path

        # 清理 - 删除数据库文件及其WAL文件
        for ext in ["", "-wal", "-shm"]:
            file_path = temp_path + ext
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except PermissionError:
                    # 文件可能仍被占用，忽略错误
                    pass

    @pytest.fixture
    def storage_manager(self, temp_db_file):
        """创建存储管理器实例"""
        # 重置单例
        StorageManager._instance = None

        manager = StorageManager.__new__(StorageManager)
        manager.db_path = temp_db_file
        manager._init_db()
        manager._initialized = True

        yield manager

        # 清理
        StorageManager._instance = None

    # ==================== 存储操作测试 ====================

    def test_set_simple_value(self, storage_manager):
        """测试设置简单值"""
        # 执行
        result = storage_manager.set("simple_key", "simple_value")

        # 验证
        assert result is True
        value = storage_manager.get("simple_key")
        assert value == "simple_value"

    def test_set_integer_value(self, storage_manager):
        """测试设置整数"""
        result = storage_manager.set("int_key", 42)

        assert result is True
        value = storage_manager.get("int_key")
        assert value == 42

    def test_set_boolean_value(self, storage_manager):
        """测试设置布尔值"""
        result = storage_manager.set("bool_key", True)

        assert result is True
        value = storage_manager.get("bool_key")
        assert value is True

    def test_set_dict_value(self, storage_manager):
        """测试设置字典"""
        test_dict = {"key1": "value1", "key2": "value2"}
        result = storage_manager.set("dict_key", test_dict)

        assert result is True
        value = storage_manager.get("dict_key")
        assert value == test_dict

    def test_set_list_value(self, storage_manager):
        """测试设置列表"""
        test_list = [1, 2, 3, 4, 5]
        result = storage_manager.set("list_key", test_list)

        assert result is True
        value = storage_manager.get("list_key")
        assert value == test_list

    def test_get_with_default(self, storage_manager):
        """测试获取值（带默认值）"""
        # 执行（键不存在）
        value = storage_manager.get("nonexistent_key", "default_value")

        # 验证
        assert value == "default_value"

    def test_get_existing_key(self, storage_manager):
        """测试获取已存在的键"""
        # 先设置
        storage_manager.set("existing_key", "existing_value")

        # 获取（不带默认值）
        value = storage_manager.get("existing_key")

        # 验证
        assert value == "existing_value"

    def test_overwrite_value(self, storage_manager):
        """测试覆盖已存在的值"""
        # 设置初始值
        storage_manager.set("overwrite_key", "old_value")

        # 覆盖
        storage_manager.set("overwrite_key", "new_value")

        # 验证
        value = storage_manager.get("overwrite_key")
        assert value == "new_value"

    # ==================== 批量操作测试 ====================

    def test_set_multi(self, storage_manager):
        """测试批量设置"""
        items = {"key1": "value1", "key2": "value2", "key3": "value3"}

        # 执行
        result = storage_manager.set_multi(items)

        # 验证
        assert result is True
        assert storage_manager.get("key1") == "value1"
        assert storage_manager.get("key2") == "value2"
        assert storage_manager.get("key3") == "value3"

    def test_get_multi(self, storage_manager):
        """测试批量获取"""
        # 先设置多个值
        storage_manager.set_multi(
            {"key1": "value1", "key2": "value2", "key3": "value3"}
        )

        # 执行
        result = storage_manager.get_multi(["key1", "key2", "key3"])

        # 验证
        assert result["key1"] == "value1"
        assert result["key2"] == "value2"
        assert result["key3"] == "value3"

    def test_get_multi_partial(self, storage_manager):
        """测试批量获取（部分键不存在）"""
        # 设置部分值
        storage_manager.set("key1", "value1")
        storage_manager.set("key2", "value2")

        # 执行（包含不存在的键）
        result = storage_manager.get_multi(["key1", "key2", "key3"])

        # 验证
        assert result["key1"] == "value1"
        assert result["key2"] == "value2"
        assert "key3" not in result

    def test_delete_single_key(self, storage_manager):
        """测试删除单个键"""
        # 先设置
        storage_manager.set("delete_key", "value")

        # 执行
        result = storage_manager.delete("delete_key")

        # 验证
        assert result is True
        value = storage_manager.get("delete_key", "default")
        assert value == "default"

    def test_delete_multi(self, storage_manager):
        """测试批量删除"""
        # 先设置多个值
        storage_manager.set_multi(
            {"key1": "value1", "key2": "value2", "key3": "value3"}
        )

        # 执行
        result = storage_manager.delete_multi(["key1", "key2"])

        # 验证
        assert result is True
        assert storage_manager.get("key1", "default") == "default"
        assert storage_manager.get("key2", "default") == "default"
        assert storage_manager.get("key3") == "value3"  # key3应该还在

    def test_clear_all(self, storage_manager):
        """测试清空所有存储"""
        # 设置多个值
        storage_manager.set_multi({"key1": "value1", "key2": "value2"})

        # 执行
        result = storage_manager.clear()

        # 验证
        assert result is True
        assert storage_manager.get("key1", "default") == "default"
        assert storage_manager.get("key2", "default") == "default"

    def test_get_all_keys(self, storage_manager):
        """测试获取所有键"""
        # 设置多个值
        storage_manager.set_multi(
            {"key1": "value1", "key2": "value2", "key3": "value3"}
        )

        # 执行
        keys = storage_manager.get_all_keys()

        # 验证
        assert len(keys) == 3
        assert "key1" in keys
        assert "key2" in keys
        assert "key3" in keys

    # ==================== 事务测试 ====================

    def test_transaction_success(self, storage_manager):
        """测试成功事务"""
        # 执行事务
        with storage_manager.transaction():
            storage_manager.set("tx_key1", "tx_value1")
            storage_manager.set("tx_key2", "tx_value2")

        # 验证
        assert storage_manager.get("tx_key1") == "tx_value1"
        assert storage_manager.get("tx_key2") == "tx_value2"

    def test_transaction_rollback(self, storage_manager):
        """测试事务回滚"""
        # 设置初始值
        storage_manager.set("key1", "original_value1")

        # 执行失败的事务
        try:
            with storage_manager.transaction():
                storage_manager.set("key1", "modified_value1")
                storage_manager.set("key2", "modified_value2")
                raise Exception("Transaction failed")
        except Exception:
            pass

        # 验证（应该回滚）
        assert storage_manager.get("key1") == "original_value1"
        assert storage_manager.get("key2", "default") == "default"

    def test_transaction_nested(self, storage_manager):
        """测试嵌套事务"""
        # 外层事务
        with storage_manager.transaction():
            storage_manager.set("outer_key", "outer_value")

            # 内层事务
            with storage_manager.transaction():
                storage_manager.set("inner_key", "inner_value")

        # 验证
        assert storage_manager.get("outer_key") == "outer_value"
        assert storage_manager.get("inner_key") == "inner_value"

    # ==================== 属性访问测试 ====================

    def test_getattr(self, storage_manager):
        """测试属性访问获取值"""
        # 设置值
        storage_manager.set("attr_key", "attr_value")

        # 执行
        value = storage_manager.attr_key

        # 验证
        assert value == "attr_value"

    def test_setattr(self, storage_manager):
        """测试属性访问设置值"""
        # 执行
        storage_manager.new_attr_key = "new_attr_value"

        # 验证
        value = storage_manager.get("new_attr_key")
        assert value == "new_attr_value"

    def test_getattr_nonexistent(self, storage_manager):
        """测试访问不存在的属性"""
        # 执行并验证抛出异常
        with pytest.raises(AttributeError):
            _ = storage_manager.nonexistent_key

    # ==================== 错误处理测试 ====================

    def test_get_before_initialization(self):
        """测试初始化前获取值"""
        # 重置单例
        StorageManager._instance = None

        # 创建未初始化的管理器
        manager = StorageManager.__new__(StorageManager)
        manager._initialized = False

        # 执行（应该返回默认值）
        value = manager.get("any_key", "default")

        # 验证
        assert value == "default"

    def test_set_before_initialization(self):
        """测试初始化前设置值"""
        # 重置单例
        StorageManager._instance = None

        # 创建未初始化的管理器
        manager = StorageManager.__new__(StorageManager)
        manager._initialized = False

        # 执行（应该失败）
        result = manager.set("any_key", "any_value")

        # 验证
        assert result is False

    def test_handle_invalid_json(self, storage_manager):
        """测试处理无效JSON数据"""
        # 直接插入无效JSON到数据库
        with sqlite3.connect(storage_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
                ("invalid_json", "{invalid json"),
            )
            conn.commit()

        # Mock logger
        with patch("ErisPulse.Core.logger.logger") as mock_logger:
            # 执行（应该处理错误）
            value = storage_manager.get("invalid_json")

            # 验证
            # 应该返回原始字符串而不是解析后的对象
            assert value == "{invalid json"

    # ==================== 单例模式测试 ====================

    def test_singleton_pattern(self):
        """测试单例模式"""
        # 重置单例
        StorageManager._instance = None

        # 创建多个实例
        manager1 = StorageManager()
        manager2 = StorageManager()

        # 验证
        assert manager1 is manager2

    # ==================== 嵌套键测试 ====================

    def test_nested_key_get_simple(self, storage_manager):
        """测试简单的嵌套键获取"""
        # 先设置嵌套对象
        storage_manager.set("user", {"name": "Alice", "age": 25})

        # 获取嵌套值
        name = storage_manager.get("user.name")
        age = storage_manager.get("user.age")

        # 验证
        assert name == "Alice"
        assert age == 25

    def test_nested_key_get_deep(self, storage_manager):
        """测试深层嵌套键获取"""
        # 设置深层嵌套对象
        storage_manager.set(
            "config", {"app": {"settings": {"theme": "dark", "language": "en"}}}
        )

        # 获取深层嵌套值
        theme = storage_manager.get("config.app.settings.theme")
        language = storage_manager.get("config.app.settings.language")

        # 验证
        assert theme == "dark"
        assert language == "en"

    def test_nested_key_get_with_default(self, storage_manager):
        """测试嵌套键获取（带默认值）"""
        # 设置部分嵌套对象
        storage_manager.set("user", {"name": "Bob"})

        # 获取存在的嵌套键
        name = storage_manager.get("user.name")

        # 获取不存在的嵌套键（使用默认值）
        age = storage_manager.get("user.age", 30)

        # 获取完全不存在的嵌套键
        email = storage_manager.get("user.contact.email", "default@example.com")

        # 验证
        assert name == "Bob"
        assert age == 30
        assert email == "default@example.com"

    def test_nested_key_set_simple(self, storage_manager):
        """测试简单的嵌套键设置"""
        # 设置嵌套值（自动创建嵌套结构）
        storage_manager.set("user.name", "Charlie")
        storage_manager.set("user.age", 30)

        # 验证嵌套值被正确设置
        assert storage_manager.get("user.name") == "Charlie"
        assert storage_manager.get("user.age") == 30

        # 验证根对象被正确创建
        user = storage_manager.get("user")
        assert user == {"name": "Charlie", "age": 30}

    def test_nested_key_set_update_existing(self, storage_manager):
        """测试更新现有的嵌套对象"""
        # 先设置完整的嵌套对象
        storage_manager.set("user", {"name": "David", "age": 25, "city": "NYC"})

        # 更新嵌套值
        storage_manager.set("user.age", 26)
        storage_manager.set("user.country", "USA")

        # 验证更新后的值
        user = storage_manager.get("user")
        assert user == {"name": "David", "age": 26, "city": "NYC", "country": "USA"}

    def test_nested_key_set_deep(self, storage_manager):
        """测试深层嵌套键设置"""
        # 设置深层嵌套值（自动创建嵌套结构）
        storage_manager.set("config.server.port", 8080)
        storage_manager.set("config.server.host", "localhost")

        # 验证深层嵌套结构被正确创建
        config = storage_manager.get("config")
        assert config == {"server": {"port": 8080, "host": "localhost"}}

        # 验证可以获取深层嵌套值
        assert storage_manager.get("config.server.port") == 8080
        assert storage_manager.get("config.server.host") == "localhost"

    def test_nested_key_set_update_deep(self, storage_manager):
        """测试更新深层嵌套对象"""
        # 先设置深层嵌套对象
        storage_manager.set("app", {"ui": {"theme": "light", "fontSize": 14}})

        # 更新深层嵌套值
        storage_manager.set("app.ui.theme", "dark")
        storage_manager.set("app.ui.fontFamily", "Arial")

        # 验证更新后的值
        app = storage_manager.get("app")
        assert app == {"ui": {"theme": "dark", "fontSize": 14, "fontFamily": "Arial"}}

    def test_nested_key_delete_simple(self, storage_manager):
        """测试删除简单的嵌套键"""
        # 设置嵌套对象
        storage_manager.set("user", {"name": "Eve", "age": 28, "city": "London"})

        # 删除嵌套键
        result = storage_manager.delete("user.age")

        # 验证删除成功
        assert result is True
        user = storage_manager.get("user")
        assert user == {"name": "Eve", "city": "London"}

        # 验证被删除的键不存在
        assert storage_manager.get("user.age", "default") == "default"

    def test_nested_key_delete_deep(self, storage_manager):
        """测试删除深层嵌套键"""
        # 设置深层嵌套对象
        storage_manager.set(
            "config",
            {
                "database": {
                    "host": "localhost",
                    "port": 5432,
                    "credentials": {"username": "admin", "password": "secret"},
                }
            },
        )

        # 删除深层嵌套键
        result = storage_manager.delete("config.database.credentials.password")

        # 验证删除成功
        assert result is True
        config = storage_manager.get("config")
        assert config == {
            "database": {
                "host": "localhost",
                "port": 5432,
                "credentials": {"username": "admin"},
            }
        }

    def test_nested_key_delete_root(self, storage_manager):
        """测试删除根键"""
        # 设置嵌套对象
        storage_manager.set("temp", {"data": "value"})

        # 删除根键
        result = storage_manager.delete("temp")

        # 验证删除成功
        assert result is True
        assert storage_manager.get("temp", "default") == "default"

    def test_nested_key_delete_nonexistent(self, storage_manager):
        """测试删除不存在的嵌套键"""
        # 设置嵌套对象
        storage_manager.set("user", {"name": "Frank"})

        # 删除不存在的嵌套键
        result = storage_manager.delete("user.nonexistent.field")

        # 验证删除失败
        assert result is False

        # 验证原始数据未受影响
        user = storage_manager.get("user")
        assert user == {"name": "Frank"}

    def test_nested_key_list_operations(self, storage_manager):
        """测试嵌套键在列表中的操作"""
        # 设置包含列表的嵌套对象
        storage_manager.set("data", {"items": ["item1", "item2", "item3"]})

        # 获取列表中的元素（通过索引）
        item1 = storage_manager.get("data.items.0")
        item2 = storage_manager.get("data.items.1")

        # 验证
        assert item1 == "item1"
        assert item2 == "item2"

    def test_nested_key_numeric_segment_as_dict_key(self, storage_manager):
        """测试纯数字段应作为字典键而非列表索引（OOM 回归测试）"""
        # 模拟 QQ 群号等大数字 ID 作为嵌套键路径的一段
        # 修复前：会误判为数组索引，分配 ~7GB 内存导致 OOM Kill
        storage_manager.set("QvQChat.groups.871684833", {"enable_ai": True})

        # 验证值被正确写入为字典的字符串键
        assert storage_manager.get("QvQChat.groups.871684833") == {"enable_ai": True}

        # 验证中间层是字典而非列表
        groups = storage_manager.get("QvQChat.groups")
        assert isinstance(groups, dict)
        assert "871684833" in groups

        # 验证可以继续在同一节点下设置其他键
        storage_manager.set("QvQChat.groups.871684833.name", "测试群")
        assert storage_manager.get("QvQChat.groups.871684833.name") == "测试群"

    def test_nested_key_numeric_segment_multiple(self, storage_manager):
        """测试多个连续数字段均作为字典键"""
        storage_manager.set("app.nodes.123.456.789", "value")
        assert storage_manager.get("app.nodes.123.456.789") == "value"

        nodes = storage_manager.get("app.nodes")
        assert isinstance(nodes, dict)
        assert isinstance(nodes["123"], dict)
        assert isinstance(nodes["123"]["456"], dict)

    def test_nested_key_existing_list_index_set_within_limit(self, storage_manager):
        """测试对已存在的列表进行合理范围内的索引设置"""
        storage_manager.set("data", {"items": ["a", "b", "c"]})

        # 在已有列表范围内通过索引写入
        storage_manager.set("data.items.1", "updated")
        assert storage_manager.get("data.items.1") == "updated"
        assert storage_manager.get("data.items") == ["a", "updated", "c"]

    def test_nested_key_list_index_safety_limit(self, storage_manager):
        """测试超大索引不会导致内存爆炸（安全限制）"""
        storage_manager.set("data", {"items": [1, 2, 3]})

        # 对已有列表使用超大索引应被安全拒绝，不触发内存分配
        result = storage_manager.set("data.items.999999999", "boom")
        assert result is True  # set 操作本身成功，但内部跳过了危险写入
        assert storage_manager.get("data.items") == [1, 2, 3]

    def test_nested_key_mixed_operations(self, storage_manager):
        """测试混合的嵌套键操作"""
        # 设置初始嵌套结构
        storage_manager.set(
            "app", {"version": "1.0.0", "features": {"auth": True, "logging": False}}
        )

        # 获取嵌套值
        assert storage_manager.get("app.version") == "1.0.0"
        assert storage_manager.get("app.features.auth") is True

        # 更新嵌套值
        storage_manager.set("app.features.logging", True)
        storage_manager.set("app.features.cache", True)

        # 删除嵌套值
        storage_manager.delete("app.features.auth")

        # 验证最终状态
        app = storage_manager.get("app")
        assert app == {"version": "1.0.0", "features": {"logging": True, "cache": True}}

    def test_backward_compatibility(self, storage_manager):
        """测试向后兼容性"""
        # 测试带点的键名仍然可以作为简单键使用
        storage_manager.set("simple.key.with.dots", "value")

        # 验证可以作为简单键获取
        assert storage_manager.get("simple.key.with.dots") == "value"

        # 设置一个对象
        storage_manager.set("object", {"key": "value"})

        # 验证可以获取整个对象
        obj = storage_manager.get("object")
        assert obj == {"key": "value"}

        # 验证可以获取嵌套值
        assert storage_manager.get("object.key") == "value"

    def test_nested_key_overwrite_simple_value(self, storage_manager):
        """测试嵌套键覆盖非嵌套值"""
        # 先设置一个简单值
        storage_manager.set("config", "simple_value")
        assert storage_manager.get("config") == "simple_value"

        # 使用嵌套键设置，应该覆盖为嵌套对象
        storage_manager.set("config.timeout", 30)

        # 验证现在变成了嵌套对象
        config = storage_manager.get("config")
        assert config == {"timeout": 30}
        assert storage_manager.get("config.timeout") == 30


# ==================== 全局存储实例测试 ====================


class TestGlobalStorage:
    """全局存储实例测试"""

    @pytest.fixture(autouse=True)
    def reset_global_storage(self):
        """重置全局存储"""
        # 保存原始实例
        original_instance = StorageManager._instance
        original_db_path = None

        if original_instance and hasattr(original_instance, "db_path"):
            original_db_path = original_instance.db_path

        # 重置单例
        StorageManager._instance = None

        yield

        # 恢复
        StorageManager._instance = original_instance

    def test_global_storage_exists(self):
        """测试全局存储实例存在"""
        assert storage is not None
        assert isinstance(storage, StorageManager)

    def test_global_storage_singleton(self):
        """测试全局存储是单例"""
        from ErisPulse.Core.storage import storage as storage1
        from ErisPulse.Core.storage import storage as storage2

        # 验证
        assert storage1 is storage2


# ==================== 错误日志验证测试 ====================


class TestStorageErrorLogging:
    """验证原先静默吞异常的写操作失败时现在会产出 logger.error/trace 日志"""

    @pytest.fixture
    def storage_manager(self, tmp_path):
        """创建一个可用的存储管理器实例"""
        StorageManager._instance = None
        manager = StorageManager.__new__(StorageManager)
        manager.db_path = str(tmp_path / "test.db")
        manager._init_db()
        manager._initialized = True
        yield manager
        StorageManager._instance = None

    def _force_conn_failure(self, manager):
        """返回一个总是抛异常的 _get_connection patch 上下文"""
        return patch.object(
            type(manager),
            "_get_connection",
            side_effect=sqlite3.OperationalError("forced failure"),
        )

    def test_set_multi_failure_logs_error(self, storage_manager):
        """set_multi 失败时应记录 logger.error"""
        with (
            self._force_conn_failure(storage_manager),
            patch("ErisPulse.Core.storage.logger") as mock_logger,
        ):
            result = storage_manager.set_multi({"a": 1})
        assert result is False
        mock_logger.error.assert_called_once()

    def test_delete_failure_logs_error(self, storage_manager):
        """delete 失败时应记录 logger.error"""
        storage_manager.set("temp.key", 1)
        with (
            self._force_conn_failure(storage_manager),
            patch("ErisPulse.Core.storage.logger") as mock_logger,
        ):
            result = storage_manager.delete("temp.key")
        assert result is False
        mock_logger.error.assert_called_once()

    def test_delete_multi_failure_logs_error(self, storage_manager):
        """delete_multi 失败时应记录 logger.error"""
        storage_manager.set("temp.k1", 1)
        with (
            self._force_conn_failure(storage_manager),
            patch("ErisPulse.Core.storage.logger") as mock_logger,
        ):
            result = storage_manager.delete_multi(["temp.k1"])
        assert result is False
        mock_logger.error.assert_called_once()

    def test_clear_failure_logs_error(self, storage_manager):
        """clear 失败时应记录 logger.error"""
        storage_manager.set("temp.key", 1)
        with (
            self._force_conn_failure(storage_manager),
            patch("ErisPulse.Core.storage.logger") as mock_logger,
        ):
            result = storage_manager.clear()
        assert result is False
        mock_logger.error.assert_called_once()

    def test_has_table_failure_logs_error(self, storage_manager):
        """HasTable 失败时应记录 logger.error"""
        with (
            self._force_conn_failure(storage_manager),
            patch("ErisPulse.Core.storage.logger") as mock_logger,
        ):
            result = storage_manager.HasTable("nope")
        assert result is False
        mock_logger.error.assert_called_once()
