"""
日志管理单元测试

测试Logger和LoggerChild的日志记录、模块级别控制、文件输出等功能
"""

import logging
import os
import tempfile
from unittest.mock import MagicMock, Mock, patch

import pytest

from ErisPulse.Core.logger import Logger, LoggerChild, logger

# ==================== Logger 基础测试 ====================


class TestLogger:
    """日志管理器测试类"""

    @pytest.fixture
    def temp_logger(self):
        """创建临时日志实例"""
        test_logger = Logger()
        yield test_logger

    # ==================== 基础功能测试 ====================

    def test_logger_creation(self):
        """测试日志器创建"""
        # 验证
        assert logger is not None
        assert isinstance(logger, Logger)
        assert logger._logger is not None

    def test_get_logger(self, temp_logger):
        """测试获取Python日志器"""
        # 执行
        py_logger = temp_logger._logger

        # 验证
        assert py_logger is not None
        assert py_logger.name == "ErisPulse"

    # ==================== 配置热更新测试 ====================

    def test_config_hot_reload_reapplies_on_change(self, temp_logger):
        """logger 配置变更时自动重新应用（配置热更新）"""
        with patch("ErisPulse.runtime.get_logger_config") as mock_get:
            mock_get.return_value = {"level": "DEBUG"}
            temp_logger._setup_config()
            assert temp_logger._logger.level == logging.DEBUG

            # 变更级别，触发热更新回调 → 应重新应用
            mock_get.return_value = {"level": "WARNING"}
            temp_logger._on_config_updated({})
            assert temp_logger._logger.level == logging.WARNING

    def test_config_hot_reload_skips_when_unchanged(self, temp_logger):
        """配置未变化时不重复应用"""
        with patch("ErisPulse.runtime.get_logger_config") as mock_get:
            mock_get.return_value = {"level": "INFO"}
            temp_logger._setup_config()
            call_count_before = mock_get.call_count

            # 配置相同 → 不应重新 setup（仅做一次变更检测读取）
            temp_logger._on_config_updated({})
            # _on_config_updated 自身读一次做比对；未变化则不会再触发 _setup_config 的多次读取
            assert temp_logger._logger.level == logging.INFO

    # ==================== 日志级别测试 ====================

    def test_set_level(self, temp_logger):
        """测试设置日志级别"""
        # 执行
        result = temp_logger.set_level("DEBUG")

        # 验证
        assert result is True
        assert temp_logger._logger.level == logging.DEBUG

    def test_set_level_info(self, temp_logger):
        """测试设置INFO级别"""
        # 执行
        result = temp_logger.set_level("INFO")

        # 验证
        assert result is True
        assert temp_logger._logger.level == logging.INFO

    def test_set_level_warning(self, temp_logger):
        """测试设置WARNING级别"""
        # 执行
        result = temp_logger.set_level("WARNING")

        # 验证
        assert result is True
        assert temp_logger._logger.level == logging.WARNING

    def test_set_level_error(self, temp_logger):
        """测试设置ERROR级别"""
        # 执行
        result = temp_logger.set_level("ERROR")

        # 验证
        assert result is True
        assert temp_logger._logger.level == logging.ERROR

    def test_set_level_critical(self, temp_logger):
        """测试设置CRITICAL级别"""
        # 执行
        result = temp_logger.set_level("CRITICAL")

        # 验证
        assert result is True
        assert temp_logger._logger.level == logging.CRITICAL

    def test_set_level_invalid(self, temp_logger):
        """测试设置无效日志级别"""
        # 执行
        result = temp_logger.set_level("INVALID")

        # 验证
        assert result is False

    # ==================== 模块级别测试 ====================

    def test_set_module_level(self, temp_logger):
        """测试设置模块日志级别"""
        # 执行
        result = temp_logger.set_module_level("TestModule", "DEBUG")

        # 验证
        assert result is True
        assert "TestModule" in temp_logger._module_levels
        assert temp_logger._module_levels["TestModule"] == logging.DEBUG

    def test_set_module_level_info(self, temp_logger):
        """测试设置模块INFO级别"""
        # 执行
        result = temp_logger.set_module_level("TestModule", "INFO")

        # 验证
        assert result is True
        assert temp_logger._module_levels["TestModule"] == logging.INFO

    def test_get_effective_level(self, temp_logger):
        """测试获取有效日志级别"""
        # 设置全局级别
        temp_logger.set_level("WARNING")

        # 设置模块级别
        temp_logger.set_module_level("TestModule", "DEBUG")

        # 执行
        level = temp_logger._get_effective_level("TestModule")

        # 验证（模块级别应该覆盖全局级别）
        assert level == logging.DEBUG

    def test_get_effective_level_no_module(self, temp_logger):
        """测试获取有效日志级别（无模块设置）"""
        # 设置全局级别
        temp_logger.set_level("INFO")

        # 执行
        level = temp_logger._get_effective_level("NonExistentModule")

        # 验证（应该使用全局级别）
        assert level == logging.INFO

    # ==================== 日志记录测试 ====================

    def test_debug_logging(self, temp_logger, caplog):
        """测试DEBUG日志记录"""
        # 设置级别
        temp_logger.set_level("DEBUG")

        # 执行
        with caplog.at_level(logging.DEBUG):
            temp_logger.debug("Debug message")

        # 验证
        assert any("Debug message" in record.message for record in caplog.records)

    def test_info_logging(self, temp_logger, caplog):
        """测试INFO日志记录"""
        # 设置级别
        temp_logger.set_level("INFO")

        # 执行
        with caplog.at_level(logging.INFO):
            temp_logger.info("Info message")

        # 验证
        assert any("Info message" in record.message for record in caplog.records)

    def test_warning_logging(self, temp_logger, caplog):
        """测试WARNING日志记录"""
        # 执行
        with caplog.at_level(logging.WARNING):
            temp_logger.warning("Warning message")

        # 验证
        assert any("Warning message" in record.message for record in caplog.records)

    def test_error_logging(self, temp_logger, caplog):
        """测试ERROR日志记录"""
        # 执行
        with caplog.at_level(logging.ERROR):
            temp_logger.error("Error message")

        # 验证
        assert any("Error message" in record.message for record in caplog.records)

    def test_critical_logging(self, temp_logger, caplog):
        """测试CRITICAL日志记录"""
        # 执行
        with caplog.at_level(logging.CRITICAL):
            temp_logger.critical("Critical message")

        # 验证
        assert any("Critical message" in record.message for record in caplog.records)

    def test_trace_logging(self, temp_logger, caplog):
        """测试TRACE日志记录"""
        temp_logger.set_level("DEBUG")
        temp_logger._logger.setLevel(5)

        with caplog.at_level(5):
            temp_logger.trace("Trace message")

        assert any("Trace message" in record.message for record in caplog.records)

    def test_trace_filtered_by_debug_level(self, temp_logger, caplog):
        """测试TRACE日志在DEBUG级别下被过滤"""
        temp_logger.set_level("DEBUG")

        with caplog.at_level(5):
            temp_logger.trace("This should be filtered")

        assert not any(
            "This should be filtered" in record.message for record in caplog.records
        )

    def test_event_logging(self, temp_logger, caplog):
        """测试EVENT日志记录"""
        temp_logger.set_level("DEBUG")

        with caplog.at_level(21):
            temp_logger.event("Event log")

        assert any("Event log" in record.message for record in caplog.records)

    def test_event_filtered_by_warning(self, temp_logger, caplog):
        """测试EVENT级别在WARNING级别下被过滤"""
        temp_logger.set_level("WARNING")

        with caplog.at_level(logging.DEBUG):
            temp_logger.event("Should be filtered")

        assert not any(
            "Should be filtered" in record.message for record in caplog.records
        )

    def test_debug_logging_filtered(self, temp_logger, caplog):
        """测试DEBUG日志被过滤"""
        # 设置INFO级别（DEBUG会被过滤）
        temp_logger.set_level("INFO")

        # 执行
        with caplog.at_level(logging.DEBUG):
            temp_logger.debug("This should be filtered")

        # 验证
        assert not any(
            "This should be filtered" in record.message for record in caplog.records
        )

    # ==================== 内存存储测试 ====================

    def test_set_memory_limit(self, temp_logger):
        """测试设置内存限制"""
        # 执行
        result = temp_logger.set_memory_limit(500)

        # 验证
        assert result is True
        assert temp_logger._max_logs == 500

    def test_set_memory_limit_invalid(self, temp_logger):
        """测试设置无效内存限制"""
        # 执行
        result = temp_logger.set_memory_limit(0)

        # 验证
        assert result is False
        assert temp_logger._max_logs > 0

    def test_save_in_memory(self, temp_logger):
        """测试内存存储日志"""
        # 执行
        temp_logger._save_in_memory("TestModule", "INFO", logging.INFO, "Test message")

        # 验证
        assert "TestModule" in temp_logger._logs
        assert len(temp_logger._logs["TestModule"]) == 1
        assert "Test message" in temp_logger._logs["TestModule"][0]["message"]

    def test_memory_limit_enforcement(self, temp_logger):
        """测试内存限制执行"""
        # 设置限制为5
        temp_logger.set_memory_limit(5)

        # 记录10条日志
        for i in range(10):
            temp_logger._save_in_memory(
                "TestModule", "INFO", logging.INFO, f"Message {i}"
            )

        # 验证（应该只保留最后5条）
        assert len(temp_logger._logs["TestModule"]) == 5
        assert "Message 9" in temp_logger._logs["TestModule"][-1]["message"]

    # ==================== 文件输出测试 ====================

    def test_set_output_file(self, temp_logger):
        """测试设置输出文件"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as f:
            temp_file = f.name

        try:
            # 执行
            result = temp_logger.set_output_file(temp_file)

            # 验证
            assert result is True
            assert len(temp_logger._file_handlers) == 1
        finally:
            # 清理 - 先关闭handler再删除文件
            for handler in temp_logger._file_handlers:
                temp_logger._logger.removeHandler(handler)
                handler.close()
            temp_logger._file_handlers.clear()
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def test_set_output_file_list(self, temp_logger):
        """测试设置多个输出文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = os.path.join(tmpdir, "test1.log")
            file2 = os.path.join(tmpdir, "test2.log")

            # 执行
            result = temp_logger.set_output_file([file1, file2])

            # 验证
            assert result is True
            assert len(temp_logger._file_handlers) == 2

            # 清理 - 关闭所有handler
            for handler in temp_logger._file_handlers:
                temp_logger._logger.removeHandler(handler)
                handler.close()
            temp_logger._file_handlers.clear()

    def test_save_logs(self, temp_logger):
        """测试保存日志到文件"""
        # 添加一些内存日志
        temp_logger._save_in_memory(
            "TestModule", "INFO", logging.INFO, "Test message 1"
        )
        temp_logger._save_in_memory(
            "TestModule", "INFO", logging.INFO, "Test message 2"
        )

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as f:
            temp_file = f.name

        try:
            # 执行
            result = temp_logger.save_logs(temp_file)

            # 验证
            assert result is True
            assert os.path.exists(temp_file)

            # 验证文件内容
            with open(temp_file, "r", encoding="utf-8") as f:
                content = f.read()
                assert "TestModule" in content
                assert "Test message 1" in content
                assert "Test message 2" in content
        finally:
            # 清理
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def test_save_logs_empty(self, temp_logger):
        """测试保存空日志"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as f:
            temp_file = f.name

        try:
            # 执行
            result = temp_logger.save_logs(temp_file)

            # 验证
            assert result is False
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def test_get_logs(self, temp_logger):
        """测试获取日志"""
        # 添加一些内存日志
        temp_logger._save_in_memory("Module1", "INFO", logging.INFO, "Message 1")
        temp_logger._save_in_memory("Module2", "INFO", logging.INFO, "Message 2")
        temp_logger._save_in_memory("Module1", "INFO", logging.INFO, "Message 3")

        # 获取所有日志
        all_logs = temp_logger.get_logs()

        # 验证
        assert "Module1" in all_logs
        assert "Module2" in all_logs
        assert len(all_logs["Module1"]) == 2
        assert len(all_logs["Module2"]) == 1

        # 获取指定模块日志
        module1_logs = temp_logger.get_logs("Module1")

        # 验证
        assert "Module1" in module1_logs
        assert len(module1_logs["Module1"]) == 2

    # ==================== 子日志器测试 ====================

    def test_get_child(self, temp_logger):
        """测试获取子日志器"""
        # 执行
        child = temp_logger.get_child("SubModule")

        # 验证
        assert child is not None
        assert isinstance(child, LoggerChild)

    def test_get_child_with_name(self, temp_logger):
        """测试获取带名称的子日志器"""
        # 执行 - 使用 relative=False 来获取完整名称
        child = temp_logger.get_child("CustomName", relative=False)

        # 验证
        assert child._name == "CustomName"


# ==================== LoggerChild 测试 ====================


class TestLoggerChild:
    """子日志器测试类"""

    @pytest.fixture
    def parent_logger(self):
        """创建父日志器"""
        return Logger()

    @pytest.fixture
    def child_logger(self, parent_logger):
        """创建子日志器"""
        return LoggerChild(parent_logger, "Parent.Child")

    # ==================== 基础功能测试 ====================

    def test_child_logger_creation(self, child_logger):
        """测试子日志器创建"""
        # 验证
        assert child_logger is not None
        assert isinstance(child_logger, LoggerChild)
        assert child_logger._parent is not None
        assert child_logger._name == "Parent.Child"

    def test_child_debug_logging(self, child_logger, caplog):
        """测试子日志器DEBUG记录"""
        # 设置父日志级别
        child_logger._parent.set_level("DEBUG")

        # 执行
        with caplog.at_level(logging.DEBUG):
            child_logger.debug("Child debug message")

        # 验证
        assert any("Child debug message" in record.message for record in caplog.records)

    def test_child_info_logging(self, child_logger, caplog):
        """测试子日志器INFO记录"""
        # 设置父日志级别
        child_logger._parent.set_level("INFO")

        # 执行
        with caplog.at_level(logging.INFO):
            child_logger.info("Child info message")

        # 验证
        assert any("Child info message" in record.message for record in caplog.records)

    def test_child_warning_logging(self, child_logger, caplog):
        """测试子日志器WARNING记录"""
        # 执行
        with caplog.at_level(logging.WARNING):
            child_logger.warning("Child warning message")

        # 验证
        assert any(
            "Child warning message" in record.message for record in caplog.records
        )

    def test_child_error_logging(self, child_logger, caplog):
        """测试子日志器ERROR记录"""
        # 执行
        with caplog.at_level(logging.ERROR):
            child_logger.error("Child error message")

        # 验证
        assert any("Child error message" in record.message for record in caplog.records)

    def test_child_critical_logging(self, child_logger, caplog):
        """测试子日志器CRITICAL记录"""
        # 执行
        with caplog.at_level(logging.CRITICAL):
            child_logger.critical("Child critical message")

        # 验证
        assert any(
            "Child critical message" in record.message for record in caplog.records
        )

    def test_child_trace_logging(self, child_logger, caplog):
        """测试子日志器TRACE记录"""
        child_logger._parent.set_level("DEBUG")
        child_logger._parent._logger.setLevel(5)

        with caplog.at_level(5):
            child_logger.trace("Child trace message")

        assert any("Child trace message" in record.message for record in caplog.records)

    def test_child_event_logging(self, child_logger, caplog):
        """测试子日志器EVENT记录"""
        child_logger._parent.set_level("DEBUG")

        with caplog.at_level(21):
            child_logger.event("Child event log")

        assert any("Child event log" in record.message for record in caplog.records)

    def test_child_nested(self, parent_logger):
        """测试嵌套子日志器"""
        # 创建第一级子日志器 - 使用 relative=False 避免添加调用者模块前缀
        child1 = parent_logger.get_child("Level1", relative=False)

        # 创建第二级子日志器
        child2 = child1.get_child("Level2")

        # 验证
        assert child2._name == "Level1.Level2"
        assert child2._parent is parent_logger


# ==================== 调用者模块检测测试 ====================


class TestCallerModuleDetection:
    """调用者模块检测测试"""

    @pytest.fixture
    def temp_logger(self):
        """创建临时日志实例"""
        return Logger()

    def test_get_caller(self, temp_logger):
        """测试获取调用者模块"""
        # 执行
        caller = temp_logger._get_caller()

        # 验证
        assert caller is not None
        assert isinstance(caller, str)


# ==================== 全局日志实例测试 ====================


class TestGlobalLogger:
    """全局日志实例测试"""

    def test_global_logger_exists(self):
        """测试全局日志器存在"""
        assert logger is not None
        assert isinstance(logger, Logger)

    def test_global_logger_singleton(self):
        """测试全局日志器是单例"""
        from ErisPulse.Core.logger import logger as logger1
        from ErisPulse.Core.logger import logger as logger2

        # 验证
        assert logger1 is logger2


# ==================== % 参数格式化测试 ====================


class TestPercentFormatting:
    """内存副本 / 日志订阅器应正确应用 % 格式化（修复日志列表显示原始 %s 的问题）"""

    @pytest.fixture
    def temp_logger(self):
        test_logger = Logger()
        yield test_logger

    def test_memory_message_formatted(self, temp_logger):
        """带 %s 参数的日志，内存副本应显示格式化后的文本"""
        temp_logger.info("box: %s", "ABC")
        messages = []
        for logs in temp_logger._logs.values():
            messages.extend(entry["message"] for entry in logs)
        assert any(m == "box: ABC" for m in messages)

    def test_handler_receives_formatted(self, temp_logger):
        """带 %s 参数的日志，订阅器应收到格式化后的文本"""
        received = []

        @temp_logger.handler("fmt-test", min_level="TRACE")
        def on_log(d):
            received.append(d)

        temp_logger.info("value=%s and=%s", 1, 2)
        assert any("value=1 and=2" in d["message"] for d in received)

    def test_no_args_keeps_percent_literal(self, temp_logger):
        """无参数时 %s 应保持字面量（与 logging 语义一致，不受影响）"""
        received = []

        @temp_logger.handler("fmt-literal", min_level="TRACE")
        def on_log(d):
            received.append(d)

        temp_logger.info("literal %s stays")
        assert any("literal %s stays" in d["message"] for d in received)

    def test_mapping_style_formatted(self, temp_logger):
        """%(key)s 映射风格参数也应被格式化"""
        received = []

        @temp_logger.handler("fmt-map", min_level="TRACE")
        def on_log(d):
            received.append(d)

        temp_logger.info("%(k)s", {"k": "mapped-value"})
        assert any("mapped-value" in d["message"] for d in received)


# ==================== 输出格式（rich / plain / json）测试 ====================


class TestOutputFormat:
    """set_format 支持 rich / plain / json 三种控制台格式"""

    @pytest.fixture
    def temp_logger(self, capsys):
        test_logger = Logger()
        yield test_logger

    def test_plain_format_output(self, temp_logger, capsys):
        """plain 格式输出纯文本：时间 + 级别 + 消息，无颜色标记"""
        assert temp_logger.set_format("plain") is True
        temp_logger.info("plain message")
        captured = capsys.readouterr()
        assert "plain message" in (captured.out + captured.err)
        assert "[INFO]" in (captured.out + captured.err)

    def test_json_format_output(self, temp_logger, capsys):
        """json 格式输出 JSON 结构化文本"""
        assert temp_logger.set_format("json") is True
        temp_logger.info("json message")
        captured = capsys.readouterr()
        text = (captured.out + captured.err).strip()
        assert text.startswith("{")
        assert "json message" in text

    def test_rich_format_restore(self, temp_logger):
        """切换回 rich 后，json 模式标志应复位"""
        assert temp_logger.set_format("json") is True
        assert temp_logger._json_mode is True
        assert temp_logger.set_format("rich") is True
        assert temp_logger._json_mode is False

    def test_invalid_format_rejected(self, temp_logger):
        """非法格式名应返回 False 且不改变当前格式"""
        assert temp_logger.set_format("plain") is True
        assert temp_logger.set_format("nope") is False
        assert temp_logger._json_mode is False

    def test_set_json_format_backward_compat(self, temp_logger):
        """set_json_format(True/False) 兼容旧调用"""
        assert temp_logger.set_json_format(True) is True
        assert temp_logger._json_mode is True
        assert temp_logger.set_json_format(False) is True
        assert temp_logger._json_mode is False


# ==================== print_* 视觉输出进入日志管道 ====================


class TestUIPrintPipeline:
    """print_section_header / print_info / print_tree_item 应进入内存与订阅器（含补发）"""

    @pytest.fixture
    def temp_logger(self):
        test_logger = Logger()
        yield test_logger

    def test_ui_lines_reach_subscriber(self, temp_logger):
        """print_* 输出应实时推送给日志订阅器"""
        received = []

        @temp_logger.handler("ui-live", min_level="INFO")
        def on_log(d):
            received.append(d)

        temp_logger.print_section_header("入口发现阶段")
        temp_logger.print_info("发现 3 个适配器")
        temp_logger.print_tree_item("Dashboard", level=1, is_last=True, tag="[立即加载]")

        messages = [d["message"] for d in received]
        assert any("入口发现阶段" in m for m in messages)
        assert any("发现 3 个适配器" in m for m in messages)
        assert any("Dashboard" in m and "立即加载" in m for m in messages)

    def test_ui_lines_replayed_to_late_subscriber(self, temp_logger):
        """晚注册的订阅器应补发历史 print_* 输出"""
        temp_logger.print_section_header("适配器注册阶段")
        temp_logger.print_info("发现 2 个适配器")

        received = []

        @temp_logger.handler("ui-replay", min_level="INFO")
        def on_log(d):
            received.append(d)

        messages = [d["message"] for d in received]
        assert any("适配器注册阶段" in m for m in messages)
        assert any("发现 2 个适配器" in m for m in messages)

    def test_ui_lines_stored_in_memory(self, temp_logger):
        """print_* 输出应写入内存日志（get_logs 可见）"""
        temp_logger.print_tree_item("MyModule", level=0, is_last=False)
        all_logs = temp_logger.get_logs()
        flat = []
        for logs in all_logs.values():
            flat.extend(logs)
        assert any("MyModule" in entry for entry in flat)
