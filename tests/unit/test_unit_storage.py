"""
存储管理单元测试

测试StorageManager的键值存储和事务功能
"""

import pytest
import os
import json
import tempfile
import sqlite3
from unittest.mock import Mock, patch, MagicMock

from ErisPulse.Core.storage import StorageManager, storage


# ==================== StorageManager 基础测试 ====================

class TestStorageManager:
    """存储管理器测试类"""
    
    @pytest.fixture
    def temp_db_file(self):
        """创建临时数据库文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as f:
            temp_path = f.name
        
        yield temp_path
        
        # 清理 - 删除数据库文件及其WAL文件
        for ext in ['', '-wal', '-shm']:
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
        items = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        }
        
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
        storage_manager.set_multi({
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        })
        
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
        storage_manager.set_multi({
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        })
        
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
        storage_manager.set_multi({
            "key1": "value1",
            "key2": "value2"
        })
        
        # 执行
        result = storage_manager.clear()
        
        # 验证
        assert result is True
        assert storage_manager.get("key1", "default") == "default"
        assert storage_manager.get("key2", "default") == "default"
    
    def test_get_all_keys(self, storage_manager):
        """测试获取所有键"""
        # 设置多个值
        storage_manager.set_multi({
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        })
        
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
            cursor.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
                        ("invalid_json", "{invalid json"))
            conn.commit()
        
        # Mock logger
        with patch('ErisPulse.Core.logger.logger') as mock_logger:
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


# ==================== 全局存储实例测试 ====================

class TestGlobalStorage:
    """全局存储实例测试"""
    
    @pytest.fixture(autouse=True)
    def reset_global_storage(self):
        """重置全局存储"""
        # 保存原始实例
        original_instance = StorageManager._instance
        original_db_path = None
        
        if original_instance and hasattr(original_instance, 'db_path'):
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
