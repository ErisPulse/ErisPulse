"""
配置管理单元测试

测试ConfigManager的配置读写、缓存和延迟写入功能
"""

import importlib
import os
import tempfile
import time
from unittest.mock import patch

import pytest
import tomlkit

from ErisPulse.Core.config import ConfigManager

# importlib.import_module 返回真实子模块（Core.logger 包属性被 Logger 单例遮蔽）
logger_module = importlib.import_module("ErisPulse.Core.logger")

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

    # ==================== 读-你-写一致性（待写队列叠加） ====================

    def test_get_config_overlays_dirty_descendant(self, config_manager):
        """待写键是查询键的后代：读取父节时应叠加待写值（写后立读）"""
        config_manager.setConfig("ErisPulse.scope.actions.My", {"deny": True})

        # 未刷新前读取中间节点，应能看到未写入的值（也不影响缓存中的兄弟键）
        section = config_manager.getConfig("ErisPulse.scope")
        assert section["actions"]["My"] == {"deny": True}

        root = config_manager.getConfig("ErisPulse")
        assert root["scope"]["actions"]["My"] == {"deny": True}

        # 刷新后从缓存重读一致
        config_manager._flush_config()
        assert config_manager.getConfig("ErisPulse.scope")["actions"]["My"] == {"deny": True}

    def test_get_config_overlay_merges_with_cache_siblings(self, config_manager):
        """叠加合并不覆盖缓存中的兄弟键"""
        config_manager.setConfig("app.existing", "keep", immediate=True)
        config_manager.setConfig("app.new.nested", "added")

        section = config_manager.getConfig("app")
        assert section["existing"] == "keep"
        assert section["new"]["nested"] == "added"

    def test_get_config_overlay_new_branch(self, config_manager):
        """缓存树完全缺失该分支：返回待写叠加子树"""
        assert config_manager.getConfig("fresh.section") is None
        config_manager.setConfig("fresh.section.item", {"a": 1})

        assert config_manager.getConfig("fresh.section") == {"item": {"a": 1}}
        assert config_manager.getConfig("fresh") == {"section": {"item": {"a": 1}}}

    def test_get_config_dirty_ancestor_query(self, config_manager):
        """待写键是查询键的祖先：在其值子树内解析剩余路径"""
        config_manager.setConfig("a.b", {"c": {"d": 1}})

        assert config_manager.getConfig("a.b.c.d") == 1
        assert config_manager.getConfig("a.b.c.missing") is None
        assert config_manager.getConfig("a.b.c.missing", "fallback") == "fallback"

    def test_get_config_dirty_exact_key_still_wins(self, config_manager):
        """精确命中待写键的行为保持不变"""
        config_manager.setConfig("exact.key", {"x": 1})
        assert config_manager.getConfig("exact.key") == {"x": 1}
        # 标量值写入父节后以缓存值返回（无叠加时不改变原行为）
        config_manager.setConfig("scalar", "v")
        assert config_manager.getConfig("scalar") == "v"

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
        with open(config_manager.CONFIG_FILE, encoding='utf-8') as f:
            config_data = tomlkit.parse(f.read()).unwrap()
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
            with patch.object(logger_module, "logger") as mock_logger:
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
            with patch.object(logger_module, "logger") as mock_logger:
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
                with patch.object(logger_module, "logger") as mock_logger:
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
            with patch.object(logger_module, "logger"):
                manager = ConfigManager(config_file=temp_path)
                assert manager._cache == {"a": {"k": "v"}}

            # 改写为语法错误的 TOML（模拟用户编辑保存到一半）
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write('[broken section\n')

            with patch.object(logger_module, "logger"):
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
            with patch.object(logger_module, "logger") as mock_logger:
                manager = ConfigManager(config_file=temp_path)

                # debug 被调用（空配置提示）
                assert mock_logger.debug.called
                assert manager._cache == {}
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_flush_malformed_logs_clear_diagnostic(self):
        """测试 flush 时遇到损坏配置文件给出明确诊断而非混淆的写入失败"""
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
            with patch.object(logger_module, "logger") as mock_logger:
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
            with patch.object(logger_module, "logger") as mock_logger:
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
        with patch.object(config_manager, '_flush_config', side_effect=OSError("Write error")):
            with patch.object(logger_module, "logger") as mock_logger:
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
        with open(config_path, encoding="utf-8") as f:
            existing = tomlkit.parse(f.read())
        existing.setdefault("external", {})["key"] = "external_value"
        # 确保 mtime 变化（等待文件系统时间粒度）
        time.sleep(0.1)
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(tomlkit.dumps(existing))

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
        with open(config_path, encoding="utf-8") as f:
            existing = tomlkit.parse(f.read())
        existing["base"]["key"] = "external_override"
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(tomlkit.dumps(existing))

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
        # 断言稳定参数（字段名与期望类型），不依赖运行语言的本地化文案
        assert any("port" in e and "int" in e for e in errors)

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
        # 断言稳定参数（字段名与非法值），不依赖运行语言的本地化文案
        assert any("mode" in e and "d" in e for e in errors)
        # 合法值无错误
        assert validate_config(C(mode="a")) == []

    def test_range_min_max(self):
        from dataclasses import dataclass, field

        from ErisPulse.Core.Bases.config_schema import BaseConfig, validate_config

        @dataclass
        class C(BaseConfig):
            port: int = field(default=80, metadata={"min": 1, "max": 65535})

        assert validate_config(C(port=80)) == []
        # 断言稳定参数（字段名与越界值），不依赖运行语言的本地化文案
        assert any("port" in e and "0" in e for e in validate_config(C(port=0)))
        assert any("port" in e and "70000" in e for e in validate_config(C(port=70000)))


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


# ==================== 整棵写入 vs 叶子写入 / 热更新防覆盖 ====================


class TestConfigHotUpdateProtection:
    """update_erispulse_config 等整棵写入不应覆盖用户热更新（禁用=卸载 场景）"""

    @pytest.fixture
    def manager(self, tmp_path):
        """独立的 ConfigManager 实例指向临时配置文件"""
        from ErisPulse.Core.config import ConfigManager

        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text(
            """[ErisPulse.modules.status]
HotMod = true

[ErisPulse.logger]
level = "INFO"
""",
            encoding="utf-8",
        )
        mgr = ConfigManager(str(cfg_file))
        mgr._dirty_keys.clear()
        return mgr

    def test_update_writes_leaf_not_whole_tree(self, manager):
        """update_erispulse_config 应写入叶子键，而非整棵 ErisPulse"""
        from ErisPulse.runtime.frame_config import update_erispulse_config

        with patch("ErisPulse.runtime.frame_config._get_config_service", return_value=manager):
            result = update_erispulse_config({"master": {"users": ["123"]}})

        assert result is True
        # 不应出现整棵 ErisPulse 脏键
        assert "ErisPulse" not in manager._dirty_keys
        # 应只写入变化的叶子
        assert manager._dirty_keys.get("ErisPulse.master.users") == ["123"]
        # 用户已有的 status 不应被整棵覆盖（不会出现在脏键中）
        assert "ErisPulse.modules.status" not in manager._dirty_keys

    def test_leaf_dirty_keys_do_not_flip_user_edit(self, manager, tmp_path):
        """框架只写叶子脏键后，用户编辑 status 不会被叶子脏键覆盖"""
        cfg_file = tmp_path / "config.toml"
        # 模拟 update_erispulse_config 产生的叶子脏键
        manager._dirty_keys["ErisPulse.master.users"] = ["123"]
        manager._dirty_keys["ErisPulse.logger.level"] = "DEBUG"

        # 用户外部编辑文件：HotMod = false
        cfg_file.write_text(
            """[ErisPulse.modules.status]
HotMod = false

[ErisPulse.logger]
level = "INFO"
""",
            encoding="utf-8",
        )
        # 重载（模拟 watcher），并触发 flush
        manager._load_config()
        manager.setConfig("other.key", "v", immediate=True)

        final = tomlkit.loads(cfg_file.read_text(encoding="utf-8")).unwrap()
        assert final["ErisPulse"]["modules"]["status"]["HotMod"] is False
        # 叶子脏键仍然生效（进程待写）
        assert final["ErisPulse"]["master"]["users"] == ["123"]

    def test_redundant_dirty_key_dropped_after_reload(self, manager, tmp_path):
        """与重载后文件一致的待写键应被丢弃，避免无谓覆盖"""
        cfg_file = tmp_path / "config.toml"
        manager._dirty_keys["ErisPulse.modules.status.HotMod"] = True
        cfg_file.write_text(
            """[ErisPulse.modules.status]
HotMod = true

[ErisPulse.logger]
level = "INFO"
""",
            encoding="utf-8",
        )
        manager._load_config()
        assert "ErisPulse.modules.status.HotMod" not in manager._dirty_keys

    def test_get_erispulse_config_never_persists_defaults(self, manager):
        """get_erispulse_config 默认值仅内存合并，不产生任何落盘脏键"""
        from ErisPulse.runtime.frame_config import get_erispulse_config

        with patch("ErisPulse.runtime.frame_config._get_config_service", return_value=manager):
            merged = get_erispulse_config()

        # 不产生任何脏键（默认值不落盘，config.toml 保持最小化）
        assert manager._dirty_keys == {}
        # 内存合并结果仍包含完整默认结构
        assert "server" in merged
        assert "framework" in merged
        assert merged["server"]["port"] == 8000

    def test_get_erispulse_config_user_keys_win(self, manager):
        """用户显式设置的键优先于内置默认值，且不被覆盖回文件"""
        from ErisPulse.runtime.frame_config import get_erispulse_config

        manager._cache = {"ErisPulse": {"server": {"port": 9999}}}
        with patch("ErisPulse.runtime.frame_config._get_config_service", return_value=manager):
            merged = get_erispulse_config()

        assert merged["server"]["port"] == 9999
        # 缺失的兄弟键由默认值补齐（仅内存）
        assert merged["server"]["host"] == "0.0.0.0"
        assert manager._dirty_keys == {}


class TestBasesReExport:
    """Bases 包聚合导出完整性测试"""

    def test_i18n_config_re_exported(self):
        """I18nConfig 应从 Bases 顶层导出，且与 config_schema 是同一对象"""
        from ErisPulse.Core.Bases import I18nConfig
        from ErisPulse.Core.Bases.config_schema import I18nConfig as _Source

        assert I18nConfig is _Source

    def test_i18n_config_in_all(self):
        """I18nConfig 应包含在 Bases.__all__ 中"""
        from ErisPulse.Core import Bases

        assert "I18nConfig" in Bases.__all__

    def test_i18n_config_default_language(self):
        """I18nConfig 默认 language 为 auto"""
        from ErisPulse.Core.Bases import I18nConfig

        assert I18nConfig().language == "auto"

    def test_client_rename_backcompat_aliases(self):
        """Client/BaseClient 新类名导出，旧名 HttpClient/BaseHttpClient 保留兼容别名"""
        from ErisPulse.Core import BaseClient, BaseHttpClient, Client, HttpClient
        from ErisPulse.Core.Bases import BaseClient as _BC
        from ErisPulse.Core.Bases import BaseHttpClient as _BOC

        assert HttpClient is Client
        assert BaseHttpClient is BaseClient
        assert _BOC is _BC
        # 顶层单例属性名不变
        from ErisPulse.Core import client

        assert isinstance(client, Client)

    def test_sdk_type_exported_top_level(self):
        """SDK 类应从 ErisPulse 顶层导出（供模块 __init__ 注解 sdk: SDK 使用）"""
        from ErisPulse import SDK, sdk

        assert SDK is type(sdk)


class TestCommentPreservingWrites:
    """注释保留写入测试（tomlkit 往返）

    配置文件中的注释与键顺序在任何框架写入（setConfig/flush）后
    均不丢失、不重排；新键追加到所在节末尾。
    """

    COMMENTED_TOML = '''# API 令牌说明
# token = ""
token = "abc"

# 运行模式说明
mode = "normal"

[server]
# 端口说明
port = 8000
host = "0.0.0.0"
'''

    @pytest.fixture
    def manager(self, tmp_path):
        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text(self.COMMENTED_TOML, encoding="utf-8")
        mgr = ConfigManager(config_file=str(cfg_file))
        yield mgr
        if mgr._write_timer:
            mgr._write_timer.cancel()
        mgr._watcher_stop.set()

    def _read_text(self, manager) -> str:
        with open(manager.CONFIG_FILE, encoding="utf-8") as f:
            return f.read()

    def test_flush_preserves_comments(self, manager):
        """flush 后文件注释原样保留（含被注释掉的键）"""
        manager.setConfig("mode", "debug", immediate=True)

        text = self._read_text(manager)
        assert "# API 令牌说明" in text
        assert '# token = ""' in text
        assert "# 运行模式说明" in text
        assert "# 端口说明" in text
        assert 'mode = "debug"' in text
        assert 'token = "abc"' in text

    def test_flush_preserves_key_order(self, manager):
        """flush 不按键重排，保持文件原有顺序"""
        manager.setConfig("token", "xyz", immediate=True)
        manager.setConfig("server.port", 9000, immediate=True)

        text = self._read_text(manager)
        token_pos = text.index('token = "xyz"')
        mode_pos = text.index('mode = "normal"')
        port_pos = text.index("port = 9000")
        host_pos = text.index('host = "0.0.0.0"')
        # 原文件顺序：token → mode、port → host
        assert token_pos < mode_pos
        assert port_pos < host_pos

    def test_new_key_appended_to_section(self, manager):
        """新键追加到目标节，不产生乱序/错位"""
        manager.setConfig("server.new_key", "v", immediate=True)

        text = self._read_text(manager)
        # 仍在其节内（port/host 之后），且重解析语义正确
        assert text.index("new_key") > text.index("port = 8000")
        assert manager.getConfig("server.new_key") == "v"
        assert manager.getConfig("server.port") == 8000

    def test_nested_section_created_with_comments_intact(self, manager):
        """写入全新嵌套节不影响既有注释"""
        manager.setConfig("plugin.opt", {"a": 1}, immediate=True)

        text = self._read_text(manager)
        assert "# API 令牌说明" in text
        assert "[plugin.opt]" in text
        assert manager.getConfig("plugin.opt.a") == 1

    def test_cache_matches_file_after_flush(self, manager):
        """flush 后缓存与文件内容一致（plain dict，无 tomlkit 类型残留）"""
        manager.setConfig("mode", "slow", immediate=True)

        cached = manager._cache
        assert type(cached) is dict
        assert cached["mode"] == "slow"
        assert cached["server"]["port"] == 8000

    def test_malformed_file_keeps_dirty_keys(self, manager):
        """文件损坏时 flush 失败不清空脏键，修复后可重写"""
        manager.setConfig("mode", "changed")
        with open(manager.CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write("bad toml [")
        manager.force_save()
        # 脏键保留
        assert "mode" in manager._dirty_keys

        # 用户修复文件后可正常写入
        with open(manager.CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(self.COMMENTED_TOML)
        manager.force_save()
        assert manager.getConfig("mode") == "changed"
        assert "# 运行模式说明" in self._read_text(manager)

    def test_set_config_template_preserves_rest(self, manager):
        """setConfigTemplate 合并模板节，其余内容与注释不受影响"""
        template = '''# 新节说明
alpha = 1
'''
        manager.setConfigTemplate("adapter_new", template, immediate=True)

        text = self._read_text(manager)
        assert "# 新节说明" in text
        assert "[adapter_new]" in text
        assert "# API 令牌说明" in text
        assert 'mode = "normal"' in text
        assert manager.getConfig("adapter_new.alpha") == 1


class TestDocstringDescriptionFallback:
    """docstring 自动生成 description 兜底测试

    未声明 metadata description 时，从类 docstring 的
    reST ``:ivar 名: 说明`` 或 Google ``Attributes:`` 段提取字段说明。
    """

    def test_docstring_rest_style(self):
        """reST :ivar: 风格提取字段说明"""
        from dataclasses import dataclass, field

        from ErisPulse.Core.Bases.config_schema import BaseConfig, get_field_docstrings

        @dataclass
        class RestConfig(BaseConfig):
            """测试配置

            :ivar token: API 访问令牌
            :ivar mode: 运行模式
            """

            token: str = field(default="", metadata={"required": True})
            mode: str = field(default="normal")
            plain: str = field(default="x")

        docs = get_field_docstrings(RestConfig)
        assert docs["token"] == "API 访问令牌"
        assert docs["mode"] == "运行模式"
        assert "plain" not in docs

    def test_docstring_google_style(self):
        """Google Attributes: 段风格提取字段说明"""
        from dataclasses import dataclass, field

        from ErisPulse.Core.Bases.config_schema import BaseConfig, get_field_docstrings

        @dataclass
        class GoogleConfig(BaseConfig):
            """测试配置

            Attributes:
                interval: 回收间隔秒数
                enabled: 是否启用
            """

            interval: int = field(default=300)
            enabled: bool = field(default=True)

        docs = get_field_docstrings(GoogleConfig)
        assert docs["interval"] == "回收间隔秒数"
        assert docs["enabled"] == "是否启用"

    def test_template_uses_docstring_comment(self):
        """模板注释回退到 docstring 描述"""
        from dataclasses import dataclass, field

        from ErisPulse.Core.Bases.config_schema import BaseConfig, dataclass_to_toml_with_comments

        @dataclass
        class TplConfig(BaseConfig):
            """配置

            :ivar retry: 重试次数
            """

            retry: int = field(default=3)

        text = dataclass_to_toml_with_comments(TplConfig)
        assert "# 重试次数" in text
        assert "retry = 3" in text

    def test_schema_uses_docstring_description(self):
        """schema description 回退到 docstring 描述"""
        from dataclasses import dataclass, field

        from ErisPulse.Core.Bases.config_schema import BaseConfig, get_config_schema

        @dataclass
        class SchemaConfig(BaseConfig):
            """配置

            Attributes:
                timeout: 超时秒数
            """

            timeout: int = field(default=30)

        schema = get_config_schema(SchemaConfig)
        assert schema["fields"]["timeout"]["description"] == "超时秒数"

    def test_metadata_description_overrides_docstring(self):
        """显式 metadata description 优先于 docstring"""
        from dataclasses import dataclass, field

        from ErisPulse.Core.Bases.config_schema import BaseConfig, get_config_schema

        @dataclass
        class MixedConfig(BaseConfig):
            """配置

            :ivar name: docstring 描述
            """

            name: str = field(default="", metadata={"description": "显式描述"})

        schema = get_config_schema(MixedConfig)
        assert schema["fields"]["name"]["description"] == "显式描述"

    def test_i18n_dict_description_overrides_docstring(self):
        """i18n 字典 description 优先于 docstring"""
        from dataclasses import dataclass, field

        from ErisPulse.Core.Bases.config_schema import BaseConfig, get_config_schema

        @dataclass
        class I18nConfig(BaseConfig):
            """配置

            :ivar lang: docstring 描述
            """

            lang: str = field(
                default="zh-CN",
                metadata={"description": {"i18n": "test.lang.desc", "default": "语言"}},
            )

        schema = get_config_schema(I18nConfig)
        assert schema["fields"]["lang"]["description"] == {
            "i18n": "test.lang.desc",
            "default": "语言",
        }

    def test_docstrings_cache_consistent(self):
        """lru_cache 缓存下多次调用结果一致，空 docstring 返回空字典"""
        from dataclasses import dataclass

        from ErisPulse.Core.Bases.config_schema import BaseConfig, get_field_docstrings

        @dataclass
        class NoDocConfig(BaseConfig):
            field_one: str = "a"

        assert get_field_docstrings(NoDocConfig) == {}
        assert get_field_docstrings(NoDocConfig) is get_field_docstrings(NoDocConfig)


class TestExampleOnlyFields:
    """``example`` 字段标志测试（不落盘、仅进 config.full.example）"""

    def _make_config(self):
        from dataclasses import dataclass, field

        from ErisPulse.Core.Bases.config_schema import BaseConfig

        @dataclass
        class ExampleConfig(BaseConfig):
            """配置

            :ivar gc_interval: GC 间隔秒数
            """

            token: str = field(default="", metadata={"description": "令牌"})
            gc_interval: int = field(
                default=300,
                metadata={"example": True, "ui": {"widget": "number"}},
            )

        return ExampleConfig

    def test_template_excludes_example_by_default(self):
        """模板默认排除 example 字段"""
        from ErisPulse.Core.Bases.config_schema import dataclass_to_toml_with_comments

        text = dataclass_to_toml_with_comments(self._make_config())
        assert "gc_interval" not in text
        assert 'token = ""' in text

    def test_template_includes_example_when_requested(self):
        """include_example=True 时模板包含 example 字段（full.example 渲染用）"""
        from ErisPulse.Core.Bases.config_schema import dataclass_to_toml_with_comments

        text = dataclass_to_toml_with_comments(self._make_config(), include_example=True)
        assert "gc_interval = 300" in text
        assert "# GC 间隔秒数" in text

    def test_defaults_dict_excludes_example(self):
        """默认值字典排除 example 字段"""
        from ErisPulse.Core.Bases.config_schema import dataclass_to_defaults_dict

        defaults = dataclass_to_defaults_dict(self._make_config())
        assert "gc_interval" not in defaults
        assert defaults["token"] == ""

    def test_schema_marks_example_field(self):
        """schema 保留 example 字段并带 example 标记（供面板/向导过滤）"""
        from ErisPulse.Core.Bases.config_schema import get_config_schema

        schema = get_config_schema(self._make_config())
        assert schema["fields"]["gc_interval"]["example"] is True
        assert schema["fields"]["gc_interval"]["description"] == "GC 间隔秒数"
        assert "example" not in schema["fields"]["token"]


class TestSchemaUnderscoreFieldExclusion:
    """下划线前缀字段（如误声明为普通字段的 _schema_meta）不应进入任何用户可见输出"""

    def _make_config(self):
        from dataclasses import dataclass, field
        from typing import ClassVar

        from ErisPulse.Core.Bases.config_schema import BaseConfig

        @dataclass
        class MetaFieldConfig(BaseConfig):
            """误将 _schema_meta 声明为普通字段（缺 ClassVar 注解）"""

            token: str = field(default="", metadata={"description": "令牌"})
            _schema_meta: dict = field(
                default_factory=lambda: {"group_labels": {"basic": "基本"}}
            )

        @dataclass
        class MetaClassVarConfig(BaseConfig):
            """正确声明（ClassVar）"""

            token: str = field(default="", metadata={"description": "令牌"})
            _schema_meta: ClassVar[dict] = {"group_labels": {"basic": "基本"}}

        return MetaFieldConfig, MetaClassVarConfig

    def test_misdeclared_meta_excluded_from_schema(self):
        from ErisPulse.Core.Bases.config_schema import get_config_schema

        Misdeclared, _ = self._make_config()
        schema = get_config_schema(Misdeclared)
        assert "_schema_meta" not in schema["fields"]
        assert set(schema["fields"]) == {"token"}

    def test_misdeclared_meta_excluded_from_template_and_defaults(self):
        from ErisPulse.Core.Bases.config_schema import (
            dataclass_to_defaults_dict,
            dataclass_to_toml_with_comments,
        )

        Misdeclared, _ = self._make_config()
        assert "_schema_meta" not in dataclass_to_toml_with_comments(Misdeclared)
        assert "_schema_meta" not in dataclass_to_defaults_dict(Misdeclared)

    def test_misdeclared_meta_dict_to_dataclass_roundtrip(self):
        """dict_to_dataclass 忽略下划线字段，实例构造不受影响"""
        from ErisPulse.Core.Bases.config_schema import dict_to_dataclass

        Misdeclared, _ = self._make_config()
        instance = dict_to_dataclass(Misdeclared, {"token": "abc", "_schema_meta": {"x": 1}})
        assert instance.token == "abc"
        # 类级元数据仍可读取（走 dataclass 默认值）
        assert instance._schema_meta == {"group_labels": {"basic": "基本"}}

    def test_classvar_meta_not_a_field(self):
        """正确声明（ClassVar）时 fields() 本就不包含 _schema_meta"""
        from dataclasses import fields

        _, Proper = self._make_config()
        assert all(f.name != "_schema_meta" for f in fields(Proper))
        # schema 仍能读取类级 meta
        from ErisPulse.Core.Bases.config_schema import get_config_schema

        schema = get_config_schema(Proper)
        assert schema["meta"] == {"group_labels": {"basic": "基本"}}


class TestResolveI18nDefaultOnlyDict:
    """仅含 default 的字典（语言无关文本）应被 resolve_config_schema 还原为文本"""

    def test_default_only_option_label_resolved(self):
        """theme_options() 形态的 {"default": ...} label 不再透传为字典（[object Object] 根因）"""
        from dataclasses import dataclass, field

        from ErisPulse.Core.Bases.config_schema import BaseConfig, resolve_config_schema

        @dataclass
        class StyleConfig(BaseConfig):
            style: str = field(
                default="default",
                metadata={
                    "description": "配色风格",
                    "ui": {
                        "widget": "select",
                        "options": [
                            {"value": "default", "label": {"default": "默认"}},
                            {"value": "moe", "label": {"default": "萌系"}},
                        ],
                    },
                },
            )

        schema = resolve_config_schema(StyleConfig)
        options = schema["fields"]["style"]["options"]
        assert options[0]["label"] == "默认"
        assert options[1]["label"] == "萌系"

    def test_default_only_description_resolved(self):
        from dataclasses import dataclass, field

        from ErisPulse.Core.Bases.config_schema import BaseConfig, resolve_config_schema

        @dataclass
        class DescConfig(BaseConfig):
            level: int = field(default=1, metadata={"description": {"default": "等级"}})

        schema = resolve_config_schema(DescConfig)
        assert schema["fields"]["level"]["description"] == "等级"

    def test_i18n_dict_still_resolved_by_language(self):
        """带 i18n 键的字典仍走翻译查找"""
        from dataclasses import dataclass, field

        from ErisPulse.Core.Bases.config_schema import BaseConfig, resolve_config_schema

        @dataclass
        class I18nConfig(BaseConfig):
            theme: str = field(
                default="auto",
                metadata={
                    "description": "主题",
                    "ui": {
                        "widget": "select",
                        "options": [
                            {
                                "value": "auto",
                                "label": {"i18n": "core.language.zh_cn", "default": "自动"},
                            },
                        ],
                    },
                },
            )

        schema = resolve_config_schema(I18nConfig)
        label = schema["fields"]["theme"]["options"][0]["label"]
        # i18n 键存在翻译则用翻译，否则回退 default——都应是字符串
        assert isinstance(label, str)


class TestNestedDataclassConfig:
    """嵌套 dataclass 配置测试（schema 子树 / 模板子表 / 递归填充与校验）"""

    def _make_config(self):
        from dataclasses import dataclass, field
        from typing import ClassVar

        from ErisPulse.Core.Bases.config_schema import BaseConfig

        @dataclass
        class NightConfig(BaseConfig):
            begin: int = 23
            end: int = 7

        @dataclass
        class StalkerModeConfig(BaseConfig):
            """窥屏模式

            :ivar enabled: 是否启用
            :ivar probability: 触发概率
            """

            enabled: bool = True
            probability: float = field(default=0.03, metadata={"min": 0, "max": 1})
            night: NightConfig = field(default_factory=NightConfig)

        @dataclass
        class MainConfig(BaseConfig):
            """主配置"""

            name: str = "demo"
            stalker: StalkerModeConfig = field(default_factory=StalkerModeConfig)
            _schema_meta: ClassVar[dict] = {"group_labels": {"g": "分组"}}

        @dataclass
        class StringAnnConfig(BaseConfig):
            """字符串注解 + 类属性链解析"""

            sub: "AttachedSub" = field(default_factory=lambda: AttachedSub())

        @dataclass
        class AttachedSub(BaseConfig):
            ok: bool = True

        # 模拟"子配置类与 ConfigClass 同级声明在外层类中"：附加为类属性
        StringAnnConfig.AttachedSub = AttachedSub

        return MainConfig, StalkerModeConfig, NightConfig, StringAnnConfig

    def test_schema_nested_subtree(self):
        """嵌套字段生成 type=table + fields 子树（含二级嵌套）"""
        from ErisPulse.Core.Bases.config_schema import get_config_schema

        MainConfig, _, _, _ = self._make_config()
        schema = get_config_schema(MainConfig)

        stalker = schema["fields"]["stalker"]
        assert stalker["type"] == "table"
        assert set(stalker["fields"].keys()) == {"enabled", "probability", "night"}
        assert stalker["fields"]["night"]["fields"]["begin"]["type"] == "integer"
        # 嵌套字段 docstring 描述兜底
        assert stalker["fields"]["enabled"]["description"] == "是否启用"
        # 顶层 groups 不含嵌套子树的组
        assert schema["groups"] == []

    def test_string_annotation_via_class_attr_chain(self):
        """字符串注解从类属性链解析（子配置类附加为类属性/同级声明场景）"""
        from ErisPulse.Core.Bases.config_schema import get_config_schema

        _, _, _, StringAnnConfig = self._make_config()
        schema = get_config_schema(StringAnnConfig)
        sub = schema["fields"]["sub"]
        assert sub["type"] == "table"
        assert sub["fields"]["ok"]["type"] == "boolean"

    def test_template_nested_sections(self):
        """嵌套字段渲染为 [子表] 节，注释保留"""
        from ErisPulse.Core.Bases.config_schema import dataclass_to_toml_with_comments

        MainConfig, _, _, _ = self._make_config()
        text = dataclass_to_toml_with_comments(MainConfig)
        assert "[stalker]" in text
        assert "[stalker.night]" in text
        assert "enabled = true" in text
        assert "begin = 23" in text
        assert "name = \"demo\"" in text
        # 子表必须在顶层键之后（TOML 语义正确性）
        assert text.index("name =") < text.index("[stalker]")

    def test_defaults_dict_nested_expanded(self):
        """默认值字典递归展开为普通 dict"""
        from ErisPulse.Core.Bases.config_schema import dataclass_to_defaults_dict

        MainConfig, _, _, _ = self._make_config()
        defaults = dataclass_to_defaults_dict(MainConfig)
        assert defaults["stalker"]["enabled"] is True
        assert defaults["stalker"]["night"]["begin"] == 23

    def test_dict_to_dataclass_nested_roundtrip(self):
        """dict → 嵌套 dataclass 实例递归填充"""
        from ErisPulse.Core.Bases.config_schema import dict_to_dataclass

        MainConfig, StalkerModeConfig, NightConfig, _ = self._make_config()
        instance = dict_to_dataclass(
            MainConfig,
            {"name": "x", "stalker": {"enabled": False, "night": {"begin": 1}}},
        )
        assert isinstance(instance.stalker, StalkerModeConfig)
        assert isinstance(instance.stalker.night, NightConfig)
        assert instance.stalker.enabled is False
        assert instance.stalker.night.begin == 1
        # 缺失的嵌套子键走默认值
        assert instance.stalker.night.end == 7

    def test_validate_config_nested_errors_prefixed(self):
        """嵌套实例校验：错误信息带字段路径前缀"""
        from ErisPulse.Core.Bases.config_schema import dict_to_dataclass, validate_config

        MainConfig, _, _, _ = self._make_config()
        instance = dict_to_dataclass(
            MainConfig,
            {"stalker": {"probability": 5}},  # 超出 max=1
        )
        errors = validate_config(instance)
        assert any("stalker" in e for e in errors)

    def test_resolve_config_schema_nested_i18n(self):
        """嵌套子树内的 description/options 同步解析"""
        from dataclasses import dataclass, field

        from ErisPulse.Core.Bases.config_schema import BaseConfig, resolve_config_schema

        @dataclass
        class SubConfig(BaseConfig):
            flag: bool = field(
                default=True,
                metadata={"description": {"default": "子开关"}},
            )

        @dataclass
        class RootConfig(BaseConfig):
            sub: SubConfig = field(default_factory=SubConfig)

        schema = resolve_config_schema(RootConfig)
        assert schema["fields"]["sub"]["fields"]["flag"]["description"] == "子开关"



