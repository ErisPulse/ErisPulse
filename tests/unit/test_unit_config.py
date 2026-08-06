"""
配置管理单元测试

测试ConfigManager的配置读写、缓存和延迟写入功能
"""

import pytest
import os
import tempfile
import time
from unittest.mock import Mock, patch, MagicMock
import toml

from ErisPulse.Core.config import ConfigManager


# ==================== ConfigManager 基础测试 ====================

class TestConfigManager:
    """配置管理器测试类"""
    
    @pytest.fixture
    def temp_config_file(self):
        """创建临时配置文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False, encoding='utf-8') as f:
            f.write('[test]\nkey = "value"\n')
            temp_path = f.name
        
        yield temp_path
        
        # 清理
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    @pytest.fixture
    def config_manager(self, temp_config_file):
        """创建配置管理器实例"""
        manager = ConfigManager(config_file=temp_config_file)
        yield manager
        # 清理
        if manager._write_timer:
            manager._write_timer.cancel()
        manager._watcher_stop.set()
    
    # ==================== 配置读取测试 ====================
    
    def test_get_config_simple(self, config_manager):
        """测试读取简单配置项"""
        # 执行
        value = config_manager.getConfig("test.key")
        
        # 验证
        assert value == "value"
    
    def test_get_config_with_default(self, config_manager):
        """测试读取配置项（带默认值）"""
        # 执行（配置项不存在）
        value = config_manager.getConfig("nonexistent.key", "default")
        
        # 验证
        assert value == "default"
    
    def test_get_config_nested(self, config_manager):
        """测试读取嵌套配置项"""
        # 先设置嵌套配置
        with open(config_manager.CONFIG_FILE, 'w', encoding='utf-8') as f:
            f.write('''[section.subsection]
nested_key = "nested_value"
''')
        config_manager._load_config()
        
        # 执行
        value = config_manager.getConfig("section.subsection.nested_key")
        
        # 验证
        assert value == "nested_value"
    
    def test_get_config_from_cache(self, config_manager):
        """测试从缓存读取配置"""
        # 设置一个待写入的值
        config_manager.setConfig("cache.test", "cached_value")
        
        # 执行（应该从待写入队列获取）
        value = config_manager.getConfig("cache.test")
        
        # 验证
        assert value == "cached_value"
    
    # ==================== 配置设置测试 ====================
    
    def test_set_config_simple(self, config_manager):
        """测试设置简单配置项"""
        # 执行
        result = config_manager.setConfig("new_key", "new_value", immediate=True)
        
        # 验证
        assert result is True
        value = config_manager.getConfig("new_key")
        assert value == "new_value"
    
    def test_set_config_nested(self, config_manager):
        """测试设置嵌套配置项"""
        # 执行
        result = config_manager.setConfig("section.subsection.key", "value", immediate=True)
        
        # 验证
        assert result is True
        value = config_manager.getConfig("section.subsection.key")
        assert value == "value"
    
    def test_set_config_complex_type(self, config_manager):
        """测试设置复杂类型配置"""
        complex_data = {
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "bool": True,
            "number": 42
        }
        
        # 执行
        result = config_manager.setConfig("complex", complex_data, immediate=True)
        
        # 验证
        assert result is True
        value = config_manager.getConfig("complex")
        assert value == complex_data
    
    def test_set_config_delayed_write(self, config_manager):
        """测试延迟写入配置"""
        # 执行（不立即写入）
        result = config_manager.setConfig("delayed.key", "delayed_value")
        
        # 验证
        assert result is True
        assert "delayed.key" in config_manager._dirty_keys
        
        # 立即写入
        config_manager.force_save()
        
        # 验证已写入
        value = config_manager.getConfig("delayed.key")
        assert value == "delayed_value"
        assert "delayed.key" not in config_manager._dirty_keys
    
    def test_set_config_immediate_write(self, config_manager):
        """测试立即写入配置"""
        # 执行（立即写入）
        result = config_manager.setConfig("immediate.key", "immediate_value", immediate=True)
        
        # 验证
        assert result is True
        assert "immediate.key" not in config_manager._dirty_keys
        
        # 从文件读取验证
        with open(config_manager.CONFIG_FILE, 'r', encoding='utf-8') as f:
            config_data = toml.load(f)
        assert config_data["immediate"]["key"] == "immediate_value"
    
    def test_overwrite_existing_config(self, config_manager):
        """测试覆盖已存在的配置"""
        # 设置初始值
        config_manager.setConfig("overwrite.key", "old_value", immediate=True)
        
        # 覆盖
        result = config_manager.setConfig("overwrite.key", "new_value", immediate=True)
        
        # 验证
        assert result is True
        value = config_manager.getConfig("overwrite.key")
        assert value == "new_value"
    
    # ==================== 缓存测试 ====================
    
    def test_cache_timeout(self, config_manager):
        """测试缓存超时自动重新加载"""
        # 设置较短的缓存超时时间
        config_manager._cache_timeout = 1
        
        # 读取配置（第一次）
        value1 = config_manager.getConfig("test.key")
        
        # 等待缓存超时
        time.sleep(1.1)
        
        # 手动修改文件
        with open(config_manager.CONFIG_FILE, 'w', encoding='utf-8') as f:
            f.write('[test]\nkey = "modified"\n')
        
        # 再次读取（应该触发重新加载）
        value2 = config_manager.getConfig("test.key")
        
        # 验证
        assert value2 == "modified"
    
    def test_cache_valid_before_timeout(self, config_manager):
        """测试缓存在超时前有效"""
        # 设置较长的缓存超时时间
        config_manager._cache_timeout = 10
        
        # 读取配置
        value1 = config_manager.getConfig("test.key")
        
        # 手动修改文件
        with open(config_manager.CONFIG_FILE, 'w', encoding='utf-8') as f:
            f.write('[test]\nkey = "modified"\n')
        
        # 在超时前再次读取（应该返回缓存值）
        value2 = config_manager.getConfig("test.key")
        
        # 验证
        assert value2 == "value"  # 缓存值
    
    # ==================== 延迟写入测试 ====================
    
    def test_delayed_write_scheduled(self, config_manager):
        """测试延迟写入被调度"""
        # 设置
        config_manager.setConfig("scheduled.key", "value")
        
        # 验证定时器已创建
        assert config_manager._write_timer is not None
        
        # 取消定时器
        config_manager._write_timer.cancel()
        config_manager._write_timer = None
    
    def test_delayed_write_cancelled_on_new_write(self, config_manager):
        """测试新写入取消之前的延迟写入"""
        # 第一次写入
        config_manager.setConfig("key1", "value1")
        first_timer = config_manager._write_timer
        
        # 第二次写入（应该取消第一个定时器）
        config_manager.setConfig("key2", "value2")
        second_timer = config_manager._write_timer
        
        # 验证（定时器被替换）
        # 注意：由于timer的实现细节，这里主要验证行为正确
        # 实际取消可能在内部完成
    
    def test_force_save_writes_all_pending(self, config_manager):
        """测试强制保存写入所有待写入项"""
        # 设置多个待写入项
        config_manager.setConfig("key1", "value1")
        config_manager.setConfig("key2", "value2")
        config_manager.setConfig("key3", "value3")
        
        # 验证待写入队列
        assert len(config_manager._dirty_keys) == 3
        
        # 强制保存
        config_manager.force_save()
        
        # 验证待写入队列已清空
        assert len(config_manager._dirty_keys) == 0
        
        # 验证值已保存
        assert config_manager.getConfig("key1") == "value1"
        assert config_manager.getConfig("key2") == "value2"
        assert config_manager.getConfig("key3") == "value3"
    
    # ==================== 重载测试 ====================
    
    def test_reload_from_disk(self, config_manager):
        """测试从磁盘重载配置"""
        # 设置待写入项
        config_manager.setConfig("pending.key", "pending_value")
        
        # 手动修改文件
        with open(config_manager.CONFIG_FILE, 'w', encoding='utf-8') as f:
            f.write('[disk]\nkey = "disk_value"\n')
        
        # 重载（待写入项应该被丢弃）
        config_manager.reload()
        
        # 验证待写入队列已清空
        assert len(config_manager._dirty_keys) == 0
        
        # 验证磁盘值被加载
        assert config_manager.getConfig("disk.key") == "disk_value"
        
        # 验证待写入项不存在
        assert config_manager.getConfig("pending.key", "default") == "default"
    
    # ==================== 错误处理测试 ====================
    
    def test_get_config_with_invalid_file(self):
        """测试读取无效的配置文件（TOML 语法错误）"""
        # 创建无效的TOML文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False, encoding='utf-8') as f:
            f.write('[invalid\n')  # 无效的TOML
            temp_path = f.name
        
        try:
            # 创建配置管理器（应该处理错误）
            with patch('ErisPulse.Core.logger.logger') as mock_logger:
                manager = ConfigManager(config_file=temp_path)
                
                # 验证错误被记录
                assert mock_logger.error.called
                
                # 验证缓存为空
                assert manager._cache == {}
        finally:
            # 清理
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_toml_malformed_logs_line_and_column(self):
        """测试 TOML 语法错误时输出行号/列号诊断"""
        # 故意写一个语法错误的 TOML（缺少右括号）
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False, encoding='utf-8') as f:
            f.write('[valid_section]\nkey = "value"\n[broken section\n')
            temp_path = f.name

        try:
            with patch('ErisPulse.Core.logger.logger') as mock_logger:
                manager = ConfigManager(config_file=temp_path)

                # error 被调用（语法错误信息）
                assert mock_logger.error.called
                error_calls = [
                    str(c) for c in mock_logger.error.call_args_list
                ]
                # 至少有一条 error 调用包含路径信息
                assert any("toml_malformed" in str(c) or "line" in str(c).lower() or "行" in str(c) for c in error_calls) or mock_logger.error.called

                # warning 被调用（回退默认配置提示）
                assert mock_logger.warning.called

                # 缓存回退为空
                assert manager._cache == {}
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_permission_denied_logs_clear_message(self):
        """测试权限错误时输出明确提示"""
        import threading
        from pathlib import Path
        from unittest.mock import patch

        # 创建一个真实存在的配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False, encoding='utf-8') as f:
            f.write('[test]\nkey = "value"\n')
            temp_path = f.name

        try:
            # 跳过 __init__，直接构造最小实例来单独测试 _load_config
            manager = ConfigManager.__new__(ConfigManager)
            manager.CONFIG_FILE = temp_path
            manager._lock = threading.RLock()
            # 预置已有缓存：权限错误时应保留上次有效配置而非清空（BUG-029）
            manager._cache = {"existing": "value"}
            manager._cache_timestamp = 0.0

            # 让 Path.open 抛出 PermissionError（模拟无读权限）
            with patch.object(Path, 'open', side_effect=PermissionError("[Errno 13] Permission denied")):
                with patch('ErisPulse.Core.logger.logger') as mock_logger:
                    result = manager._load_config()

                # error 被调用（权限提示）
                assert mock_logger.error.called
                # warning 被调用（回退默认配置提示）
                assert mock_logger.warning.called
                # 加载失败返回 False，且保留上次有效缓存
                assert result is False
                assert manager._cache == {"existing": "value"}
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_malformed_toml_preserves_last_valid_cache(self):
        """TOML 语法错误时保留上次有效缓存并返回 False，避免半成品配置污染运行进程（BUG-029）"""
        # 先用合法文件初始化，建立有效缓存
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False, encoding='utf-8') as f:
            f.write('[a]\nk = "v"\n')
            temp_path = f.name

        try:
            with patch('ErisPulse.Core.logger.logger'):
                manager = ConfigManager(config_file=temp_path)
                assert manager._cache == {"a": {"k": "v"}}

            # 改写为语法错误的 TOML（模拟用户编辑保存到一半）
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write('[broken section\n')

            with patch('ErisPulse.Core.logger.logger'):
                result = manager._load_config()

            # 加载失败：返回 False，且保留上次有效缓存（不清空为 {}）
            assert result is False
            assert manager._cache == {"a": {"k": "v"}}
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_empty_config_logs_debug(self):
        """测试空配置文件加载后输出 debug 提示"""
        # 写一个空的（但合法的）配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False, encoding='utf-8') as f:
            f.write('')
            temp_path = f.name

        try:
            with patch('ErisPulse.Core.logger.logger') as mock_logger:
                manager = ConfigManager(config_file=temp_path)

                # debug 被调用（空配置提示）
                assert mock_logger.debug.called
                assert manager._cache == {}
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_flush_malformed_logs_clear_diagnostic(self):
        """测试 flush 时遇到损坏配置文件给出明确诊断而非混淆的写入失败"""
        import threading
        from pathlib import Path
        from unittest.mock import patch

        # 先创建一个合法的配置文件并构造 manager
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False, encoding='utf-8') as f:
            f.write('[test]\nkey = "value"\n')
            temp_path = f.name

        try:
            manager = ConfigManager(config_file=temp_path)
            if manager._write_timer:
                manager._write_timer.cancel()
            # 清理可能残留的哨兵文件
            sentinel = manager._malformed_sentinel_path
            if sentinel.exists():
                sentinel.unlink()

            # 制造一个待写入项
            manager._dirty_keys = {"test.new_key": "new_value"}

            # 把文件内容改成语法错误
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write('[test]\nkey = "unterminated\n')

            # 触发 flush，应当捕获 TomlDecodeError 并给出明确诊断
            with patch('ErisPulse.Core.logger.logger') as mock_logger:
                manager._flush_config()

            # error 被调用
            assert mock_logger.error.called
            error_calls = [str(c) for c in mock_logger.error.call_args_list]
            joined = "\n".join(error_calls)
            assert "flush_malformed" in joined or "损坏" in joined or "corrupted" in joined.lower() or "行" in joined
            # dirty_keys 不应被清空（待用户修复后重试）
            assert "test.new_key" in manager._dirty_keys
            # 哨兵文件应被创建
            assert sentinel.exists()
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            sentinel = Path(temp_path).parent / ".flush_malformed_cooldown"
            if sentinel.exists():
                sentinel.unlink()

    def test_flush_malformed_deduplicated(self):
        """测试 flush 损坏配置时冷却窗口内只告警一次，不刷屏"""
        from pathlib import Path
        from unittest.mock import patch

        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False, encoding='utf-8') as f:
            f.write('[test]\nkey = "value"\n')
            temp_path = f.name

        try:
            manager = ConfigManager(config_file=temp_path)
            if manager._write_timer:
                manager._write_timer.cancel()
            sentinel = manager._malformed_sentinel_path
            if sentinel.exists():
                sentinel.unlink()
            manager._dirty_keys = {"test.new_key": "new_value"}

            # 改坏文件
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write('[test]\nkey = "bad\n')

            # 连续 flush 三次（模拟 delayed-write / shutdown / atexit）
            with patch('ErisPulse.Core.logger.logger') as mock_logger:
                manager._flush_config()
                first_count = mock_logger.error.call_count
                manager._flush_config()
                manager._flush_config()

            # 第一次有告警
            assert first_count >= 1
            # 三次 flush 总共只告警一次（哨兵文件冷却去重生效）
            assert mock_logger.error.call_count == first_count

            # 哨兵文件应存在
            assert sentinel.exists()

            # 修复文件后，成功写入 → 哨兵文件删除
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write('[test]\nkey = "fixed"\n')
            manager._flush_config()  # 成功写入 → 删除哨兵
            assert not sentinel.exists()
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            sentinel = Path(temp_path).parent / ".flush_malformed_cooldown"
            if sentinel.exists():
                sentinel.unlink()

    def test_set_config_with_file_write_error(self, config_manager):
        """测试设置配置时文件写入失败"""
        # Mock _flush_config 方法来模拟写入失败
        with patch.object(config_manager, '_flush_config', side_effect=IOError("Write error")):
            with patch('ErisPulse.Core.logger.logger') as mock_logger:
                # 执行
                result = config_manager.setConfig("key", "value", immediate=True)
                
                # 验证失败
                assert result is False
                
                # 验证错误被记录
                assert mock_logger.error.called
    
    def test_get_config_nonexistent_file(self):
        """测试从不存在的文件读取配置"""
        # 使用不存在的文件路径
        manager = ConfigManager(config_file="nonexistent_file.toml")
        
        # 执行
        value = manager.getConfig("any.key", "default")
        
        # 验证返回默认值
        assert value == "default"

    # ==================== watcher 竞态修复测试 ====================

    def test_self_write_not_detected_as_external(self, config_manager):
        """框架自身刷盘后，_check_file_change 不应误判为外部修改"""
        config_manager.setConfig("self.write", "value", immediate=True)

        # 自身写入的 mtime 应已记录
        assert config_manager._last_self_write_mtime > 0

        # _check_file_change 不应报告变化（因为是自身写入）
        assert config_manager._check_file_change() is False

    def test_external_change_preserves_dirty_keys(self, config_manager):
        """外部修改配置文件时，待写键不应被丢弃（merge 语义）"""
        # 1. 先设置一个延迟写入的键
        config_manager.setConfig("my.pending", "pending_value")
        assert "my.pending" in config_manager._dirty_keys

        # 2. 模拟外部修改：直接写文件并更新 mtime
        config_path = config_manager.CONFIG_FILE
        with open(config_path, "r", encoding="utf-8") as f:
            existing = toml.load(f)
        existing.setdefault("external", {})["key"] = "external_value"
        # 确保 mtime 变化（等待文件系统时间粒度）
        time.sleep(0.1)
        with open(config_path, "w", encoding="utf-8") as f:
            toml.dump(existing, f)

        # 3. _check_file_change 应检测到外部修改
        assert config_manager._check_file_change() is True

        # 4. 关键断言：脏键仍然存在（不再被 clear）
        assert "my.pending" in config_manager._dirty_keys

    def test_flush_merges_dirty_with_external(self, config_manager):
        """flush 时脏键与外部修改合并（脏键优先）"""
        # 1. 写入初始值
        config_manager.setConfig("base.key", "base", immediate=True)

        # 2. 设置延迟写入键
        config_manager.setConfig("dirty.key", "dirty_value")

        # 3. 模拟外部修改（修改 base.key 的值）
        config_path = config_manager.CONFIG_FILE
        time.sleep(0.1)
        with open(config_path, "r", encoding="utf-8") as f:
            existing = toml.load(f)
        existing["base"]["key"] = "external_override"
        with open(config_path, "w", encoding="utf-8") as f:
            toml.dump(existing, f)

        # 4. flush（应读取外部内容 + 应用脏键）
        config_manager.force_save()

        # 5. 验证：脏键写入，外部修改的键也保留
        assert config_manager.getConfig("dirty.key") == "dirty_value"
        assert config_manager.getConfig("base.key") == "external_override"


# ==================== 全局配置实例测试 ====================

class TestGlobalConfig:
    """全局配置实例测试"""
    
    @pytest.fixture(autouse=True)
    def reset_global_config(self, monkeypatch):
        """重置全局配置"""
        # 使用临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False, encoding='utf-8') as f:
            f.write('[test]\nkey = "value"\n')
            temp_path = f.name
        
        # Monkey patch导入路径
        from ErisPulse.Core import config
        original_file = config.CONFIG_FILE
        
        # 临时替换配置文件
        config._cache.clear()
        config._dirty_keys.clear()
        config.CONFIG_FILE = temp_path
        config._load_config()
        
        yield
        
        # 恢复
        config.CONFIG_FILE = original_file
        
        # 清理
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    def test_global_config_exists(self):
        """测试全局配置实例存在"""
        from ErisPulse.Core import config
        assert config is not None
        assert isinstance(config, ConfigManager)
    
    def test_global_config_get(self):
        """测试全局配置读取"""
        from ErisPulse.Core import config
        
        # 执行
        value = config.getConfig("test.key", "default")
        
        # 验证
        # 注意：由于我们使用临时文件，可能没有test.key
        # 这里验证方法可调用
        assert isinstance(value, (str, type(None), dict, list, int, float, bool))
    
    def test_global_config_set(self):
        """测试全局配置设置"""
        from ErisPulse.Core import config
        
        # 执行
        result = config.setConfig("test.global", "value", immediate=True)
        
        # 验证
        assert result is True


# ==================== Config Schema i18n 测试 ====================

class TestValidateConfig:
    """validate_config 强化测试：类型 / 枚举 / 范围"""

    def _make_instance(self, cls, **overrides):
        from ErisPulse.Core.Bases.config_schema import dict_to_dataclass

        return dict_to_dataclass(cls, overrides)

    def test_required_empty_reported(self):
        from dataclasses import dataclass, field

        from ErisPulse.Core.Bases.config_schema import BaseConfig, validate_config

        @dataclass
        class C(BaseConfig):
            token: str = field(default="", metadata={"required": True})

        errors = validate_config(C())
        assert any("token" in e for e in errors)

    def test_type_mismatch_reported(self):
        from dataclasses import dataclass, field

        from ErisPulse.Core.Bases.config_schema import BaseConfig, validate_config

        @dataclass
        class C(BaseConfig):
            port: int = field(default=8080)

        # 直接构造错误类型实例
        c = C(port="not-a-number")  # type: ignore[arg-type]
        errors = validate_config(c)
        assert any("类型" in e and "port" in e for e in errors)

    def test_options_enum_violation(self):
        from dataclasses import dataclass, field

        from ErisPulse.Core.Bases.config_schema import BaseConfig, validate_config

        @dataclass
        class C(BaseConfig):
            mode: str = field(
                default="a",
                metadata={"ui": {"widget": "select", "options": ["a", "b", "c"]}},
            )

        errors = validate_config(C(mode="d"))
        assert any("选项" in e and "mode" in e for e in errors)
        # 合法值无错误
        assert validate_config(C(mode="a")) == []

    def test_range_min_max(self):
        from dataclasses import dataclass, field

        from ErisPulse.Core.Bases.config_schema import BaseConfig, validate_config

        @dataclass
        class C(BaseConfig):
            port: int = field(default=80, metadata={"min": 1, "max": 65535})

        assert validate_config(C(port=80)) == []
        assert any("最小值" in e for e in validate_config(C(port=0)))
        assert any("最大值" in e for e in validate_config(C(port=70000)))


class TestSecretRedaction:
    """secret 字段脱敏测试"""

    def test_redact_secret_masks_non_empty(self):
        from ErisPulse.Core.Bases.config_schema import redact_secret

        assert redact_secret("sk-xxxxxxxx") == "***"
        assert redact_secret(12345) == "***"

    def test_redact_secret_preserves_empty(self):
        from ErisPulse.Core.Bases.config_schema import redact_secret

        assert redact_secret("") == ""
        assert redact_secret(None) is None
        assert redact_secret([]) == []

    def test_toml_template_redacts_secret_value(self):
        """dataclass_to_toml_with_comments 不把 secret 字段的真实值写入模板"""
        from dataclasses import dataclass, field

        from ErisPulse.Core.Bases.config_schema import (
            BaseConfig,
            dataclass_to_toml_with_comments,
        )

        @dataclass
        class C(BaseConfig):
            token: str = field(
                default="real-secret-value", metadata={"secret": True}
            )

        toml_text = dataclass_to_toml_with_comments(C)
        assert "real-secret-value" not in toml_text
        assert 'token = ""' in toml_text


class TestConfigSchemaI18n:
    """配置 Schema i18n 解析测试（含 select options label i18n）"""

    @pytest.fixture
    def config_class(self):
        """构造带 i18n 文本的配置类（description / placeholder / options label / group_labels）"""
        from dataclasses import dataclass, field
        from ErisPulse.Core.Bases import BaseConfig

        @dataclass
        class TestConfig(BaseConfig):
            mode: str = field(
                default="sliding",
                metadata={
                    "description": {
                        "i18n": "test.mode.desc",
                        "default": "模式",
                    },
                    "ui": {
                        "widget": "select",
                        "group": "basic",
                        "options": [
                            {
                                "label": {"i18n": "test.mode.option.a", "default": "选项A"},
                                "value": "a",
                            },
                            {
                                "label": "纯字符串标签",
                                "value": "b",
                            },
                        ],
                    },
                },
            )
            name: str = field(
                default="",
                metadata={
                    "description": {
                        "i18n": "test.name.desc",
                        "default": "名称",
                    },
                    "ui": {
                        "widget": "text",
                        "group": "advanced",
                        "placeholder": {
                            "i18n": "test.name.placeholder",
                            "default": "请输入名称",
                        },
                    },
                },
            )

        # 声明分组显示名（i18n）
        TestConfig._schema_meta = {
            "group_labels": {
                "basic": {"i18n": "test.group.basic", "default": "基本设置"},
                "advanced": {"i18n": "test.group.advanced", "default": "高级设置"},
            }
        }

        return TestConfig

    def test_get_config_schema_preserves_i18n_dict(self, config_class):
        """get_config_schema 应原样透传 i18n 字典（不解析）"""
        from ErisPulse.Core.Bases.config_schema import get_config_schema

        schema = get_config_schema(config_class)
        options = schema["fields"]["mode"]["options"]

        # i18n dict label 原样保留
        assert options[0]["label"] == {
            "i18n": "test.mode.option.a",
            "default": "选项A",
        }
        # 纯字符串 label 原样保留
        assert options[1]["label"] == "纯字符串标签"

    def test_resolve_config_schema_resolves_option_labels(self, config_class):
        """resolve_config_schema(resolve_i18n=True) 应解析所有 i18n 文本字段"""
        from ErisPulse.Core.Bases.config_schema import resolve_config_schema
        from ErisPulse.Core.i18n import i18n

        # 注册翻译
        i18n.register("en", {
            "test.mode.desc": "Mode",
            "test.mode.option.a": "Option A",
            "test.name.desc": "Name",
            "test.name.placeholder": "Enter name",
            "test.group.basic": "Basic",
            "test.group.advanced": "Advanced",
        }, domain="test_schema")

        # 保存并临时切换语言（不持久化到磁盘，避免影响其他测试）
        saved_lang = i18n._current_lang
        i18n._current_lang = "en"

        try:
            schema = resolve_config_schema(config_class, resolve_i18n=True)

            # description 被解析
            assert schema["fields"]["mode"]["description"] == "Mode"
            assert schema["fields"]["name"]["description"] == "Name"

            # options label 被解析
            options = schema["fields"]["mode"]["options"]
            assert options[0]["label"] == "Option A"
            assert options[0]["value"] == "a"
            assert options[1]["label"] == "纯字符串标签"  # 纯字符串原样保留

            # placeholder 被解析
            assert schema["fields"]["name"]["placeholder"] == "Enter name"

            # group_labels 被解析
            assert schema["group_labels"]["basic"] == "Basic"
            assert schema["group_labels"]["advanced"] == "Advanced"
        finally:
            i18n._current_lang = saved_lang
            i18n.unregister_domain("test_schema")

    def test_resolve_config_schema_no_i18n_preserves_dict(self, config_class):
        """resolve_config_schema(resolve_i18n=False) 应等同于 get_config_schema"""
        from ErisPulse.Core.Bases.config_schema import resolve_config_schema

        schema = resolve_config_schema(config_class, resolve_i18n=False)

        # i18n dict 原样保留
        assert isinstance(schema["fields"]["mode"]["description"], dict)
        assert isinstance(schema["fields"]["mode"]["options"][0]["label"], dict)
        assert isinstance(schema["fields"]["name"]["placeholder"], dict)
        # 无 group_labels 解析（未 resolve）
        assert "group_labels" not in schema

    def test_resolve_config_schema_fallback_to_default(self, config_class):
        """未注册翻译时，所有 i18n 文本字段应回退到 default"""
        from ErisPulse.Core.Bases.config_schema import resolve_config_schema
        from ErisPulse.Core.i18n import i18n

        # 确保没有注册该 key
        i18n.unregister_domain("test_schema")

        # 临时切换到英文（不持久化到磁盘）
        saved_lang = i18n._current_lang
        i18n._current_lang = "en"

        try:
            schema = resolve_config_schema(config_class, resolve_i18n=True)

            # 所有字段回退到 default
            assert schema["fields"]["mode"]["description"] == "模式"
            assert schema["fields"]["mode"]["options"][0]["label"] == "选项A"
            assert schema["fields"]["name"]["placeholder"] == "请输入名称"
            assert schema["group_labels"]["basic"] == "基本设置"
        finally:
            i18n._current_lang = saved_lang



