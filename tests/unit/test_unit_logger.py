"""
日志管理单元测试

测试Logger和LoggerChild的日志记录、模块级别控制、文件输出等功能
"""

import pytest
import logging
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock

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
    
    def test_debug_logging_filtered(self, temp_logger, caplog):
        """测试DEBUG日志被过滤"""
        # 设置INFO级别（DEBUG会被过滤）
        temp_logger.set_level("INFO")
        
        # 执行
        with caplog.at_level(logging.DEBUG):
            temp_logger.debug("This should be filtered")
        
        # 验证
        assert not any("This should be filtered" in record.message for record in caplog.records)
    
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
        temp_logger._save_in_memory("TestModule", "Test message")
        
        # 验证
        assert "TestModule" in temp_logger._logs
        assert len(temp_logger._logs["TestModule"]) == 1
        assert "Test message" in temp_logger._logs["TestModule"][0]
    
    def test_memory_limit_enforcement(self, temp_logger):
        """测试内存限制执行"""
        # 设置限制为5
        temp_logger.set_memory_limit(5)
        
        # 记录10条日志
        for i in range(10):
            temp_logger._save_in_memory("TestModule", f"Message {i}")
        
        # 验证（应该只保留最后5条）
        assert len(temp_logger._logs["TestModule"]) == 5
        assert "Message 9" in temp_logger._logs["TestModule"][-1]
    
    # ==================== 文件输出测试 ====================
    
    def test_set_output_file(self, temp_logger):
        """测试设置输出文件"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            temp_file = f.name
        
        try:
            # 执行
            result = temp_logger.set_output_file(temp_file)
            
            # 验证
            assert result is True
            assert temp_logger._file_handler is not None
        finally:
            # 清理 - 先关闭handler再删除文件
            if temp_logger._file_handler:
                temp_logger._logger.removeHandler(temp_logger._file_handler)
                temp_logger._file_handler.close()
                temp_logger._file_handler = None
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
            
            # 清理 - 关闭handler
            if temp_logger._file_handler:
                temp_logger._logger.removeHandler(temp_logger._file_handler)
                temp_logger._file_handler.close()
                temp_logger._file_handler = None
    
    def test_save_logs(self, temp_logger):
        """测试保存日志到文件"""
        # 添加一些内存日志
        temp_logger._save_in_memory("TestModule", "Test message 1")
        temp_logger._save_in_memory("TestModule", "Test message 2")
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            temp_file = f.name
        
        try:
            # 执行
            result = temp_logger.save_logs(temp_file)
            
            # 验证
            assert result is True
            assert os.path.exists(temp_file)
            
            # 验证文件内容
            with open(temp_file, 'r', encoding='utf-8') as f:
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
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
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
        temp_logger._save_in_memory("Module1", "Message 1")
        temp_logger._save_in_memory("Module2", "Message 2")
        temp_logger._save_in_memory("Module1", "Message 3")
        
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
        assert any("Child warning message" in record.message for record in caplog.records)
    
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
        assert any("Child critical message" in record.message for record in caplog.records)
    
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
