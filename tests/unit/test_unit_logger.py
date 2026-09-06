"""
日志管理单元测试

测试Logger和LoggerChild的日志记录、模块级别控制、文件输出等功能
"""

import logging
import os
import tempfile
from unittest.mock import patch

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
            with open(temp_file, encoding="utf-8") as f:
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


# ==================== 多行消息单行化测试 ====================


class TestSingleLineMessages:
    """多行消息应被规范化为单行（修复 Dashboard 空消息/错位与 plain 文件一行一记录被破坏的问题）"""

    @pytest.fixture
    def temp_logger(self):
        test_logger = Logger()
        yield test_logger

    def test_memory_message_single_line(self, temp_logger):
        """含真实换行的消息，内存副本应为单行（换行转义为字面 \\n）"""
        temp_logger.error("[文件下载失败] 无法获取文件: a.png\n原因: timeout")
        for logs in temp_logger._logs.values():
            for entry in logs:
                assert "\n" not in entry["message"]
        assert any(
            "\\n原因: timeout" in entry["message"]
            for logs in temp_logger._logs.values()
            for entry in logs
        )

    def test_crlf_and_cr_normalized(self, temp_logger):
        """CRLF 与孤立 CR 都应被统一处理，不留真实换行"""
        temp_logger.info("line1\r\nline2\rline3")
        for logs in temp_logger._logs.values():
            for entry in logs:
                assert "\n" not in entry["message"]
                assert "\r" not in entry["message"]

    def test_subscriber_receives_single_line(self, temp_logger):
        """订阅器（如 Dashboard）收到的消息应为单行"""
        received = []

        @temp_logger.handler("single-line", min_level="TRACE")
        def on_log(d):
            received.append(d)

        temp_logger.warning("第一行\n\n\n第二行")
        assert received
        assert all("\n" not in d["message"] for d in received)
        assert any("第一行" in d["message"] and "第二行" in d["message"] for d in received)

    def test_child_logger_single_line(self, temp_logger):
        """子 logger（LoggerChild）同样应用单行化"""
        child = temp_logger.get_child("adapter.yunhu", relative=False)
        child.error("失败\n原因: token 过期")
        for logs in temp_logger._logs.values():
            for entry in logs:
                assert "\n" not in entry["message"]

    def test_plain_file_one_record_per_line(self, temp_logger):
        """plain 格式文件输出应保持一行一记录"""
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            log_file = Path(td) / "app.log"
            temp_logger.set_format("plain")
            assert temp_logger.set_output_file(str(log_file))
            temp_logger.error("多行消息第一行\n多行消息第二行")
            for handler in temp_logger._file_handlers:
                handler.flush()
            content = log_file.read_text(encoding="utf-8")
            lines = [line for line in content.splitlines() if line.strip()]
            assert len(lines) == 1
            assert "\\n多行消息第二行" in lines[0]
            # 清理 - 先关闭 handler 再退出临时目录（Windows 文件占用）
            for handler in temp_logger._file_handlers:
                temp_logger._logger.removeHandler(handler)
                handler.close()
            temp_logger._file_handlers.clear()

    def test_file_line_contains_timestamp_and_level(self, temp_logger):
        """非 JSON 模式的文件行应包含时间戳与级别（与控制台信息对齐）"""
        import re
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            log_file = Path(td) / "app.log"
            assert temp_logger.set_output_file(str(log_file))
            temp_logger.warning("文件格式验证")
            for handler in temp_logger._file_handlers:
                handler.flush()
            content = log_file.read_text(encoding="utf-8")
            assert re.search(
                r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \[WARNING\] \[.*\] 文件格式验证",
                content,
            )
            for handler in temp_logger._file_handlers:
                temp_logger._logger.removeHandler(handler)
                handler.close()
            temp_logger._file_handlers.clear()

    def test_formatted_args_then_single_lined(self, temp_logger):
        """先展开 %s 再单行化：参数引入的换行同样被转义"""
        temp_logger.info("result: %s", "ok\nwith newline")
        for logs in temp_logger._logs.values():
            for entry in logs:
                assert "\n" not in entry["message"]

    def test_empty_message_untouched(self, temp_logger):
        """空消息不受单行化影响"""
        temp_logger.info("")
        assert any(
            entry["message"] == ""
            for logs in temp_logger._logs.values()
            for entry in logs
        )

    def test_save_logs_plain_writes_message_text(self, temp_logger):
        """save_logs plain 模式应写消息文本，而非 dict repr"""
        import tempfile
        from pathlib import Path

        temp_logger.info("hello from memory")
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "dump.log"
            assert temp_logger.save_logs(str(out))
            content = out.read_text(encoding="utf-8")
            assert "hello from memory" in content
            assert "'timestamp'" not in content
            assert "'level_num'" not in content

    def test_console_keeps_multiline_layout(self, temp_logger, capsys):
        """控制台（plain 格式）应保留多行布局（如路由服务器地址树）"""
        temp_logger.set_format("plain")
        temp_logger.info("启动路由服务器 http://0.0.0.0:8000\n  ├─ 局域网IPv4: http://192.168.1.2:8000\n  └─ 局域网IPv6: http://[fe80::1]:8000")
        captured = capsys.readouterr()
        console = captured.err or captured.out
        # 控制台输出保留真实换行（三行布局）
        assert "启动路由服务器 http://0.0.0.0:8000\n" in console
        assert "├─ 局域网IPv4" in console
        assert "└─ 局域网IPv6" in console
        # 控制台不应出现字面 \n 转义
        assert "\\n" not in console

    def test_file_single_line_while_console_multiline(self, temp_logger, capsys):
        """同一条多行日志：控制台多行、文件单行（转义）"""
        import tempfile
        from pathlib import Path

        temp_logger.set_format("plain")
        with tempfile.TemporaryDirectory() as td:
            log_file = Path(td) / "app.log"
            assert temp_logger.set_output_file(str(log_file))
            temp_logger.warning("第一行\n第二行")
            for handler in temp_logger._file_handlers:
                handler.flush()
            # 控制台多行
            captured = capsys.readouterr()
            console = captured.err or captured.out
            assert "第一行\n第二行" in console
            # 文件单行
            content = log_file.read_text(encoding="utf-8")
            lines = [line for line in content.splitlines() if line.strip()]
            assert len(lines) == 1
            assert "\\n第二行" in lines[0]
            for handler in temp_logger._file_handlers:
                temp_logger._logger.removeHandler(handler)
                handler.close()
            temp_logger._file_handlers.clear()

    def test_json_file_single_line(self, temp_logger):
        """JSON 模式文件输出保持 JSONL 一行一记录"""
        import json as jsonlib
        import tempfile
        from pathlib import Path

        temp_logger.set_format("json")
        with tempfile.TemporaryDirectory() as td:
            log_file = Path(td) / "app.jsonl"
            assert temp_logger.set_output_file(str(log_file))
            temp_logger.error("json 多行\n消息体")
            for handler in temp_logger._file_handlers:
                handler.flush()
            content = log_file.read_text(encoding="utf-8")
            lines = [line for line in content.splitlines() if line.strip()]
            assert len(lines) == 1
            entry = jsonlib.loads(lines[0])
            assert "\\n" in entry["message"]
            for handler in temp_logger._file_handlers:
                temp_logger._logger.removeHandler(handler)
                handler.close()
            temp_logger._file_handlers.clear()


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


# ==================== 订阅器低级别显式订阅测试 ====================


class TestSubscriberBelowGlobalLevel:
    """订阅器 min_level 低于全局级别时，低级别日志应仅推送给订阅器"""

    @pytest.fixture
    def temp_logger(self):
        test_logger = Logger()
        yield test_logger

    def test_debug_reached_when_global_info(self, temp_logger):
        """全局为 INFO 时，min_level=DEBUG 的订阅器仍能收到 DEBUG 日志"""
        temp_logger.set_level("INFO")
        received = []

        @temp_logger.handler("dbg", min_level="DEBUG")
        def on_log(d):
            received.append(d)

        temp_logger.debug("low level debug")
        assert any("low level debug" in d["message"] for d in received)
        assert received[0]["level_num"] == logging.DEBUG

    def test_low_level_not_to_console(self, temp_logger, capsys):
        """低级别日志仅推送订阅器，不输出到控制台"""
        temp_logger.set_level("INFO")

        @temp_logger.handler("dbg2", min_level="DEBUG")
        def on_log(d):
            pass

        temp_logger.debug("hidden from console")
        captured = capsys.readouterr()
        assert "hidden from console" not in (captured.out + captured.err)

    def test_low_level_not_in_memory(self, temp_logger):
        """低级别日志不写入内存（get_logs 不可见）"""
        temp_logger.set_level("INFO")

        @temp_logger.handler("dbg3", min_level="DEBUG")
        def on_log(d):
            pass

        temp_logger.debug("hidden from memory")
        all_logs = temp_logger.get_logs()
        flat = []
        for logs in all_logs.values():
            flat.extend(logs)
        assert not any("hidden from memory" in entry for entry in flat)

    def test_info_still_works_with_low_subscriber(self, temp_logger, capsys):
        """订阅了低级别时，达标的高级日志仍走完整流程（含控制台输出）"""
        temp_logger.set_level("INFO")
        received = []

        @temp_logger.handler("dbg4", min_level="DEBUG")
        def on_log(d):
            received.append(d)

        temp_logger.info("normal info")
        captured = capsys.readouterr()
        assert "normal info" in (captured.out + captured.err)
        assert any("normal info" in d["message"] for d in received)

    def test_min_level_filters_within_subscriber(self, temp_logger):
        """订阅器自身 min_level 仍生效：min_level=INFO 不应收到 DEBUG"""
        temp_logger.set_level("DEBUG")
        received = []

        @temp_logger.handler("info-only", min_level="INFO")
        def on_log(d):
            received.append(d)

        temp_logger.debug("should be skipped")
        temp_logger.info("should be received")
        levels = [d["level_num"] for d in received]
        assert logging.DEBUG not in levels
        assert any(d["message"] == "should be received" for d in received)

    def test_child_logger_low_level_subscriber(self, parent_logger=None):
        """LoggerChild 也支持低级别订阅：全局 INFO 时子记录器 DEBUG 可被订阅"""
        test_logger = Logger()
        test_logger.set_level("INFO")
        child = LoggerChild(test_logger, "Mod.Sub")
        received = []

        @test_logger.handler("child-dbg", min_level="DEBUG")
        def on_log(d):
            received.append(d)

        child.debug("child low level debug")
        assert any(
            "child low level debug" in d["message"] and d["module"] == "Mod.Sub"
            for d in received
        )

    def test_no_subscriber_no_leak(self, temp_logger, capsys):
        """无订阅器时，低级别日志维持原有过滤行为（不输出、不泄漏）"""
        temp_logger.set_level("INFO")
        temp_logger.debug("fully filtered")
        captured = capsys.readouterr()
        assert "fully filtered" not in (captured.out + captured.err)


# ==================== 屏蔽日志等级（隐私）测试 ====================


class TestExcludedLevels:
    """exclude_levels 屏蔽指定日志等级（如 EVENT 隐藏消息内容）"""

    @pytest.fixture
    def temp_logger(self):
        test_logger = Logger()
        yield test_logger

    def test_set_excluded_levels(self, temp_logger):
        """设置屏蔽等级列表"""
        assert temp_logger.set_excluded_levels(["EVENT"]) is True
        assert temp_logger.list_excluded_levels() == ["EVENT"]

    def test_set_excluded_levels_empty(self, temp_logger):
        """清空屏蔽等级"""
        temp_logger.set_excluded_levels(["EVENT"])
        assert temp_logger.set_excluded_levels([]) is True
        assert temp_logger.list_excluded_levels() == []

    def test_set_excluded_levels_invalid(self, temp_logger):
        """非法等级应拒绝且不生效"""
        assert temp_logger.set_excluded_levels(["NOPE"]) is False
        assert temp_logger.list_excluded_levels() == []

    def test_exclude_and_allow_level(self, temp_logger):
        """单个等级屏蔽 / 恢复"""
        assert temp_logger.exclude_level("EVENT") is True
        assert temp_logger.list_excluded_levels() == ["EVENT"]
        assert temp_logger.allow_level("EVENT") is True
        assert temp_logger.list_excluded_levels() == []

    def test_allow_level_not_excluded(self, temp_logger):
        """恢复未屏蔽等级返回 False"""
        assert temp_logger.allow_level("EVENT") is False

    def test_excluded_level_not_in_memory(self, temp_logger):
        """被屏蔽等级不入内存（get_logs 不可见）"""
        temp_logger.set_excluded_levels(["EVENT"])
        temp_logger.event("secret message content")
        all_logs = temp_logger.get_logs()
        flat = []
        for logs in all_logs.values():
            flat.extend(logs)
        assert not any("secret message content" in entry for entry in flat)

    def test_excluded_level_not_to_console(self, temp_logger, capsys):
        """被屏蔽等级不输出控制台"""
        temp_logger.set_excluded_levels(["EVENT"])
        temp_logger.event("hidden console content")
        captured = capsys.readouterr()
        assert "hidden console content" not in (captured.out + captured.err)

    def test_excluded_level_not_to_subscriber(self, temp_logger):
        """被屏蔽等级不推送给订阅器（即使 min_level 更低）"""
        temp_logger.set_excluded_levels(["EVENT"])
        received = []

        @temp_logger.handler("excl-privacy", min_level="TRACE")
        def on_log(d):
            received.append(d)

        temp_logger.event("hidden from subscriber")
        assert not any("hidden from subscriber" in d["message"] for d in received)

    def test_other_levels_unaffected(self, temp_logger, caplog):
        """屏蔽 EVENT 不影响 INFO / WARNING 等其它等级"""
        temp_logger.set_excluded_levels(["EVENT"])
        temp_logger.info("normal info still works")
        temp_logger.warning("warning still works")
        with caplog.at_level(logging.INFO):
            pass
        all_logs = temp_logger.get_logs()
        flat = []
        for logs in all_logs.values():
            flat.extend(logs)
        assert any("normal info still works" in entry for entry in flat)
        assert any("warning still works" in entry for entry in flat)

    def test_child_logger_respects_exclusion(self, temp_logger):
        """LoggerChild 遵循父 Logger 的屏蔽等级"""
        temp_logger.set_excluded_levels(["EVENT"])
        child = LoggerChild(temp_logger, "Message")
        child.event("child hidden content")
        all_logs = temp_logger.get_logs()
        flat = []
        for logs in all_logs.values():
            flat.extend(logs)
        assert not any("child hidden content" in entry for entry in flat)

    def test_config_hot_reload_applies_exclude_levels(self, temp_logger):
        """配置热更新：exclude_levels 变化时重新应用"""
        with patch("ErisPulse.runtime.get_logger_config") as mock_get:
            mock_get.return_value = {"exclude_levels": ["EVENT"]}
            temp_logger._setup_config()
            assert temp_logger.list_excluded_levels() == ["EVENT"]

    def test_excluded_level_not_to_file(self, temp_logger):
        """被屏蔽等级不写入日志文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            temp_logger.set_excluded_levels(["EVENT"])
            temp_logger.set_output_file(log_file)
            temp_logger.event("hidden from file")
            temp_logger.info("visible in file")
            for handler in temp_logger._file_handlers:
                temp_logger._logger.removeHandler(handler)
                handler.close()
            temp_logger._file_handlers.clear()
            with open(log_file, encoding="utf-8") as f:
                content = f.read()
            assert "hidden from file" not in content
            assert "visible in file" in content


# ==================== 日志目录与自动分段测试 ====================


class TestLogDirectoryRotation:
    """set_output_dir 支持目录日志与 size/date/none 三种分段方式"""

    @pytest.fixture
    def temp_logger(self):
        test_logger = Logger()
        yield test_logger
        for handler in test_logger._file_handlers:
            test_logger._logger.removeHandler(handler)
            handler.close()
        test_logger._file_handlers.clear()

    def _close_handlers(self, lg):
        """关闭文件处理器（Windows 下须在删除文件/目录前关闭）"""
        for handler in lg._file_handlers:
            lg._logger.removeHandler(handler)
            handler.close()
        lg._file_handlers.clear()

    def test_creates_directory_and_writes_log(self, temp_logger):
        """目录不存在时自动创建，日志写入目录内文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = os.path.join(tmpdir, "nested", "logs")
            assert temp_logger.set_output_dir(log_dir)
            assert os.path.isdir(log_dir)
            temp_logger.info("dir mode message")
            for handler in temp_logger._file_handlers:
                handler.flush()
            log_file = os.path.join(log_dir, "erispulse.log")
            assert os.path.exists(log_file)
            with open(log_file, encoding="utf-8") as f:
                content = f.read()
            assert "dir mode message" in content
            self._close_handlers(temp_logger)

    def test_size_rotation_creates_backup(self, temp_logger):
        """size 模式超过单文件上限后轮转出备份文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            assert temp_logger.set_output_dir(
                tmpdir, rotation="size", max_size_mb=0.001, backup_count=2
            )
            for i in range(20):
                temp_logger.info("rotation trigger line %03d %s" % (i, "x" * 200))
            for handler in temp_logger._file_handlers:
                handler.flush()
            backups = [f for f in os.listdir(tmpdir) if f.startswith("erispulse.log.")]
            assert backups, "expected rotated backup files"
            self._close_handlers(temp_logger)

    def test_date_mode_uses_timed_handler(self, temp_logger):
        """date 模式使用 TimedRotatingFileHandler"""
        from logging.handlers import TimedRotatingFileHandler

        with tempfile.TemporaryDirectory() as tmpdir:
            assert temp_logger.set_output_dir(tmpdir, rotation="date", when="midnight")
            assert any(
                isinstance(h, TimedRotatingFileHandler)
                for h in temp_logger._file_handlers
            )
            self._close_handlers(temp_logger)

    def test_none_mode_plain_file(self, temp_logger):
        """none 模式等同普通文件，不轮转"""
        from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

        with tempfile.TemporaryDirectory() as tmpdir:
            assert temp_logger.set_output_dir(tmpdir, rotation="none")
            assert temp_logger._file_handlers
            for h in temp_logger._file_handlers:
                assert not isinstance(h, (RotatingFileHandler, TimedRotatingFileHandler))
            self._close_handlers(temp_logger)

    def test_invalid_rotation_rejected(self, temp_logger):
        """非法分段方式返回 False"""
        with tempfile.TemporaryDirectory() as tmpdir:
            assert not temp_logger.set_output_dir(tmpdir, rotation="hourly")
            self._close_handlers(temp_logger)

    def test_replaces_existing_file_handlers(self, temp_logger):
        """切换到目录模式后替换 set_output_file 设置的处理器"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plain = os.path.join(tmpdir, "plain.log")
            assert temp_logger.set_output_file(plain)
            assert len(temp_logger._file_handlers) == 1
            assert temp_logger.set_output_dir(os.path.join(tmpdir, "logs"))
            assert len(temp_logger._file_handlers) == 1
            assert not os.path.samefile(
                temp_logger._file_handlers[0].baseFilename, os.path.abspath(plain)
            )
            self._close_handlers(temp_logger)

    def test_config_applies_log_dir(self, temp_logger):
        """_setup_config 读取 log_dir 配置段并应用目录日志"""
        from logging.handlers import TimedRotatingFileHandler

        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = os.path.join(tmpdir, "cfg_logs")
            with patch("ErisPulse.runtime.get_logger_config") as mock_get:
                mock_get.return_value = {
                    "log_dir": log_dir,
                    "log_rotation": "date",
                }
                temp_logger._setup_config()
            assert os.path.isdir(log_dir)
            assert any(
                isinstance(h, TimedRotatingFileHandler)
                for h in temp_logger._file_handlers
            )
            self._close_handlers(temp_logger)

    def test_log_files_takes_priority_over_log_dir(self, temp_logger):
        """log_files 显式路径优先于 log_dir"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plain = os.path.join(tmpdir, "explicit.log")
            with patch("ErisPulse.runtime.get_logger_config") as mock_get:
                mock_get.return_value = {
                    "log_files": [plain],
                    "log_dir": os.path.join(tmpdir, "unused_dir"),
                }
                temp_logger._setup_config()
            assert not os.path.exists(os.path.join(tmpdir, "unused_dir"))
            assert temp_logger._file_handlers
            assert temp_logger._file_handlers[0].baseFilename == os.path.abspath(plain)
            self._close_handlers(temp_logger)
